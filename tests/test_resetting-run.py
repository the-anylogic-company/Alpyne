import unittest

from alpyne.data.constants import RunStatus

from alpyne.data.spaces import Action

from alpyne import AlpyneClient


class MyTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.client = AlpyneClient(r"Dummy Process\Exported\Dummy Process.zip", #Dummy Process Exported\model.jar",
                                   blocking=True, verbose=True)

    def test_reset_before_run(self):
        cfg = self.client.configuration_template
        cfg.interarrival_seconds = 1
        cfg.apply_multipliers = False
        cfg.logging = True
        cfg.engine_seed = 1  # reproducible results (NOTE: values may change if the model is changed)

        exp = self.client.create_reinforcement_learning(cfg)

        # trying to reset before calling run should throw an error
        #   since experiment has not been started.
        self.assertRaises(RuntimeError, lambda: exp.reset())

    def test_reset_after_run(self):
        cfg = self.client.configuration_template
        cfg.interarrival_seconds = 1
        cfg.apply_multipliers = False
        cfg.logging = True
        cfg.engine_seed = 1  # reproducible results (NOTE: values may change if the model is changed)

        exp = self.client.create_reinforcement_learning(cfg).run()

        _, info1 = exp.get_state()
        exp.reset()
        _, info2 = exp.get_state()

        # Pre-reset should be episode 1
        self.assertEqual(info1['episode_count'], 1)
        # Post-reset should be episode 2
        self.assertEqual(info2['episode_count'], 2)
        # They should have both had the same action at the same time
        self.assertEqual(info1['model_time'], info2['model_time'])

    def test_reset_after_action(self):
        cfg = self.client.configuration_template
        cfg.interarrival_seconds = 1
        cfg.apply_multipliers = False
        cfg.logging = True
        cfg.engine_seed = 1  # reproducible results (NOTE: values may change if the model is changed)

        exp = self.client.create_reinforcement_learning(cfg).run()

        # It should be episode 1, step 1 at time 1.0
        _, info1 = exp.get_state()
        self.assertEqual(info1['episode_count'], 1)
        self.assertEqual(info1['step_count'], 1)
        self.assertEqual(info1['model_time'], 1.0)

        # Take some action on the first run thru, let progress to the next step
        exp.take_action(Action(process_time=2.0))

        # Now it @ step 2 at time 2.0
        _, info2 = exp.get_state()
        self.assertEqual(info2['episode_count'], 1)
        self.assertEqual(info2['step_count'], 2)
        self.assertEqual(info2['model_time'], 2.0)

        exp.reset(cfg)

        # Resetting should send it back to the first step
        _, info3 = exp.get_state()
        self.assertEqual(info3['episode_count'], 2)
        self.assertEqual(info3['step_count'], 1)
        self.assertEqual(info3['model_time'], 1.0)

    def test_reset_after_stoptime(self):
        cfg = self.client.configuration_template
        cfg.interarrival_seconds = 1
        cfg.apply_multipliers = False
        cfg.logging = True
        cfg.engine_seed = 1  # reproducible results (NOTE: values may change if the model is changed)
        cfg.engine_stop_time = 10

        exp = self.client.create_reinforcement_learning(cfg).run()

        while not exp.is_terminal():
            exp.take_action(Action(process_time=1.0))

        # It should still be the end of the episode (time 10)
        status1, info1 = exp.get_state()
        print(status1, info1)

        self.assertEqual(status1, RunStatus.COMPLETED)
        self.assertEqual(info1['episode_count'], 1)
        self.assertEqual(info1['step_count'], 11)
        self.assertEqual(info1['model_time'], 10.0)

        exp.reset()

        # resetting should've sent it back and it should now be at the first step of episode 2
        status2, info2 = exp.get_state()
        print(status2, info2)

        self.assertEqual(info2['episode_count'], 2)
        self.assertEqual(info2['step_count'], 1)
        self.assertEqual(info2['model_time'], 1.0)

    def test_reset_after_stopcondition(self):
        cfg = self.client.configuration_template
        cfg.interarrival_seconds = 1
        cfg.apply_multipliers = False
        cfg.logging = True
        cfg.engine_seed = 1  # reproducible results (NOTE: values may change if the model is changed)

        exp = self.client.create_reinforcement_learning(cfg).run()

        while not exp.is_terminal():
            exp.take_action(Action(process_time=1.0))

        # It should still be the end of the episode (time 10)
        status1, info1 = exp.get_state()
        print(status1, info1)

        self.assertEqual(status1, RunStatus.COMPLETED)
        self.assertEqual(info1['episode_count'], 1)
        self.assertEqual(info1['step_count'], 100)
        self.assertEqual(info1['model_time'], 100.0)

        exp.reset()

        # resetting should've sent it back and it should now be at the first step of episode 2
        status2, info2 = exp.get_state()
        print(status2, info2)

        self.assertEqual(info2['episode_count'], 2)
        self.assertEqual(info2['step_count'], 1)
        self.assertEqual(info2['model_time'], 1.0)



if __name__ == '__main__':
    unittest.main()
