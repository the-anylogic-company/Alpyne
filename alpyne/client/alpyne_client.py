import atexit
import logging
import os
import subprocess
from typing import List, Callable, Optional

from alpyne import LOG_LEVEL
from alpyne.client.http_client import HttpClient
from alpyne.client.model_run import ModelRun
from alpyne.client.utils import resolve_model_jar, \
    get_wildcard_paths, shorten_by_relativeness, get_resources_path
from alpyne.data.constants import ExperimentType
from alpyne.data.inputs import Inputs
from alpyne.data.model_error import ModelError
from alpyne.data.model_version import ModelVersion
from alpyne.data.single_run_outputs import SingleRunOutputs
from alpyne.data.spaces import Configuration, Observation, Action

ConfigQuery = Callable[[Configuration], Configuration]
ActionQuery = Callable[[Observation, Action, Optional[int], Optional[SingleRunOutputs]], Action]


class AlpyneClient:
    """
    The main object to initiate the Alpyne application and derive simulation runs from.
    """
    def __init__(self, model_loc: str, blocking: bool = False, port: int = 51150, verbose: bool = False):
        """
        :param model_loc: a relative or absolute path to the exported model zip or extracted model.jar file
        :param blocking: whether to halt the calling Python thread during time-consuming tasks (e.g., advancing the sim)
        :param port: what local port to run the Alpyne app on
        :param verbose: whether to enable detailed app logging
        :raises ModelError: if the app fails to start
        """
        logging.basicConfig(
            level=LOG_LEVEL,
            format=f"%(asctime)s [%(name)s @ %(lineno)s][%(levelname)8s] %(message)s",
            handlers=[logging.StreamHandler()],
        )
        self.log = logging.getLogger(__name__)

        self._blocking = blocking
        self._proc = self._start_app(model_loc, blocking, port, verbose)

        try:
            self._http_client = HttpClient(f"http://127.0.0.1:{port}")
            _, _, output = self._http_client.get("/versions/number/0")
            self.version = ModelVersion.from_json(output)
        except:
            raise ModelError(f"Failed to properly start the app. Error from process: {self._proc.stderr.read().decode()}")

    def _start_app(self, model_loc: str, blocking: bool, port: int, verbose: bool) -> subprocess.Popen:
        """
        Execute the backend app with the desired preferences.

        :param model_loc:
        :param port:
        :param blocking:
        """
        model_loc = resolve_model_jar(model_loc).parent.absolute()

        # temporarily change to the exported model folder's directory for starting purposes
        # (needed to make sure database is properly connected to)
        initdir = os.getcwd()
        os.chdir(str(model_loc.absolute()))

        jar_sources = get_wildcard_paths(str(get_resources_path())) + get_wildcard_paths(str(model_loc))
        jar_sources = shorten_by_relativeness(jar_sources)

        if os.name == "nt":
            class_path = ";".join(jar_sources)
        else:
            class_path = ":".join(jar_sources)

        cmdline_args = ["java",
                        "-cp", class_path,
                        "com.anylogic.alpyne.AlpyneServer",
                        "-p", f"{port}",
                        "-l", "WARNING" if not verbose else "ALL",
                        "."]

        self.log.debug(f"Executing:\n{' '.join(cmdline_args)}\n")
        
        proc = subprocess.Popen(cmdline_args,
                                stdin=subprocess.PIPE,  # Needed for quitting the app
                                stdout=subprocess.PIPE, # Both stdout and stderr should be empty,
                                stderr=subprocess.PIPE) #   but open up just in case.

        # return back to original directory
        os.chdir(initdir)

        returncode = proc.poll()
        if returncode is not None and returncode != 0:
            err_message = proc.stderr.readlines()
            raise EnvironmentError(f"Process returned code: {returncode}; message: {err_message}")

        self.log.debug(f"PID = {proc.pid}")

        atexit.register(self._quit_app)

        return proc

    def _quit_app(self):
        # Trigger self-destruct, killing any active runs
        self._http_client.api_request("/", "DELETE", None)
        try:
            # send arbitrary text directly to process to trigger shutdown
            stdout, stderr = self._proc.communicate('q'.encode(), 3)
            if stdout:
                self.log.debug(f"Uncaught output from app's stdout: {stdout.decode()}")
            if stderr:
                self.log.debug(f"Uncaught output from app's stderr: {stderr.decode()}")
        except Exception as e:
            self.log.error(f"Failed to communicate: {e}")

        try:
            self._proc.wait(1)
        except Exception as e:
            self.log.error(f"Force killing app; did not quit as expected: {e}")
            self._proc.kill()

    def _status(self):
        return self._http_client.post("/")

    @property
    def configuration_template(self) -> Configuration:
        """
        :return: a blank copy of the Configuration object
        """
        return self.version.get_configuration_template()

    @property
    def observation_template(self) -> Observation:
        """
        :return: a blank copy of the Observation object
        """
        return self.version.get_observation_template()

    @property
    def action_template(self) -> Action:
        """
        :return: a blank copy of the Action object
        """
        return self.version.get_action_template()

    @property
    def output_names(self) -> List[str]:
        """
        :return: a list of the detected output objects; specified as part of a run's get_outputs method
        """
        return [o.name for o in self.version.get_outputs_template()]

    def create_default_rl_inputs(self) -> Configuration:
        """
        Get the object intended to be filled out and passed in the creation of a new model run.

        :return: a copy of the Configuration object; equivalent to accessing the `configuration_template` attribute
        """
        return self.configuration_template

    def create_reinforcement_learning(self, inputs: Optional[Configuration]) -> ModelRun:
        """
        Builds a new, single RL experiment using the provided configuration, or the default if none is provided.

        Note: "the default" is all zeros/nulls (*not* your parameter's defaults), so this should only be omitted
        if your logic handles this or if you have no Configuration.

        :param inputs: the initial configuration to start the model with
        :return: an object referencing the created model run
        """
        return ModelRun(self._http_client, ExperimentType.REINFORCEMENT_LEARNING, inputs, self._blocking)
