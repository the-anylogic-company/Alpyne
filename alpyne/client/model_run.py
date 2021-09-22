import json
import time
from logging import Logger
from typing import List, Tuple, NoReturn, Optional

from alpyne import LOG_LEVEL
from alpyne.client.http_client import HttpClient
from alpyne.data.constants import ExperimentType, RunStatus, RLCommand
from alpyne.data.model_error import ModelError
from alpyne.data.single_run_outputs import SingleRunOutputs
from alpyne.data.spaces import Configuration, Action, Observation, Number

# TODO remove blocking conditionals once blocking is implemented server-side


class ModelRun:
    """
    Represents a single run of your model, spawned from the Alpyne Client object.

    End users should not create this object manually. Instead, use the relevant method in your Alpyne Client object.
    """

    DEFAULT_POLLING_PERIOD = 0.1

    def __init__(self, http_client: HttpClient, type_: ExperimentType, inputs: Configuration, blocking: bool,
                 polling_period: Optional[Number] = None):
        self.log = Logger("ModelRun", LOG_LEVEL)

        self.http_client = http_client
        self.type = type_
        self.blocking = blocking
        self.polling_period = polling_period or ModelRun.DEFAULT_POLLING_PERIOD

        self.id = None
        self.inputs = inputs
        self.last_state = (None, None)  # as per `get_state()`; NOT to be confused with a last observation

    def run(self) -> 'ModelRun':
        """
        Begin the experiment and allow the model to start execution.
        This is only meant to be called once after creation. Other methods are used for resetting/stopping.

        If `blocking` is enabled, this method will consume the current thread until the operation is complete.

        :param polling_period: how long to wait in between status polling, before model is done processing; \
            only applicable if this object was created with blocking = True.
        :return: this object

        """
        if self.id is not None:
            raise RuntimeError("This method has already been called and cannot be called again for the same run.")
        endpoint = "/runs"
        body = {"experimentType": self.type, "inputs": self.inputs}
        _, _, response = self.http_client.post(endpoint, body)

        self.id = response['id']
        if self.blocking:
           return self.wait_for_completion()
        return self

    def reset(self, inputs: Optional[Configuration] = None) -> 'ModelRun':
        """
        Setup the instance to begin a new run with the specified inputs.
        After calling this method, the server will automatically start the next run.

        If `blocking` is enabled, this method will consume the current thread until the operation is complete.

        :param inputs: the new configuration to use, or none to use the last configuration again
        :return: this object

        """
        if inputs is not None:
            self.inputs = inputs
        #self.stop()

        # calling to set the configuration will reset the sim
        endpoint = f"/runs/{self.id}/rl"
        body = {"command": RLCommand.CONFIGURATION.value, "argument": self.inputs}
        _, _, result = self.http_client.post(endpoint, body)

        if self.blocking:
            return self.wait_for_completion()

        return self

    def stop(self) -> 'ModelRun':
        """
        Instructs the Alpyne app to halt execution of the current model (if it's not halted - for any reason - already).

        If `blocking` is enabled, this method will consume the thread until the operation is completed.

        :return: this object

        """
        _ = self.http_client.post(f"/runs/{self.id}/stop")
        if self.blocking:
            return self.wait_for_completion()
        return self

    # def _delete(self) -> NoReturn:
    #     _ = self.http_client.api_request(f"/runs/{self.id}", "DELETE")

    def wait_for_completion(self) -> 'ModelRun':
        """
        Blocks the current thread until the model's execution is in some non-processing state \
            (e.g., paused, completed, stopped, failed)

        :return: this object
        :except ModelError: If the model's status is failed (due to an error)

        """

        status, info = self.get_state()
        while status not in [RunStatus.PAUSED, RunStatus.COMPLETED, RunStatus.STOPPED]:
            if status == RunStatus.FAILED:
                raise ModelError(info)
            time.sleep(self.polling_period)
            status, info = self.get_state()
        return self

    def get_state(self) -> Tuple[RunStatus, dict]:
        """
        Queries the state of the current run's execution. This is *not* to be confused with the (RL) observation.

        :return: a constant representing its status and a dictionary with more detailed information

        """
        endpoint = f"/runs/{self.id}/progress"
        _, _, output = self.http_client.get(endpoint)

        self.log.debug(f"state output = {output}")

        # validate status is recognized type
        assert output['status'] in RunStatus.__dict__, f"Unrecognized run status: {output['status']}"

        status, info = RunStatus(output['status']), json.loads(output['message'])
        self.last_state = (status, info)
        return self.last_state

    def get_observation(self) -> Observation:
        """
        Queries the run for the current observation (as per your RL experiment).
        It's intended to only be used when the model is in a non-processing state (e.g., paused, completed, stopped).

        :return: an object containing fields with the name and values as per the
        "Observation" section in the model's RL experiment.

        """
        endpoint = f"/runs/{self.id}/rl"
        body = {"command": RLCommand.OBSERVATION.value}
        _, _, result = self.http_client.post(endpoint, body)
        return Observation(result)

    def take_action(self, action: Action) -> 'ModelRun':
        """
        Executes the specified action on the model and allow it to continue. It's intended to only be called when the
        model is in a paused state.

        If `blocking` is enabled, this method will consume the thread until the sim has reached some non-processing
        state (e.g., paused, completed, stopped, failed).

        :param action: an object containing fields with the name/types as per the "Action" section
        of the model's RL experiment
        :return: this object

        """
        endpoint = f"/runs/{self.id}/rl"
        body = {"command": RLCommand.ACTION.value, "argument": action}
        _ = self.http_client.post(endpoint, body)
        if self.blocking:
            return self.wait_for_completion()
        return self

    def is_terminal(self) -> bool:
        """
        Checks whether the model is considered "complete" - i.e., whether it's execution is finished due to
        a pre-defined reason (stop time/date or stop condition in the RL experiment).

        Non-"complete" reasons include if the sim encountered an error, is currently processing, or is waiting on
        further input.

        :return: whether the current run status is `COMPLETED`

        """
        status, _ = self.get_state()
        return status == RunStatus.COMPLETED

    def get_outputs(self, names: List[str] = None) -> SingleRunOutputs:
        """
        Retrieves the the current value of the specified Analysis objects (e.g., Output, histogram data, etc).

        Objects must be present on the top-level agent (commonly Main) to be detected.
        Available names can be checked via the `output_names` attribute of the `AlpyneClient` object - and
        further information from its `version` attribute.

        :param names: An optional list of object names (i.e., the Java variable names) to retrieve the values of;
        if None, all objects will be received.
        :return: an object containing attributes with the object names

        """
        endpoint = f"/runs/results/{self.id}"
        if names:
            # add in as a query parameter; a list of names
            endpoint += f"?names={','.join(names)}"
        _, _, output = self.http_client.get(endpoint)
        return SingleRunOutputs(output)
