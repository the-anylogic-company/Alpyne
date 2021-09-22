import json
import os
import tempfile
import zipfile
from collections.abc import Sequence
from datetime import datetime as dt
from datetime import time
from enum import Enum
from pathlib import Path
from typing import List, Tuple, Any
from warnings import warn

import alpyne
from alpyne.data.model_data import ModelData
from alpyne.data.spaces import RLSpace, Number


class AlpyneJSONEncoder(json.JSONEncoder):
    """
    A custom encoder to convert Alpyne classes to JSON, in a format expected by the alpyne app.

    To use it, pass a reference to the class to the `cls` argument of `json.dump` or `json.dumps`).
    For example, `json.dumps(my_object, cls=AlpyneJSONEncoder)`
    """
    def default(self, o):
        """ Overridden method to handle classes used by Alpyne. """
        if callable(o):
            return o()
        elif isinstance(o, RLSpace):
            # recursively call `default` on each of the values
            output = list(map(self.default, o._data.values()))
            return output
        elif isinstance(o, ModelData):
            return {"name": o.name, "type": o.type_, "value": o.value, "units": o.units}
        elif isinstance(o, dt):
            return o.isoformat()
        elif isinstance(o, Enum):
            return o.value
        elif isinstance(o, str):
            # format of vars for engine settings ("{NAME}") is confusing the default encoder
            return str(o)
        try:
            import numpy
            if isinstance(o, numpy.integer):
                return int(o)
            elif isinstance(o, numpy.floating):
                return float(o)
            elif isinstance(o, numpy.ndarray):
                return o.tolist()
        except:
            pass
        return super().default(o)


def _is_collection_type(o) -> bool:
    """
    Check whether the provided type/annotation is one which can hold elements. Necessarily since the minor versions
    of Python 3 have evolving ways of comparing type annotations.

    :param o: An annotation or type reference
    :return: Whether it represents a type which can hold elements
    """
    try:
        # Py3.9+
        from typing import get_origin
        cls = get_origin(o) or o
        return issubclass(cls, Sequence)
    except ImportError:
        pass

    # extract the base type if 'o' is an annotation
    cls = o if type(o) == type else o.__orig_bases__[0]
    return issubclass(cls, Sequence)


def case_insensitive_equals(name1: str, name2: str) -> bool:
    """
    Convenience method to check whether two strings match, irrespective of their case and any surrounding whitespace.
    """
    return name1.strip().lower() == name2.strip().lower()


def convert_from_string(value: str, dtype: str) -> Any:
    """
    Convenience method to handle any edge cases when converting a JSON string to an object.
    """
    if dtype == "STRING":
        return value
    return json.loads(value)


def convert_to_string(value: Any) -> str:
    """
    A convenience method to handle any edge cases when dumping an object to a JSON string.
    """
    if type(value) == str:
        return value
    return json.dumps(value)


def resolve_model_jar(model_loc: str) -> Path:
    """
    Validate the provided location of a supposed model. It handles location validation, unzipping zip files to a
    temporary directory, and other cases.

    :param model_loc: The user-specified location of their model
    :return: A (possibly updated) location of the model.jar
    :raises ValueError: If the location is ambiguous or couldn't be properly resolved
    """
    path = Path(model_loc)
    if path.is_dir():  # TODO check folder for zip/jar
        raise ValueError("Ambiguous model location. Point to a model.jar or exported zip file")

    # find path to model jar, unzipping if necessary
    if path.suffix == ".jar":
        model_jar_path = path
    elif path.suffix == ".zip":
        # [00000-99999] based on the current time of day
        day_ratio = int((dt.now() - dt.combine(dt.now().date(), time())).total_seconds() / 864 * 1000)
        tmp_dir = tempfile.mkdtemp(prefix=f"alpyne_{day_ratio:05d}_")

        warn(f"Unzipping to temporary directory ({tmp_dir})")

        with zipfile.ZipFile(path, 'r') as zip_ref:
            zip_ref.extractall(tmp_dir)
        model_jar_path = Path(tmp_dir, "model.jar")
    else:
        raise Exception("Unrecognized file type. Pass in a zip or jar file")

    return model_jar_path


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
        ds += ([x]*n)
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
    return alpyne.ROOT_PATH.joinpath("resources")


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
