import unittest
import LotData.ExtractorsAndTables as EnT
import LotData.Record as ld
import Browser
import utility.LogingUtility
import utility.TestUtil as tu
import utility.webscrapingUtil as wut

class ClosedDiamondLID(unittest.TestCase):
    closed_LID_diamonds = "84559939"
    latest_bid_timestamp = utility.LogingUtility.getTimeStamp()
    soup_data_timestamp = utility.LogingUtility.getTimeStamp()
    meta_data = EnT.MetadataExtractor(closed_LID_diamonds, utility.LogingUtility.getTimeStamp(), 715, "Diamonds")
    latest_bid_table = EnT.LatestBidTable(latest_bid_timestamp, Browser.LotApi.getLotDescription(closed_LID_diamonds))
    soup_data = EnT.SoupExtractor(soup_data_timestamp,Browser.SeleniumBrowser.getClosedAuctionSoup(closed_LID_diamonds))
    record = ld.AuctionRecord({"latest_bid_data": latest_bid_table, "meta_data": meta_data,"soup_data":soup_data})

    def test_LID(self):
        favorite_df = self.record.getRecordForDatabaseCopy()
        self.assertEqual(self.closed_LID_diamonds, favorite_df["LID"].iloc[0])
        self.assertEqual(1,len(favorite_df["LID"].unique()))

    def test_timestamp(self):
        favorite_df = self.record.getRecordForDatabaseCopy()
        self.assertEqual(self.latest_bid_timestamp, favorite_df["latest_bid_timestamp"][0])
        self.assertEqual(1, len(favorite_df["latest_bid_timestamp"].unique()))
        self.assertEqual(self.soup_data_timestamp, favorite_df["soup_timestamp"][0])
        self.assertEqual(1, len(favorite_df["soup_timestamp"].unique()))

    def test_est(self):
        favorite_df = self.record.getRecordForDatabaseCopy()
        self.assertEqual(1300, favorite_df["experts_estimate_min"][0])
        self.assertEqual(1600, favorite_df["experts_estimate_max"][0])


if __name__ == '__main__':
    unittest.main()
