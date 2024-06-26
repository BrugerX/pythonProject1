import unittest
import LotData.LotData as ld
import utility.webscrapingUtil as wut
import database.DatabaseManager as dbm
from sqlalchemy.sql import text

class MyTestCase(unittest.TestCase):
    session,egine = dbm.getSessionEngine()

    def test_record_key_to_table_name(self):
        l_data = ld.LotData(None)

        query = f"SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';"

        #We get the results in this format [(name1,),(name2,)...]
        expected_table_names = self.session.execute(text(query)).fetchall()
        expected_table_names = set([name_tuple[0] for name_tuple in expected_table_names])

        #We need them as sets otherwise the ordering matters
        record_key_based_names = set([wut.recordIntoTabe(record_key) for record_key in l_data.keys()])

        self.assertEqual(expected_table_names,record_key_based_names)



if __name__ == '__main__':
    unittest.main()
