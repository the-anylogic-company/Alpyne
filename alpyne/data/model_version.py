from typing import Dict, Union, List

from alpyne.data.model_data import ModelData
from alpyne.data.model_error import ModelError
from alpyne.data.spaces import Configuration, Observation, Action


class ModelVersion:
    """ Contains the templates for each of the possible data-holding objects.

    - Inputs: Parameters of your top-level agent.
    - Outputs: Analysis objects (Output, DataSet, HistogramData, etc.) on your top-level agent.
    - Configuration: Defined data fields in the *Configuration* section of the RL experiment.
    Also includes "special" fields representing various engine settings (random seed, start and stop time/date).
    - Observation: Defined data fields in the *Observation* section of the RL experiment.
    - Action: Defined data fields in the *Action* section of the RL experiment.

    For the purposes of Alpyne, Configuration replaces Cloud's usage of Inputs (which is kept for user-reference).
    """
    def __init__(self, version: int, experiment_template: Dict[str, Union[list, dict]]):
        self.version = version
        self.experiment_template = experiment_template

    def get_inputs_template(self) -> List[ModelData]:
        return [ModelData.from_json(x) for x in self.experiment_template['inputs']]

    def get_outputs_template(self) -> List[ModelData]:
        return [ModelData.from_json(x) for x in self.experiment_template['outputs']]

    def get_configuration_template(self) -> Configuration:
        return Configuration(self.experiment_template['reinforcement_learning']['configuration'])

    def get_observation_template(self) -> Observation:
        return Observation(self.experiment_template['reinforcement_learning']['observation'])

    def get_action_template(self) -> Action:
        return Action(self.experiment_template['reinforcement_learning']['action'])

    @staticmethod
    def from_json(json_data: Dict[str, Union[int, dict]]):
        if json_data is None:
            raise RuntimeError("Attempted to parse 'None' Version data; check that the app started correctly.")
        return ModelVersion(json_data["version"],
                            json_data["experimentTemplate"])
