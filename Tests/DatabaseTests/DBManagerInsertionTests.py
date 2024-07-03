import unittest
import database.DatabaseManager as dbm
import pandas as pd
from datetime import datetime, timedelta

class MyTestCase(unittest.TestCase):
    session,engine = dbm.getSessionEngine()
    db_manager = dbm.DatabaseManager(session,engine)

    # Define the columns as per the table schema
    columns = [
        "bid_id", "lid", "amount", "currency_code", "from_order", "explanation_type",
        "bid_placed_timestamp", "bidder_name", "bidder_token", "bidder_country_code",
        "bid_api_timestamp", "is_final_bid", "is_reserve_price_met", "favorite_count",
        "aid", "latest_bid_timestamp"
    ]

    # Define a base timestamp for 0 BC (1 AD)
    base_timestamp = datetime(1, 1, 1)

    # Generate example data with the modified base timestamp and currency code
    num_rows = 10  # number of rows in the dataframe

    data = []

    for i in range(num_rows):
        bid_id = i
        lid = 1000 + i
        amount = i * 10 + 10
        currency_code = 'EUR'
        from_order = True
        explanation_type = "Example"
        bid_placed_timestamp = base_timestamp + timedelta(minutes=i)
        bidder_name = "TEST"
        bidder_token = "TOKEN"
        bidder_country_code = "US"
        bid_api_timestamp = base_timestamp + timedelta(minutes=i + 1)
        is_final_bid = True if i == num_rows - 1 else False
        is_reserve_price_met = 1
        favorite_count = i * 5
        aid = 2000 + i
        latest_bid_timestamp = base_timestamp + timedelta(minutes=i + 2)

        row = [
            bid_id, lid, amount, currency_code, from_order, explanation_type,
            bid_placed_timestamp, bidder_name, bidder_token, bidder_country_code,
            bid_api_timestamp, is_final_bid, is_reserve_price_met, favorite_count,
            aid, latest_bid_timestamp
        ]

        data.append(row)

    # Create the DataFrame
    bids_df = pd.DataFrame(data, columns=columns)

    def test_inserting_duplicate_bids(self):
        pass


if __name__ == '__main__':
    unittest.main()
