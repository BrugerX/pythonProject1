import unittest
from Runnables.RunningSettings import wanted_categories
import Browser as brwsr
import utility.webscrapingUtil as wut

class TestingCategories(unittest.TestCase):



    def test_wanted_categories_correct(self):

        for (cat_int,cat_name) in wanted_categories.items():
            cat_base_url = brwsr.CategoryOverview.getCategoryBaseURL()
            redirected_url = brwsr.Browser.get_redirected_url(f"{cat_base_url}{cat_int}")
            (cat_int_real,cat_name_real) = wut.getCategoryFromURL(redirected_url)

            self.assertEqual((cat_int,cat_name),(cat_int_real,cat_name_real),msg=f"Expected category int and name: {cat_int,cat_name} but got {cat_int_real,cat_name_real}")


if __name__ == '__main__':
    unittest.main()
