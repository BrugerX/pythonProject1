from abc import ABC,abstractmethod
import pandas as pd


class Record(ABC):

    def __init__(self):
        self.required_downloaded_data = self.getRequiredDownloadedData()
        self.record_dataframe = None

    @abstractmethod
    def getRequiredDownloadedData(self):
        return None

    @abstractmethod
    def getRecordForDatabaseCopy(self):
        self.composeRecordIfNotExists()

        return pd.DataFrame

    @abstractmethod
    def recordTimestampDownloadedData(self):
        return None

    @abstractmethod
    def composeRecordForDatabase(self):
        pass

    def composeRecordIfNotExists(self):
        if(self.record_dataframe is None):
            self.composeRecordForDatabase()

class BidRecord(Record):

    def __init__(self,downloadedData):
        super().__init__()
        self.meta_data = downloadedData["meta_data"]
        self.latest_bid_table = downloadedData["latest_bid_data"]
        self.bid_table = downloadedData["bid_data"]

    def getRequiredDownloadedData(self):
        return ["meta_data","latest_bid_data","bid_data"]

    def composeRecordForDatabase(self):
        bids_df = self.bid_table.getDataframeCopy()
        lbid_df = self.latest_bid_table.getDataframeCopy()

        is_auction_closed = self.latest_bid_table.getIsClosed()

        # Convert lbids_df to a dictionary for easy lookup
        current_bid_dict = lbid_df.set_index('currency')['current_bid_amount'].to_dict()

        #We check to see which of the bids match the latest bid and whether the auction is closed
        bids_df['is_final_bid'] = bids_df.apply(
            lambda x: x['amount'] == current_bid_dict.get(x['currency_code'], None) and is_auction_closed, axis=1
        )


        reserve_price_met = self.latest_bid_table.getReservePriceMet()
        bids_df["is_reserve_price_met"] = reserve_price_met

        #We don't use these columns
        bids_df = bids_df.drop(columns=["country.flag_png_url", "country.flag_svg_url"])
        bids_df["favorite_count"] = self.latest_bid_table.getFavoriteCount()
        bids_df["AID"] = lbid_df["auction_id"][0]
        bids_df["LID"] = self.meta_data.getLID()

        self.record_dataframe = bids_df
        self.recordTimestampDownloadedData()

    def getRecordForDatabaseCopy(self):
        self.composeRecordIfNotExists()

        return self.record_dataframe.copy()


    def recordTimestampDownloadedData(self):
        self.record_dataframe["latest_bid_timestamp"] = self.latest_bid_table.getDownloadedTimestamp()

class ImageRecord(Record):

    def __init__(self,downloadedData):
        super().__init__()
        self.meta_data = downloadedData["meta_data"]
        self.image_data = downloadedData["image_data"]

    def composeRecordForDatabase(self):
        self.record_dataframe = self.image_data.getDataframeCopy()
        self.record_dataframe["LID"] = self.meta_data.getLID()

    def getRecordForDatabaseCopy(self):
        self.composeRecordIfNotExists()
        return self.record_dataframe.copy()

    def recordTimestampDownloadedData(self):
        pass

    def getRequiredDownloadedData(self):
        return ["meta_data", "image_data"]





