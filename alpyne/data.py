import logging
import pprint
import re
import sys
import typing
from collections import UserDict
from dataclasses import dataclass, InitVar
from datetime import datetime, timedelta
from math import inf
from typing import Any, Optional

import numpy as np

from alpyne.errors import NotAFieldException
from alpyne.typing import EngineSettingKeys, Number
from alpyne.constants import EngineState, TYPE_LOOKUP, DATE_PATTERN_LOOKUP
from alpyne.outputs import TimeUnits, UnitValue
from alpyne.utils import parse_number


class _SimRLSpace(UserDict):
    """ Base class describing a dictionary-type object. Subclasses should override the `SUBSCHEMA_KEY`,
            a string referring to the key to use to lookup the schema definition in the AnyLogicSim object."""
    SUBSCHEMA_KEY = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        subschema = self._schema
        for key in subschema:
            if key not in self:  # check for if this class (treated like a dict) has the field named 'key'
                # when it's missing, use the default
                self[key] = self.__missing__(key)
            elif not isinstance(self[key], subschema[key].py_type):  # check if converted to the intended type
                # TODO move these cases to decoder?
                if isinstance(self[key], str) and subschema[key].py_type in (int, float):
                    # auto-handle for when numeric types are infinity;
                    self[key] = parse_number(self[key])
                elif isinstance(self[key], (np.integer, np.floating)):
                    # ignore when value is a numpy type and `py_type` is the plain python equivalent (the latter assumed)
                    pass
                else:
                    logging.getLogger(__name__).warning(f"{self.SUBSCHEMA_KEY}.{key} = {self[key]} ({type(self[key])}) "
                                                        f"was not parsed to the expected type ({subschema[key].py_type})")

    def __missing__(self, key):
        # when a given key is not found, lookup its default value
        # or throw an error if the key is missing
        subschema = self._schema
        if key not in subschema:
            raise NotAFieldException(self.__class__, list(subschema.keys()), key)
        return subschema[key].py_value

    def __setitem__(self, key, item):
        # don't allow to set any values that aren't defined in this schema
        subschema = self._schema
        if key not in subschema:
            raise NotAFieldException(self.__class__, list(subschema.keys()), key)
        super().__setitem__(key, item)

    @property
    def _schema(self):
        from alpyne.sim import AnyLogicSim
        return getattr(AnyLogicSim.schema, self.SUBSCHEMA_KEY)


class SimConfiguration(_SimRLSpace):
    """
    A subclass of UserDict describing the desired Configuration, as defined in the RL experiment, for the sim to use when resetting.

    Usage of this class adds validation to ensure only the pre-defined fields can be set.
    """
    SUBSCHEMA_KEY = "configuration"


class SimObservation(_SimRLSpace):
    """
    A subclass of UserDict describing the received Observation, as defined in the RL experiment, received from the sim.
    """
    SUBSCHEMA_KEY = "observation"


class SimAction(_SimRLSpace):
    """
    A subclass of UserDict describing the desired Action, as defined in the RL experiment, for the sim to use when submitting an action.

    Usage of this class adds validation to ensure only the pre-defined fields can be set.
    """
    SUBSCHEMA_KEY = "action"


@dataclass
class SimStatus:
    """A report of the current simulation model's status

    :param state: The current state of the model's engine; this matches the value of what AnyLogic reports
      (e.g., from ``getEngine().getState()``)
    :param observation: A dictionary-subclass-typed object mapping field names with values,
      as defined in the RL Experiment
    :param stop: The value of the RL Experiment's "Simulation run stop condition" field;
      indicates whether the episode should be terminated (e.g., fail or success condition)
    :param sequence_id: A counter of how many actionable requests (i.e., resets + actions) have been taken
    :param episode_num: A counter of how many resets have been taken
    :param step_num: A counter of how many actions have been taken
    :param time: The model time, in the engine's set time units
    :param date: The model date
    :param progress: If the engine has a set stop time/date, this is a value between 0-1 indicating
      it's percent completion; otherwise (i.e., set to run indefinitely), this will be -1
    :param message: An informal message from the underlying Alpyne app, used to report potential reasons for the current
      state of the model; usually set when some stopping scenario has occurred. It may be None. May change in the future.
    """

    state: EngineState

    # experiment-related
    observation: SimObservation
    stop: bool
    sequence_id: int
    episode_num: int
    step_num: int

    # engine-related
    time: float
    date: datetime | int
    progress: float
    message: str | None

    def __post_init__(self):
        if isinstance(self.state, str):
            self.state = EngineState.__members__[self.state]
        if isinstance(self.date, int):
            self.date = datetime.fromtimestamp(int(self.date / 1000))
        if isinstance(self.observation, dict):
            self.observation = SimObservation(**self.observation)


@dataclass
class EngineStatus:
    """A report for the status of the underlying AnyLogic engine driving the simulation model.

    .. warning:: This object is not currently part of the public API and is intended for debugging purposes only.
      It may be refactored or removed in the future.

    :param state: The current state of the model's engine; this matches the value of what AnyLogic reports
      (e.g., from ``getEngine().getState()``)
    :param engine_events: The number of currently scheduled events in the model (both by the user and the engine)
    :param engine_steps: A counter of how many of events have been executed by the engine
    :param next_engine_step: The time (in the engine's time units) which will be after the **engine's** next ``step()``
      execution. If the model is about to finish, returns negative infinity. Special cases: in system-dynamics models
      the result may depend on the selected accuracy in system-dynamics models some conditional events may occur based
      on the value obtained from numerical solver within the step.
    :param next_engine_event: The time (in the engine's time units) of the next event scheduled
    :param time: The current model (logical) time, in the engine's time units
    :param date: The current model date
    :param progress: The progress of the simulation: the part of model time simulated so far in case the stop time
      is set, or -1 if it is not set
    :param message: An informal message from the underlying Alpyne app, used to report potential reasons for the current
      state of the model; usually set when some stopping scenario has occurred. It may be None. May change in the future.
    :param settings: A dictionary mapping the engine setting key names to the values currently in use by the model
    """
    state: EngineState

    engine_events: int
    engine_steps: int

    next_engine_step: float
    next_engine_event: float

    time: float
    date: datetime | str
    progress: float
    message: str | None

    settings: dict[EngineSettingKeys, Number | datetime | TimeUnits]


@dataclass
class FieldData:
    """
    Represents a single data element with a name, type, value, and (optional) units.

    Used to describe the space information in the schema object or basic input/output types.

    Two properties - `py_type` and `py_value` - are available to convert the Java type and value (respectively) to
    Python native equivalents (e.g., Python's `datetime.datetime` for Java's `Date` type; `UnitValue` objects for
    Outputs with a unit-type).

    :param name: The user-defined field name
    :param type: The "simple" (Java) class name
    :param value: The default value that will be used if omitted
    :param units: The AnyLogic unit type constant, when relevant (None otherwise)
    """
    name: str
    type: str
    value: Any
    units: str = None

    @property
    def py_type(self):
        # prioritize primitive lists since they also include element data type (but python doesn't care about that)
        if '[]' in self.type:
            return list
        return TYPE_LOOKUP.get(self.type, Any)

    @property
    def py_value(self):
        # special case: None value always means None value, regardless of the type (i.e., unlike Java's primitives);
        # this also suppresses type-validation errors when the default value is not explicitly set
        if self.value is None:
            return None

        if self.py_type == datetime:
            if not isinstance(self.value, str):  # as of v1.0.0, only accept strings
                raise TypeError(f"Unexpected type for value: {type(self.value)}")

            value = self.value  # don't modify original

            # handle for py < 3.12 not having '%:z' directive,
            # allowing for compatible ISO 8601 format for tz with colons
            if sys.version_info < (3, 12):
                pattern = r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{1,6}[-+])(\d+):*(\d+)*:*(\d+)*(\.\d+)*"
                match = re.match(pattern, self.value)
                if match is not None:
                    # contains the base string plus up to 4 parts of the timezone or None if it doesn't have it
                    value = ''.join(i for i in match.groups() if i is not None)

            for pat, fmt in DATE_PATTERN_LOOKUP.items():
                if re.match(pat, value):
                    return datetime.strptime(value, fmt)
            raise ValueError(f"Could not find a match for the given date pattern ({self.value})")
        if self.units is not None and isinstance(self.value, (int, float)):
            return UnitValue(self.value, self.units)
        elif isinstance(self.value, dict) and self.py_type != dict:
            # assume py_type is an analysis object type
            return self.py_type(**self.value)
        elif self.py_type in (int, float):
            return parse_number(self.value)
        elif self.py_type == TimeUnits:
            return TimeUnits[self.value]
        # assume already intended data type
        assert isinstance(self.value, self.py_type), f"Unhandled type conversion: value of type {type(self.value)} not instance of {self.py_type}"
        return self.value


@dataclass
class SimSchema:
    """ Contains information describing each of the possible data-holding objects. Each attribute is a dictionary
    mapping the field name to its data. These are provided as a reference for what's available and is not intended
    to be modified.

    :param _schema_def: A pseudo-field used only for initializing the schema
    :param inputs: Parameters of the top-level agent
    :param outputs: Analysis objects (Output, DataSet, HistogramData, etc.)
    :param configuration: Defined data fields in the *Configuration* section of the RL experiment
    :param engine_settings: Represents various engine settings (model units, random seed, start and stop time/date)
    :param observation: Defined data fields in the *Observation* section of the RL experiment
    :param action: Defined data fields in the *Action* section of the RL experiment.

    .. note:: The ``inputs`` are provided for information about the model and not currently able to be assigned (v1.0.0)

    """
    _schema_def: InitVar[dict]
    inputs: dict[str, FieldData] = None
    outputs: dict[str, FieldData] = None
    configuration: dict[str, FieldData] = None
    engine_settings: dict[str, FieldData] = None
    observation: dict[str, FieldData] = None
    action: dict[str, FieldData] = None

    def __post_init__(self, _schema_def: dict):
        def make_dict(key):
            return {data['name']: FieldData(**data) for data in _schema_def[key]}

        self.inputs = make_dict('inputs')
        self.outputs = make_dict('outputs')
        self.configuration = make_dict('configuration')
        self.engine_settings = make_dict('engine_settings')
        self.observation = make_dict('observation')
        self.action = make_dict('action')

    def __str__(self):
        pp = pprint.PrettyPrinter(indent=4, width=120, depth=2)

        def pform(obj):
            """Use PrettyPrinter's format + custom formatting to put the first container element on its own line"""
            output = pp.pformat(obj)

            # put the first key/val pair on its own line, similar to subsequent pairs;
            # an extra space is needed too to compensate for how pp formats the first entry
            output = re.sub(r"^{", r"{\n ", output)

            # put the final curly bracket on its own line
            output = re.sub(r"}$", r"\n}", output)

            return output

        out = "SimSchema\n=========\n"
        out += f"input = {pform(self.inputs)}\n"
        out += f"outputs = {pform(self.outputs)}\n"
        out += f"configuration = {pform(self.configuration)}\n"
        out += f"engine_settings = {pform(self.engine_settings)}\n"
        out += f"observation = {pform(self.observation)}\n"
        out += f"action = {pform(self.action)}\n"
        return out


class EngineSettings:
    """
    Settings to use for the underlying AnyLogic engine to run the simulation model with; contains fields for the
    time units, start/stop time/date, and RNG seed.
    """

    def __init__(self, **override_kwargs: dict[EngineSettingKeys, datetime | TimeUnits | Number | UnitValue | TimeUnits | None]):
        """
        :param override_kwargs: Desired mapping between setting name and value to override in the sim's RL experiment
        """
        from alpyne.sim import AnyLogicSim
        subschema = AnyLogicSim.schema.engine_settings
        self._using_stop_time = True
        self._stop_arg: Number | datetime = subschema['stop_time'].py_value

        # Define the initial values based on the schema
        self.units: TimeUnits = subschema['units'].py_value  # The time units used by the model and its engine
        self.start_time: Number = subschema['start_time'].py_value  # The time (in the units) to start the sim's runs at
        self.start_date: datetime = subschema['start_date'].py_value  # The date to start the sim's runs at
        self.seed: Optional[int] = subschema['seed'].py_value  # The seed for the engine's RNG; None implies random

        if override_kwargs:
            # to handle cases such as wanting to override the start time and units,
            #   make sure it's done in an order that allows conversion of start time to a number.
            if override_kwargs.get('units'):
                self.units = override_kwargs.get('units')
            # convert any times provided to numbers
            if isinstance(override_kwargs.get('start_time'), UnitValue):
                prev_val: UnitValue = override_kwargs.get('start_time')
                new_val = prev_val(self.units)
                override_kwargs['start_time'] = new_val
            if isinstance(override_kwargs.get('stop_time'), UnitValue):
                prev_val: UnitValue = override_kwargs.get('stop_time')
                new_val = prev_val(self.units)
                override_kwargs['stop_time'] = new_val
            # include validation that only correct engine settings keys are used
            valid_args = typing.get_args(EngineSettingKeys)
            for key, val in override_kwargs.items():
                if key not in valid_args:
                    raise AttributeError(f"Given engine settings key '{key}' is invalid.")
                # call setattr to enable support for the properties (i.e., 'stop_time' / 'stop_date')
                setattr(self, key, val)

    def __str__(self):
        return repr(self)

    def __repr__(self):
        t_symb = "**" if self._using_stop_time else ""
        d_symb = "" if self._using_stop_time else "**"
        return f"EngineSettings(units={self.units}, seed={self.seed}, start_time={self.start_time}, start_date={self.start_date}, {t_symb}stop_time={self.stop_time}, {d_symb}stop_date={self.stop_date})"

    @property
    def stop_time(self):
        """The time (in the units) to set the model's engine to a FINISHED state,
        preventing further events or actions from being taken."""
        if self._using_stop_time:
            return self._stop_arg
        tdelta = (self.stop_date - self.start_date).total_seconds()
        return TimeUnits.SECOND.convert_to(tdelta, self.units)

    @stop_time.setter
    def stop_time(self, new_value: Number | UnitValue):
        """Assign a time-based stop condition to the model (in its units),
        overriding the previous stop conditions, if any were set."""
        self._using_stop_time = True
        if isinstance(new_value, UnitValue):
            # convert to a number in the model's time units
            new_value = new_value.unit.convert_to(new_value.value, self.units)
        self._stop_arg = new_value

    @property
    def stop_date(self) -> datetime | None:
        """The date to set the model's engine to a FINISHED state,
        preventing further events or actions from being taken."""
        if not self._using_stop_time:
            return self._stop_arg
        if self.stop_time == inf:
            return None
        tdelta = self.units.convert_to(self.stop_time - self.start_time, TimeUnits.SECOND)
        return self.start_date + timedelta(seconds=tdelta)

    @stop_date.setter
    def stop_date(self, value: datetime):
        """
        Assign a date-based stop condition to the model, overriding the previous stop conditions, if any were set.
        """
        self._using_stop_time = False
        self._stop_arg = value
