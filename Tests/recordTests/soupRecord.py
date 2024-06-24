import unittest
import LotData.ExtractorsAndTables as EnT
import LotData.Record as ld
import Browser
import utility.LoggingUtility as lut
import utility.TestUtil as tu
import ast
import utility.webscrapingUtil as wut

class ClosedDiamondLID(unittest.TestCase):
        closed_LID_diamonds = "84559939"
        soup_data_timestamp = lut.getTimeStamp()
        meta_data = EnT.MetadataExtractor(closed_LID_diamonds, lut.getTimeStamp(), 715, "Diamonds")
        soup_data = EnT.SoupExtractor(soup_data_timestamp,
                                      Browser.SeleniumBrowser.getClosedAuctionSoup(closed_LID_diamonds))
        record = ld.SpecRecord({"meta_data": meta_data, "soup_data": soup_data})

        def test_LID(self):
            favorite_df = self.record.getRecordForDatabaseCopy()
            self.assertEqual(self.closed_LID_diamonds, favorite_df["lid"].iloc[0])
            self.assertEqual(1, len(favorite_df["lid"].unique()))

        def test_timestamp(self):
            favorite_df = self.record.getRecordForDatabaseCopy()
            self.assertEqual(self.soup_data_timestamp, favorite_df["soup_timestamp"][0])
            self.assertEqual(1, len(favorite_df["soup_timestamp"].unique()))

        def test_specs_dict(self):
            soup_df = self.record.getRecordForDatabaseCopy()
            expected_specs_dict = {'Diamond type': 'Natural',
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

            extracted_specs_dict = ast.literal_eval(soup_df["spec_dict"][0])

            expected_keys = set([key for key in expected_specs_dict.keys()])
            extracted_keys = set([key for key in extracted_specs_dict.keys()])

            keys_needed = expected_keys - extracted_keys
            kees_in_excess = extracted_keys - expected_keys

            self.assertEqual(expected_specs_dict,extracted_specs_dict,msg=f"We need but do not extract the keys {keys_needed}, we extract but shouldn't extract the keys {kees_in_excess}")

        def test_seller_story(self):
            soup_df = self.record.getRecordForDatabaseCopy()

            expected_seller_story ="Our family business has over 35 years of experience in jewellery, diamonds, watches, silver, precious metals, coins and banknotes.\n\nMany beautiful objects are offered to us through our more than 100 offices of Gold Exchange Office.\n\nBecause we are also active in Belgium and Germany as Gold Exchange Office, Comptoir de l'Or and Goldwechselhaus, we continuously have a new and varied range of top properties.\n\nWe are a member of the following trade associations: 'The Antwerp Exchange for Diamond Trade & NVMH (Dutch Association of Coin Traders)\n\nView our current offer on our supplier page!"
            self.assertEqual(soup_df["seller_story"][0],expected_seller_story)

        def test_description(self):
            soup_df = self.record.getRecordForDatabaseCopy()

            expected_description = \
                "Diamond - 0.48ct. - Brilliant - W-X, light yellow - SI2\n" \
                "Cut: Excellent" \
                "\nPolish: Very Good" \
                "\nSymmetry: Very Good" \
                "\nFluorescence: Very Slight" \
                "\nReport number: 532234282\nQuality: For your own impression, see photos.\nLot number 12-114672\nAll our items are shipped by registered mail.\nYou can also pick up the lot in one of our more than 100 offices in the Netherlands, Belgium or Germany.\nCheck the website of Goud Exchange Office (for NL and BE), Comptoir de l'Or (for BE) or Goldwechselhaus (for DE) for the nearest location.\nPlease let us know your preference via your Catawiki account."
            self.assertEqual(soup_df["description"][0], expected_description)

        def test_seller_story_none(self):
            no_seller_LID = 85374085
            soup_data_timestamp = lut.getTimeStamp()
            meta_data = EnT.MetadataExtractor(no_seller_LID, lut.getTimeStamp(), 715, "Diamonds")
            soup_data = EnT.SoupExtractor(soup_data_timestamp,
                                          Browser.SeleniumBrowser.getActiveAuctionSoup(no_seller_LID))
            record = ld.SpecRecord({"meta_data": meta_data, "soup_data": soup_data})

            soup_df = record.getRecordForDatabaseCopy()
            self.assertIsNone(soup_df["seller_story"][0])



if __name__ == '__main__':
    unittest.main()
