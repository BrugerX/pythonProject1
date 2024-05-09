import re

"""
    Takes a string of the format "$ 18,000" and turns it into an int of 18000
    It is neutral to non-numbers, such that
    f("$ 18,000") = f("asdbc 18,000) = f("18000") = 18000
"""

def turnDecimalNumberIntoInt( decimalNumber):
    return int("".join(re.findall("[0-9]+", decimalNumber)))