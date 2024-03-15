import logging
from datetime import datetime
from enum import Enum, Flag, auto

from alpyne.outputs import DataSet, StatisticsDiscrete, StatisticsContinuous, HistogramSimpleData, \
    HistogramSmartData, Histogram2DData, TimeUnits

DATE_PATTERN_LOOKUP = {  # TODO confirm these work as expected
    r"^\d{4}-\d{2}-\d{2}$": "%Y-%m-%d",
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$": "%Y-%m-%dT%H:%M:%S",
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{1,6}$": "%Y-%m-%dT%H:%M:%S.%f",
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{1,6}[-+]\d{2,6}\.*\d*$": "%Y-%m-%dT%H:%M:%S.%f%z",
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{1,6}[-+](?:\d{2}:*)+(?:\.\d+)*$": "%Y-%m-%dT%H:%M:%S.%f%:z",  # only for 3.12+
    r"^[A-Za-z]{3}, \d{2} [A-Za-z]{3} \d{4} \d{2}:\d{2}:\d{2}[ A-Z]{0,4}$": "%a, %d %b %Y %H:%M:%S %Z"
}
"""Constant mapping between a regex for valid date/time pattern and the equivalent datetime.strftime/strptime pattern"""

TYPE_LOOKUP = {
    "long": int,
    "Long": int,
    "int": int,
    "Integer": int,
    "double": float,
    "Double": float,
    "float": float,
    "Float": float,
    "String": str,
    "boolean": bool,
    "Boolean": bool,
    "Map": dict,
    "HashMap": dict,
    "TreeMap": dict,
    "LinkedHashMap": dict,
    "ArrayList": list,
    "LinkedList": list,
    "LinkedHashSet": list,  # all sets are interpreted as lists due to JSON conversion
    "HashSet": list,
    "TreeSet": list,
    "TimeUnits": TimeUnits,
    "Date": datetime,
    "DataSet": DataSet,
    "StatisticsDiscrete": StatisticsDiscrete,
    "StatisticsContinuous": StatisticsContinuous,
    "HistogramSimpleData": HistogramSimpleData,
    "HistogramSmartData": HistogramSmartData,
    "Histogram2DData": Histogram2DData
}
"""Constant mapping between simple names of Java classes to the Python equivalent"""


class JavaLogLevel(Enum):
    """
    Represents the log level to use in the Alpyne Java application.
    """

    SEVERE = "SEVERE"
    """A message level indicating a serious failure"""

    WARNING = "WARNING"
    """A message level indicating a potential problem"""

    INFO = "INFO"
    """A message level for informational messages"""

    CONFIG = "CONFIG"
    """A message level for static configuration messages"""

    FINE = "FINE"
    """A message level providing tracing information"""

    FINER = "FINER"
    """A fairly detailed tracing message"""

    FINEST = "FINEST"
    """A highly detailed tracing message"""

    @classmethod
    def from_py_level(cls, level: str | int):
        # convert to an int to make it comparable to the constants
        if isinstance(level, str):
            # `getLevelName` will return another string if it doesn't have the name recorded
            _level = logging.getLevelName(level)
            if isinstance(_level, str):
                raise ValueError(f"Input level ({level}) cannot be properly converted to a known Python level")
            level = _level
        if level <= logging.DEBUG:  # 10
            return cls.FINEST
        elif level <= logging.INFO:  # 20
            return cls.INFO
        elif level <= logging.WARNING:  # 30
            return cls.WARNING
        else:  # up to, or beyond, logging.SEVERE (40) and logging.CRITICAL (50)
            return cls.SEVERE


class EngineState(Flag):
    """
    Represents the state of the sim's engine.
    """

    IDLE = auto()
    """ Just started, waiting for the configuration """

    PAUSED = auto()
    """ Mid-run, waiting for action and open to observation and output querying """

    RUNNING = auto()
    """ The model is being actively executed """

    FINISHED = auto()
    """ The model execution is finished successfully  """

    ERROR = auto()
    """ Internal model error """

    PLEASE_WAIT = auto()
    """ In the process of executing an uninterruptible command (`pause()`, `stop()`, `step()`) """

    @classmethod
    def ANY(cls):
        return ~cls(0)

    @staticmethod
    def ready():
        return EngineState.PAUSED | EngineState.FINISHED | EngineState.ERROR
