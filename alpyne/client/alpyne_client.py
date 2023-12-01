import atexit
import logging
import os
import shutil
import subprocess
from http import HTTPStatus
from tempfile import TemporaryDirectory
from typing import List, Literal
import socket

import psutil as psutil
from psutil import NoSuchProcess

from alpyne.client.http_client import HttpClient
from alpyne.client.utils import resolve_model_jar, \
    get_wildcard_paths, shorten_by_relativeness, get_resources_path, space_name_orders
from alpyne.data.constants import State, PyLogLevel, JavaLogLevel
from alpyne.data.model_data import ModelTemplate, ModelVersion, EngineStatus, ExperimentStatus, EngineSettings
from alpyne.data.model_error import ModelError
from alpyne.data.spaces import Configuration, Action, Observation

PyLogType = Literal[PyLogLevel.CRITICAL, PyLogLevel.ERROR, PyLogLevel.WARNING, PyLogLevel.INFO, PyLogLevel.DEBUG]
JavaLogType = Literal[JavaLogLevel.SEVERE, JavaLogLevel.WARNING, JavaLogLevel.INFO, JavaLogLevel.CONFIG, JavaLogLevel.FINE, JavaLogLevel.FINER, JavaLogLevel.FINEST]

def find_free_port() -> int:
    with socket.socket() as s:
        s.bind(('', 0))
        return s.getsockname()[1]

class AlpyneClient:
    """
    The main object to initiate the Alpyne application and derive simulation runs from.
    """

    def __init__(self, model_loc: str, port: int = 0,
                 py_log_level: PyLogType = PyLogLevel.WARNING, java_log_level: JavaLogType = JavaLogLevel.INFO,
                 **kwargs):
        """
        :param model_loc: a relative or absolute path to the exported model zip or extracted model.jar file
        :param blocking: whether to halt the calling Python thread during time-consuming tasks (e.g., advancing the sim)
        :param port: what local port to run the Alpyne app on
        :param py_log_level: constant representing a python log level for the python client
        :param java_log_level: constant representing a Java log level for the server (writes to files)
        :param kwargs: optional arguments
        :raises ModelError: if the app fails to start
        """
        if port == 0:
            port = find_free_port()

        logging.basicConfig(
            level=py_log_level.name,
            format=f"%(asctime)s [%(name)s @ %(lineno)s][%(levelname)8s] %(message)s",
            handlers=[logging.StreamHandler()],
        )

        self.log = logging.getLogger(__name__)

        self._internal_args = kwargs
        self._proc = self._start_app(model_loc, port, java_log_level)

        try:
            self._http_client = HttpClient(f"http://127.0.0.1:{port}")
            _, _, output = self._http_client.get("/version")

            self.version = ModelVersion(output)
            self.template = ModelTemplate(self.version)
        except:
            raise ModelError(f"Failed to properly start the app. Check the logs.")

        # set the name order for the RL spaces
        alp = kwargs.get('alp')
        if alp:
            Configuration._NAME_ORDER, Observation._NAME_ORDER, Action._NAME_ORDER = space_name_orders(alp)

    def _start_app(self, model_loc: str, port: int, java_log_level: JavaLogType) -> subprocess.Popen:
        """
        Execute the backend app with the desired preferences.

        :param model_loc:
        :param port:
        :param java_log_level:
        """
        # get the directory for the model, optionally extracting it to a temp dir if necessary
        model_jar, temp_dir = resolve_model_jar(model_loc)
        model_dir = str(model_jar.parent.absolute())

        # temporarily change to the exported model folder's directory for starting purposes
        # (needed to make sure database is properly connected to)
        initdir = os.getcwd()

        os.chdir(model_dir)

        # get the directory for the alpyne server library
        alpyne_path = self._internal_args.get('alpyne_path', str(get_resources_path()))

        self.log.debug(f"Loading server from {alpyne_path}")
        self.log.debug(f"Launching using model in {model_dir}")

        # build the class path argument, reformatting to use wildcards so as to avoid the cp arg len limit
        jar_sources = get_wildcard_paths(alpyne_path) + get_wildcard_paths(str(model_dir))
        jar_sources = shorten_by_relativeness(jar_sources)
        if os.name == "nt":
            class_path = ";".join(jar_sources)
        else:
            class_path = ":".join(jar_sources)

        cmdline_args = ["java",
                        "-cp", class_path,
                        "com.anylogic.alpyne.AlpyneServer",
                        "-p", f"{port}",
                        "-l", java_log_level.name,
                        "."
                        ]

        self.log.debug(f"Executing:\n{' '.join(cmdline_args)}\n")

        try:
            proc = subprocess.Popen(cmdline_args,
                                    stdin=subprocess.PIPE,  # Needed for quitting the app
                                    )
        except FileNotFoundError:
            raise RuntimeError("Java not found. Please check your system path.")

        # return back to original directory
        os.chdir(initdir)

        returncode = proc.poll()
        if returncode is not None and returncode != 0:
            err_message = proc.stderr.readlines()
            raise EnvironmentError(f"Process returned code: {returncode}; message: {err_message}")

        self.log.info(f"Started app | PID = {proc.pid}")

        atexit.register(self._quit_app, temp_dir)

        return proc

    def _quit_app(self, temp_dir: TemporaryDirectory = None):
        """
        Trigger app's self-destruct, killing any active runs, in addition to cleaning up any temporary files

        :param temp_dir: The location of the temporary unzipped model, or None if the app was started with a \
            non-temporary model
        """
        # Trigger self-destruct, killing the active run
        self._http_client.api_request("/", "DELETE")
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
            rcode = self._proc.wait(1)
            self.log.info(f"Quit with return code {rcode}")
        except Exception as e:
            self.log.error(f"Force killing app; did not quit as expected: {e}")
            self._proc.kill()

        try:
            _ = psutil.Process(self._proc.pid)
            msg = "All attempts to force kill app failed. Requires system restart or manual quit to close."
            self.log.error(msg)
            print(f"[ALPYNE: FATAL ERROR] {msg}")
        except NoSuchProcess:
            pass

        if temp_dir:
            temp_dir.cleanup()
            self.log.info(f"Deleted temporary directory: {temp_dir.name}")

    def reset(self, config: Configuration, settings: EngineSettings = None) -> bool:
        """
        :param config: RL Experiment's Configuration
        :param settings: Specification of engine settings; if omitted, default values (as defined in the exported experiment) are used
        :return: Whether the reset request was accepted
        """
        # override a generated template with user specified values
        modified_config = self.template.configuration
        modified_config.__dict__.update(config.__dict__)

        # override a generated template with user specified values (when provided)
        modified_settings = self.template.engine_settings
        if settings is not None:
            modified_settings.__dict__.update(settings.__dict__)

        code, _, _ = self._http_client.put("/rl", dict(configuration=modified_config, engineSettings=modified_settings))
        return code == HTTPStatus.CREATED

    def step(self, action: Action) -> bool:
        """
        :param action: RL Experiment's Action
        :return: Whether the action request was accepted
        """
        # override a generated template with user specified values
        modified_action = self.template.action
        modified_action.__dict__.update(action.__dict__)

        code, _, _ = self._http_client.patch("/rl", dict(action=action))
        return code == HTTPStatus.ACCEPTED

    def rl_status(self) -> ExperimentStatus:
        """

        :return: An immutable object providing experiment-level information
        """
        _, _, body = self._http_client.get("/rl")
        return ExperimentStatus(**body)

    def engine_status(self) -> EngineStatus:
        """

        :return: An immutable object providing engine-level information
        """
        _, _, body = self._http_client.get("/engine")
        return EngineStatus(**body)

    def wait_for(self, flag: State, timeout: int) -> ExperimentStatus:  # TODO need to change to EngineStatus in server then update here
        """
        Hang the active thread until the engine is in a given state.
        :param flag: An encoded indicator for which state(s) to wait for the engine to be in
        :param timeout: Maximum wait time, in seconds
        :return: An immutable object providing engine-level information
        """
        names = [state.name for state in State if flag & state]
        code, _, body = self._http_client.get("/engine/lock", dict(state=names, timeout=timeout*1000))
        status = ExperimentStatus(**body)
        if code == HTTPStatus.REQUEST_TIMEOUT:
            raise TimeoutError(f"Failed to reached any of '{flag}' before timeout ({timeout}). Current status: {status}")
        return status

    def outputs(self, outputs: List[str]) -> dict:
        """
        :param outputs: The names of output objects to query the current value of
        :return: A mapping between the output name and its value
        """
        code, _, body = self._http_client.get("/outputs", dict(names=outputs))  # TODO make this singular in the server then updat ehere
        return body
