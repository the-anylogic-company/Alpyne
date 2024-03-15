"""
Finds the optimal number of inspectors for each shift in the schedule, defined in the Excel file in the model
source, then writes them back to the file.

The strategy uses Bayesian Optimization for its sample efficiency.

Each shift has its own AnyLogicSim object and instance of the optimizer so that each iteration (round of suggestion)
can have the runs executing in parallel. To help facilitate the logic, a custom class is used to consolidate settings
and behaviors.
"""
import os

import numpy as np

from typing import SupportsFloat

from gymnasium import spaces
from gymnasium.core import ActType, ObsType
from stable_baselines3 import SAC
from stable_baselines3.common.env_util import make_vec_env

from alpyne.data import SimStatus, SimConfiguration
from alpyne.env import AlpyneEnv
from alpyne.sim import AnyLogicSim
from alpyne.utils import next_num


class ABCAEnv(AlpyneEnv):
    def __init__(self, sim: AnyLogicSim):
        super().__init__(sim)
        # need to be a single-valued array - i.e., (1,) - for training algorithm
        self.observation_space = spaces.Box(low=0, high=2, shape=(1,))
        # order: num Res A, num Res B, process delay, conveyor speed
        self.action_space = spaces.Box(low=np.array([1, 1, 1, 1e-6]),
                                       high=np.array([20, 20, 12, 15]))

    def _get_config(self) -> SimConfiguration | None:
        return SimConfiguration(
            arrivalRate=np.random.choice(np.arange(0.25, 2.25, 0.25)),  # random each run
            sizeBufferQueues=15  # 90 == default size
        )

    def _get_obs(self, status: SimStatus) -> ObsType:
        # Pack the arrival rate for this run - retrieved from the RL Observation - into the format
        # specified by this class's observation_space
        return np.array([status.observation['arrivalRate']])

    def _to_action(self, action: ActType) -> dict:
        # Explicitly round the value for resources (int values) and convert to simple types
        return dict(numResourceA=int(action[0].round()), numResourceB=int(action[1].round()),
                    processDelay=float(action[2]), conveyorSpeed=float(action[3]))

    def _calc_reward(self, status: SimStatus) -> SupportsFloat:
        # based on cost per product (CPP) value retrieved from the RL Observation
        rew = -status.observation['costPerProduct']
        # fail condition accumulates extra large negative
        # (True if the buffer queues become overloaded)
        if status.stop:
            rew -= 1_000
        # ~~note: discovered (approximate) max for CPP for 6mo is 15k~~
        return rew

    def _is_terminal(self, status: SimStatus) -> bool:
        # True if the buffer queues become overloaded
        return status.stop

    def _is_truncated(self, status: SimStatus) -> bool:
        # Stop time/date is reached
        return status.progress >= 1.0


if __name__ == '__main__':
    assert os.path.exists(r"ModelExported/model.jar"), r"Missing file 'ModelExported/model.jar'. To fix, create the folder if it does not exist and export/unzip in-place."

    # This keeps the default stop time of 180 days
    env = make_vec_env(lambda: ABCAEnv(AnyLogicSim("ModelExported/model.jar",
                                                       engine_overrides=dict(seed=next_num)  # random sim seed each run
                                                       )
                                           ),
                       n_envs=5,  # parallel environments
                       seed=1  # fixed seed for action space sampling
                       )
    # Slightly tuned parameters; should get to mean reward of ~-85 in 5-10 min
    policy = SAC("MlpPolicy", env, tensorboard_log="tblog",
                 gamma=0.9, tau=0.08, target_update_interval=128, replay_buffer_kwargs=dict(),
                 batch_size=256, gradient_steps=1, policy_kwargs=dict(net_arch=[512, 512]),
                 seed=1,  # fixed seed for training algorithm
                 verbose=1)
    policy.learn(10_000, log_interval=100)
    policy.save("ABCA_SAC")
