import unittest

import pandas as pd

from utility import TestUtil as tu


class MyTestCase(unittest.TestCase):

    def test_columns_follow_leader(self):
        df = pd.DataFrame.from_dict(
            [{"a":1,"b":2,"c":3,"d":4},
             {"a":1,"b":1,"c":3,"d":4}, #Dict with same a,c,d but different b as the previous
             {"a":2,"b":1,"c":1,"d":1}]) #Dict with different a,b,c,d from the other two
        self.assertTrue(tu.columnsFollowing(df,"a",["c","d"]))
        self.assertFalse(tu.columnsFollowing(df,"a",["b","c","d"]))


if __name__ == '__main__':
    unittest.main()
