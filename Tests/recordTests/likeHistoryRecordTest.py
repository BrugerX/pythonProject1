import unittest
import LotDataPackage.ExtractorsAndTables as EnT
import LotDataPackage.Record as ld
import Browser
import utility.LogingUtility
import utility.TestUtil as tu
import utility.webscrapingUtil as wut

class ClosedDiamondLID(unittest.TestCase):
    closed_LID_diamonds = "84559939"
    latest_bid_timestamp = utility.LogingUtility.getTimeStamp()
    meta_data = EnT.MetadataExtractor(closed_LID_diamonds, utility.LogingUtility.getTimeStamp(), 715, "Diamonds")
    latest_bid_table = EnT.LatestBidTable(latest_bid_timestamp,Browser.LotApi.getLotDescription(closed_LID_diamonds))
    favorite_history_record = ld.FavoriteHistory({"latest_bid_data":latest_bid_table,"meta_data":meta_data})



    #We check to see if it has the correct LID
    def test_LID(self):
        favorite_df = self.favorite_history_record.getRecordForDatabaseCopy()
        self.assertEqual(self.closed_LID_diamonds, favorite_df["LID"].iloc[0])
        self.assertEqual(1,len(favorite_df["LID"].unique()))

    def test_timestamp(self):
        favorite_df = self.favorite_history_record.getRecordForDatabaseCopy()
        self.assertEqual(self.latest_bid_timestamp, favorite_df["latest_bid_timestamp"][0])
        self.assertEqual(1, len(favorite_df["latest_bid_timestamp"].unique()))

    def test_favorite_count(self):
        favorite_df = self.favorite_history_record.getRecordForDatabaseCopy()
        self.assertEqual(32, favorite_df["favorite_count"][0])


if __name__ == '__main__':
    unittest.main()
