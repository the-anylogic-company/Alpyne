import copy
import json
from typing import Any, List, Optional

from alpyne.data.model_data import ModelData


class SingleRunOutputs:
    """
    Represents a collection of one or more outputs from a simulation run.

    In addition to being iterable, specific values of elements whose name is known can be accessed by directly
    querying the name.
    """
    def __init__(self, aggregations: Optional[List[dict]] = None):
        #self._outputs = list(map(lambda o: self._identity_to_modeldata(o), aggregations))
        # put values in a dictionary for faster reference
        self._datas = dict()
        if aggregations:
            for agg in aggregations:
                model_data = self._identity_to_modeldata(agg)
                self._datas[model_data.name] = model_data

    def __str__(self):  # TODO nicer outputs
        #body = ", ".join([f"{o.name}={o.value}" for o in self._outputs])
        body = ", ".join([f"{o.name}={o.value}" for o in self._datas.values()])
        return f"Outputs[{body}]"

    def __repr__(self):
        #body = ", ".join([f"{o.name}={o.value}" for o in self._outputs])
        body = ", ".join([f"{o.name}={o.value}" for o in self._datas.values()])
        return f"Outputs[{body}]"

    def __getattr__(self, name: str) -> Any:
        return self._datas[name].value

    def __iter__(self):
        #return iter(self._outputs)
        return iter(self._datas.values())

    def names(self) -> List[str]:
        #return list(map(lambda o: o['name'], self._outputs))
        return list(self._datas.keys())

    def value(self, name: str) -> Any:
        return self.__getattr__(name)
        # try:
        #     output = next(filter(lambda o: o['name'] == name, self._outputs))
        #     return output.value
        # except StopIteration as e:
        #     raise Exception("Output value '" + name + "' not found")

    def get_raw_outputs(self) -> Any:
        return self._outputs

    @staticmethod
    def _identity_to_modeldata(aggregation):
        res = copy.deepcopy(aggregation['outputs'][0])
        res['value'] = json.loads(aggregation['value'])
        return ModelData.from_json(res)