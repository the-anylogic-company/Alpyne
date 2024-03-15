import logging
import os
from typing import SupportsFloat, Any

import numpy as np
from gymnasium import spaces
from gymnasium.core import ActType, ObsType, RenderFrame
from gymnasium.experimental.wrappers import RescaleObservationV0
from gymnasium.experimental.wrappers.lambda_action import RescaleActionV0
from gymnasium.wrappers import NormalizeReward
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import EvalCallback
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv

from alpyne.data import SimStatus
from alpyne.env import AlpyneEnv
from alpyne.sim import AnyLogicSim


class StockGameEnv(AlpyneEnv):
    """
    Custom Gym Environment for the Stock Management Game example model.

    Observation:
        Type: Box(1)
        Name            Min     Max         Notes
        stock           0.0     10000.0
        last_stock      0.0     10000.0     Stock at last action
        demand          0.0     50.0        (Provided by the sim but not intended to be trained with)
        order_rate      0.0     50.0

    Actions:
        Type: Box(1)
        Name            Min     Max         Notes
        order_rate      0       50.0        per day

    Reward:
        1 if stock amount at 5000; falls off quartically

    Episode termination:
        If the stock amount falls beyond the configured limits
    """
    def __init__(self, sim: AnyLogicSim, ):
        super().__init__(sim)

        self.observation_space = spaces.Box(0, np.array([10_000, 50]), shape=(2,))
        self.action_space = spaces.Box(0, 50, shape=(1,))
        self.render_mode = "human"

        self._last_obs = None
        self._last_info = None
        self._last_action = None
        self._last_rew = None

    def _get_obs(self, status: SimStatus) -> ObsType:
        return np.clip(
            np.array([status.observation['stock'], status.observation['order_rate']]),
            self.observation_space.low,
            self.observation_space.high
        )

    def _calc_reward(self, status: SimStatus) -> SupportsFloat:
        return max(-1.0, -((status.observation['stock']-5000)/2500)**4+1)

    def _to_action(self, act: ActType) -> dict:
        return dict(order_rate=act[0])

    def _is_truncated(self, status: SimStatus) -> bool:
        return status.time > 10_000

    def _get_info(self, status: SimStatus) -> dict[str, Any] | None:
        info = super()._get_info(status)
        info['demand'] = status.observation['demand']
        return info

    def reset(self, *, seed: int | None = None, options: dict[str, Any] | None = None) -> tuple[ObsType, dict[str, Any]]:
        obs, info = super().reset(seed=seed, options=options)
        self._last_obs = obs
        self._last_info = info
        return obs, info

    def step(self, action: ActType) -> tuple[ObsType, SupportsFloat, bool, bool, dict[str, Any]]:
        obs, rew, term, trunc, info = super().step(action)
        self._last_action = action
        self._last_obs = obs
        self._last_info = info
        self._last_rew = rew
        return obs, rew, term, trunc, info

    def render(self) -> RenderFrame | list[RenderFrame] | None:
        print(f"{self._last_action} -> {self._last_obs}  = {self._last_rew:.2f} ({self._last_info}")


if __name__ == '__main__':
    assert os.path.exists(r"ModelExported/model.jar"), r"Missing file 'ModelExported/model.jar'. To fix, create the folder if it does not exist and export/unzip in-place."
    sim = AnyLogicSim(
        r"ModelExported/model.jar",
        config_defaults=dict(acquisition_lag_days=1, action_recurrence_days=30, stop_condition_limits=[500, 9500], demand_volatility=5),)

    # wrap sim in our custom gym environment, then in other transformative wrappers
    env = StockGameEnv(sim)
    env = NormalizeReward(env)
    env = RescaleObservationV0(env, -1, 1)
    env = RescaleActionV0(env, -1, 1)
    env = DummyVecEnv([lambda: Monitor(env)])

    eval_callback = EvalCallback(env,
                                 eval_freq=250, n_eval_episodes=1,
                                 deterministic=True, render=True)

    # pass it to stable-baselines for RL training
    model = PPO("MlpPolicy", env, learning_rate=.0003, n_steps=320, verbose=1)

    # should be enough to get a decent reward in ~5-10 min train time
    model.learn(5000, callback=eval_callback)
    model.save("SMG_PPO.zip")

