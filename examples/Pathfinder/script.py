import json
from collections import Counter
from copy import deepcopy

from alpyne.sim import AnyLogicSim
import time
import numpy as np
import random


class PathfinderTrainer:
    # Do not change the order of these! They're based on the order of the collection in the sim
    DIRECTIONS = ["EAST", "SOUTH", "WEST", "NORTH", "NORTHEAST", "NORTHWEST", "SOUTHEAST", "SOUTHWEST"]

    def __init__(self, sim,
                 config_kwargs,
                 lr=0.7,
                 max_steps=100,
                 gamma=0.95,
                 max_epsilon=1.0, min_epsilon=0.05,
                 decay_rate=0.0005):
        # model related vars
        self.sim = sim
        self.config_kwargs = config_kwargs

        # rl related vars
        self.lr = lr
        self.max_steps = max_steps
        self.gamma = gamma
        self.max_epsilon = max_epsilon
        self.min_epsilon = min_epsilon
        self.decay_rate = decay_rate
        self.q_table = np.zeros((64, 8 if config_kwargs.get('useMooreNeighbors') else 4))

    def print_board(self, status=None):
        if status is None:
            status = self.sim.reset(**self.config_kwargs)

        obs = status.observation
        board = [["■" if i == -1 else ("⌂" if i == 1 else " ") for i in row] for row in obs['cells']]
        board[obs['pos'][0]][obs['pos'][1]] = "☺"

        border = "- " * len(obs['cells'][0])
        body = "\n".join(" ".join(row) for row in board)
        print(f"{border}{status.observation['pos']}\n{body}\n{border}{str(status.stop)[0]}")

    def get_epsilon(self, episode: int):
        return self.min_epsilon + (self.max_epsilon - self.min_epsilon) * np.exp(-self.decay_rate * episode)

    def get_action(self, state: int, episode: int) -> int:
        # episode < 0 == testing/evaluation == always use greedy
        if episode < 0 or random.uniform(0, 1) > self.get_epsilon(episode):
            action = np.argmax(self.q_table[state])
        else:
            action = random.randint(0, self.q_table.shape[1] - 1)
        return action

    def _execute(self, n_eps, in_train, config_overrides: dict = None, **kwargs):
        print_initial_board = kwargs.get('print_initial_board', False)
        log_every = kwargs.get('log_every', 0)
        verbose_log = kwargs.get('verbose_log', False)

        reward_totals = []
        for episode in range(n_eps):
            do_log = log_every > 0 and episode % log_every == 0
            if do_log:
                print(f"\nEPISODE {episode} / {n_eps}")

            # reset the environment, using default engine engine_settings
            this_config = deepcopy(self.config_kwargs)
            if config_overrides:
                this_config.update(config_overrides)
            status = self.sim.reset(**this_config)

            if episode == 0 and print_initial_board:
                self.print_board(status)

            reward_total = 0

            for step in range(self.max_steps):
                if do_log:
                    if verbose_log:
                        self.print_board(status)
                    else:
                        print(f"\tSTEP {step:2d} | {str(status.stop):5s} | {str(status.observation['pos']):7s}")

                if status.stop:
                    r, c = status.observation['pos']
                    final_reward = status.observation['cells'][r][c]

                    if do_log:
                        print(f"\t\t= {final_reward}")

                    break

                row, col = status.observation['pos']
                state = row * 8 + col  # 8x8 board
                action = self.get_action(state,
                                         episode if in_train else -1)  # use only greedy policy (-1 "episode" in testing)

                new_status = self.sim.take_action(dir=PathfinderTrainer.DIRECTIONS[action])
                new_row, new_col = new_status.observation['pos']
                new_state = new_row * 8 + new_col  # 8x8 board

                reward = status.observation['cells'][new_row][new_col]
                reward_total += reward

                if do_log:
                    print(f"\t\t-> {PathfinderTrainer.DIRECTIONS[action]} ({action}) => + {reward} = {reward_total}")

                if in_train:
                    self.q_table[state][action] = self.q_table[state][action] + self.lr * (
                            reward + self.gamma * np.max(self.q_table[new_state]) - self.q_table[state][action])

                status = new_status
            reward_totals.append(reward_total)
            if do_log:
                print(f"Score counts: {dict(Counter(reward_totals))} | Epsilon: {self.get_epsilon(episode):.3f}\n\n")

        return reward_totals

    def train(self, n_eps, **kwargs):
        return self._execute(n_eps, True, **kwargs)

    def test(self, n_eps, config_overrides: dict = None, **kwargs):
        return self._execute(n_eps, False, config_overrides=config_overrides, **kwargs)


if __name__ == "__main__":
    sim = AnyLogicSim(r"ModelExported\model.jar", engine_overrides=dict(seed=147))

    print(sim.schema)
    print("---------")

    start = time.time()

    random.seed(0)
    config = dict(numHoles=6, minStepsRequired=4, useMooreNeighbors=True, slipChance=0.0, throwOnInvalidActions=False)
    trainer = PathfinderTrainer(sim, config,
                                lr=0.7,
                                gamma=0.6,
                                decay_rate=0.005
                                )

    rewards_per_eps = trainer.train(100, log_every=50, verbose_log=False, print_initial_board=True)

    with open(r"ModelSource\qTable.json", "w") as f:  # point to/move this file in the model to have it be loaded
        json.dump(trainer.q_table.tolist(), f)

    print("Count of reward occurrence:", Counter(rewards_per_eps))
    print(f"Seconds to train: {time.time() - start}")
    print("Test reward results (no slipping):", Counter(trainer.test(10, config_overrides=dict(slipChance=0))))
    print("Test reward results (same config):", Counter(trainer.test(10)))
    print("Test reward results (2x slipping):",
          Counter(trainer.test(10, config_overrides=dict(slipChance=config['slipChance'] * 2))))
