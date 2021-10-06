#import sys
#sys.path.insert(0, r"C:\Users\Tyler Wolfe-Adam\Documents\Project Pypeline\Case 2\AL_Pyne\source\PythonWorkspace\Alpyne")

import unittest
import random
from alpyne.client.alpyne_client import AlpyneClient


class SetupTestCases(unittest.TestCase):
    def setUp(self) -> None:
        self.client = AlpyneClient(r"Dummy Process\Exported\Dummy Process.zip", verbose=True)

    def test_templates(self):
        cfg = self.client.configuration_template
        self.assertEqual(cfg.interarrival_seconds, 0)
        self.assertEqual(cfg.apply_multipliers, None)
        self.assertEqual(cfg.logging, None)

        obs = self.client.observation_template
        self.assertEqual(obs.agent_multiplier, 0)
        self.assertEqual(obs.times_remaining, None)

        act = self.client.action_template
        self.assertEqual(act.process_time, 0)

        ops = self.client.output_names
        # Sort both b/c order may change
        self.assertListEqual(sorted(ops),
                             sorted(['delayDistribution', 'processSizeDS', 'agentsInLimbo', 'agentsProcessed']))

    def test_config_creations(self):
        cfg1 = self.client.configuration_template
        cfg2 = self.client.create_default_rl_inputs()
        self.assertEqual(cfg1, cfg2)

    def test_config_static(self):
        cfg = self.client.configuration_template
        self.assertEqual(cfg.interarrival_seconds, 0)

        INTERARRIVAL_SECS = 1
        cfg.interarrival_seconds = INTERARRIVAL_SECS
        self.assertEqual(cfg.interarrival_seconds, INTERARRIVAL_SECS)

    def test_config_dynamic_range(self):
        cfg = self.client.configuration_template
        self.assertEqual(cfg.interarrival_seconds, 0)

        INTERARRIVAL_SECS = (1, 5, 2)
        cfg.interarrival_seconds = INTERARRIVAL_SECS
        self.assertEqual(cfg.interarrival_seconds, 1)
        self.assertEqual(cfg.interarrival_seconds, 3)
        self.assertEqual(cfg.interarrival_seconds, 5)
        self.assertEqual(cfg.interarrival_seconds, 1)

    def test_config_dynamic_callable(self):
        cfg = self.client.configuration_template
        self.assertEqual(cfg.interarrival_seconds, 0)

        INTERARRIVAL_SECS = lambda: random.randint(1, 10)

        random.seed(1)
        expected = [INTERARRIVAL_SECS() for _ in range(5)]

        # reset seed
        random.seed(1)
        self.assertListEqual([cfg.interarrival_seconds for _ in range(5)], expected)

    def test_action_static(self):
        act = self.client.action_template
        self.assertEqual(act.process_time, 0)

        PROC_TIME = 2
        act.process_time = PROC_TIME
        self.assertEqual(act.process_time, PROC_TIME)


if __name__ == '__main__':
    unittest.main()