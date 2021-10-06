import unittest

from alpyne import AlpyneClient


class MyTestCase(unittest.TestCase):
    def test_something(self):
        """ Starting multiple clients will cause the 2nd app to terminate, with run creation going to the 1st """
        self.client1 = AlpyneClient(r"Dummy Process\Exported\Dummy Process Exported\model.jar",
                                   blocking=True, verbose=True)
        cfg1 = self.client1.configuration_template
        cfg1.interarrival_seconds = 1
        cfg1.apply_multipliers = False
        cfg1.logging = True
        cfg1.engine_seed = 1  # reproducible results (NOTE: values may change if the model is changed)

        run1 = self.client1.create_reinforcement_learning(cfg1).run()

        self.client2 = AlpyneClient(r"Dummy Process\Exported\Dummy Process Exported\model.jar",
                                    blocking=True, verbose=True)
        cfg2 = self.client2.configuration_template
        cfg2.interarrival_seconds = 100
        run2 = self.client2.create_reinforcement_learning(cfg2).run()

        self.assertEqual(run1.id, 1)
        self.assertEqual(run2.id, 2)



if __name__ == '__main__':
    unittest.main()
