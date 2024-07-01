from enum import Enum
import utility.webscrapingUtil as wut

"""
    All data in dicts (bid,last_bid etc.) are in singular!
    [meta_data,latest_bid_data,bid_data,soup_data,shipping_data,image_data]

"""

def getAllDownloadableDataKeys():
    return ["meta_data","latest_bid_data","bid_data","soup_data","shipping_data","image_data"]

def getAllRecordKeys():
    return ["shipping_record","favorite_history_record",
                        "bid_record","image_record",
                        "auction_history_record","auction_record",
                        "spec_record","meta_record"]

def getAllRecordTables():
    return [wut.recordIntoTabe(record_key) for record_key in getAllRecordKeys()]

class ReservePriceEnum:

    @staticmethod
    def getReservePriceCode(is_reserve_met):

        if(is_reserve_met is None):
            return -1
        elif(is_reserve_met == False):
            return 0
        elif(is_reserve_met == True):
            return 1
        elif(is_reserve_met == "almost"):

            return 2

        raise Exception(f"{is_reserve_met} of type {type(is_reserve_met)} doesn't match any of the previously established codes!")

