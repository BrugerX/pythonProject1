import unittest
import LotData.ExtractorsAndTables as eta
import Browser as brwsr
import LotData.Record as lt
import utility.webscrapingUtil as wut
import utility.TestUtil as tut


class MyTestCase(unittest.TestCase):

    def instantiate_bids_record(self):
        LID_closed = tut.getRandomClosedLID()
        t_bids = wut.getTimeStamp()
        t_lbids = wut.getTimeStamp()
        meta_data = eta.MetadataExtractor(LID_closed,123,111,"abc")
        bid_table = eta.BidsTable(t_bids,brwsr.BidApi.getBids(LID_closed))
        lbids_table = eta.LatestBidTable(t_lbids,brwsr.LotApi.getLotDescription(LID_closed))
        return lt.BidRecord({"bid_data":bid_table,"latest_bid_data":lbids_table,"meta_data":meta_data})


    #We test if the timestamps of latest_bid_table and bid_table matches the one in the record
    def test_correct_timestamps(self):
        LID_closed = tut.getRandomClosedLID()
        t_bids = wut.getTimeStamp()
        t_lbids = wut.getTimeStamp()
        meta_data = eta.MetadataExtractor(LID_closed,123,111,"abc")
        bid_table = eta.BidsTable(t_bids,brwsr.BidApi.getBids(LID_closed))
        lbids_table = eta.LatestBidTable(t_lbids,brwsr.LotApi.getLotDescription(LID_closed))
        bid_record = lt.BidRecord({"bid_data":bid_table,"latest_bid_data":lbids_table,"meta_data":meta_data})
        bid_record_df = bid_record.getRecordForDatabaseCopy()

        #All bids timestamp, match the proper timestamp
        count_different_timestamps_bids = len(bid_record_df[bid_record_df["bids_timestamp"] != t_bids])
        self.assertEqual(0,count_different_timestamps_bids)
        count_same_timestamps_bids = len(bid_record_df[bid_record_df["bids_timestamp"] == t_bids])
        self.assertEqual(count_same_timestamps_bids,len(bid_record_df))

        #All lbids_timestamps match the proper lbid_timestamp
        count_different_timestamps_lbids = len(bid_record_df[bid_record_df["latest_bid_timestamp"] != t_lbids])
        self.assertEqual(0,count_different_timestamps_lbids)
        count_same_timestamps_lbids = len(bid_record_df[bid_record_df["bids_timestamp"] == t_lbids])
        self.assertEqual(count_same_timestamps_lbids,len(bid_record_df))

    def test_unique_BIDS_amounts(self):
        bid_record = self.instantiate_bids_record()
        bid_record_df = bid_record.getRecordForDatabaseCopy()
        unique_bids = bid_record_df["amount"].nunique()
        unique_bid_ids = bid_record_df["BID"].nunique()
        self.assertEqual(unique_bids,len(bid_record_df))
        self.assertEqual(unique_bid_ids,len(bid_record_df))




if __name__ == '__main__':
    unittest.main()
