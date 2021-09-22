"""

"""
import logging
from abc import abstractmethod
from typing import List
from typing import Union, Tuple, Dict, Optional, NoReturn

import numpy as np
import gym
from gym import spaces

from alpyne.client.alpyne_client import AlpyneClient
from alpyne.client.model_run import ModelRun
from alpyne.data.constants import RunStatus
from alpyne.data.single_run_outputs import SingleRunOutputs
from alpyne.data.spaces import Configuration
from alpyne.data.spaces import Observation, Action


class BaseMultiRun:
    """
    A base class for running multiple sims. It handles much of the routine logic (e.g., checking states), allowing for
    higher brevity user code.

    To use, create a subclass - e.g., `class MyMultiRun(BaseMultiRun):` - and implement the two abstract methods.

    You may also wish to override the optional methods, `on_episode_step` and `on_episode_finish`, if you wish to
    add callback logic.

    Tip: Override `on_episode_finish` if you wish to query the outputs of a sim before it gets reset.
    """
    def __init__(self, client: AlpyneClient, n_workers: int, verbose: bool = False):
        self.sims = []

        self._client = client  # keep reference for templates
        self._n_workers = n_workers  # keep reference to build sim list in `run`

        self._logger = logging.getLogger(__name__)
        self._logger.setLevel(logging.WARNING if not verbose else logging.INFO)

    @abstractmethod
    def get_configuration(self, template: Configuration) -> Configuration:
        """Set the configuration with the desired values to run an episode with.

        :param template: the template Configuration (user-defined values defaulted at 0 or None; engine-level settings
        are set to their model defaults)
        :return: the filled-out Configuration to run an episode with
        """
        raise NotImplementedError

    @abstractmethod
    def get_action(self, observation: Observation, template: Action) -> Action:
        """Set the action template with the desired values to run the next step with.

        :param observation: the current model Observation
        :param template: a template Action object (values defaulted to 0 or None)
        :return: the filled-out Action to run the step with
        """
        raise NotImplementedError

    def on_episode_step(self, sim: ModelRun) -> NoReturn:
        """
        An optional callback, fired at the start of the step event, before the action is queried.

        :param sim: The requesting run
        """
        pass

    def on_episode_finish(self, sim: ModelRun) -> NoReturn:
        """
        An optional callback, fired when the episode finishes, before resetting for the next episode.

        :param sim: The finished run
        """
        pass

    def run(self, n_episodes):
        """
        Simulate all workers for a given number of episodes.
        Once called, it will block the current thread until complete.
        This can be called multiple, subsequent times, if it's desired to run episodes in batches.

        :param n_episodes: the number of episodes to run all workers for
        """
        if not self.sims:
            self.sims = [self._client.create_reinforcement_learning(
                self.get_configuration(self._client.configuration_template))
                for _ in range(self._n_workers)]
            _ = [sim.run() for sim in self.sims]
            self._logger.info(f"Created {self._n_workers} model runs")

        n = 0
        while n < n_episodes:
            for i, sim in enumerate(self.sims):
                state, info = sim.get_state()

                # expected state
                if state == RunStatus.PAUSED:
                    # sim is waiting for an action to be taken
                    self.on_episode_step(sim)

                    obs = sim.get_observation()
                    act = self.get_action(obs, self._client.action_template)

                    self._logger.info(f"[#{i}] Current sim status/info = {state} | {info}")
                    self._logger.info(f"[#{i}] Observation = {obs}")

                    sim.take_action(act)

                # resettable conditions
                elif state in [RunStatus.COMPLETED, RunStatus.STOPPED, RunStatus.FAILED]:
                    self.on_episode_finish(sim)

                    # keep all configuration values from initial setup
                    sim.reset()

                    if state == RunStatus.FAILED:
                        # let user know what happened
                        self._logger.warning(f"Sim index {i} / ID {sim.id} encountered an error: {info}")
                    else:
                        # only increment episode count if it's been properly completed
                        n += 1
                        self._logger.info(f"Sim index {i} completed episode {n} / {n_episodes}")

                else:
                    # RUNNING; check on it next loop
                    pass

    def get_outputs(self, names: Optional[List[str]] = None) -> List[SingleRunOutputs]:
        """
        Retrieves the the current value of the specified Analysis objects (e.g., Output, histogram data, etc).

        Objects must be present on the top-level agent (commonly Main) to be detected.
        Available names can be checked via the `output_names` attribute of the `AlpyneClient` object - and
        further information from its `version` attribute.

        :param names: An optional list of object names (i.e., the Java variable names) to retrieve the values of in
        each available sim; if None, all objects will be received.
        :return: a list of objects containing attributes with the analysis object names
        """
        return [sim.get_outputs(names) for sim in self.sims]



class BaseAlpyneEnv(gym.Env):
    """
    An abstract Gym environment. It's purpose is to simplify using Alpyne with RL libraries expecting Gym environments
    (e.g., stable-baselines).

    This base class comes with the routine/common code needed to take steps and reset the sim already implemented.
    To utilize it, you need to implement the code which is model-specific. Namely:

    - Describing the observation space and the action space (a requirement for custom Gym environments).
    - Converting your `Observation` objects (taken from the underlying model) to the type described by your observation
    space.
    - Converting the action passed from the RL library to an `Action` object (that your underlying model can process).
    - Calculating the numerical reward based on the observation taken in the next step after an action.

    Additionally, there is a non-required method that you can override to serve as an additional terminal condition
    (on top of the ones setup by your model).

    """

    # The possible types that the gym Space objects can represent.
    PyObservationType = PyActionType = Union[np.ndarray, int, float,
                                             Tuple[np.ndarray, int, float, tuple, dict],
                                             Dict[str, Union[np.ndarray, int, float, tuple, dict]]]
    def __init__(self, sim: ModelRun):
        """
        Construct a new environment for the provided sim.

        Note that the configuration passed as part of its creation is what will be used for all episodes.
        If it's desired to have this be changed, the configuration values
        should be assigned to callable values or tuples consisting of (start, stop, step).
        See the `ModelRun` or `Configuration` class documentation for more information.

        :param sim: a created - but not yet started - instance of your model
        :raise ValueError: if the run has been started
        """

        # complain if the sim was already started
        if sim.id:
            raise ValueError("The provided model run should not have been started!")

        self.sim = sim.run()  # submit new run
        self.sim.wait_for_completion()  # wait until start is finished setting up

        self.observation_space = self._get_observation_space()
        self.action_space = self._get_action_space()

    @abstractmethod
    def _get_observation_space(self) -> spaces.Space:
        """ Describe the dimensions and bounds of the observation """
        raise NotImplementedError()

    @abstractmethod
    def _convert_from_observation(self, observation: Observation) -> 'BaseAlpyneEnv.PyObservationType':
        """ Convert your Observation object to the format expected by Gym """
        raise NotImplementedError()

    @abstractmethod
    def _get_action_space(self) -> spaces.Space:
        """ Describe the dimensions and bounds of the action """
        raise NotImplementedError()

    @abstractmethod
    def _convert_to_action(self, action: 'BaseAlpyneEnv.PyActionType') -> Action:
        """ Convert the action sent as part of the Gym interface to an Alpyne Action object """
        raise NotImplementedError()

    @abstractmethod
    def _calc_reward(self, observation: Observation) -> float:
        """ Evaluate the performance of the last action based on the current observation """
        # TODO decide if it's better to have this as an Observation (the alpyne-based type) \
        #  or as the type described by `observation_space`
        raise NotImplementedError()

    def _terminal_alternative(self, observation: Observation) -> bool:
        """ Optional method to add *extra* terminating conditions """
        return False

    def step(self, action: 'BaseAlpyneEnv.PyActionType') -> Tuple['BaseAlpyneEnv.PyObservationType', float, bool, Optional[dict]]:
        """
        A method required as part of the gym interface to run one step of the sim.

        Take an action in the sim and advance the sim to the start of the next step. This method returns once the sim
        has reached the next step or encounters a terminal condition.

        You may override this method to add on your own custom logic. To see how this is done, see the advanced
        usage of the documentation.
        TODO add specific reference in doc to step overriding

        :param action: The action to send to the sim (in the type expressed by your action space)
        :return: The current observation, the reward, whether the episode is in a terminal state, and debug information
        """
        alpyne_action = self._convert_to_action(action)
        self.sim.take_action(alpyne_action)

        self.sim.wait_for_completion()

        alpyne_obs = self.sim.get_observation()
        obs = self._convert_from_observation(alpyne_obs)
        reward = self._calc_reward(alpyne_obs)
        done = self.sim.is_terminal() or self._terminal_alternative(alpyne_obs)
        info = self.sim.last_state[1]  # dictionary of info
        return obs, reward, done, info

    def reset(self) -> 'BaseAlpyneEnv.PyObservationType':
        """
        A method required as part of the gym interface to revert the sim to the start.

        The sim will use the same configuration object as it was created with. If it was passed dynamic values, these
        will be re-queried.

        You may override this method to add on your own custom logic. To see how this is done, see the advanced
        usage of the documentation.
        TODO add specific reference in doc to reset overriding

        :return: The first observation (in the type expressed by your observation space)
        """
        self.sim.reset()
        self.sim.wait_for_completion()
        alpyne_obs = self.sim.get_observation()
        obs = self._convert_from_observation(alpyne_obs)
        return obs

    def render(self, mode="human") -> Optional[Union[np.ndarray, str]]:
        """
        A method required as part of the gym interface to convert the current sim to a useful format
        (e.g., for console printing or animation).

        You may override this method to add on your own custom logic. To see how this is done, see the advanced
        usage of the documentation.
        TODO aadd specific reference in doc to render overriding

        :param mode: the rendering type
        :return: varies based on the mode type
        """
        if mode != "human":
            raise ValueError("Mode not supported: " + mode)

        # lazy implementation; simple printing
        print(f"Last status: {self.sim.last_state[0]} | Debug: {self.sim.last_state[1]}")
        return
