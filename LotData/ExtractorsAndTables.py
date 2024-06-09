import pandas as pd
import Browser as brws
import re
import utility.webscrapingUtil as wbsu
from abc import ABC,abstractmethod
import json
from LotDataSettings import ReservePriceEnum


class DownloadedData:

    def __init__(self,timestamp):
        self.downloaded_timestamp = timestamp

    def getDownloadedTimestamp(self):
        return self.downloaded_timestamp

"""

    Responsible for extracting data out of the website's soup.

"""

class SoupExtractor(DownloadedData):

    def __init__(self,timestamp,soup):
        super().__init__(timestamp)
        self.soup = soup

        self.euroNumberPattern = "€([0-9])+(,([0-9])+)?"  # Pattern for € 8,000
        self.expertEstimatePattern = re.compile(f"expertestimate{self.euroNumberPattern}-{self.euroNumberPattern}")



    def getSpecs(self):
        specs = self.soup.findAll("div", {"class": "be-lot-specifications u-m-t-sm-xl u-m-t-xxl-2"})
        specifications = {}

        # Iterate over all spec values and names and turn them into a dict.
        for spec in specs[0].find_all("div", class_="be-lot-specification"):
            name = spec.find("span", class_="be-lot-specification__name").get_text(strip=True)
            value = spec.find("div", class_="be-lot-specification__value").get_text(strip=True)
            specifications[name] = value

        return specifications

    def getSoup(self):
        return self.soup


    """
    
    @input A BS4 soup of the website that has accounted for whether the auction was closed or not at the time of scraping
    @return Expert's estimate of an auction, with (m1,m2) where m1<=m2.
    """

    def getExpertEstimates(self):
        spans = self.soup.find_all("span")

        #Find the span with the expert estimate text
        for idx,span in enumerate(spans):
            spanParentText = span.find_parent().text
            sanitizedParentText = "".join(spanParentText.split()).lower()  # Lowercase without spaces between


            if (re.match(self.expertEstimatePattern, sanitizedParentText) is not None):
                #We have now found the proper span
                return self.extractExpertEstimateFromText(sanitizedParentText)

        raise RuntimeError(f"Didn't find expert estimate in the list of spans, got to index {idx} \n With spans: {spans}")


    """

    @:arg expertEstSpan The sanitized text of the span node and its parent, such that their combined RAW text is of the form:
        "Expert Estimate € 8,000 - € 9,000" - where the second number always has to be larger than the first.

        The sanitized text must be all lowercase with no white spaces, such that
        "Expert Estimate € 8,000 - € 9,000" -> "expertestimate€8,000-€9,000"


    @return The expert's estimates as ints, where return[0] < return[1] - example [8000,9000]
    """

    def extractExpertEstimateFromText(self,expertEstSpanText):
        estMinMax = wbsu.multipleReplaceReGeX({"expertestimate": "", "€": "", ",": ""}, expertEstSpanText).split(
            "-")  # Remove unneccessary chars and split it on the "-"
        estMinMax = [int(est) for est in estMinMax]

        if (estMinMax[0] < estMinMax[1]):
            return tuple(estMinMax)  # We turn it into a tuple, so we don't accidentally mutate it later
        else:
            raise RuntimeError(
                f"Our scraping method for expert's estimates didn't work.\n For the following test: {expertEstSpanText} we got the following estimate min: {estMinMax[0]} and max {estMinMax[1]}")



class Table(DownloadedData,ABC):

    def __init__(self,timestamp,api_json):
        super().__init__(timestamp)
        self.api_json = api_json
        self.dataframe = None


    @abstractmethod
    def addTimeStampToDF(self):
        pass

    @abstractmethod
    def extractDFFromJson(self):
        pass

    def getDataframeCopy(self):
        self.extractDataframeIfDoesntExist()

        return self.dataframe.copy()

    def extractDataframeIfDoesntExist(self):
        if(self.dataframe is None):
            self.extractDFFromJson()

class LatestBidTable(Table):

    def __init__(self,timestamp,api_json):
        super().__init__(timestamp,api_json)
        self.api_json = self.api_json

    def extractDFFromJson(self):
        # Extracting bid amounts and currencies dynamically
        df = pd.DataFrame.from_dict(self.api_json["lots"][0])
        #When we use the from_dict our index becomes the currency codes.
        df.index.name = "currency"
        self.dataframe = df.reset_index()
        self.addTimeStampToDF()

    def addTimeStampToDF(self):
        self.dataframe["latest_bids_timestamp"] = self.getDownloadedTimestamp()

    def getFavoriteCount(self):
        self.extractDataframeIfDoesntExist()
        return self.dataframe["favorite_count"][0]

    def getIsClosed(self):
        self.extractDataframeIfDoesntExist()
        return self.dataframe["closed"][0]

    #There is a special case of reserve price almost being met, we would like to handle
    def getReservePriceMet(self):
        self.extractDataframeIfDoesntExist()
        reserve_met = self.dataframe["reserve_price_met"][0]
        return ReservePriceEnum.getReservePriceCode(reserve_met)


class BidsTable(Table):

    def __init__(self,timestamp,api_json):
        super().__init__(timestamp,api_json)
        self.api_json = self.api_json["bids"]

    def addTimeStampToDF(self):
        self.dataframe["bids_timestamp"] = self.getDownloadedTimestamp()

    def extractDFFromJson(self):
        #WRITTEN BY CHATGPT
        df = pd.DataFrame.from_dict(self.api_json)

        bidder_df = pd.json_normalize(df['bidder'])

        # Drop the original nested columns and concatenate the normalized data
        df = df.drop(columns=['bidder'])

        # Combine the DataFrame with the normalized columns
        self.dataframe = pd.concat([df, bidder_df], axis=1)
        self.dataframe.rename(columns={"id":"BID"},inplace=True)
        self.addTimeStampToDF()


class ImagesTable(Table):

    def __init__(self,timestamp,api_json):
        super().__init__(timestamp,api_json)

    def addTimeStampToDF(self):
        self.dataframe["images_timestamp"] = self.getDownloadedTimestamp()

    def extractDFFromJson(self):
        #WRITTEN BY CHATGPT
        records = []
        index = 0
        for entry in self.api_json:
            entry_type = entry['type']
            for image_set in entry['images']:
                for size, details in image_set.items():
                    record = {
                        'idx': index,
                        'type': entry_type,
                        'size': size,
                        'url': details['url'],
                        'orientation': details['orientation'],
                        'width': details['width'],
                        'height': details['height']
                    }
                    records.append(record)
                index += 1

        # Create dataframe
        self.dataframe = pd.DataFrame(records)
        self.addTimeStampToDF()

class ShippingTable(Table):

    #Should only be called ONCE and is already being called in extractDFFromJson
    #We get the prices as 2000 when the real price is 20.00
    def correctShippingRates(self):
        self.dataframe["price"] = self.dataframe["price"].apply(lambda x: x/100 )
    def addTimeStampToDF(self):
        self.dataframe["shipping_timestamp"] = self.getDownloadedTimestamp()

    def extractDFFromJson(self):
        # Extract the rates data
        rates = self.api_json["shipping"]["rates"]

        # Extract other relevant information
        estimated_delivery_times = self.api_json["shipping"]["estimated_delivery_times"]
        destination_country = self.api_json["shipping"]["destination_country"]
        combined_shipping_allowed = self.api_json["shipping"]["combined_shipping_allowed"]
        delivery_methods = self.api_json["shipping"]["delivery_methods"]
        extra_insurance = self.api_json["shipping"]["extra_insurance"]
        provider_id = self.api_json["shipping"]["provider_id"]
        is_pickup_preferable = self.api_json["shipping"]["is_pickup_preferable"]
        is_pickup_only = self.api_json["shipping"]["is_pickup_only"]
        pickup_location = self.api_json["shipping"]["pickup_location"]

        # Add these details to each rate entry
        expanded_rates = []
        for rate in rates:
            rate_entry = rate.copy()
            rate_entry.update({
                "estimated_delivery_from_days": estimated_delivery_times[0]["from_days"],
                "estimated_delivery_to_days": estimated_delivery_times[0]["to_days"],
                "destination_country_name": destination_country["country"]["name"],
                "destination_country_short_code": destination_country["country"]["short_code"],
                "combined_shipping_allowed": combined_shipping_allowed,
                "delivery_methods": ', '.join(delivery_methods),
                "extra_insurance": extra_insurance,
                "provider_id": provider_id,
                "is_pickup_preferable": is_pickup_preferable,
                "is_pickup_only": is_pickup_only,
                "pickup_location_country_code": pickup_location["country_code"],
                "pickup_location_city": pickup_location["city"]
            })
            expanded_rates.append(rate_entry)

        # Create a DataFrame
        self.dataframe = pd.DataFrame(expanded_rates)
        self.correctShippingRates()
        self.addTimeStampToDF()


class MetadataExtractor(DownloadedData):

    def __init__(self,LID,timestamp,category_int,category_name):
        super().__init__(timestamp)
        self.LID = LID
        self.category_int = category_int
        self.categoy_name = category_name

    def getLID(self):
        return self.LID

