import re
import warnings
from collections import namedtuple
from typing import Dict, Union, List, Any

from alpyne.data.constants import TimeUnits, State
from alpyne.data.spaces import Configuration, Observation, Action

# Custom type annotations
Number = Union[int, float]

# Immutable "base" data objects
_ExperimentStatusBase = namedtuple("ExperimentStatus", "successful message observation done state sequenceId episodeNum stepNum")
_EngineStatusBase = namedtuple("EngineStatus", "successful message state time date eventCount stepCount nextStepTime nextEventTime progress settings")

# Subclassing the namedtuples
class ExperimentStatus(_ExperimentStatusBase):
    def __new__(cls, successful, message, observation, done, state, sequenceId, episodeNum, stepNum):
        observation_obj = Observation(**observation)
        state_flag = None if state is None else State[state]
        return super(ExperimentStatus, cls).__new__(cls, successful, message, observation_obj, done, state_flag, sequenceId, episodeNum, stepNum)


class EngineStatus(_EngineStatusBase):
    def __new__(cls, successful, message, state, time, date, eventCount, stepCount, nextStepTime, nextEventTime, progress, settings):
        state_flag = None if state is None else State[state]
        settings_obj = None if settings is None else EngineSettings(**settings)
        return super(EngineStatus, cls).__new__(cls, successful, message, state_flag, time, date, eventCount, stepCount, nextStepTime, nextEventTime, progress, settings_obj)



class ModelData:
    """
    Represents a single data element with a name, type, value, and (optional) units.
    Used to describe the space information in the version object or basic input/output types.
    """
    def __init__(self, name, type_, value, units=None):
        self.name = name
        self.type_ = type_
        self.units = units
        self.value = value

    def __str__(self):
        unit_suffix = "" if self.units is None else " " + self.units
        return str(self.value) + unit_suffix

    def __repr__(self):
        return f"{self.name}:{self.type_}={str(self)}"

    # def to_jsonable(self) -> Dict[str, Any]:
    #     return {"name": self.name, "type": self.type_, "value": self.value, "units": self.units}

    @staticmethod
    def from_json(data: Dict[str, Any]) -> 'ModelData':
        """
        Expands the values in a parsed JSON entry (a dictionary).

        :param data: an entry in the list of objects provided by the server (e.g., in the template)
        :return: an instance of this object, based on the data provided
        """
        return ModelData(data.get("name"),
                         data.get("type"),
                         data.get("value"),
                         data.get("units"))


class ModelVersion:
    """ Contains information describing each of the possible data-holding objects.
    These are purely provided as reference for what's available.

    - inputs: Parameters of your top-level agent.
    - outputs: Analysis objects (Output, DataSet, HistogramData, etc.) on your top-level agent.
    - configuration: Defined data fields in the *Configuration* section of the RL experiment.
    - engine_settings: Represents various engine settings (random seed, start and stop time/date).
    - observation: Defined data fields in the *Observation* section of the RL experiment.
    - action: Defined data fields in the *Action* section of the RL experiment.
    """

    def __init__(self, version_def: dict):
        """
        :param version_def: A parsed JSON object returned by the version endpoint
        """
        self._version_def = version_def

    def __repr__(self):
        cfg_abbv = ",".join(x.name for x in self.configuration)
        obs_abbv = ",".join(x.name for x in self.observation)
        act_abbv = ",".join(x.name for x in self.action)
        ops_abbv = ",".join(x.name for x in self.outputs)
        return f"Version(cfg=[{cfg_abbv}], obs=[{obs_abbv}], act=[{act_abbv}], ops=[{ops_abbv}])"

    def __str__(self):
        output = "[Version]"
        output += "\nInputs\n\t- " + "\n\t- ".join(repr(x) for x in self.inputs)
        output += "\nOutputs\n\t- " + "\n\t- ".join(repr(x) for x in self.outputs)
        output += "\nEngine Settings\n\t- " + "\n\t- ".join(repr(x) for x in self.engine_settings)
        output += "\nConfiguration\n\t- " + "\n\t- ".join(repr(x) for x in self.configuration)
        output += "\nObservation\n\t- " + "\n\t- ".join(repr(x) for x in self.observation)
        output += "\nAction\n\t- " + "\n\t- ".join(repr(x) for x in self.action)
        return output

    @property
    def inputs(self) -> List[ModelData]:
        return [ModelData.from_json(data) for data in self._version_def['inputs']]

    @property
    def outputs(self) -> List[ModelData]:
        return [ModelData.from_json(data) for data in self._version_def['outputs']]

    @property
    def engine_settings(self) -> List[ModelData]:
        return [ModelData.from_json(data) for data in self._version_def['engineSettings']]

    @property
    def configuration(self) -> List[ModelData]:
        return [ModelData.from_json(data) for data in self._version_def['configuration']]

    @property
    def observation(self) -> List[ModelData]:
        return [ModelData.from_json(data) for data in self._version_def['observation']]

    @property
    def action(self) -> List[ModelData]:
        return [ModelData.from_json(data) for data in self._version_def['action']]


class ModelTemplate:
    """
    Contains "clean" (i.e., default) objects used by each function in this library that expects an argument.
    """

    def __init__(self, version: ModelVersion):
        self._version = version

    def __str__(self):
        output = "[ModelTemplate]\n"
        output += f"Configuration: {self.configuration}\n"
        output += f"Engine Settings: {self.engine_settings}\n"
        output += f"Action: {self.action}\n"
        output += f"Outputs: {self.outputs}"
        return output

    @property
    def configuration(self) -> Configuration:
        return Configuration(**{item.name: item.value for item in self._version.configuration})

    @property
    def engine_settings(self) -> 'EngineSettings':
        return EngineSettings(**{item.name: item.value for item in self._version.engine_settings})

    @property
    def action(self) -> Action:
        return Action(**{item.name: item.value for item in self._version.action})

    @property
    def outputs(self) -> List[str]:
        return [item.name for item in self._version.outputs]


class EngineSettings:
    DATE_PATTERNS = [r"\d{4}-\d{2}-\d{2}",  # TODO confirm these work as expected
                     r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{6}",
                     r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{6}-\d{2,4}",
                     r"[A-Za-z]{3}, \d{2} \d{2} \d{4} \d{2}:\d{2}:\d{2}[ A-Z]{0,4}"]

    def __init__(self, units: Union[str, TimeUnits] = None, startTime: Number = None,
                 startDate: Union[int, str] = None, stopTime: Number = None, stopDate: Union[int, str] = None,
                 seed: int = None,
                 **kwargs):  # TODO remove kwargs once consolidate key names between server and client
        self.units = TimeUnits[units] if isinstance(units, str) else (units if isinstance(units, TimeUnits) else None)
        self.startTime = startTime if startTime is not None else kwargs.get('start_time')
        self.startDate = startDate if startDate is not None else kwargs.get('start_date')
        self.stopTime = stopTime if stopTime is not None else kwargs.get('stop_time')
        self.stopDate = stopDate if stopDate is not None else kwargs.get('stop_date')
        self.seed = seed

        if not self._recognized_date_format(self.startDate):
            warnings.warn(f"Start date '{startDate}' does not match any recognized patterns (<EngineSettings.DATE_PATTERNS>); this may cause issues")

        if not self._recognized_date_format(self.stopDate):
            warnings.warn(f"Start date '{stopDate}' does not match any recognized patterns (<EngineSettings.DATE_PATTERNS>); this may cause issues")

    def __repr__(self):
        return "EngineSettings{" + f"units={self.units}, seed={self.seed}, startTime={self.startTime}, startDate={self.startDate}, stopTime={self.stopTime}, stopDate={self.stopDate}" + "}"

    def __str__(self):
        return repr(self)

    def _recognized_date_format(self, date) -> bool:
        # [NOTE] Jackson allowed formats: "yyyy-MM-dd'T'HH:mm:ss.SSSX", "yyyy-MM-dd'T'HH:mm:ss.SSS", "EEE, dd MMM yyyy HH:mm:ss zzz", "yyyy-MM-dd"
        #         Refs: https://docs.oracle.com/javase/8/docs/api/java/text/SimpleDateFormat.html
        #               https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes

        #FORMATS = ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S.%f%z", "%a, %d %m %Y %H:%M:%S %Z"]
        if date and isinstance(date, str):
            return any(re.match(fmt, date) for fmt in self.DATE_PATTERNS)
        return True