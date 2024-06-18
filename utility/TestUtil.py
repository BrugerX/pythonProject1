import utility.webscrapingUtil as wut

"""

    For every unique value of the leading column, there must only be a single value in the corresponding
    following columns of the dataframe.

    That is if leading_col = a then for all i,j for all following_cols
    df[leading_col = a][following_col][i] = df[leading_col = a][following_col][j]

"""

def columnsFollowing(dataframe,leading_col,following_cols):

    for leader in dataframe[leading_col].unique():
        for following_col in following_cols:
            if (len(dataframe[dataframe[leading_col] == leader][following_col].unique()) != 1):
                return False
    return True


def getRandomClosedLID(category = None):
    return "84559939"

def testIfToArraysAreEqual(A,B):
    return set(A).issubset(set(B)) and set(B).issubset(set(A))

