import os
import numpy as np
from stable_baselines3 import PPO


class SMGPolicyQuerier:
    def __init__(self, file: str):
        if not os.path.exists(file):
            raise FileNotFoundError(f"Cannot create a querier object, policy file '{file}' not found!")
        self.policy = PPO.load(file)

    def query(self, input_: list) -> float:
        """
        Make a single inference of the loaded policy.

        :param input_: A single input in the sim's natural observation space
        :return: The output value, in the sim's natural action space
        """
        # the policy expects scaled inputs and produces scaled outputs, so we'll compensate for both
        obs = np.array([input_[0] / 5000.0, input_[1] / 25.0]) - 1
        prediction = self.policy.predict(obs)
        act = prediction[0]
        return (act[0] + 1) * 25


if __name__ == '__main__':
    querier = SMGPolicyQuerier("SMG_PPO.zip")
    print(querier.query([0, 25]))
    print(querier.query([0, 50]))
    print(querier.query([5000, 25]))
    print(querier.query([10000, 0]))
