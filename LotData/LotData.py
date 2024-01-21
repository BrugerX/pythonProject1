import json
import time
from abc import ABC,abstractmethod
from Browser import Browser,BidApi,ShippingApi
from Settings import Settings


class LotData(ABC):

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



class BidData:

    def __init__(self, LID: str, currencyCode = Settings.getDefaultCurrencyCode()):
        self.LID = LID
        self.currencyCode = currencyCode
        self.finalBidDict = json.loads(BidApi.getLatestBid(LID).text)["lots"][0]
        self.allBidsDicts = json.loads(BidApi.getBids(LID,self.currencyCode).text)["bids"]
        self.nrOfBids = len(self.allBidsDicts)
        self.bidRows = []

        for bidDict in self.allBidsDicts:
            self.bidRows += [BidRow(self.LID,bidDict,self.finalBidDict)]
        print(self.bidRows)



"""

@:arg bidDict: A single dict from the history of bids.
@:arg finalBidsDict: The dict containing information about the final bid.

Takes those two arguments and turns its dataDict into a single row in the BidSQL

"""
class BidRow(LotData):

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
class ShippingData:

    def __init__(self,LID,waitBetweenCallsSeconds = 2, defaultCurrencyCode = Settings.getDefaultCurrencyCode()):
        self.LID = LID
        self.waitBetweenCallsSeconds = waitBetweenCallsSeconds
        self.defaultCurrencyCode = defaultCurrencyCode

        self.shippingRows = []
        self.paymentRows = []
        jsonData = ShippingApi.getShippingAndPaymentInformation(LID)

        self.countryCodes = self.extractCountryCodes(jsonData)

        for countryCode in self.countryCodes:
            self.shippingRows += [ShippingRow(self.LID,countryCode,self.defaultCurrencyCode)]


        print(self.shippingRows)


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


"""

Each lot can have various shipping options depending on which country the item has to be shipped to. 
There is therefore one row per one of these options.

"""
class ShippingRow(LotData):

    def __init__(self,LID,countryCode, currencyCode = Settings.getDefaultCurrencyCode()):

        self.LID = LID
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


if __name__ == '__main__':

    randomLID = 78396749
    bidBs4 = BidApi.getBids(randomLID)
    """for bid in json.loads(bidBs4.text)["bids"]:
        bidsDicts = bid

        #We check to see if this is the final bid
        finalBidsDict = json.loads(BidApi.getLatestBid(randomLID).text)["lots"][0]
        print(BidData(randomLID,bidsDicts,finalBidsDict))"""

    ShippingData(randomLID)
    BidData(randomLID)




