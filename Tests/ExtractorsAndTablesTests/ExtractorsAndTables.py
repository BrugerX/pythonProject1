import unittest
import LotDataPackage.ExtractorsAndTables as EnT
import Browser
from utility import TestUtil as tu


class SoupExtractorTests(unittest.TestCase):



    """
    The extractor can get specs from two different categories
    """
    #Specific to these LIDs
    def test_soup_gets_specs_diamonds_watches(self):
        closed_LID_diamonds = "84559939"
        closed_LID_watches = "84654169"

        soup_diamonds = Browser.SeleniumBrowser.getClosedAuctionSoup(closed_LID_diamonds)
        soup_extractor_diamonds = EnT.SoupExtractor("",soup_diamonds)

        realSpecsDiamonds = {'Diamond type': 'Natural', 'Lab report number': '532234282', 'Number of diamonds': '1', 'Total carat weight': '0.48', 'Cut grade': 'Excellent', 'Diamond Clarity Grade': 'SI2', 'Fluorescence': 'Very slight fluorescence', 'Symmetry': 'Very good', 'Polish': 'Very good', 'Laboratory Report': 'International Gemological Institute (IGI)', 'Sealed by laboratory': 'Yes', 'Laser Engraved': 'No', 'Shape': 'Round', 'Cutting style': 'Brilliant cut'}
        self.assertEqual(realSpecsDiamonds,soup_extractor_diamonds.getSpecs())  # add assertion here

        soup_watches = Browser.SeleniumBrowser.getClosedAuctionSoup(closed_LID_watches)
        soup_extractor_watches = EnT.SoupExtractor("",soup_watches)
        real_specs_watches = {'Brand': 'TAG Heuer', 'Case material': 'Steel', 'Condition': 'Worn & in very good condition', 'Diameter/ Width Case': '45 mm', 'Era': 'After 2000', 'Extras': 'Box, Documents, Warranty', 'Gender': 'Men', 'Length watch band': '165 mm', 'Model': 'Connected', 'Movement': 'Quartz', 'Period': '2011-present', 'Reference Number': 'SBG8A10', 'Shipped Insured': 'Yes'}
        self.assertEqual(real_specs_watches,soup_extractor_watches.getSpecs())

    #Specific to these LIDS
    def test_soup_gets_experts_estimate_diamonds_watches(self):
        closed_LID_diamonds = "84559939"
        closed_LID_watches = "85071793"

        soup_diamonds = Browser.SeleniumBrowser.getClosedAuctionSoup(closed_LID_diamonds)
        soup_extractor_diamonds = EnT.SoupExtractor("",soup_diamonds)

        soup_watches = Browser.SeleniumBrowser.getClosedAuctionSoup(closed_LID_watches)
        soup_extractor_watches = EnT.SoupExtractor("",soup_watches)

        real_experts_estimates_diamonds = (1300,1600)
        real_experts_estimates_watches = (850,950)

        self.assertEqual(real_experts_estimates_watches,soup_extractor_watches.getExpertEstimates())
        self.assertEqual(real_experts_estimates_diamonds,soup_extractor_diamonds.getExpertEstimates())

    def test_experts_estimate_three_digit_thousands(self):
        closed_LID_three_digit_diamond = "84642777"
        soup_diamonds = Browser.SeleniumBrowser.getClosedAuctionSoup(closed_LID_three_digit_diamond)
        soup_extractor_diamonds = EnT.SoupExtractor("",soup_diamonds)

        real_experts_estimates = (120000,160000)
        self.assertEqual(real_experts_estimates,soup_extractor_diamonds.getExpertEstimates())

    def test_experts_estimate_none_when_no_estimate(self):
        LID_no_estimate = "85072201"
        soup_diamonds = Browser.SeleniumBrowser.getActiveAuctionSoup(LID_no_estimate)
        soup_extractor_diamonds = EnT.SoupExtractor("",soup_diamonds)
        self.assertEqual((None,None), soup_extractor_diamonds.getExpertEstimates())

    def test_experts_estimate_retail_estimate(self):
        LID_retail_estimate = "85228119"
        soup_diamonds = Browser.SeleniumBrowser.getActiveAuctionSoup(LID_retail_estimate)
        real_estimate = (4600,5700)
        soup_extractor_diamonds = EnT.SoupExtractor("",soup_diamonds)
        self.assertEqual(real_estimate, soup_extractor_diamonds.getExpertEstimates())


    def test_bid_table(self):
        closed_LID_diamonds = "84559939"
        bid_table = EnT.BidsTable("",Browser.BidApi.getBids(closed_LID_diamonds))
        self.assertIsNone(bid_table.dataframe)
        dataframe = bid_table.getDataframeCopy()


        self.assertTrue(dataframe["BID"].is_unique)
        self.assertTrue(dataframe["amount"].is_unique)

        #Check that the same token and country is used for every name
        for name in dataframe["name"].unique():
            self.assertEqual(len(dataframe[dataframe["name"] == name]["token"].unique()),1)
            self.assertEqual(len(dataframe[dataframe["name"] == name]["country.code"].unique()), 1)

    def test_image_table_diamonds(self):
        closed_LID_diamonds = "84559939"
        images_table = EnT.ImagesTable("",Browser.ImageApi.getImageGallery(closed_LID_diamonds))

        img_df = images_table.getDataframeCopy()

        self.assertTrue(tu.columnsFollowing(img_df,"size",["width","height"]))
        self.assertTrue(tu.columnsFollowing(img_df,"image_idx",["image_type"]))

    def test_images_table_multiple_categories(self):
        closed_LID_diamonds = "84559939"
        images_table = EnT.ImagesTable("",Browser.ImageApi.getImageGallery(closed_LID_diamonds))

        img_df = images_table.getDataframeCopy()

        self.assertTrue(tu.columnsFollowing(img_df,"size",["width","height"]))
        self.assertTrue(tu.columnsFollowing(img_df,"image_idx",["image_type"]))

        closed_comic_books = "84765561"
        images_table = EnT.ImagesTable("",Browser.ImageApi.getImageGallery(closed_comic_books))

        img_df = images_table.getDataframeCopy()

        self.assertTrue(tu.columnsFollowing(img_df,"size",["width","height"]))
        self.assertTrue(tu.columnsFollowing(img_df,"image_idx",["image_type"]))

    #Specific to this LID
    def test_shipping_table_correct_prices(self):
        closed_LID_diamonds = "84559939"
        shipping_table = EnT.ShippingTable("",Browser.ShippingApi.getShippingAndPaymentInformation(closed_LID_diamonds))

        shipping_df = shipping_table.getDataframeCopy()
        count = len(shipping_df[(shipping_df["price"] > 1000) | (shipping_df["price"] < 1)]) #None below 1 and none above 1000 EUR

        self.assertEqual(0,count)
        # We know the shipping price to DK is 23 EUR for this LID
        self.assertEqual(23,shipping_df[shipping_df["region_name"] == "Denmark"]["price"].iloc[0])



    #TODO: Test what happens if experts min and max is equal
    #TODO: Create a method that generates LIDs from our database to test on a certain percentage



if __name__ == '__main__':
    unittest.main()
