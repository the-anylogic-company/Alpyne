from typing import Dict, Any

from alpyne.data.constants import InputTypes


class ModelData:
    """
    Represents a single data element with a name, type, value, and (optional) units.

    This class is what each of the collection types
    (Inputs, Outputs, Configuration, Observation, Action) are composed of.
    """
    def __init__(self, name, type_, value, units=None):
        self.name = name
        self.type_ = type_
        self.py_type = InputTypes.to_class(type_)
        self.units = units
        self.value = value or (0 if self.py_type in [int, float] else None)

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

    @staticmethod
    def from_pair(name: str, value: Any) -> 'ModelData':
        """
        Construct an instance based on the provided information.

        Used as part of a workaround when it's preferable to build the object from Python information,
        rather than via the template.

        Note that since Python types are simpler than Java's, the assigned type may not match up to what is set
        in the model. The alpyne app will accept certain compatible types.

        :param name: the element's name
        :param value: the element's value
        :return: a ModelData object
        """
        type_ = InputTypes.from_value(value)
        return ModelData(name, type_, value, None)
