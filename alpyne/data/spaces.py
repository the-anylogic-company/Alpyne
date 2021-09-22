import itertools
import logging
from collections import Iterable, Mapping
from datetime import datetime
from math import ceil
from typing import Any, Dict, List, Optional, Union, Tuple, Callable

from alpyne.data.constants import EngineSettings, InputTypes
from alpyne.data.model_data import ModelData

Number = Union[int, float]
DataDicts = List[Dict[str, Optional[Union[str, Number, list, dict]]]]

StartStopStep = Union[Tuple[Number, Number], Tuple[Number, Number, Number]]
ValueGenerator = Callable[[], Number]

log = logging.getLogger("RLSpace")

class RLSpace:
    """
    A generic object containing the core structure for the Configuration, Observation, and Action spaces.
    """

    def __init__(self, data: Optional[DataDicts] = None, **kwargs):
        """
        :param data: a list of dictionaries, where each element contains the keys "name", "type", "value", and "unit"
        :param kwargs: name-value pairs to include; type is converted based on checked type of values
        """
        # Hold the converted elements in a dictionary for internal storage + quicker ref (than a list)
        self._data = dict()
        # Keep a reference to names to preserve the order
        self._names = []

        if data:
            for element in data:
                model_data = ModelData.from_json(element)
                self._data[model_data.name] = model_data
                self._names.append(model_data.name)
        for name, value in kwargs.items():
            model_data = ModelData.from_pair(name, value)
            self._data[model_data.name] = model_data
            self._names.append(model_data.name)

    def __getattr__(self, item: str) -> Any:
        """
        Called as a fallback to __getattribute__ when Python cannot find the specified item in the class's variables.
        :param item: The name of the ModelData element to retrieve.
        :return: The specified ModelData's current value.
        :exception AttributeError: When the name is incorrect/not found.
        """
        # '_data' isn't saved in dict until after initialization, so handle special case during setup
        if item == '_data':
            return {}
        value = self._data[item].value
        value = value if not callable(value) else value()
        # TODO figure out what __getstate__ is (for pickling) and implement whatever's needed
        return value

    def __getattribute__(self, item):
        value = super().__getattribute__(item)
        return value

    def __setattr__(self, key: str, value: Union[Number, StartStopStep, ValueGenerator]) -> None:
        """
        Called *every time* a value is attempted to be set in this object.
        :param key: the name of the data element to assign (as defined in the sim)
        :param value: either a static value, a 3-tuple describing the {start, stop, step}, or a generator
            (the two allowed dynamic types are queried/advanced whenever the value is accessed)
        """
        if not self.__dict__:
            # no internal objects; called when the first class var is being created
            super(RLSpace, self).__setattr__(key, value)
        elif key in self._data:
            # one of the data elements, assign via the dictionary
            self._data[key].value = value
        else:  # fallback to parent functionality (TODO when does this happen (practically)?)
            super(RLSpace, self).__setattr__(key, value)

    def __str__(self):
        return str([f"{x.name}={x.value}" for x in self._data.values()]).replace("'", "").replace('"', "")

    def __repr__(self):  # TODO add more content to the string
        return str([repr(x) for x in self._data.values()]).replace("'", "").replace('"', "")

    def get_input(self, name: str) -> Any:
        # TODO since this is only *based* on the cloud's Inputs class, maybe rename get/set_input to get/set_value
        return self.__getattr__(name)

    def set_input(self, name: str, value: Any) -> None:
        self.__setattr__(name, value)

    def names(self) -> List[str]:
        return self._names

    def _flatten(self, values):
        for val in values:
            if isinstance(val, Mapping):
                yield from self._flatten(val.values())
            elif isinstance(val, Iterable) and not isinstance(val, (str, bytes)):
                yield from self._flatten(val)
            else:
                yield val

    def values(self, order: List[str] = None, flatten: bool = False) -> List[Any]:
        """
        :param order: a list of names to order the values with; can also be used to get a subset of values.\
        None defaults to the original order.
        :param flatten: whether to collapse the values to one-dimension.\
        (note: dictionary objects will their value method called, which does not guarentee order)
        :return: a list of python typed (non-alpyne) objects
        :Example:
        >>> Observation(time=720, sample=[11.1, 22.2], myagent={'util': 0.75, 'costs': [-1, -2, -5]}).values()
        [720, [0.1, 23.4], {'util': 0.75, 'costs': [-1, -2, -5]}
        >>> Observation(time=720, sample=[11.1, 22.2], myagent={'util': 0.75, 'costs': [-1, -2, -5]}).values(["sample", "time"])
        [[11.1, 22.2], 720]
        >>> Observation(time=720, sample=[11.1, 22.2], myagent={'util': 0.75, 'costs': [-1, -2, -5}).values(flatten=True)
        [720, 11.1, 22.2, 0.75, -1, -2, -5]

        """
        order = order or self._names

        vals = [self._data[name].value for name in order]
        if flatten:
            vals = list(self._flatten(vals))
        return vals


    # def to_jsonable(self) -> DataDicts:
    #     """
    #     :return: a JSON-friendly object
    #     """
    #     return [d.to_jsonable() for d in self._data.values()]


class Configuration(RLSpace):
    """
    An object representing the starting values to pass to the sim at the start of each run.
    Two special features of Configurations:

    1. Supports engine-level parameters, implemented as settable properties, and with special names to
    avoid conflicts. These consist of:

        - engine_start_time: Number
        - engine_start_date: datetime
        - engine_stop_time: Number
        - engine_stop_date: datetime
        - engine_seed: int

    2. Allows values to be assigned as either:

        - static numbers
        - 3-tuples describing start, stop, step (auto-advances to the next step whenever it is queried)
        - generators (retrieves the next value whenever it is queried)

    """

    def __init__(self, template: Optional[DataDicts] = None, **kwargs):
        super().__init__(template, **kwargs)

    def __getattr__(self, name: str) -> Any:
        if not self.__dict__:
            # required as part of initial setup
            return {}
        if name not in self._data:
            raise AttributeError(f"Configuration space has no attribute '{name}'")
        # trying to access a value in the space
        value = self._data[name].value
        output = value if not callable(value) else value()
        return output

    def __setattr__(self, key, value: Union[Number, StartStopStep, ValueGenerator, None]):
        if self.__dict__ and key not in self._data and key not in dir(self) and key != "_names":
            raise AttributeError(f"Configuration space has no attribute '{key}' to be set to {value}")

        # TODO general type checking on assigned values (e.g., no callables for engine settings)
        # Convert StartStopStep type to a callable generator.
        # This avoids needing to keep track of where in the range the current value is at.
        if isinstance(value, tuple):
            # manually construct array of values to handle floats in range (avoids single-use numpy dependency)
            step = 1 if len(value) == 2 else value[2]
            count = abs(int(ceil((value[1] - value[0]) / step)))
            values = [i for i in itertools.islice(itertools.count(value[0], step), count)]
            cycler = itertools.cycle(values)
            value = lambda: next(cycler)
        super().__setattr__(key, value)

    @property
    def engine_start_time(self) -> Optional[Number]:
        if EngineSettings.START_TIM.valueE.value not in self._data:
            return None
        return self._data[EngineSettings.START_TIME.value].value

    @engine_start_time.setter
    def engine_start_time(self, value: Number):
        if EngineSettings.START_TIME.value not in self._data:  # add if not already included
            self._data[EngineSettings.START_TIME.value] = ModelData(EngineSettings.START_TIME.value, InputTypes.DOUBLE, 0)
        self._data[EngineSettings.START_TIME.value].value = value

    @property
    def engine_start_date(self) -> Optional[datetime]:
        if EngineSettings.START_DATE.value not in self._data:
            return None
        return self._data[EngineSettings.START_DATE.value].value

    @engine_start_date.setter
    def engine_start_date(self, value: datetime):
        if EngineSettings.START_DATE.value not in self._data:  # add if not already included
            self._data[EngineSettings.START_DATE.value] = ModelData(EngineSettings.START_DATE.value, InputTypes.STRING,
                                                              datetime.now())
        self._data[EngineSettings.START_DATE.value].value = value

    @property
    def engine_stop_time(self) -> Optional[Number]:
        if EngineSettings.STOP_TIME.value not in self._data:
            return None
        return self._data[EngineSettings.STOP_TIME.value].value

    @engine_stop_time.setter
    def engine_stop_time(self, value: Number):
        if EngineSettings.STOP_TIME.value not in self._data:  # add if not already included
            self._data[EngineSettings.STOP_TIME.value] = ModelData(EngineSettings.STOP_TIME.value, InputTypes.DOUBLE, None)
        self._data[EngineSettings.STOP_TIME.value].value = value

    @property
    def engine_stop_date(self) -> Optional[datetime]:
        if EngineSettings.STOP_DATE.value not in self._data:
            return None
        return self._data[EngineSettings.STOP_DATE.value].value

    @engine_stop_date.setter
    def engine_stop_date(self, value: datetime):
        if EngineSettings.STOP_DATE.value not in self._data:  # add if not already included
            self._data[EngineSettings.STOP_DATE.value] = ModelData(EngineSettings.STOP_DATE.value, InputTypes.STRING, None)
        self._data[EngineSettings.STOP_DATE.value].value = value

    @property
    def engine_seed(self) -> Optional[int]:
        if EngineSettings.SEED.value not in self._data:
            return None
        return self._data[EngineSettings.SEED.value].value

    @engine_seed.setter
    def engine_seed(self, value: int):
        if EngineSettings.SEED.value not in self._data:  # add if not already included
            self._data[EngineSettings.SEED.value] = ModelData(EngineSettings.SEED.value, InputTypes.LONG, None)
        self._data[EngineSettings.SEED.value].value = value


class Observation(RLSpace):
    """ A read-only object representing an observation taken from the simulator """

    # default constructor

    def __setattr__(self, key, value):
        # data elements are read-only in observation
        if key in self._data:
            raise TypeError("Operation not permitted for this class type.")
        super().__setattr__(key, value)


class Action(RLSpace):
    """
    An object representing an action to sent to the simulator.
    Allows values to be assigned as either:

    - static numbers
    - 3-tuples describing start, stop, step (auto-advances to the next step whenever it is queried)
    - generators (retrieves the next value whenever it is queried)

    """
    pass  # no current special attributes
