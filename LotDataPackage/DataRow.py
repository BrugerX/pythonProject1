import json
import time
from abc import ABC,abstractmethod
from copy import copy
import re

from selenium.common import TimeoutException
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import bs4

from Browser import Browser,BidApi,ShippingApi,ImageApi,SeleniumBrowser, LotApi
from Settings import Settings
from utility.webscrapingUtil import multipleReplaceReGeX
from utility.LoggingUtility import getTimeStamp
import pandas as pd


class DataRow(ABC):

    def __init__(self,LID: str):

        self.LID = LID
        self.dataDict = {"LID":LID}


    """
    @:return Should set and return the data dict of the lotdata.
    This datadict is later used to parse the relevant information about the lotdata and store it in the database.
    
    """
    @abstractmethod
    def getDataDict(self):
        return dict

    def __repr__(self):
        return f"{self.dataDict}"

    def __getitem__(self, item):
        return self.dataDict[item]

    def keys(self):
        return self.dataDict.keys()

class LotData(ABC):

    def __init__(self, LID: str):
        self.LID = LID
        self.dataRows = []


        #We start at -1, because if we start at 0 it fucks up and ends the iteration 1 iteration too soon - do the maths in "__next__"
        self.currentDataRowNr = -1


    @abstractmethod
    def getDataRows(self):
        return list(self.dataRows)

    def setNrDataRows(self):
        self.nrDataRows = len(self.dataRows)

    def __str__(self):
        printStr = ""
        for row in self.dataRows:
            printStr += f"\n{row}"
        return f"{printStr}\n"

    def __iter__(self):
        self.currentDataRowNr = -1
        return self

    def __next__(self):
        self.currentDataRowNr += 1

        if(self.currentDataRowNr>=self.nrDataRows):
            raise StopIteration

        resultOfNext = self.getDataRows()[self.currentDataRowNr]

        #We require our dataRows to be either dataRows with dataDicts or outright dicts
        if(isinstance(resultOfNext,DataRow)):
            resultOfNext = resultOfNext.getDataDict()
        elif(type(resultOfNext) == dict):
            pass
        else:
            raise Exception(f"self.dataRows not properly formatted: {resultOfNext} with type {type(resultOfNext)}")


        return resultOfNext

    def __len__(self):
        return self.nrDataRows

    def __getitem__(self, item):
        return self.dataRows[item].getDataDict()


"""
    Most of our scrapers simply use the website's own API to get the neccessary information.
    However some of them need the lot's dynamic BS4 soup.
    In order to avoid overburdening the server with unneccessary requests we have created this object, which takes the lot's soup and gathers the information from there.

"""
class ScrapingBasedLotData(LotData):
    def __init__(self, LID: str, lotSoup):
        super().__init__(LID)
        self.lotSoup = lotSoup


class BidData(LotData):

    def __init__(self, LID: str, timeStamp, currencyCode=Settings.getDefaultCurrencyCode()):
        super().__init__(LID)
        self.currencyCode = currencyCode
        self.timeStamp = timeStamp
        self.finalBidDict = json.loads(BidApi.getLatestBid(LID).text)["lots"][0]
        self.allBidsDicts = json.loads(BidApi.getBids(LID,self.currencyCode).text)["bids"]


        for bidDict in self.allBidsDicts:
            self.dataRows += [BidRow(self.LID,bidDict,self.finalBidDict,self.timeStamp)]

        self.setNrDataRows()

    def getDataRows(self):
        return self.dataRows


"""

@:arg bidDict: A single dict from the history of bids.
@:arg finalBidsDict: The dict containing information about the final bid.

Takes those two arguments and turns its dataDict into a single row in the BidSQL

"""
class BidRow(DataRow):

    def __init__(self, LID: str, bidDict, finalBidsDict,timestamp):
        super().__init__(LID)

        self.bidDict = bidDict
        self.finaBidsDict = finalBidsDict

        currentBidAmount = []
        currencies = []
        self.dataDict["BID"] = bidDict["id"]

        # Two bids cannot have the same amount, so if the latest bid and our bid have the same amount, they must be the same
        if (self.bidDict["amount"] == finalBidsDict["current_bid_amount"][self.bidDict["currency_code"]]):
            isLatestBid = True

            # It makes sense to get all the currencies so we know the conversion rates between them in case we need to convert the other non latest bids
            for currency in ["EUR", "USD", "GBP"]:
                try:
                    currentBidAmount += [finalBidsDict["current_bid_amount"][currency]]
                    currencies += [currency]
                except:
                    pass

        else:
            isLatestBid = False
            currentBidAmount += [self.bidDict["amount"]]
            currencies += [self.bidDict["currency_code"]]

        self.dataDict["bidAmount"] = currentBidAmount
        self.dataDict["currencies"] = currencies
        # TODO: If we webscrape the latest bid before the auction closes, we should have a mechanism for recording the extra data that may appear such as more favourites or the like.
        self.dataDict["isLatestBid"] = isLatestBid

        # Booleans
        isFinalBid = finalBidsDict["closed"]
        isReservePriceMet = finalBidsDict["reserve_price_met"]
        isBuyNowAvailable = finalBidsDict["is_buy_now_available"]
        isFromOrder = self.bidDict["from_order"]

        self.dataDict["isFinalBid"] = isFinalBid and isLatestBid
        self.dataDict["isClosedAtScraping"] = isFinalBid
        self.dataDict["isReservePriceMet"] = isReservePriceMet
        self.dataDict["isBuyNowAvailable"] = isBuyNowAvailable
        self.dataDict["isFromOrder"] = isFromOrder

        favouriteCount = finalBidsDict["favorite_count"]
        AID = finalBidsDict["auction_id"]

        self.dataDict["favouriteCount"] = favouriteCount
        self.dataDict["aid"] = AID

        # Related to bidder
        bidderDict = self.bidDict["bidder"]
        bidderToken = bidderDict["token"]
        bidderName = bidderDict["name"]
        bidderCountryCode = bidderDict["country"]["code"]

        self.dataDict["bidderToken"] = bidderToken
        self.dataDict["bidderName"] = bidderName
        self.dataDict["bidderCountryCode"] = bidderCountryCode

        timeStamp = self.bidDict["created_at"]
        explanationType = self.bidDict["explanation_type"]

        self.dataDict["bidTimeStamp"] = timeStamp
        self.dataDict["explanationType"] = explanationType
        self.dataDict["scraping_timestamp"] = timeStamp

    def getDataDict(self):
        return self.dataDict


"""

Organizes the various shipping and logistics related rows.

"""
class ShippingData(LotData):

    def __init__(self, LID, waitBetweenCallsSeconds=2, defaultCurrencyCode=Settings.getDefaultCurrencyCode()):
        super().__init__(LID)
        self.waitBetweenCallsSeconds = waitBetweenCallsSeconds
        self.defaultCurrencyCode = defaultCurrencyCode


        self.paymentRows = []
        jsonData = ShippingApi.getShippingAndPaymentInformation(LID)

        self.countryCodes = self.extractCountryCodes(jsonData)

        for countryCode in self.countryCodes:
            self.dataRows += [ShippingRow(self.LID,countryCode,self.defaultCurrencyCode)]

        self.setNrDataRows()

    def extractCountryCodes(self,jsonData):
        countryCodes = set()

        # Extract from 'rates'
        for rate in jsonData['shipping']['rates']:
            if 'region_code' in rate:
                countryCodes.add(rate['region_code'])

        # Extract from 'destination_country'
        if 'short_code' in jsonData['shipping']['destination_country']['country']:
            countryCode = jsonData['shipping']['destination_country']['country']['short_code']
            countryCodes.add(countryCode)

        return list(countryCodes)

    def getDataRows(self):
        return self.dataRows

"""

Each lot can have various shipping options depending on which country the item has to be shipped to. 
There is therefore one row per one of these options.

The scraper's host country will always show, even if it is covered by a super-region.
I.g DK will be shown even if there is a general shipping rate for EU.

"""
class ShippingRow(DataRow):

    def __init__(self, LID, countryCode, currencyCode=Settings.getDefaultCurrencyCode()):

        super().__init__(LID)
        self.countryCode = countryCode
        self.currencyCode = currencyCode

        data = ShippingApi.getShippingAndPaymentInformation(self.LID, self.countryCode, self.currencyCode)

        # Initialize resultDict with default values
        resultDict = {
            "LID": self.LID,
            "country_code": countryCode,
            "country_name": None,
            "currency_code": currencyCode,  # Use the passed currency code directly
            "estimated_delivery_times_days_lower": None,
            "estimated_delivery_times_days_upper": None,
            "price": None,
            "combined_shipping_allowed": None
        }

        if 'shipping' in data:
            shippingInfo = data['shipping']

            for rate in shippingInfo.get('rates', []):
                if rate.get('region_code') == countryCode:
                    resultDict['country_name'] = rate.get('region_name')
                    resultDict['price'] = rate.get('price', 0) / 100  # Convert to correct format
                    break

            if 'estimated_delivery_times' in shippingInfo and len(shippingInfo['estimated_delivery_times']) > 0:
                resultDict['estimated_delivery_times_days_lower'] = shippingInfo['estimated_delivery_times'][0].get(
                    'from_days')
                resultDict['estimated_delivery_times_days_upper'] = shippingInfo['estimated_delivery_times'][0].get(
                    'to_days')

            resultDict['combined_shipping_allowed'] = shippingInfo.get('combined_shipping_allowed')

        self.dataDict = resultDict

    def getDataDict(self):
        return self.dataDict


"""
class ImageData(LotData):
    def __init__(self,LID):

        self.LID = LID
        soup = Browser.load_bs4(f"https://www.catawiki.com/en/l/{LID}-1-pcs-diamonds-1-00-ct-round-f-vs2-no-reserve-price")

        # Find all <img> tags and filter based on a specific pattern in 'src' or a parent class
        img_tags = soup.find_all('img')
        stone_imgs = [img['src'] for img in img_tags if 'catawiki' in img['src'] and 'lot_card' in img['src']]

        print(stone_imgs)

    def getDataRows(self):
        return self.dataRows
"""


class ImageData(LotData):

    def __init__(self, LID, waitBetweenCallsSeconds=2,):
        super().__init__(LID)
        self.waitTimeBetweenCallsSeconds = waitBetweenCallsSeconds
        self.imageGallery = ImageApi.getImageGallery(self.LID,self.waitTimeBetweenCallsSeconds)

        counter = 0
        for subGallery in self.imageGallery:
            type = subGallery["type"]
            for imageDict in subGallery["images"]:
                counter += 1
                for size in imageDict.keys():
                    self.dataRows += [ImageRow(self.LID,counter,type,imageDict[size],size)]

        self.setNrDataRows()

    def getDataRows(self):
        return self.dataRows

class ImageRow(DataRow):
    def __init__(self, LID, idx, type, imageDict, size):
        self.size = size
        self.idx = idx
        self.type = type
        self.imageDict = imageDict
        self.LID = LID

        self.imageDict["LID"] = LID
        self.imageDict["idx"] = idx
        self.imageDict["type"] = type
        self.imageDict["size"] = size
        self.imageDict["image_format"] = self.getFormat(self.imageDict)


        self.dataDict = copy(self.imageDict)



    def getFormat(self,imageDict):
        url = imageDict["url"].split(".")
        format = "." + url[-1]
        return format

    def getDataDict(self):
        return self.dataDict


class SpecData(ScrapingBasedLotData):

    def __init__(self,LID,lotSoup):
        super(SpecData, self).__init__(LID,lotSoup)
        self.dataRows = self.getSpecsFromSoup(self.lotSoup)
        self.dataRows["LID"] = LID
        self.setNrDataRows()

    def setNrDataRows(self):
        self.nrDataRows = len([self.dataRows])
    def getDataRows(self):
        return [self.dataRows]

    def getSpecsFromSoup(self, soup):
        specs = soup.findAll("div", {"class": "be-lot-specifications u-m-t-sm-xl u-m-t-xxl-2"})
        specifications = {}

        # Iterate over all spec values and names and turn them into a dict.
        for spec in specs[0].find_all("div", class_="be-lot-specification"):
            name = spec.find("span", class_="be-lot-specification__name").get_text(strip=True)
            value = spec.find("div", class_="be-lot-specification__value").get_text(strip=True)
            specifications[name] = value

        return specifications

class AuctionData(ScrapingBasedLotData):

    def __init__(self,LID,lotSoup,timeStamp):
        super(AuctionData, self).__init__(LID,lotSoup)

        #Regex patterns
        #TODO: Make a Regex object?
        self.timeStamp = timeStamp
        self.euroNumberPattern = "€([0-9])+(,([0-9])+)?"  # Pattern for € 8,000
        self.expertEstimatePattern = re.compile(f"expertestimate{self.euroNumberPattern}-{self.euroNumberPattern}")

        self.dataRows = {"LID":LID}



    """

    @:arg expertEstSpan The sanitized text of the span node and its parent, such that their combined RAW text is of the form:
        "Expert Estimate € 8,000 - € 9,000" - where the second number always has to be larger than the first.

        The sanitized text must be all lowercase with no white spaces, such that
        "Expert Estimate € 8,000 - € 9,000" -> "expertestimate€8,000-€9,000"


    @return The expert's estimates as ints, where return[0] < return[1] - example [8000,9000]
    """

    def extractExpertEstimateFromText(self,expertEstSpanText):
        estMinMax = multipleReplaceReGeX({"expertestimate": "", "€": "", ",": ""}, expertEstSpanText).split(
            "-")  # Remove unneccessary chars and split it on the "-"
        estMinMax = [int(est) for est in estMinMax]

        if (estMinMax[0] < estMinMax[1]):
            return tuple(estMinMax)  # We turn it into a tuple, so we don't accidentally mutate it later
        else:
            raise RuntimeError(
                f"Our scraping method for expert's estimates didn't work.\n For the following test: {expertEstSpanText} we got the following estimate min: {estMinMax[0]} and max {estMinMax[1]}")

    def findExpertEstimate(self,spans):

        #Find the span with the expert estimate text
        for idx,span in enumerate(spans):
            spanParentText = span.find_parent().text

            # TODO: The below thing is O(3n) = O(n), maybe there is a faster way where we don't have to turn it lowercase and remove white spaces first?
            sanitizedParentText = "".join(spanParentText.split()).lower()  # Lowercase without spaces between


            if (re.match(self.expertEstimatePattern, sanitizedParentText) is not None):
                #We have now found the proper span
                return self.extractExpertEstimateFromText(sanitizedParentText)

        raise RuntimeError(f"Didn't find expert estimate in the list of spans, got to index {idx} \n {spans}")

    def scrapeSoup(self,soup):

        spans = soup.find_all("span")
        (e1,e2) = self.findExpertEstimate(spans)
        self.dataRows["expert_estimate_min"] = e1
        self.dataRows["expert_estimate_max"] = e2

    def getAuctionData(self):
        self.scrapeSoup(self.lotSoup)

        #The API result also contains metadata
        lotAPIResult = LotApi.getLotDescription(self.LID)["lots"][0]
        
        self.dataRows["is_closed_at_scraping"] = lotAPIResult["closed"]
        self.dataRows["is_buy_now_available"] = lotAPIResult["is_buy_now_available"]
        self.dataRows["bidding_start_timestamp"] = lotAPIResult["bidding_start_time"]
        self.dataRows["bidding_close_timestamp"] = lotAPIResult["bidding_end_time"]
        self.dataRows["is_reserve_price_met"] = lotAPIResult["reserve_price_met"]
        self.dataRows["favourite_count"] = lotAPIResult["favorite_count"]
        self.dataRows["aid"] = lotAPIResult["auction_id"]


        self.dataRows["scraping_timestamp"] = self.timeStamp

        self.setNrDataRows()

    def setNrDataRows(self):
        self.nrDataRows = len([self.dataRows])


    def getDataRows(self):
        return [self.dataRows]


"""
NOTE: dataRows is not a list but a dict in the case of AllLotData

"""
class ALlLotData(LotData):

    def __init__(self, LID):
        super().__init__(LID)
        self.LID = LID
        self.isClosed = None
        self.lotSoup = None
        self.bidData = self.imageData = self.shippingData = self.auctionData = self.specData = None
        self.metaData = dict()
        self.timeStamp = getTimeStamp()
        self.errorsProcessing = []
        self.URLUsed = SeleniumBrowser.getAuctionURL(self.LID)

        self.setNrDataRows()


    def getAPIBasedData(self):
        #TODO: Implement proper exception calling and handling within the various LotData objects
        try:
            self.bidData = self.getBidData(self.LID,self.timeStamp)
            self.imageData = self.getImageData(self.LID)
            self.shippingData = self.getShippingData(self.LID)
        except Exception as e:
            print(f"Encountered error: {e} \n while getting API based data")
            self.errorsProcessing += [e]

    def getScrapingBasedData(self):

        if(self.lotSoup is None):
            raise RuntimeError("Lot soup not yet scraped properly")

        """Scraping based lotDatas need to be given the soup in order to minimize the amount of times we need to instantiate the webbrowser"""
        self.auctionData = self.getAuctioNData(self.LID, self.lotSoup, self.timeStamp)
        self.specData = self.getSpecData(self.LID,self.lotSoup)


    def getDataRows(self):
        return [self.dataRows]
    def composeDataRows(self):

        self.getAPIBasedData()
        self.checkIfIsClosed()
        self.getLotSoup()

        self.getScrapingBasedData()
        self.composeMetaData()

        self.dataRows = {"meta_data":self.metaData,"shipping_data":self.shippingData,"colored_gemstone_specs": self.specData,"bid_data":self.bidData,"image_data":self.imageData, "auction_data":self.auctionData}

    def checkIfIsClosed(self):
    #TODO: Make this dependent on the auctionData instead as for auctions with 0 bids, we get a bad result


        """If we already have the bid dict we can't their servers
        if(self.bidData is not None and len(self.bidData) >0):
            for bidRow in self.bidData:
                if(bidRow["isFinalBid"]):
                    self.isClosed = True

                self.isClosed = False
        else:

        PROBLEM: This doesn't always work due to the lag between when we get bidData and when the auction might've closed.
        """

        self.isClosed = LotApi.getLotDescription(self.LID)["lots"][0]["closed"]

    def getLotSoup(self):

        if(self.isClosed is None):
            raise RuntimeError("Tried getting lot soup without first determining if it is closed")

        #We make a first guess
        if(self.isClosed):
            soup = SeleniumBrowser.getClosedAuctionSoup(self.LID)
        else:
            soup = SeleniumBrowser.getActiveAuctionSoup(self.LID)

        if(soup is None):
            raise RuntimeError(f"Unable to get lot soup for LID: {self.LID} - assumed the auction was closed? : {self.isClosed}")

        self.lotSoup = soup

    def getAuctioNData(self,LID,lotSoup,timeStamp):
        auctionData = AuctionData(LID,lotSoup,timeStamp)
        auctionData.getAuctionData()
        return auctionData

    def getShippingData(self,LID):
        return ShippingData(LID)

    def composeMetaData(self):
        if(self.isClosed is None):
            raise RuntimeError("isClosed has to be specified! Cannot be null!")

        self.metaData = [{"LID":self.LID,"lot_url_used":self.URLUsed, "errors_processing":self.errorsProcessing, "scraping_timestamp":self.timeStamp ,'is_closed':self.isClosed}]

    def getBidData(self,LID,timeStamp):
        return BidData(LID,timeStamp)

    def getImageData(self,LID):
        return ImageData(LID)

    def getSpecData(self,LID,lotSoup):
        return SpecData(LID,lotSoup)

    def __getitem__(self, item):
        return self.dataRows[item]

    def keys(self):
        return self.dataRows.keys()







if __name__ == '__main__':

    randomLID = 79066981

    lotData = ALlLotData(randomLID)
    lotData.composeDataRows()
    for key in lotData.keys():
        print(f"\n Current key: {key} \n")
        drow = lotData[key]
        for row in drow:
            print(row)






