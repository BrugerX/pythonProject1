import LotData.Record as rcrd
import Browser as brws
import LotData.ExtractorsAndTables as ent
import utility.LoggingUtility as lut
import utility.webscrapingUtil as wut
import LotData.LotDataSettings as lds
import database.DatabaseManager as dbm

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
        l_bid_timestamp = lut.getTimeStamp()
        l_bid_table = ent.LatestBidTable(l_bid_timestamp,latest_bid_json)
        self.downloadedData["latest_bid_data"] = l_bid_table

    def downloadSaveSoupData(self):
        isClosed = self.isClosed()
        LID = self.getLID()

        if (isClosed):
            soup = brws.SeleniumBrowser.getClosedAuctionSoup(LID)
        else:
            soup = brws.SeleniumBrowser.getActiveAuctionSoup(LID)

        soup_timestamp = lut.getTimeStamp()

        soup_exctr = ent.SoupExtractor(soup_timestamp, soup)
        self.downloadedData["soup_data"] = soup_exctr

    def downloadSaveImageData(self):
        LID = self.getLID()
        image_json_api = brws.ImageApi.getImageGallery(LID)
        image_timestamp = lut.getTimeStamp()
        image_table = ent.ImagesTable(image_timestamp,image_json_api)
        self.downloadedData["image_data"] = image_table

    def downloadSaveShippingData(self):
        LID = self.getLID()
        json_api = brws.ShippingApi.getShippingAndPaymentInformation(LID)
        timestamp = lut.getTimeStamp()
        table = ent.ShippingTable(timestamp, json_api)
        self.downloadedData["shipping_data"] = table

    def downloadSaveBidData(self):
        LID = self.getLID()
        json_api = brws.BidApi.getBids(LID)
        timestamp = lut.getTimeStamp()
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

    """
    
    @return True if there was a match case with the key, false else
    
    """

    def downloadSaveData(self, key):
        match key:

            case "latest_bid_data":
                self.downloadSaveLatestBidData()
                return True

            case "soup_data":
                self.downloadSaveSoupData()
                return True

            case "shipping_data":
                self.downloadSaveShippingData()
                return True

            case "image_data":
                self.downloadSaveImageData()
                return True

            case "bid_data":
                self.downloadSaveBidData()
                return True

        return False

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

        self.records = {"meta_record":rcrd.MetaRecord,"shipping_record":rcrd.ShippingRecord,"favorite_history_record":rcrd.FavoriteHistory,
                        "bid_record":rcrd.BidRecord,"image_record":rcrd.ImageRecord,
                        "auction_history_record":rcrd.AuctionHistory,"auction_record":rcrd.AuctionRecord,
                        "spec_record":rcrd.SpecRecord}

    def downloadNeccessaryData(self,downloadable_data):

        for data in downloadable_data:
            self.download_manager.getData(data)

    def getRecordClass(self,class_name):
        return self.records[class_name]

    def getDataframe(self,record_key):
        record_class = self.getRecordClass(record_key)
        self.downloadNeccessaryData(record_class.getRequiredDownloadedData())
        record = record_class(self.download_manager)
        return record.getRecordForDatabaseCopy()

    def __getitem__(self, item):
        return self.getDataframe(item)

    def keys(self):
        return self.records.keys()



"""
    Unlike LotData which was a purely local representation of the record data of each lot,
    RunnableInsertion is meant to model not just the local data but also the model of our lot in the database.
    
    @param check_scheduling_factors: Will update the scheduling factors based off of information available in the database

"""
class RunnableInsertion(LotData):

    def __init__(self, session,engine, meta_data, scheduling_factors, check_scheduling_factors=False):
        super().__init__(meta_data)
        self.db_manager = dbm.DatabaseManager(session,engine)
        self.sched_factors = scheduling_factors

        self.initializeNotInsertedTables()

        if check_scheduling_factors:
            self.queryUpdateSchedulingFactors()

    def isNotInsertedTablesEmpty(self):
        not_inserted_tables = self.getNotInsertedTables()
        return (len(not_inserted_tables) == 0)
    def initializeNotInsertedTables(self):
        if(self.isNotInsertedTablesEmpty()):
            self.sched_factors["not_inserted_tables"] = lds.getAllRecordTables()


    def getNotInsertedTables(self):
        return self.sched_factors["not_inserted_tables"]

    """

    If there is a discprancy between our local inserted tables and the one in the database,
    we should call this method to check the database for all the real tables, we've already inserted this LID into.

    """

    def queryUpdateNotInserted(self):
        LID = self.download_manager.getLID()
        inserted_tables = set()
        all_tables = set(lds.getAllRecordTables())

        for record_key in self.keys():
            table_name = wut.recordIntoTabe(record_key)

            if(self.db_manager.exists(LID,table_name)):
                inserted_tables.add(table_name)

        self.sched_factors["not_inserted_tables"] = list(all_tables - inserted_tables)

    def localCheckIfExists(self,table):
        return (table not in self.sched_factors["not_inserted_factors"])

    def removeFromNotInsert(self,table_name):
        self.sched_factors["not_inserted_factors"] = [table for table in self.getNotInsertedTables() if table != table_name]

    def insert(self,record_key):
        table_name = wut.recordIntoTabe(record_key)
        unique_constraints = self.getRecordClass(record_key).getUniqueConstraints()
        record_df = self.__getitem__(record_key) #Downloads the neccessary data and gets the dataframe
        (result_insert,error_insert) = self.db_manager.insertRecordDataframe(record_df,table_name,unique_constraints)


        if(result_insert):
            self.removeFromNotInsert(table_name)

            # Keep track of various scheduling factors
            match table_name:

                case "bid":
                    self.sched_factors["has_final_bid"] = record_df["is_final_bid"].any()

                # TODO: Create tests for updating the timestamp. The current update method assumes that the auction and auction_history records retreive data from the same source.
                case "auction_history":
                    self.sched_factors["is_closed"] = record_df["is_closed"][0]
                    self.sched_factors["bidding_close_timestamp"] = record_df["bidding_close_timestamp"]

                case "auction":
                    self.sched_factors["bidding_close_timestamp"] = record_df["bidding_close_timestamp"]

        else:
            return (result_insert,error_insert)


    def queryAlterLastProcessed(self):
        if (not self.localCheckIfExists("meta")):
            self.insert("meta_record")

        return self.db_manager.update("meta",self.download_manager.getLID(),"last_processed_timestamp",lut.getTimeStamp())


    def queryUpdateSchedulingFactors(self):
        LID = self.download_manager.getLID()
        self.sched_factors["is_closed"] = self.db_manager.isClosed(LID)
        self.sched_factors["has_final_bid"] = self.db_manager.hasFinalBid(LID)
        self.sched_factors["bidding_close_timestamp"] = self.db_manager.getBiddingCloseTimestamp(LID)
        self.queryUpdateNotInserted()

    def getScheduledFactors(self):
        return self.sched_factors




