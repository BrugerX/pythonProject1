import time

import requests
import bs4
import json

from Settings import Settings

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
    def load_bs4(URL,parser = "lxml", delayTimeSeconds = 0):

        time.sleep(delayTimeSeconds)
        request = Browser.load_request(URL)

        if request.status_code != 200:
            raise Exception(f"Got error code:{request.status_code} when trying to load_bs4 for {URL}")

        return bs4.BeautifulSoup(request.content,parser)


class Api:

    def __init__(self):

        #This is the standard currency code used in our business
        self.defaultCurrencyCode = "USD"
        #This is the default country code we're operating our business from
        self.defaultCountryCode = "dk"

#TODO: Make all the APIs return JSON dicts
class BidApi(Api):

    def __init__(self):
        super().__init__()

    @staticmethod
    def getBids(LID,currencyCode = Settings.getDefaultCurrencyCode()):
        bidApiCallUrl = fr"https://www.catawiki.com/buyer/api/v3/lots/{LID}/bids?currency_code={currencyCode}&per_page=200"
        return Browser.load_bs4(bidApiCallUrl)

    @staticmethod
    def getLatestBid(LID):
        latestBidApiCallUrl = fr"https://www.catawiki.com/buyer/api/v3/bidding/lots?ids={LID}"
        return Browser.load_bs4(latestBidApiCallUrl)


class ShippingApi(Api):

    def __init__(self):
        super().__init__()

    """
    
    Contains information related to:
    Shipping:
            * Price to ship to different world regions (including the specified country the API caller is from).
            This price is in the format 3995 EUR = 39,95 EUR
            * Estimated arrival to the specified country code (this can indeed change depend on the countryCode specified)
    Payment method:
        * Which payment methods are available.
    
    """
    @staticmethod
    def getShippingAndPaymentInformation(LID, countryCode = Settings.getDefaultCountryCode(), currencyCode = Settings.getDefaultCurrencyCode(), waitTimeBetweenCalls = Settings.getDefaultWaitTimeBetweenCallsSeconds()):
        shippingAndPaymentApiCall = fr"https://www.catawiki.com/buyer/api/v2/lots/{LID}/shipping?locale=en&currency_code={currencyCode}&destination_country={countryCode}&amount=365000"
        return json.loads(Browser.load_bs4(shippingAndPaymentApiCall,delayTimeSeconds= waitTimeBetweenCalls).text)

class ImageApi(Api):

    def __init__(self):
        super().__init__()

    @staticmethod
    def getImageGallery(LID,waitTimeBetweenCalls = Settings.getDefaultWaitTimeBetweenCallsSeconds()):
        imageDictsApiCall = fr"https://www.catawiki.com/buyer/api/v3/lots/{LID}/gallery"
        return json.loads(Browser.load_bs4(imageDictsApiCall,delayTimeSeconds =  waitTimeBetweenCalls).text)["gallery"]
