import re

"""
    Takes a string of the format "$ 18,000" and turns it into an int of 18000
    It is neutral to non-numbers, such that
    f("$ 18,000") = f("asdbc 18,000) = f("18000") = 18000
"""

def turnDecimalNumberIntoInt( decimalNumber):
    return int("".join(re.findall("[0-9]+", decimalNumber)))



"""

    Takes a list of Beautifulsoup HTML tags and returns the one with the highest integer value
    Currently no way of handling bad use cases, where it is not possible to turn the text into an int.

"""
def maxIntElements(htmlElements):
    currentMax = 0
    for htmlElement in htmlElements:
        integerValue = int(htmlElement.text)
        if(integerValue>currentMax):
            currentMax = integerValue
    return currentMax

def getLIDFromLink(URL):
    # Regular expression to extract only the digits following '/l/' and before the hyphen
    pattern = r"/l/([0-9]+)-"

    # Using findall to get all matches of the digit pattern
    matches = re.findall(pattern, URL)

    # Assuming there is only one match, return it directly
    if( matches):
        return matches[0]
    else:
        raise RuntimeError(f"No match for link: {URL}")