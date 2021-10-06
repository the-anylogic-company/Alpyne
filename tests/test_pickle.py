import pickle
import unittest

from alpyne.data.spaces import Action

# TODO

class MyTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.action = Action(process_time=10)

    def test_pickle(self):
        print(pickle.dumps(self.action))
        self.assertTrue(False)


if __name__ == '__main__':
    unittest.main()
