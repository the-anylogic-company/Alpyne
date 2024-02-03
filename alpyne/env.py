import dataclasses
from abc import abstractmethod
from typing import Any, SupportsFloat

import numpy as np
from gymnasium import Env, spaces
from gymnasium.core import ObsType, ActType

from alpyne.sim import AnyLogicSim
from alpyne.constants import EngineState
from alpyne.data import SimStatus, SimConfiguration, SimAction, FieldData


# def transform_observation(obs_or_field: Any, obs_space: ObsType) -> ObsType:  # TODO test this before adding it in formally
#     """
#     Attempt to transform the given observation (from the AnyLogic sim), including any nested fields,
#         to the defined gymnasium observation space.
#
#     The logic is setup to handle cases such as wrapping scalars to lists and filtering unspecified fields.
#
#     :param obs_or_field: The observation received from AnyLogic or any fields from an observation (relevant for recursive calls)
#     :param obs_space: The defined intended observation space defined for the RL training
#     :return: A transformed version of the AnyLogic observation
#     :raise ValueError: For non-implemented space types or when a field type could not be recognized
#     """
#     if obs_space.contains(obs_or_field):
#         # already in correct format
#         return obs_or_field
#     elif isinstance(obs_space, (spaces.Box, spaces.MultiDiscrete, spaces.MultiBinary)):
#         # in some list-like structure; ensure the data type and shape are correct
#         return np.array(obs_or_field, dtype=obs_space.dtype).reshape(obs_space.shape)
#     elif isinstance(obs_space, spaces.Dict):
#         # in a dictionary, apply on each expected key in the space recursively
#         # note: this naturally handles filtering extra fields given from the model that aren't in the obs_space
#         return {
#             key: transform_observation(obs_or_field[key], obs_space[key]) for key in obs_space.spaces
#         }
#
#     raise ValueError(f"Cannot transform {obs_or_field} for {obs_space}")
#
#
# def transform_action(action: ActType, act_schema: dict[str, FieldData]) -> dict: # TODO test this before adding it in formally
#     """
#     Attempt to transform the given action to the defined action schema defined in the model.
#
#     The logic is setup to handle cases such as unwrapping lists-of-one intended to be scalars.
#
#     :param action_or_field: The action received as part of the RL training
#     :param act_schema: The simulation model's action schema
#     :return: A dictionary able to be passed to the simulation model
#     :raise ValueError: For non-implemented space types or when a field type could not be recognized
#     """
#     if not isinstance(action, spaces.Dict):
#         raise ValueError(f"Cannot transform {action} for {act_schema}")
#
#     return {
#         name: data.flatten()[0] if isinstance(data, np.ndarray) and
#                                    act_schema[name].py_type in (int, float) else data
#         for name, data in action.items()
#     }


class AlpyneEnv(Env):
    """
    A mostly-complete implementation of an environment using the Gymnasium interface, setup to handle most of the routine
    communication with a provided instance of the AnyLogicSim.

    To use it, you'll need to either create a subclass or use the provided :func:`make_alpyne_env` function.

    When subclassing, you are required to implement the `_calc_reward` function and
    extend the `__init__` function to assign the `observation_space` and `action_space` class attributes.

    You may need to override the other "private" functions if their logic do not match your scenario.
    """

    # TODO "The provided logic contains automatic handling of wrapping/unwrapping scalars-as-values (passed by AnyLogic)
    #     to lists-of-one (common requirement for RL libraries) and filtering excess fields provided
    #     in the sim's observation which are not in the observation space."

    def __init__(self, sim: AnyLogicSim):
        self._sim = sim
        self.observation_space: ObsType = None
        self.action_space: ActType = None

    def _get_config(self) -> dict | None:
        """
        Called at the start of each new episode. If a Configuration is returned, that will take highest priority.
        Otherwise, if None is returned, it will use the default configuration (either defined by you in the sim constructor or Java defaults).
        """
        return None

    def _get_obs(self, status: SimStatus) -> ObsType:
        """
        Convert the current status of your model to the defined observation type.

        :raises NotImplementedError: If your observation space deviates from the assumptions (thus requiring you to implement them)
        """
        if not isinstance(self.observation_space, spaces.Dict):
            raise NotImplementedError(
                "Cannot infer the assignment for a non-Dict type (you will need to overload this function with a correct implementation)")
        #obs = transform_observation(status.observation, self.observation_space)
        obs = status.observation
        # fail if validation check does not pass
        if not self.observation_space.contains(obs):
            raise NotImplementedError(
                f"The processed observation does not fit within the observation space (you will need to overload this function with a correct implementation): {obs}")
        return obs

    @abstractmethod
    def _calc_reward(self, status: SimStatus) -> SupportsFloat:
        raise NotImplementedError()

    def _to_action(self, act: ActType) -> dict:
        """
        Convert the action received by the code/library using this environment to an action instance to be passed to the sim.
        """
        if not isinstance(self.action_space, spaces.Dict):
            raise NotImplementedError(
                "Cannot infer the assignment for a non-Dict type (you will need to overload this function with a correct implementation)")
        #return transform_action(act, self._sim.schema.action)
        return act

    def _get_info(self, status: SimStatus) -> dict[str, Any] | None:
        """ Provide some (technically optional) auxiliary diagnostic information """
        return dict(time=status.time, sequence_id=status.sequence_id)

    def _is_terminal(self, status: SimStatus) -> bool:
        """
        Whether the sim is considered 'terminal' by gymnasium standards
        - in summary, the episode is ended due to conditions explicit to the model definition (e.g., some "win" or "lose" condition, completion of full work day or other times on a model with a finite time horizon).

        For a more complete/correct definition, see: https://gymnasium.farama.org/tutorials/gymnasium_basics/handling_time_limits/

        For a simulation-based definition of finite vs infinite time horizons, see: https://rossetti.github.io/RossettiArenaBook/ch3-finiteVsInfinite.html

        The default assumption is based on the value of the 'stop' condition (i.e., "Simulation run stop condition" in the RL experiment)
        or the simulation being in the "FINISHED" or "ERROR" state (e.g., from the model having called `finish()`, the stop time/date being met, logical error).
        """
        return status.stop or EngineState.FINISHED in status.state

    def _is_truncated(self, status: SimStatus) -> bool:
        """
        Whether the sim is considered 'truncated' by gymnasium standards
        - in summary, the episode is ended due to conditions not explicit to the model definition
        (e.g., artificial time limit on a model with an infinite time horizon).

        For a more complete/correct definition, see: https://gymnasium.farama.org/tutorials/gymnasium_basics/handling_time_limits/

        For a simulation-based definition of finite vs infinite time horizons, see: https://rossetti.github.io/RossettiArenaBook/ch3-finiteVsInfinite.html

        The default assumption is the model is never truncated (i.e., False).
        """
        return False

    def reset(self, *, seed: int | None = None, options: dict[str, Any] | None = None) -> tuple[
        ObsType, dict[str, Any]]:
        """ Resets the simulation model, advancing to the first stopping point (usually a call to `takeAction`)."""

        # TODO consider having the seed set the sim seed or allow passing engine updates to ``options``

        super().reset(seed=seed, options=options)

        # return type based on client constructor
        status: SimStatus | None = self._sim.reset(self._get_config())
        if status is None:  # handle if auto_wait == False; we want the status when it's ready
            status = self._sim.lock()

        return self._get_obs(status), self._get_info(status)

    def step(self, action: ActType) -> tuple[ObsType, SupportsFloat, bool, bool, dict[str, Any]]:
        """ Submit an action to the simulation model and run to the next stopping point (the next call to ``takeAction``
         or any terminating condition)."""

        alpyne_action = self._to_action(action)
        # return type based on sim constructor
        status: SimStatus | None = self._sim.take_action(alpyne_action)
        if status is None:  # handle if auto_wait == False; we want the status when it's ready
            status = self._sim.lock()

        obs = self._get_obs(status)
        return (obs, self._calc_reward(status),
                self._is_terminal(status), self._is_truncated(status),
                self._get_info(status))
