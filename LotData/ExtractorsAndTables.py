import pandas as pd
import Browser as brws
import re
import utility.webscrapingUtil as wbsu
from abc import ABC,abstractmethod
import json

class DownloadedData:

    def __init__(self,timestamp):
        self.downloaded_timestamp = timestamp

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

    def getDataframe(self):

        if(self.dataframe is None):
            self.extractDFFromJson()


        return self.dataframe

class BidsTable(Table):

    def __init__(self,timestamp,api_json):
        super().__init__(timestamp,api_json)
        self.api_json = self.api_json["bids"]

    def addTimeStampToDF(self):
        self.dataframe["timestamp"] = self.downloaded_timestamp

    def extractDFFromJson(self):
        #WRITTEN BY CHATGPT
        df = pd.DataFrame.from_dict(self.api_json)

        bidder_df = pd.json_normalize(df['bidder'])

        # Drop the original nested columns and concatenate the normalized data
        df = df.drop(columns=['bidder'])

        # Combine the DataFrame with the normalized columns
        self.dataframe = pd.concat([df, bidder_df], axis=1)
        self.addTimeStampToDF()


