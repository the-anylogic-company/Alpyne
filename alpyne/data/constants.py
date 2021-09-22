from datetime import datetime
from enum import Enum
from typing import Any, Type, Union


class ExperimentType(Enum):
    """ Internally used when creating a new model run. """
    #SIMULATION = "SIMULATION"
    REINFORCEMENT_LEARNING = "REINFORCEMENT_LEARNING"


class RLCommand(Enum):
    """ Internally used when POSTing to the /rl/ endpoint. """
    CONFIGURATION = "CONFIGURATION"
    OBSERVATION = "OBSERVATION"
    ACTION = "ACTION"


class RunStatus(Enum):
    """
    Represents the status of a run's engine.

    In general, the engine can be considered either waiting for some type of user-input, actively processing, or
    in a halted state (which may or may not be recoverable). The various statuses divide these three categories
    into subcategories, to provide more useful context.
    """
    FRESH = "FRESH"
    """ Just started, waiting for the configuration. End users will typically not see this status due to configuration \
    being provided in conjunction with some other command (e.g., reset). """

    PAUSED = "PAUSED"
    """ Mid-run, waiting for action and open to observation and output querying. """

    RUNNING = "RUNNING"
    """ The model is being actively executed (cannot be interacted with). """

    COMPLETED = "COMPLETED"
    """ Reached stopping condition - either time/date or based on the RL experiment's "done" field. """

    STOPPED = "STOPPED"
    """ Manually finished (by API call). """


    FAILED = "FAILED"
    """ Encountered runtime error. """



class InputTypes(Enum):
    """ Represents the data types of elements provided in the inputs/configuration. """
    STRING = "STRING"
    DOUBLE = "DOUBLE"
    INTEGER = "INTEGER"
    LONG = "LONG"
    BOOLEAN = "BOOLEAN"
    OBJECT = "OBJECT"
    DATE_TIME = "DATE_TIME"

    @staticmethod
    def to_class(input_: Union[str, 'InputTypes']) -> Union[Type, None]:
        # first check for `_ARRAY` types (not specfied in this enum but considered valid)
        if isinstance(input_, str) and input_.endswith("_ARRAY"):
            return list

        try:
            itype = input_ if isinstance(input_, InputTypes) else InputTypes(input_)
        except ValueError:
            # currently occurs when trying to convert output-typed objects
            #warn(f"Input '{input_}' does not have an equivalent input type")
            return None

        if itype == InputTypes.STRING:
            return str
        elif itype == InputTypes.DOUBLE:
            return float
        elif itype == InputTypes.INTEGER or itype == InputTypes.LONG:
            return int
        elif itype == InputTypes.BOOLEAN:
            return bool
        elif itype == InputTypes.OBJECT:
            return dict
        elif itype == InputTypes.DATE_TIME:
            return datetime
        raise ValueError(f"Unhandled input type ({itype} for input {input_}; returning None")

    @staticmethod
    def from_value(input_: Any) -> 'InputTypes':
        if isinstance(input_, str):
            return InputTypes.STRING
        elif isinstance(input_, bool): # check before ints since isinstance(True, int) == True
            return InputTypes.BOOLEAN
        elif isinstance(input_, int):
            return InputTypes.LONG # assume over int to avoid potential bit-loss
        elif isinstance(input_, float):
            return InputTypes.DOUBLE
        elif isinstance(input_, datetime):
            return InputTypes.DATE_TIME
        else:
            return InputTypes.OBJECT

    @staticmethod
    def validate(value: Any, expected: 'InputTypes') -> bool:
        """
        Checks whether the passed value is of the expected input type.
        :param value: either an object or a class of an object
        :param expected: the expected input type to check against
        :return: True if the value is an instance or a subclass of the expected type
        """
        # use different function depending on whether 'value' is an object or a class
        ischeck = issubclass if isinstance(value, type) else isinstance
        if expected == InputTypes.STRING:
            return ischeck(value, str)
        elif expected == InputTypes.DOUBLE:
            return ischeck(value, float)
        elif expected == InputTypes.INTEGER or expected == InputTypes.LONG:
            return ischeck(value, int)
        elif expected == InputTypes.BOOLEAN:
            return ischeck(value, bool)
        elif expected == InputTypes.OBJECT:
            return ischeck(value, dict)
        elif expected == InputTypes.DATE_TIME:
            return ischeck(value, (str, datetime))
        return False


class OutputTypes(Enum):
    """ Represents the data types in a `SingleRunOutputs` object. """
    STRING = "STRING"
    DOUBLE = "DOUBLE"
    INTEGER = "INTEGER"
    LONG = "LONG"
    DATE_TIME = "DATE_TIME"
    BOOLEAN = "BOOLEAN"
    DATA_SET = "DATA_SET"
    STATISTICS_DISCRETE = "STATISTICS_DISCRETE"
    STATISTICS_CONTINUOUS = "STATISTICS_CONTINUOUS"
    HISTOGRAM_DATA = "HISTOGRAM_DATA"
    HISTOGRAM_2D_DATA = "HISTOGRAM_2D_DATA"


class EngineSettings(Enum):
    """ Represents the different engine-level settings as part of a run's inputs/configuration. """
    START_TIME = "{START_TIME}"
    START_DATE = "{START_DATE}"
    STOP_TIME = "{STOP_TIME}"
    STOP_DATE = "{STOP_DATE}"
    STOP_MODE = "{STOP_MODE}"
    SEED = "{RANDOM_SEED}"
    MAX_MEMORY_MB = "{MAX_MEMORY_MB}"
