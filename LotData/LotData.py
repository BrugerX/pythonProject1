from abc import ABC,abstractmethod
import pandas as pd


class Record(ABC):

    def __init__(self):
        self.required_downloaded_data = getRequiredDownloadedData()

    @abstractmethod
    def getRequiredDownloadedData(self):
        return None

    @abstractmethod
    def getRecordForDatabase(self):
        return pd.DataFrame


class BidRecord(Record):

    def __init__(self,metaData,LatestBidTable,bidTable):
        super().__init__()
