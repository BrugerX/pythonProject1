import unittest
import LotData.ExtractorsAndTables as EnT
import LotData.LotData as ld
import Browser
import utility.TestUtil as tu
import utility.webscrapingUtil as wut

class ClosedDiamondLID(unittest.TestCase):
    closed_LID_diamonds = "84559939"
    latest_bid_timestamp = wut.getTimeStamp()
    meta_data = EnT.MetadataExtractor(closed_LID_diamonds,wut.getTimeStamp(),715,"Diamonds")
    latest_bid_table = EnT.LatestBidTable(latest_bid_timestamp,Browser.LotApi.getLotDescription(closed_LID_diamonds))
    auction_history_record = ld.AuctionHistory({"latest_bid_data":latest_bid_table, "meta_data":meta_data})



    #We check to see if it has the correct LID
    def test_LID(self):
        auction_history_df = self.auction_history_record.getRecordForDatabaseCopy()
        self.assertEqual(self.closed_LID_diamonds, auction_history_df["LID"].iloc[0])
        self.assertEqual(1,len(auction_history_df["LID"].unique()))

    def test_timestamp(self):
        auction_history_df = self.auction_history_record.getRecordForDatabaseCopy()
        self.assertEqual(self.latest_bid_timestamp, auction_history_df["latest_bid_timestamp"][0])
        self.assertEqual(1, len(auction_history_df["latest_bid_timestamp"].unique()))

    def test_is_closed_count(self):
        auction_history_df = self.auction_history_record.getRecordForDatabaseCopy()
        self.assertTrue( auction_history_df["is_closed"][0])

    def test_time_to_closed_count(self):
        auction_history_df = self.auction_history_record.getRecordForDatabaseCopy()
        self.assertEqual("2024-06-05T17:04:00Z",auction_history_df["time_to_close"][0])


if __name__ == '__main__':
    unittest.main()
