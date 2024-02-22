import itertools
import json
import logging
import os
import re
import tempfile
import zipfile
from collections import namedtuple
from dataclasses import is_dataclass, asdict
from datetime import datetime as dt
from datetime import time
from enum import Enum
from math import inf
from pathlib import Path
from typing import List, Tuple, Union

import numpy as np

import alpyne
from alpyne.typing import Number


def find_jar_overlap(src1: str, src2: str):
    path1, path2 = Path(src1), Path(src2)
    jars1, jars2 = path1.rglob("*.jar"), path2.rglob("*.jar")
    lookup1 = {re.match("[^\d]+", f.name).group(): f.relative_to(path1) for f in jars1}
    lookup2 = {re.match("[^\d]+", f.name).group(): f.relative_to(path2) for f in jars2}
    overlaps = [[(v, lookup2[k]) for k, v in lookup1.items() if k in lookup2],
                [(lookup1[k], v) for k, v in lookup2.items() if k in lookup1]]
    return overlaps


def next_num(start=0, step=1):
    """
    Helper function to return a unique number every time it's called.
    Useful for easily generating unique seeds for the engine settings (e.g., `{seed=next_unique_num}`).
    The arguments only apply the first time the function is called, so changing after the first will have no effect.

    :param start: The first number to return; where counting starts
    :param step: How much to increment each time the function is called
    :return: The next updated number in the series
    """
    global __ALPYNE_COUNTER
    try:
        _ = __ALPYNE_COUNTER
    except NameError:  # not defined
        if step == 0:
            raise ValueError("Step cannot be 0")
        __ALPYNE_COUNTER = itertools.count(start, step)
    return next(__ALPYNE_COUNTER)


class AlpyneJSONEncoder(json.JSONEncoder):
    """
    A custom encoder to convert Alpyne classes to JSON, in a format expected by the alpyne app.

    To use it, pass a reference to the class to the `cls` argument of `json.dump` or `json.dumps`).
    For example, `json.dumps(my_object, cls=AlpyneJSONEncoder)`
    """

    def default(self, o):
        """ Overridden method to handle classes used by Alpyne. """

        # local import to avoid circular dependencies
        from alpyne.data import FieldData, EngineSettings, _SimRLSpace
        from alpyne.outputs import _UnitEnum

        if callable(o):
            return o()
        elif isinstance(o, _SimRLSpace):
            return dict(o)
        elif isinstance(o, EngineSettings):
            op = {"units": o.units, "start_time": o.start_time, "start_date": o.start_date, "seed": o.seed}
            # technically server can accept both, but will use whichever one is longer;
            # only pass whichever was the last thing the user set
            if o._using_stop_time:
                op["stop_time"] = o.stop_time
            else:
                op["stop_date"] = o.stop_date
            return op
        elif isinstance(o, _UnitEnum):
            return o.name
        elif is_dataclass(o):
            # recursively call `default` on each of the values
            # output = list(map(self.default, o._data.values()))
            return asdict(o)
        elif isinstance(o, FieldData):
            return {"name": o.name, "type": o.type, "value": o.value, "units": o.units}
        elif isinstance(o, dt):
            return o.isoformat()
        elif isinstance(o, Enum):
            return o.value
        try:
            if isinstance(o, np.integer):
                return int(o)
            elif isinstance(o, np.floating):
                return float(o)
            elif isinstance(o, np.ndarray):
                return o.tolist()
        except:
            pass
        return super().default(o)


class AlpyneJSONDecoder(json.JSONDecoder):
    """
    A custom decoder to convert JSON to Alpyne classes.

    To use it, pass a reference to the class to the `cls` argument of `json.load` or `json.loads`).
    For example, `json.loads(my_json_str, cls=AlpyneJSONDecoder)`
    """

    def decode(self, s, **kwargs):
        from alpyne.data import FieldData

        obj = super().decode(s, **kwargs)
        # convert dicts with known formats to their proper types
        # TODO unhandled types here may be converted elsewhere in the code; decide a final resting spot
        if isinstance(obj, dict):
            if all(key in obj for key in ('name', 'type', 'value')):
                obj = FieldData(**obj)
        return obj


def resolve_model_jar(model_loc: str) -> Tuple[Path, tempfile.TemporaryDirectory]:
    """
    Validate the provided location of a supposed model. It handles location validation, unzipping zip files to a
    temporary directory, and other cases.

    :param model_loc: The user-specified location of their model
    :return: A (possibly updated) location of the model.jar and the TemporaryDirectory object, if one was created
    :raises ValueError: If the location is ambiguous or couldn't be properly resolved
    """
    path = Path(model_loc)
    if path.is_dir():  # TODO check folder for zip/jar
        raise ValueError("Ambiguous model location. Point to a model.jar or exported zip file")

    # find path to model jar, unzipping if necessary
    temp_dir = None
    if path.suffix == ".jar":
        model_jar_path = path
    elif path.suffix == ".zip":
        # [00000-99999] based on the current time of day
        day_ratio = int((dt.now() - dt.combine(dt.now().date(), time())).total_seconds() / 864 * 1000)
        temp_dir = tempfile.TemporaryDirectory(prefix=f"alpyne_{day_ratio:05d}_")

        logging.getLogger(__name__).info(f"Unzipping to temporary directory ({temp_dir.name})")

        with zipfile.ZipFile(path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir.name)
        model_jar_path = Path(temp_dir.name, "model.jar")
    else:
        raise Exception("Unrecognized file type. Pass in a zip or jar file")

    return model_jar_path, temp_dir


def histogram_outputs_to_fake_dataset(lower_bound: float, interval_width: float, hits: List[int]) -> \
        Tuple[List[float], List[float]]:
    """
    Convert statistics from a histogram output to a format usable by plotting libraries (e.g., matplotlib).
    This recreates the histogram in a way that visually appears the same; however, it's not (necessarily)
    statistically similar.

    :param lower_bound: The start/minimum X value
    :param interval_width: How large each "bin" is
    :param hits: A list of hits in each bin
    :return: A tuple consisting of two lists - for sample data and bins - to use in a plotting library
    :example:
      >>> histogram_outputs_to_fake_dataset(-0.5, 0.1, [1, 0, 2, 4, 1])
      ([-0.5, -0.3, -0.3, -0.2, -0.2, -0.2, -0.2, -0.1], [-0.5, -0.4, -0.3, -0.2, -0.1, 0])
    """
    ds, bins = [], []
    for i, n in enumerate(hits):
        x = lower_bound + interval_width * i
        ds += ([x] * n)
        bins.append(x)
    # add one more for the closing bin
    x = lower_bound + interval_width * len(hits)
    bins.append(x)
    return ds, bins


def limit(lower: Number, value: Number, upper: Number) -> Number:
    """ Convenience function to constrain a given value between a lower and upper bound. """
    return max(lower, min(value, upper))


def get_resources_path() -> Path:
    """ Convenience method to return the `resources` directory in this project """
    return alpyne._ROOT_PATH.joinpath("resources")


def get_wildcard_paths(model_dir: str) -> List[str]:
    """ Build wildcard references to the passed directory and all sub-directories """
    paths = [os.path.join(model_dir, "*")]
    for root, folders, files in os.walk(model_dir):
        for folder in folders:
            paths.append(os.path.join(root, folder, "*"))
    return paths


def shorten_by_relativeness(paths: List[str]) -> List[str]:
    """ Update any paths where relative reference would take up less characters """
    here = os.getcwd()
    new_paths = []
    for path in paths:
        pathstr = str(path)
        alt_pathstr = os.path.relpath(pathstr, str(here))
        if len(alt_pathstr) < len(pathstr):
            new_paths.append(alt_pathstr)
        else:
            new_paths.append(pathstr)
    return new_paths


def extended_namedtuple(name, source_fields):
    assert isinstance(source_fields, list)
    new_type_fields = []
    for f in source_fields:
        try:
            new_type_fields.extend(f._fields)
        except:
            new_type_fields.append(f)
    return namedtuple(name, new_type_fields)


def parse_number(value: Union[Number, str]) -> Number:
    if isinstance(value, str):
        if value == 'Infinity':
            return inf
        elif value == '-Infinity':
            return -inf
        else:
            raise ValueError(f"Unrecognized number type: {value}")
    return value
