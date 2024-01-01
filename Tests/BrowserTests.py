import unittest
from Browser import Browser

class MyTestCase(unittest.TestCase):
    def test_something(self):
        self.assertEqual(True, True)  # add assertion here

    def test_load_bs4_throws_exception(self):
        erroneous_URL = "https://songbird.technology"

        try:
            Browser.load_bs4(erroneous_URL)
            #If we get to this, we will fail the test; I.e if we don't throw an error
            self.assertEqual(False,True)
        except Exception as e:
            print(e.__str__())
            self.assertEqual(True,True)

    def test_load_bs4_songbird(self):
        songbird_URL = URL = "http://songbird.com/"
        songbird_text = '\nThe conditions of the solitary bird are five:\nFirst, that it flies to the highest point\nSecond, that it does not suffer for company,\n\xa0\xa0not even of its own kind\nThird, that it aims its beak to the skies\nFourth, that it does not have a definite color\nFifth, that it sings very softly\n'

        bs4 = Browser.load_bs4(songbird_URL)
        retrieved_text = bs4.find("p").text
        self.assertEqual(retrieved_text,songbird_text)


if __name__ == '__main__':
    unittest.main()
