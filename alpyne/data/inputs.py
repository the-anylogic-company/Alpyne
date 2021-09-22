import copy
from typing import Any

from alpyne.client.utils import case_insensitive_equals, convert_from_string, convert_to_string


class Inputs:
    """
    Represents the parameters on the top-level agent.

    Note: This is provided for user-reference only. It is not used to run sims with.
    """
    def __init__(self, model_version, experiment=None):
        self._model_version = model_version
        self.outputs = model_version.experiment_template["outputs"]
        self._set_inputs(experiment)

    def get_input(self, name: str):
        inp = self._input_by_name(name)
        return convert_from_string(inp["value"], inp["type"])

    def set_input(self, name: str, value: Any):  # TODO: serialize value
        inp = self._input_by_name(name)
        inp["value"] = convert_to_string(value)

    def names(self):
        return list(map(lambda i: i["name"], self.inputs_array))

    def _clone(self):
        new_inputs = Inputs(self._model_version)
        new_inputs.inputs_array = copy.deepcopy(self.inputs_array)
        return new_inputs

    def _set_inputs(self, experiment):
        if experiment is not None:
            self.inputs_array = copy.deepcopy(experiment["inputs"])
        else:
            self.inputs_array = copy.deepcopy(self._model_version.experiment_template["inputs"])
            self.inputs_array.append({"name": "{RANDOM_SEED}", "type": "LONG", "units": None, "value": "1"})

        self.inputs_array = sorted(self.inputs_array, key=lambda i: i["name"])

    def _input_by_name(self, name):
        return next(i for i in self.inputs_array if case_insensitive_equals(i["name"], name))

    def _get_key_data(self, type_):
        return {
            "inputs": self.inputs_array,
            "experimentType": type_
        }
