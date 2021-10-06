import unittest

from alpyne.data.spaces import Action

from alpyne import AlpyneClient


class MyTestCase(unittest.TestCase):
    def setUp(self) -> None:

        self.client = AlpyneClient(r"Dummy Process\Exported\Dummy Process Exported\model.jar",
                                   blocking=True, verbose=False)

    def test_new_run(self):
        cfg = self.client.configuration_template
        cfg.interarrival_seconds = 1
        cfg.apply_multipliers = False
        cfg.logging = True
        cfg.engine_seed = 1  # reproducible results (NOTE: values may change if the model is changed)

        run = self.client.create_reinforcement_learning(cfg).run()

        # step 1
        obs = run.get_observation()
        self.assertEqual(obs.agent_multiplier, 1.3)
        self.assertEqual(len(obs.times_remaining), 0)

        run.take_action(Action(process_time=3.0))

        # step 2
        obs = run.get_observation()
        self.assertEqual(obs.agent_multiplier, 0.9)
        self.assertEqual(len(obs.times_remaining), 1)
        self.assertAlmostEqual(obs.times_remaining[0], 2, delta=0.01)

        run.take_action(Action(process_time=2.0))

        # step 3
        obs = run.get_observation()
        self.assertEqual(obs.agent_multiplier, 0.7)
        self.assertEqual(len(obs.times_remaining), 2)
        self.assertAlmostEqual(obs.times_remaining[0], 1, delta=0.01)
        self.assertAlmostEqual(obs.times_remaining[1], 1, delta=0.01)

        run.take_action(Action(process_time=1.0))

        # step 4
        obs = run.get_observation()
        self.assertEqual(obs.agent_multiplier, 0.8)
        self.assertEqual(len(obs.times_remaining), 0)

        run.take_action(Action(process_time=0.5))

        # step 5
        obs = run.get_observation()
        self.assertEqual(obs.agent_multiplier, 1.5)
        self.assertEqual(len(obs.times_remaining), 0)



if __name__ == '__main__':
    unittest.main()
