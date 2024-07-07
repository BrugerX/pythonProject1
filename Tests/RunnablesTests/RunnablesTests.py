import datetime
import unittest

import LotDataPackage.LotData as ld
import LotDataPackage.ExtractorsAndTables as ent
import Runnables.JobManager as jb
import LotDataPackage.LotDataSettings as lds
import utility.LoggingUtility as lut
import utility.webscrapingUtil as wut
import database.DatabaseManager as dbm
import pq.python.pq.Queue as q
import time
import numpy as np


"""

We're gonna test a runnable, that has no priori data in any of our tables.

"""
class RunnableWithNoPrioriData(unittest.TestCase):
    LID = 84266363
    meta_data = ent.MetadataExtractor(LID, lut.getTimeStamp(), 713, "classic-motorcycles-scooters")
    session,engine = dbm.getSessionEngine()
    run_in = ld.RunnableInsertion(session,engine,meta_data)

    def test_get_expected_close(self):
        scraped_expected_close = self.run_in.getExpectedClose()
        expected_expected_close = wut.turnStringToTimestamp("2024-07-07T18:43:00Z")
        self.assertEqual(scraped_expected_close,expected_expected_close)

    def test_get_is_closed(self):
        is_closed = self.run_in.getIsClosed()
        self.assertFalse(is_closed)

    def test_has_final_bid(self):
        has_final_bid = self.run_in.getHasFinalBid()
        self.assertFalse(has_final_bid)


class MyTestCase(unittest.TestCase):
    t_start = time.time()
    conn = dbm.getPsycopg2Conn()
    Q = q.PQ(conn)
    q_dict = {"scheduling": Q["scheduling"]}
    rbq = jb.RunnableQueuer(q_dict)
    session,engine = dbm.getSessionEngine()
    db_manager = dbm.DatabaseManager(session,engine)

    def test_not_inserted_follows_reality_random(self):

            for x in range(20):
                runnable = self.rbq.getRunnable("scheduling",True)
                LID = runnable.getLID()
                not_in_start = runnable.getCopyNotInsertedTables()
                try:
                    for table in not_in_start:

                        try:
                            print(f"Inserting {table} into {LID}")
                            runnable.insert(table + "_record")
                        except KeyError as key:
                            print(key)

                    where_should_it_not_exist = set(runnable.getCopyNotInsertedTables())
                    where_should_it_exist = set(not_in_start) - where_should_it_not_exist

                    for should_exist_in in where_should_it_exist:
                        self.assertTrue(self.db_manager.exists(LID,should_exist_in),f"{LID} did not exist in {should_exist_in} even thought it should.")

                    for should_not_exist_in in where_should_it_not_exist:
                        self.assertFalse(self.db_manager.exists(LID,should_not_exist_in))

                    time.sleep(np.random.uniform(0, 1))
                finally:

                    self.rbq.insertRunnable(runnable,"scheduling")

    """
    
    In order for our scheduling algorithm to work,
    we need the timezone of our timestamp getter and the queue to be the same
    
    """
    def test_timezone_of_queue(self):
        r_number = np.random.randint(0, 100, 10)
        q_test = self.Q[f"{r_number}"]
        q_test.put("test_timezone_of_queue")
        t_now = lut.getTimeStamp().replace(tzinfo=None)
        t_enq = q_test.get().enqueued_at
        self.assertTrue(t_now - t_enq < datetime.timedelta(minutes=1))



if __name__ == '__main__':
    unittest.main()
