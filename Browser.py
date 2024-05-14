import time

import requests
import bs4
import json
from selenium import webdriver
from Settings import Settings
from selenium.common import TimeoutException
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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
        pass


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


class LotApi(Api):

    @staticmethod
    def getLotDescription(LID, currencyCode = Settings.getDefaultCurrencyCode() ,waitTimeBetweenCalls = Settings.getDefaultWaitTimeBetweenCallsSeconds()):
        lotDescriptionsApiCall = rf"https://www.catawiki.com/buyer/api/v3/bidding/lots?ids={LID}&currency_code= {currencyCode}"
        return json.loads(Browser.load_bs4(lotDescriptionsApiCall, delayTimeSeconds=waitTimeBetweenCalls).text)

class SeleniumBrowser():

    def __init__(self):
        pass

    @staticmethod
    def getEdgedriver():
        return webdriver.Edge(executable_path=r"C:\Users\DripTooHard\PycharmProjects\pythonProject1\msedgedriver.exe")

    @staticmethod
    def declinceCookies(webdriver):
        # Wait and click the cookie button
        WebDriverWait(webdriver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "gtm-cookie-bar-decline"))
        ).click()

    @staticmethod
    def getAuctionURL(LID):
        return f"https://www.catawiki.com/en/l/{LID}"

    @staticmethod
    def getClosedAuctionSoup(LID):
        requestUrl = SeleniumBrowser.getAuctionURL(LID)
        driver = SeleniumBrowser.getEdgedriver()
        driver.get(requestUrl)

        try:

            # Wait and click the cookie button
            SeleniumBrowser.declinceCookies(driver)

            try:
                view_lot_btn = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "lot-closed-banner__view-this-lot"))
                )
                driver.execute_script("arguments[0].click();", view_lot_btn)

            except TimeoutException:

                # If "View this lot" button does not exist, then find the "Show all info" button
                show_all_info_btn = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='closed-odp-show-all-info']"))
                )
                # Use JavaScript to click the "Show all info" button
                driver.execute_script("arguments[0].click();", show_all_info_btn)

            html = driver.page_source

            soup = bs4.BeautifulSoup(html)
            return soup

        except Exception as e:
            print("Error occurred while getting the closed auctions soup: ", e)

    @staticmethod
    def getActiveAuctionSoup(LID):
        requestUrl = SeleniumBrowser.getAuctionURL(LID)
        driver = SeleniumBrowser.getEdgedriver()
        driver.get(requestUrl)
        SeleniumBrowser.declinceCookies(driver)
        WebDriverWait(driver,10)
        soup = bs4.BeautifulSoup(driver.page_source)
        return soup






