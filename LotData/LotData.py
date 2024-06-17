import LotData.Record as rcrd
import Browser as brws
import LotData.ExtractorsAndTables as ent
import utility.webscrapingUtil as wut

"""

    TIMESTAMPING
    When we scrape, we would like to add a timestamp to the data we have downloaded.

    However, say we have the following times:
    t = 0s + t0: l1 = timestamp()
    t = 1s + t0: data = downloadData()
    t = 30 min, 1s + t0: createTableFromData(data)

    It is then evident, that we should choose the timestamp that is 30min from t0, 
    as this is the time at which we got our data. 
    So, we should always put timestamps immediately AFTER downloads!

"""



class DownloadManager:

    def __init__(self,meta_data):
        #Data used to create records
        self.downloadedData = {"meta_data":meta_data,"latest_bid_data":None
                                ,"soup_data": None,"shipping_data":None,
                               "image_data":None,"bid_data":None}

    def keys(self):
        return self.downloadedData.keys()



    def downloadSaveLatestBidData(self):
        latest_bid_json = brws.LotApi.getLotDescription(self.getLID())
        l_bid_timestamp = wut.getTimeStamp()
        l_bid_table = ent.LatestBidTable(l_bid_timestamp,latest_bid_json)
        self.downloadedData["latest_bid_data"] = l_bid_table

    def downloadSaveSoupData(self):
        isClosed = self.isClosed()
        LID = self.getLID()

        if (isClosed):
            soup = brws.SeleniumBrowser.getClosedAuctionSoup(LID)
        else:
            soup = brws.SeleniumBrowser.getActiveAuctionSoup(LID)

        soup_timestamp = wut.getTimeStamp()

        soup_exctr = ent.SoupExtractor(soup_timestamp, soup)
        self.downloadedData["soup_data"] = soup_exctr

    def downloadSaveImageData(self):
        LID = self.getLID()
        image_json_api = brws.ImageApi.getImageGallery(LID)
        image_timestamp = wut.getTimeStamp()
        image_table = ent.ImagesTable(image_timestamp,image_json_api)
        self.downloadedData["image_data"] = image_table

    def downloadSaveShippingData(self):
        LID = self.getLID()
        json_api = brws.ShippingApi.getShippingAndPaymentInformation(LID)
        timestamp = wut.getTimeStamp()
        table = ent.ShippingTable(timestamp, json_api)
        self.downloadedData["shipping_data"] = table

    def downloadSaveBidData(self):
        LID = self.getLID()
        json_api = brws.BidApi.getBids(LID)
        timestamp = wut.getTimeStamp()
        table = ent.BidsTable(timestamp,json_api)
        self.downloadedData["bid_data"] = table

    """

    Returns the DownloadedData if it is already downloaded
    Else it downloads and saves it first.
    THIS IS THE ONLY PUBLIC METHOD FOR THIS CLASS THAT RETURNS ANY OF THE DOWNLOADEDDATA OBJECTS!

    """

    #TODO: Test that all timestamps are within a certain margin of error.

    def getData(self, key):
        if (not self.isDownloaded(key)):
            self.downloadSaveData(key)

        return self.downloadedData[key]


    #TODO: A test to see if we have all cases in our downloadedData

    def downloadSaveData(self, key):
        match key:

            case "latest_bid_data":
                self.downloadSaveLatestBidData()

            case "soup_data":
                self.downloadSaveSoupData()

            case "shipping_data":
                self.downloadSaveShippingData()

            case "image_data":
                self.downloadSaveImageData()

            case "bid_data":
                self.downloadSaveBidData()

    def __getitem__(self, item):
        return self.getData(item)

    def isClosed(self):
        return self.getData("latest_bid_data").getIsClosed()

    #Checks whether or not the key has already been downloaded
    def isDownloaded(self,key):
        return (self.downloadedData[key] is not None)

    def getLID(self):
        meta_data = self.getData("meta_data")
        return meta_data.getLID()



class LotData:

    def __init__(self,meta_data):
        self.download_manager = DownloadManager(meta_data)

        self.records = {"shipping_record":rcrd.ShippingRecord,"favorite_history_record":rcrd.FavoriteHistory,
                        "bid_record":rcrd.BidRecord,"image_record":rcrd.ImageRecord,
                        "auction_history_record":rcrd.AuctionRecord,"auction_record":rcrd.AuctionRecord,
                        "spec_record":rcrd.SpecRecord}

    def downloadNeccessaryData(self,downloadable_data):

        for data in downloadable_data:
            self.download_manager.getData(data)

    def getRecordClass(self,class_name):
        return self.records[class_name]

    def __getitem__(self, item):
        record_class = self.getRecordClass(item)
        self.downloadNeccessaryData(record_class.getRequiredDownloadedData())
        record = record_class(self.download_manager)
        return record.getRecordForDatabaseCopy()

    def keys(self):
        return self.records.keys()