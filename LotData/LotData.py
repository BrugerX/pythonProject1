import json
import time
from abc import ABC,abstractmethod
from Browser import Browser,BidApi,ShippingApi


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



#TODO: BidData only contains a single row, it seems...?
class BidData(LotData):

    def __init__(self, LID: str, bidDict, finalBidsDict):
        super().__init__(LID)

        self.bidDict = bidDict
        self.finaBidsDict = finalBidsDict

        currentBidAmount = []
        currencies = []

        # Two bids cannot have the same amount, so if the latest bid and our bid have the same amount, they must be the same
        if (bidsDicts["amount"] == finalBidsDict["current_bid_amount"][bidsDicts["currency_code"]]):
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
            currentBidAmount += [bidsDicts["amount"]]
            currencies += [bidsDicts["currency_code"]]

        self.dataDict["bidAmount"] = currentBidAmount
        self.dataDict["currencies"] = currencies
        # TODO: If we webscrape the latest bid before the auction closes, we should have a mechanism for recording the extra data that may appear such as more favourites or the like.
        self.dataDict["isLatestBid"] = isLatestBid

        # Booleans
        isFinalBid = finalBidsDict["closed"]
        isReservePriceMet = finalBidsDict["reserve_price_met"]
        isBuyNowAvailable = finalBidsDict["is_buy_now_available"]
        isFromOrder = bidsDicts["from_order"]

        self.dataDict["isFinalBid"] = isFinalBid
        self.dataDict["isReservePriceMet"] = isReservePriceMet
        self.dataDict["isBuyNowAvailable"] = isBuyNowAvailable
        self.dataDict["isFromOrder"] = isFromOrder

        favouriteCount = finalBidsDict["favorite_count"]
        AID = finalBidsDict["auction_id"]

        self.dataDict["favouriteCount"] = favouriteCount
        self.dataDict["AID"] = AID

        # Related to bidder
        bidderDict = bidsDicts["bidder"]
        bidderToken = bidderDict["token"]
        bidderName = bidderDict["name"]
        bidderCountryCode = bidderDict["country"]["code"]

        self.dataDict["bidderToken"] = bidderToken
        self.dataDict["bidderName"] = bidderName
        self.dataDict["bidderCountryCode"] = bidderCountryCode

        timeStamp = bidsDicts["created_at"]
        explanationType = bidsDicts["explanation_type"]

        self.dataDict["timeStamp"] = timeStamp
        self.dataDict["explanationType"] = explanationType

    def getDataDict(self):
        return self.dataDict

class ShippingData:

    def __init__(self,LID,waitBetweenCallsSeconds = 2, defaultCurrencyCode = "USD"):
        self.LID = LID
        self.waitBetweenCallsSeconds = waitBetweenCallsSeconds
        self.defaultCurrencyCode = defaultCurrencyCode

        self.shippingRows = []
        self.paymentRows = []
        jsonData = ShippingApi.getShippingAndPaymentInformation(LID)

        self.countryCodes = self.extractCountryCodes(jsonData)

        for countryCode in self.countryCodes:
            self.shippingRows += [self.getShippingRow(countryCode,self.defaultCurrencyCode)]
            time.sleep(self.waitBetweenCallsSeconds)

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

    def getShippingRow(self, countryCode, currencyCode = "USD"):

        data = ShippingApi.getShippingAndPaymentInformation(self.LID, countryCode, currencyCode)

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

        return resultDict


if __name__ == '__main__':

    randomLID = 78396749
    bidBs4 = BidApi.getBids(randomLID)
    """for bid in json.loads(bidBs4.text)["bids"]:
        bidsDicts = bid

        #We check to see if this is the final bid
        finalBidsDict = json.loads(BidApi.getLatestBid(randomLID).text)["lots"][0]
        print(BidData(randomLID,bidsDicts,finalBidsDict))"""

    ShippingData(randomLID)




