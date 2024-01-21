import json
import time
from abc import ABC,abstractmethod
from copy import copy

from Browser import Browser,BidApi,ShippingApi,ImageApi
from Settings import Settings
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

class LotData(ABC):

    def __init__(self, LID: str):
        self.LID = LID
        self.dataRows = []

    @abstractmethod
    def getDataRows(self):
        return list(DataRow)

    def __str__(self):
        printStr = ""
        for row in self.dataRows:
            printStr += f"\n{row}"
        return f"{printStr}\n"



class BidData(LotData):

    def __init__(self, LID: str, currencyCode=Settings.getDefaultCurrencyCode()):
        super().__init__(LID)
        self.currencyCode = currencyCode
        self.finalBidDict = json.loads(BidApi.getLatestBid(LID).text)["lots"][0]
        self.allBidsDicts = json.loads(BidApi.getBids(LID,self.currencyCode).text)["bids"]
        self.nrOfBids = len(self.allBidsDicts)

        for bidDict in self.allBidsDicts:
            self.dataRows += [BidRow(self.LID,bidDict,self.finalBidDict)]

    def getDataRows(self):
        return self.dataRows



"""

@:arg bidDict: A single dict from the history of bids.
@:arg finalBidsDict: The dict containing information about the final bid.

Takes those two arguments and turns its dataDict into a single row in the BidSQL

"""
class BidRow(DataRow):

    def __init__(self, LID: str, bidDict, finalBidsDict):
        super().__init__(LID)

        self.bidDict = bidDict
        self.finaBidsDict = finalBidsDict

        currentBidAmount = []
        currencies = []

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

        self.dataDict["isFinalBid"] = isFinalBid
        self.dataDict["isReservePriceMet"] = isReservePriceMet
        self.dataDict["isBuyNowAvailable"] = isBuyNowAvailable
        self.dataDict["isFromOrder"] = isFromOrder

        favouriteCount = finalBidsDict["favorite_count"]
        AID = finalBidsDict["auction_id"]

        self.dataDict["favouriteCount"] = favouriteCount
        self.dataDict["AID"] = AID

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

        self.dataDict["timeStamp"] = timeStamp
        self.dataDict["explanationType"] = explanationType

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
            "countryCode": countryCode,
            "countryName": None,
            "currencyCode": currencyCode,  # Use the passed currency code directly
            "estimatedDeliveryTimesDaysLower": None,
            "estimatedDeliveryTimesDaysUpper": None,
            "price": None,
            "combinedShippingAllowed": None
        }

        if 'shipping' in data:
            shippingInfo = data['shipping']

            for rate in shippingInfo.get('rates', []):
                if rate.get('region_code') == countryCode:
                    resultDict['countryName'] = rate.get('region_name')
                    resultDict['price'] = rate.get('price', 0) / 100  # Convert to correct format
                    break

            if 'estimated_delivery_times' in shippingInfo and len(shippingInfo['estimated_delivery_times']) > 0:
                resultDict['estimatedDeliveryTimesDaysLower'] = shippingInfo['estimated_delivery_times'][0].get(
                    'from_days')
                resultDict['estimatedDeliveryTimesDaysUpper'] = shippingInfo['estimated_delivery_times'][0].get(
                    'to_days')

            resultDict['combinedShippingAllowed'] = shippingInfo.get('combined_shipping_allowed')

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
        self.imageDict["imageFormat"] = self.getFormat(self.imageDict)


        self.dataDict = copy(self.imageDict)



    def getFormat(self,imageDict):
        url = imageDict["url"].split(".")
        format = "." + url[-1]
        return format

    def getDataDict(self):
        return self.dataDict


if __name__ == '__main__':

    randomLID = 79019263
    #print(ShippingData(randomLID))
    #print(BidData(randomLID))
    print(ImageData(randomLID))




