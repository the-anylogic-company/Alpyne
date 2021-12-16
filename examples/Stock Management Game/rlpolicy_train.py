import numpy as np
from gym import spaces
try:  # handle sb2 or sb3
    # v- stops pycharm from complaining
    # noinspection PyUnresolvedReferences
    from stable_baselines3 import PPO, A2C
except ModuleNotFoundError:
    try:
        # v- stops pycharm from complaining
        # noinspection PyUnresolvedReferences
        from stable_baselines import PPO2 as PPO
    except ModuleNotFoundError:
        raise ModuleNotFoundError("Need stable baselines to run this example")
    
from alpyne.client.alpyne_client import AlpyneClient
from alpyne.client.model_run import ModelRun
from alpyne.data.spaces import Observation, Action

from alpyne.client.abstract import BaseAlpyneEnv


class MyStockGameEnv(BaseAlpyneEnv):
    """
    Custom Gym Environment for the Stock Management Game example model.

    Observation:
        Type: Box(2)
        Index   Name            Min     Max
        0       stock_amount    0.0     10000.0
        1       last_order_rate 0.0     50.0

    Actions:
        Type: Box(1)
        Index   Name            Min     Max
        0       order_rate      0       50.0

    Reward:
        1 if stock amount at 5000; falls off quartically, reaching 0 at +- 3000 and bottoming out at -1 by +- 3500
        (Reference: https://www.desmos.com/calculator/vlaaprjxvv)

    Episode termination:
        Default episode end is at/after 2 years.

        This may be different based on the configuration passed with the provided sim
        or if any additional terminal criteria is implemented.
    """

    def __init__(self, sim: ModelRun):
        super().__init__(sim)
        self.steps_near_bounds = 0  # number of steps the sim has spent near the stock bounds

    def _get_observation_space(self) -> spaces.Space:
        return spaces.Box(low=np.array([0.0, 0.0]), high=np.array([10000.0, 50.0]))

    def _convert_from_observation(self, observation: Observation):
        return np.array([observation.stock_amount, observation.last_order_rate])

    def _get_action_space(self) -> spaces.Space:
        return spaces.Box(low=0.0, high=50.0, shape=(1,), dtype=np.float16)

    def _convert_to_action(self, action: np.ndarray) -> Action:
        return Action(order_rate=float(action[0]))

    def _calc_reward(self, observation: Observation) -> float:
        return max(-1,-125e-16*(observation.stock_amount-5000)**4+1)

    def _terminal_alternative(self, observation: Observation) -> bool:
        """ Additional logic to stop the sim if too long is spent in the extremes ends """
        if 100 <= observation.stock_amount <= 9900:
            self.steps_near_bounds = 0
        else:  # +- 100 from the bounds
            self.steps_near_bounds += 1

        return self.steps_near_bounds >= 5  # arbitrarily chosen small(ish) number


if __name__ == '__main__':

    client = AlpyneClient(r"Exported\StockManagementGame\model.jar")

    # create new model run from basic configuration
    cfg = client.configuration_template
    cfg.acquisition_lag_days = 1
    sim = client.create_reinforcement_learning(cfg)



    # wrap in our custom gym environment
    env = MyStockGameEnv(sim)

    # # (optional) to distribute across parallel runs,
    # #               vectorize the environment with stable-baselines' method
    # env = make_vec_env(env, n_envs=4)

    # pass it to stable-baselines for RL training
    model = PPO('MlpPolicy', env, verbose=1)

    model.learn(500000)
    model.save("StockGamePolicy_PPO.zip")
