from enum import Enum


class ReservePriceEnum:

    @staticmethod
    def getReservePriceCode(is_reserve_met):

        if(is_reserve_met is None):
            return -1
        elif(is_reserve_met is False):
            return 0
        elif(is_reserve_met is True):
            return 1
        elif(is_reserve_met is "almost"):
            return 2

        raise Exception(f"{is_reserve_met} doesn't match any of the previously established codes!")

