import unittest
import utility.webscrapingUtil as wut
import utility.TestUtil as tut
import LotData.LotDataSettings as lds
import LotData.LotData as ltdt
import LotData.ExtractorsAndTables as ent

class ClosedDiamondAuction(unittest.TestCase):
    closed_LID = tut.getRandomClosedLID()
    category_int = 719
    category_name = "diamonds"
    all_data_keys = lds.getAllDownloadableDataKeys()

    def test_onlyHasOfficialKeys(self):
        m_timestamp = wut.getTimeStamp()
        meta_data = ent.MetadataExtractor(self.closed_LID,m_timestamp,self.category_int,self.category_name)
        download_manager = ltdt.DownloadManager(meta_data)
        d_manager_keys = list(download_manager.keys())

        self.assertTrue(tut.testIfToArraysAreEqual(self.all_data_keys,d_manager_keys))

    """
    
    Test to see whether it returns false if there is not match (+ whether it returns true, when there is a match)"
    
    """
    def test_downloadSaveData_returnsFalseNoMatch(self):
        m_timestamp = wut.getTimeStamp()
        meta_data = ent.MetadataExtractor(self.closed_LID,m_timestamp,self.category_int,self.category_name)
        download_manager = ltdt.DownloadManager(meta_data)

        self.assertFalse(download_manager.downloadSaveData("FALSE_KEY_VALUE"))
        self.assertTrue(download_manager.downloadSaveData("shipping_data"))


    """
    We would like to test, whether or not there is a case match in downloadSaveData for all the real downloadableDataTypes 
    """
    def test_hasAllDownloadSaveCases(self):
        m_timestamp = wut.getTimeStamp()
        meta_data = ent.MetadataExtractor(self.closed_LID,m_timestamp,self.category_int,self.category_name)
        download_manager = ltdt.DownloadManager(meta_data)


        for key in self.all_data_keys:
            if(key != "meta_data"):
                self.assertTrue(download_manager.downloadSaveData(key),msg=f"Didn't find key: {key}")



    #TODO: Test ability to download individual data - that is if their dataframes are correct!



if __name__ == '__main__':
    unittest.main()
