import unittest
import LotData.ExtractorsAndTables as EnT
import Browser

class SoupExtractorTests(unittest.TestCase):



    """
    The extractor can get specs from two different categories
    """
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

    def test_soup_gets_experts_estimate_diamonds_watches(self):
        closed_LID_diamonds = "84559939"
        closed_LID_watches = "84654169"

        soup_diamonds = Browser.SeleniumBrowser.getClosedAuctionSoup(closed_LID_diamonds)
        soup_extractor_diamonds = EnT.SoupExtractor("",soup_diamonds)

        soup_watches = Browser.SeleniumBrowser.getClosedAuctionSoup(closed_LID_watches)
        soup_extractor_watches = EnT.SoupExtractor("",soup_watches)

        real_experts_estimates_diamonds = (1300,1600)
        real_experts_estimates_watches = (1100,1300)

        self.assertEqual(real_experts_estimates_watches,soup_extractor_watches.getExpertEstimates())
        self.assertEqual(real_experts_estimates_diamonds,soup_extractor_diamonds.getExpertEstimates())

    def test_experts_estimate_three_digit_thousands(self):
        closed_LID_three_digit_diamond = "84642777"
        soup_diamonds = Browser.SeleniumBrowser.getActiveAuctionSoup(closed_LID_three_digit_diamond)
        soup_extractor_diamonds = EnT.SoupExtractor("",soup_diamonds)

        real_experts_estimates = (120000,160000)
        self.assertEqual(real_experts_estimates,soup_extractor_diamonds.getExpertEstimates())


    #TODO: Test what happens if experts min and max is equal





if __name__ == '__main__':
    unittest.main()
