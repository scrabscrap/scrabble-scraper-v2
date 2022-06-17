import json
import unittest

import threadanalyze


class MyTestCase(unittest.TestCase):
    def test_something(self):
        move = threadanalyze.ScrabbleMove()
        jsonstr: str = json.dumps(move.__dict__)
        print(jsonstr)
        self.assertEqual(True, False)  # add assertion here


if __name__ == '__main__':
    unittest.main()
