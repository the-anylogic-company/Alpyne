import atexit
import json
import logging
import os
import subprocess
import time
from datetime import datetime
from tempfile import TemporaryDirectory
from typing import Any
import socket
from pathlib import Path
from warnings import warn

import psutil as psutil
import requests
from requests.exceptions import ConnectionError as RequestsConnectionError, HTTPError
from psutil import NoSuchProcess

from alpyne.utils import resolve_model_jar, \
    get_wildcard_paths, shorten_by_relativeness, get_resources_path, AlpyneJSONEncoder, AlpyneJSONDecoder
from alpyne.constants import EngineState, JavaLogLevel
from alpyne.outputs import TimeUnits, UnitValue
from alpyne.typing import EngineSettingKeys, Number, OutputType
from alpyne.data import SimSchema, EngineStatus, EngineSettings, SimStatus, FieldData, \
    SimConfiguration, SimAction, SimObservation
from alpyne.errors import ModelError, ExitException


def find_free_port() -> int:
    with socket.socket() as s:
        s.bind(('', 0))
        return s.getsockname()[1]


class AnyLogicSim:
    """The class for connecting to, communicating with, and controlling an AnyLogic sim model
    exported via the RL Experiment."""

    schema: SimSchema = None
    """ A class variable (static) defining the model schema, assigned on startup """

    def __init__(self, model_path: str, port: int = 0,
                 py_log_level: int | str | bool = logging.WARNING, java_log_level: int | str | bool = logging.WARNING,
                 log_id: str = None,
                 auto_lock: bool = True,
                 auto_finish: bool = False,
                 engine_overrides: dict[EngineSettingKeys, Number | datetime | TimeUnits | UnitValue] = None,
                 config_defaults: dict[str, Any] = None,
                 lock_defaults: dict = None,
                 java_exe: str = None,
                 startup_delay: float = 0.1,
                 **kwargs):
        """
        Initialize a connection to the simulation model, with arguments for defining the model setup
        and operating behavior.

        By default, the runs will use the units, start/stop time/date, and RNG seed based on what you set
        in the RL experiment. This can be overriden by passing a dictionary to ``engine_overrides``.

        :param model_path: a relative or absolute path to the exported model zip or extracted model.jar file
        :param port: what local port to run the Alpyne app on (0 = find a free one)
        :param py_log_level: verboseness for this library; expressed as levels from the ``logging`` library or a boolean
          - True defaults to INFO, False to WARNING; defaults to WARNING
        :param java_log_level: verboseness of java-side logging (writes to alpyne.log); expressed as levels from the
          ``logging`` library or a boolean - True defaults to INFO, False to WARNING; defaults to WARNING
        :param log_id: An identifier to put between the log file name and the '.log' extension,
          useful if you do not want log files to be overridden by subsequent or parallel runs;
          you can use $p for the port number, $n for a unique number (starts from 1); defaults to None (empty string)
        :param auto_lock: whether to automatically wait for a 'ready' state after each call to reset or take_action and
          return the subsequent RL status instead of None; defaults to False
        :param auto_finish: whether to automatically force the model into a FINISH state once the stop condition
          (defined in the RL experiment) is met; defaults to False
        :param engine_overrides: definition for overrides to the engine settings;
          allowed keys: seed, units, start_time, start_date, stop_time, stop_date; defaults to None
        :param config_defaults: desired default values for the Configuration values; defaults to None
        :param lock_defaults: default values to use when calling ``lock``;
          flag arg defaults to ``EngineState.ready()``, timeout to 30
        :param java_exe: Path to Java executable; if None, uses whatever is associated with the 'java' command
        :param startup_delay: Seconds to wait between launching the application and
          sending the first request to verify it's alive. Too small and it may incorrectly detect as not started up;
          too large and it adds to startup overhead. Default 0.1
        :param kwargs: Internal arguments
        :raises ModelError: if the app fails to start

        .. warning:: For ``engine_overrides``: (1) do not override the model time units unless ensuring the model
          does not have ambiguous, unit-generic logic (e.g., calls to ``time()``),
          as this can affect the logic or outputs; (2) when setting a stop time *and* date, only the last set value
          will be used.

        """
        if port == 0:
            port = find_free_port()

        if py_log_level is True:
            py_log_level = logging.INFO
        elif py_log_level is False:
            py_log_level = logging.WARNING

        logging.basicConfig(
            #level=logging.getLevelName(py_log_level),
            format=f"%(asctime)s [%(name)s @ %(lineno)s][%(levelname)8s] %(message)s",
            handlers=[logging.StreamHandler()],
        )
        logging.getLogger("alpyne").setLevel(logging.getLevelName(py_log_level))

        self.log = logging.getLogger(__name__)

        self.auto_wait = auto_lock

        self._last_status = None  # should be updated whenever `lock` is called
        self._internal_args = kwargs
        self._proc_pids: list = []  # will store all top-level and children PIDs for killing them later

        java_exe_path = self._validate_java(java_exe)

        try:
            self._temp_dir = None  # only populated if passed as zip
            self._proc = self._start_app(java_exe_path, model_path, port, java_log_level, log_id,
                                         auto_finish, startup_delay)
        except:
            raise ModelError(f"Failed to properly start the app. Check the logs.")

        # support for "hidden" arguments for host; meant for debugging or testing purposes (may include a dedicated arg if deemed useful)
        self._base_url = f"{kwargs.get('host') or 'http://127.0.0.1'}:{port}"
        self._session = requests.Session()

        # may need more than fraction of time in `_start_app` for the server to be set up
        set_schema, time_start = False, time.time()
        while not set_schema and (time.time() - time_start <= 2):
            try:
                AnyLogicSim.schema = SimSchema(
                    self._session.get(f"{self._base_url}/version").json()
                )
                set_schema = True
            except:
                time.sleep(0.5)
        if not set_schema:
            raise ModelError(f"The underlying application failed to start. Check the logs.")

        # setup the `engine_settings` instance variable to store the desired values to use
        if engine_overrides is None:
            # default to an empty dict, so the next fallback will be used
            engine_overrides = dict()
        # omitted values will cause the object to pull from the schema
        self.engine_settings = EngineSettings(**engine_overrides)

        # overwrite the 'value' in the schema for any config fields desired to be overridden
        for key, new_value in (config_defaults or dict()).items():
            AnyLogicSim.schema.configuration[key].value = new_value

        # setup lookup for lock kwargs, specifying any missing kwargs here
        self._lock_defaults = lock_defaults or dict()
        self._lock_defaults.setdefault("flag", EngineState.ready())
        self._lock_defaults.setdefault("timeout", 30)


    def _validate_java(self, java_exe: str) -> str:
        """
        :param java_exe: Java command or path to executable
        :return: The full path to the executable file
        """
        # set some default value
        if java_exe is None:
            java_exe = "java"

        # assign initial path value and resolve as needed
        java_exe_path = Path(java_exe)
        if java_exe_path.exists():
            # file or directory
            target_file = "java" + ".exe" if os.name == "nt" else ""
            if os.path.isdir(java_exe):  # look for java[.exe] in the bin folder
                try:
                    java_exe_path = next(java_exe_path.rglob(target_file))
                except StopIteration:
                    raise RuntimeError(f"Could not find {target_file} in {java_exe}")
            elif java_exe_path.name != target_file:
                raise ValueError(f"Passed executable ({java_exe_path}) does not have the expected filename ({target_file})")
        else:
            # assume java_exe is referring to a command
            locate_cmd = "where" if os.name == "nt" else "which"
            proc = subprocess.run(f"{locate_cmd} {java_exe}", capture_output=True, shell=True)
            if proc.returncode != 0:
                logs = [proc.stdout.decode().strip(), proc.stderr.decode().strip()]
                logs = [log for log in logs if log]  # remove empty strings
                raise RuntimeError(f"Failed to find path to java executable via {locate_cmd} {java_exe}. Return code: {proc.returncode}; message: {' | '.join(logs)}")
            java_exe_path = proc.stdout.decode().strip()
        return str(java_exe_path)


    def _start_app(self, java_exe_path: str, model_path: str, port: int,
                   java_log_level: int | str | bool | JavaLogLevel, log_id: str,
                   auto_finish: bool, startup_delay: float = 0.1) -> subprocess.Popen:
        """
        Execute the backend app with the desired preferences.

        :param java_exe_path:
        :param model_path:
        :param port:
        :param java_log_level:
        :param log_id:
        :param auto_finish:
        :param startup_delay:
        """
        # get the directory for the model, optionally extracting it to a temp dir if necessary
        model_jar, self._temp_dir = resolve_model_jar(model_path)
        model_dir = str(model_jar.parent.absolute())

        # temporarily change to the exported model folder's directory for starting purposes
        # (needed to make sure database is properly connected to)
        initdir = os.getcwd()

        os.chdir(model_dir)

        # get the directory for the alpyne server library
        alpyne_path = self._internal_args.get('alpyne_path', str(get_resources_path()))

        self.log.debug(f"Using Java executable {java_exe_path}")
        self.log.debug(f"Loading server from {alpyne_path}")
        self.log.debug(f"Launching using model in {model_dir}")

        # build the class path argument, reformatting to use wildcards so as to avoid the cp arg len limit
        jar_sources = get_wildcard_paths(alpyne_path) + get_wildcard_paths(str(model_dir))
        jar_sources = shorten_by_relativeness(jar_sources)
        if os.name == "nt":
            class_path = ";".join(jar_sources)
        else:
            class_path = ":".join(jar_sources)

        # convert to a java-compatible level, if not already
        if isinstance(java_log_level, bool):
            # bool -> python logging type
            if java_log_level is True:
                java_log_level = logging.INFO
            elif java_log_level is False:
                java_log_level = logging.WARNING
        if isinstance(java_log_level, (str, int)):
            # python logging type (or compatible arg) -> java logging type
            java_log_level = JavaLogLevel.from_py_level(java_log_level)

        # preliminary list of arguments
        cmdline_args = [java_exe_path,
                        "-cp", class_path,
                        "com.anylogic.alpyne.AlpyneServer",
                        "-p", f"{port}",
                        "-l", java_log_level.name,
                        "-d", initdir
                        ]
        # handle adding conditional arguments
        if log_id is not None and len(log_id) > 0:
            # only include log id flag if non-default
            cmdline_args.extend(["-i", log_id])
        if auto_finish:
            # flag without arguments
            cmdline_args.append("-f")
        # add in final argument
        cmdline_args.append(".")

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

        # Give the previous command a moment to realize
        time.sleep(startup_delay)

        # Store the IDs from both the active process and any subprocesses spawned from it,
        # for later confirming the finality of it.
        # (this may happen when the `java` command calls itself with corrected/absolute paths)
        self._proc_pids = [proc.pid] + [c.pid for c in psutil.Process(proc.pid).children(True)]

        self.log.info(f"Started app | PID(s) = {self._proc_pids}")

        atexit.register(self._quit_app)

        return proc

    def _quit_app(self):
        """
        Trigger app's self-destruct, killing any active runs, in addition to cleaning up any temporary files
        """

        # Trigger self-destruct, killing the active run
        try:
            self._session.delete(f"{self._base_url}/")
        except RequestsConnectionError:
            self.log.debug(
                "Failed to request self-destruct from server due to connection error. Attempting other methods.")

        try:
            # send arbitrary text directly to process to trigger shutdown
            stdout, stderr = self._proc.communicate('PYTHON SMITES THEE!'.encode(), 3)
            if stdout:
                self.log.debug(f"Uncaught output from app's stdout: {stdout.decode()}")
            if stderr:
                self.log.debug(f"Uncaught output from app's stderr: {stderr.decode()}")
        except subprocess.TimeoutExpired:
            self.log.debug(f"Timed out waiting to send shutdown signal; may already be dead")

        # ensure the server self-quit, otherwise attempt to force it
        try:
            rcode = self._proc.wait(1)
            self.log.info(f"Quit with return code {rcode}")
        except subprocess.TimeoutExpired:
            self.log.debug(f"Force killing app; server did not quit as expected")
            self._proc.kill()

            for pid in self._proc_pids:
                try:
                    p = psutil.Process(pid)
                    p.kill()
                except NoSuchProcess:
                    pass

        # pause to let actions take place
        time.sleep(0.1)

        # report if any PIDs still exist
        for pid in self._proc_pids:
            try:
                _ = psutil.Process(pid)
                # wait extra little bit just in case....
                time.sleep(0.4)
                _ = psutil.Process(pid)
                msg = (f"ALERT! All attempts to kill process with ID {pid} failed! "
                       f"May requires system restart or manual quit to close.")
                self.log.error(msg)
            except NoSuchProcess:
                pass

        # final cleanup
        self._session.close()

        if self._temp_dir:
            self._temp_dir.cleanup()
            self.log.info(f"Deleted temporary directory: {self._temp_dir.name}")

        # bug in java app: even on clean close, the lck file does not get removed; handle that here for now
        for file in Path(os.getcwd()).glob("*.log.lck"):
            file.unlink(missing_ok=True)  # in case it does delete it but face a race condition

        self.log.info("Completed cleanup successfully")

    def _request(self, method: str, endpoint: str, params: dict = None, data: dict = None) -> dict | None:
        """
        Submit an HTTP request to the underlying server and return the results

        :param method: The HTTP verb
        :param endpoint: The endpoint to call upon; gets appended to the base url; starting slash is not necessary
        :param params: Query parameters to add to the url
        :param data: Body to add to the request
        :return: The processed JSON output, if any (else None)
        :raises HTTPError: If there was any problem receiving or submitting the request
        """
        try:
            if data is not None:
                data = json.dumps(data, cls=AlpyneJSONEncoder)
            self.log.debug(f"Request : {method} @ {endpoint}: {params} | {data}")
            response = self._session.request(method, f"{self._base_url}/{endpoint.strip('/')}", params=params,
                                             data=data)
            self.log.debug(f"Response: {response.status_code} | {response.content}")
            if 400 <= response.status_code < 600:
                source = "Client" if response.status_code < 500 else "Server"
                reason = response.reason
                if isinstance(reason, bytes):
                    reason = reason.decode("utf-8")
                error_msg = f"{response.status_code} {source} Error: {reason} for url {response.url} -- check alpyne.log for more info"
                raise HTTPError(error_msg)
            elif response.content:
                return response.json(cls=AlpyneJSONDecoder)
        except KeyboardInterrupt:
            # reraise an exception so that any calling function will end itself and trigger the on-exit logic
            self.log.info(f"Interrupted {method} request to {endpoint}; passing.")
            raise ExitException("Exit requested.")

    def reset(self, _config: SimConfiguration | dict = None, **config_kwargs) -> SimStatus | None:
        """
        Reset the experiment to the beginning with the specified configuration.
        Any omitted values will use the default (either defined by you in the constructor or else the Java defaults).
        You should pass an object or keyword arguments (only one necessary).

        After applying, the model will auto-run (in the background) to the first call to ``takeAction``
        or its natural finish condition, whichever comes first.

        :param _config: A dictionary or dictionary subclass with configuration arguments
        :param config_kwargs: Mapping between names defined in the RL Experiment's Configuration to the desired values
        :return: Nothing (when ``auto_wait`` == False) or the model's status post-waiting (when ``auto_wait`` == True)
        """
        if _config is None:
            _config = SimConfiguration()
        elif isinstance(_config, dict):
            _config = SimConfiguration(**_config)
        _config.update(**config_kwargs)

        _ = self._request("PUT", "rl", data=dict(configuration=_config, engine_settings=self.engine_settings))
        if self.auto_wait:
            return self.lock()

    def take_action(self, _action: SimAction | dict = None, **action_kwargs) -> SimStatus | None:
        """
        Submit an action to the model. You should pass an object or keyword arguments
        (only one necessary, with the former taking higher precedence).

        :param _action: The dataclass instance or a dictionary with action arguments
        :param action_kwargs: Direct mapping between names defined in the RL Experiment's Action to the desired values
        :return: Nothing (when ``auto_wait`` == False) or the model's status (when ``auto_wait`` == True)
        """
        if _action is None:
            _action = SimAction()
        elif isinstance(_action, dict):
            _action = SimAction(**_action)
        _action.update(**action_kwargs)

        _ = self._request("PATCH", "rl", data=dict(action=_action))
        if self.auto_wait:
            return self.lock()

    def observation(self) -> SimObservation:
        """
        Queries the current Observation, regardless of the model's current state
        (i.e., it may not be requesting an action yet!).
        This function is a shorthand for ``status().observation``.

        :return: The current model observation
        """
        return self.status().observation

    def _to_status(self, data: dict) -> SimStatus:
        """
        A centralized location for the logic to handle the response from a status request
            - whether from calling `status` or `lock`.

        :param data: The output from GET /status
        :return: The SimStatus object
        """
        # all attributes in data should match those in the SimStatus object
        status = SimStatus(**data)

        # when the message it passed, assume some important, but non-halting issue
        if status.message:  # TODO throw runtime error instead?
            warn(status.message)
        return status


    def status(self) -> SimStatus:
        """
        Queries the current status of the model, regardless of its current state
        (i.e., it may not be requesting an action yet!).

        :return: The current model status
        """
        data = self._request("GET", "status")
        return self._to_status(data)

    def _engine(self) -> EngineStatus:  # TODO remove me? rename?
        """
        :return: An immutable object providing engine-level information
        """
        data = self._request("GET", "engine")
        # received data is a dict matching the EngineStatus attributes
        return EngineStatus(**data)

    def lock(self, flag: EngineState = None, timeout: int = None) -> SimStatus:
        """
        Hang the active thread until the engine is in a given state.

        :param flag: An encoded indicator for which state(s) to wait for the engine to be in. Defaults to
          ``State.ready()`` (i.e., in PAUSED, FINISHED, or ERROR) unless this object was constructed
          with different defaults (by you).
        :param timeout: Maximum wait time, in seconds. Defaults to 30 unless this object was constructed
          with different defaults (by you).
        :return: An object providing status information
        :raise TimeoutError: If timeout elapses before the desired state is reached
        """
        # replace Nones with default values, as defined in constructor
        if flag is None:
            flag = self._lock_defaults["flag"]
        if timeout is None:
            timeout = self._lock_defaults["timeout"]

        names = [state.name for state in EngineState if flag & state]
        data = self._request("GET", "lock", params=dict(state=names, timeout=int(timeout * 1000)))
        status = self._to_status(data)
        self._last_status = status
        return status

    def outputs(self, *names: str) -> list[OutputType] | dict[str, OutputType] | None:
        """
        Retrieves the values of any analysis-related objects in the top-level agent (if any exist), as detailed
        further in the AnyLogic Help article `Data analysis items <https://anylogic.help/anylogic/analysis/index.html>`_
        and its subpages.

        Each of the analysis-related objects have a type of the same name implemented in this library.
        Output objects for plain scalar types are converted to their natural python equivalent
        (e.g., String -> str, double -> float); types units attached make use of the custom ``UnitValue`` type.

        :param names: The names (as defined in the sim) of objects to query the current value for;
            passing nothing will get everything
        :return: The desired values; provided as a list when explicit names are used (in the specified order),
            otherwise in a dictionary keyed by the names
        """
        # as the next step changes 'names', first record what the return should be
        ret_as_list = bool(names)

        # put all names if none were provided
        if not names:
            names = list(self.schema.outputs.keys())

        # instant return if model has no outputs
        if not names:
            return list() if ret_as_list else dict()

        data = self._request("GET", "outputs", params=dict(names=names))
        # received data contains a list of ModelData objects so that their types are included,
        #   which allows us to pull their converted, non-raw (non-dict / typed) values out.

        # initially store as a dict
        outputs = dict()
        for model_data in data['model_datas']:
            md = FieldData(**model_data)
            outputs[md.name] = md.py_value
        if ret_as_list:
            # explicitly use provided order in case values returned otherwise
            return [outputs[name] for name in names]
        return outputs
