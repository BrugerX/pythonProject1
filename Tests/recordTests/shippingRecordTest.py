import unittest
import LotData.ExtractorsAndTables as EnT
import LotData.Record as ld
import Browser
import utility.LoggingUtility
import utility.TestUtil as tu
import utility.webscrapingUtil as wut

class ClosedDiamondShipping(unittest.TestCase):
    closed_LID_diamonds = "84559939"
    shipping_timestamp = utility.LoggingUtility.getTimeStamp()
    meta_data = EnT.MetadataExtractor(closed_LID_diamonds, utility.LoggingUtility.getTimeStamp(), 715, "Diamonds")
    shipping_table = EnT.ShippingTable(shipping_timestamp,Browser.ShippingApi.getShippingAndPaymentInformation(closed_LID_diamonds))
    shipping_record = ld.ShippingRecord({"shipping_data":shipping_table,"meta_data":meta_data})


    """
    
    From the API we get values like 3000 EUR instead of 30 EUR as the shipping cost.
    
    We would like to test that we correctly convert the prices.
    
    """
    def test_shipping_record_correct_prices(self):
        shipping_df = self.shipping_record.getRecordForDatabaseCopy()
        count = len(shipping_df[(shipping_df["price"] > 1000) | (shipping_df["price"] < 1)]) #None below 1 and none above 1000 EUR

        self.assertEqual(0,count)
        # We know the shipping price to DK is 23 EUR for this LID
        self.assertEqual(23,shipping_df[shipping_df["region_name"] == "Denmark"]["price"].iloc[0])

    #We check to see if it has the correct LID
    def test_LID(self):
        shipping_df = self.shipping_record.getRecordForDatabaseCopy()
        self.assertEqual(self.closed_LID_diamonds, shipping_df["LID"].iloc[0])
        self.assertEqual(1,len(shipping_df["LID"].unique()))

    def test_timestamp(self):
        shipping_df = self.shipping_record.getRecordForDatabaseCopy()
        self.assertEqual(self.shipping_timestamp, shipping_df["shipping_timestamp"].iloc[0])
        self.assertEqual(1, len(shipping_df["shipping_timestamp"].unique()))


if __name__ == '__main__':
    unittest.main()
