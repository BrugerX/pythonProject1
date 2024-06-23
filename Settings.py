from selenium.webdriver import EdgeOptions

class Settings:

    def __init__(self):
        pass

    @staticmethod
    def getDefaultCurrencyCode():
        return "EUR"

    @staticmethod
    def getDefaultCountryCode():
        return "dk"

    @staticmethod
    def getDefaultWaitTimeBetweenCallsSeconds():
        return 0

    @staticmethod
    def getDriverOptions():
        edge_otpions = EdgeOptions()
        edge_otpions.add_argument("headless")
        return edge_otpions