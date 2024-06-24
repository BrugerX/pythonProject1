import unittest
import utility.TestUtil as tut
import utility.LoggingUtility as lut
import LotData.ExtractorsAndTables as ent
import Browser as brwsr

class ClosedDiamondAuction(unittest.TestCase):
    closed_LID = 84559939
    closed_soup = brwsr.SeleniumBrowser.getClosedAuctionSoup(closed_LID)
    soup_timestamp = lut.getTimeStamp()
    soup_extractor = ent.SoupExtractor(soup_timestamp,closed_soup)

    def test_proper_description(self):
        expected_description = \
            "Diamond - 0.48ct. - Brilliant - W-X, light yellow - SI2\n" \
            "Cut: Excellent" \
            "\nPolish: Very Good" \
            "\nSymmetry: Very Good" \
            "\nFluorescence: Very Slight" \
            "\nReport number: 532234282\nQuality: For your own impression, see photos.\nLot number 12-114672\nAll our items are shipped by registered mail.\nYou can also pick up the lot in one of our more than 100 offices in the Netherlands, Belgium or Germany.\nCheck the website of Goud Exchange Office (for NL and BE), Comptoir de l'Or (for BE) or Goldwechselhaus (for DE) for the nearest location.\nPlease let us know your preference via your Catawiki account."

        extracted_description = self.soup_extractor.getDescription()
        self.assertEqual(expected_description,extracted_description)


    def test_proper_seller_story(self):
        expected_seller_story ="Our family business has over 35 years of experience in jewellery, diamonds, watches, silver, precious metals, coins and banknotes.\n\nMany beautiful objects are offered to us through our more than 100 offices of Gold Exchange Office.\n\nBecause we are also active in Belgium and Germany as Gold Exchange Office, Comptoir de l'Or and Goldwechselhaus, we continuously have a new and varied range of top properties.\n\nWe are a member of the following trade associations: 'The Antwerp Exchange for Diamond Trade & NVMH (Dutch Association of Coin Traders)\n\nView our current offer on our supplier page!"
        extracted_seller_story = self.soup_extractor.getSellerStory()

        self.assertEqual(expected_seller_story,extracted_seller_story)

    def test_no_seller_story(self):
        LID_no_seller_story = 85374085
        no_seller_soup = brwsr.SeleniumBrowser.getActiveAuctionSoup(LID_no_seller_story)
        soup_timestamp = lut.getTimeStamp()
        soup_extractor = ent.SoupExtractor(soup_timestamp, no_seller_soup)

        self.assertIsNone(soup_extractor.getSellerStory())

if __name__ == '__main__':
    unittest.main()
