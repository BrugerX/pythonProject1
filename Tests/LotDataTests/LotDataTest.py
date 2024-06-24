import unittest

import utility.LogingUtility
import utility.webscrapingUtil as wut
import utility.TestUtil as tut
import LotData.LotDataSettings as lds
import LotData.LotData as ltdt
import LotData.ExtractorsAndTables as ent

class ClosedDiamondAuction(unittest.TestCase):
    closed_LID = tut.getRandomClosedLID()
    category_int = 719
    category_name = "diamonds"


    """
    
    Test to see, whether LotData uses the official names for records and all of them
    
    """
    def test_onlyHasOfficialKeys(self):
        all_record_keys = lds.getAllRecordKeys()
        m_timestamp = utility.LogingUtility.getTimeStamp()
        meta_data = ent.MetadataExtractor(self.closed_LID,m_timestamp,self.category_int,self.category_name)
        lot_data = ltdt.LotData(meta_data)
        l_data_keys = lot_data.keys()

        self.assertTrue(tut.testIfToArraysAreEqual(all_record_keys,l_data_keys))

if __name__ == '__main__':
    unittest.main()

#TODO: Test ability to download individual data - that is if the records' dataframes are correct!