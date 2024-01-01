import requests
import bs4
import lxml

"""

    The browser object assumes the role of a browser.
    It is responsible for retrieving HTMLs and other packages from websites.

"""

class Browser:

    def __init__(self):
        pass

    @staticmethod
    def load_request(URL):
        return requests.get(URL)

    @staticmethod
    def load_bs4(URL,parser = "lxml"):
        request = Browser.load_request(URL)

        if request.status_code != 200:
            raise Exception(f"Got error code:{request.status_code} when trying to load_bs4 for {URL}")

        return bs4.BeautifulSoup(request.content,parser)

