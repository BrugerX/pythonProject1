import requests
import bs4

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


class BidApi:

    def __init__(self):
        pass

    @staticmethod
    def getBids(LID):
        bidApiCallUrl = fr"https://www.catawiki.com/buyer/api/v3/lots/{LID}/bids?currency_code=EUR&per_page=200"
        return Browser.load_bs4(bidApiCallUrl)

    @staticmethod
    def getLatestBid(LID):
        latestBidApiCallUrl = fr"https://www.catawiki.com/buyer/api/v3/bidding/lots?ids={LID}"
        return Browser.load_bs4(latestBidApiCallUrl)