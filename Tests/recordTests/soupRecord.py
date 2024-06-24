import unittest
import LotData.ExtractorsAndTables as EnT
import LotData.Record as ld
import Browser
import utility.LogingUtility
import utility.TestUtil as tu
import utility.webscrapingUtil as wut

class ClosedDiamondLID(unittest.TestCase):
        closed_LID_diamonds = "84559939"
        soup_data_timestamp = utility.LogingUtility.getTimeStamp()
        meta_data = EnT.MetadataExtractor(closed_LID_diamonds, utility.LogingUtility.getTimeStamp(), 715, "Diamonds")
        soup_data = EnT.SoupExtractor(soup_data_timestamp,
                                      Browser.SeleniumBrowser.getClosedAuctionSoup(closed_LID_diamonds))
        record = ld.SpecRecord({"meta_data": meta_data, "soup_data": soup_data})

        def test_LID(self):
            favorite_df = self.record.getRecordForDatabaseCopy()
            self.assertEqual(self.closed_LID_diamonds, favorite_df["LID"].iloc[0])
            self.assertEqual(1, len(favorite_df["LID"].unique()))

        def test_timestamp(self):
            favorite_df = self.record.getRecordForDatabaseCopy()
            self.assertEqual(self.soup_data_timestamp, favorite_df["soup_timestamp"][0])
            self.assertEqual(1, len(favorite_df["soup_timestamp"].unique()))

        def test_specs_dict(self):
            favorite_df = self.record.getRecordForDatabaseCopy()
            real_specs_dict = {'Diamond type': 'Natural',
 'Lab report number': '532234282',
 'Number of diamonds': '1',
 'Total carat weight': '0.48',
 'Cut grade': 'Excellent',
 'Diamond Clarity Grade': 'SI2',
 'Fluorescence': 'Very slight fluorescence',
 'Symmetry': 'Very good',
 'Polish': 'Very good',
 'Laboratory Report': 'International Gemological Institute (IGI)',
 'Sealed by laboratory': 'Yes',
 'Laser Engraved': 'No',
 'Shape': 'Round',
 'Cutting style': 'Brilliant cut'}
            self.assertEqual(favorite_df["spec_dict"][0],real_specs_dict)

if __name__ == '__main__':
    unittest.main()
