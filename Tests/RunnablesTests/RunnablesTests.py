import copy
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
        q_test.clear()



"""

We would like to test, that when we process runnables;

    1. Their data is scraped and inserted correctly
    2. We scrape all neccessary data
    3. We do it at the right time (get specs and auction together - only get bids at the end etc)
    4. We re-insert into the queue, only when the lot isn't finished
    5. We remember to re-insert into the queue, when it is not.

"""
class ProcessingRunnables(unittest.TestCase):
    t_start = time.time()
    conn = dbm.getPsycopg2Conn()
    Q = q.PQ(conn)
    q_dict = {"scheduling": Q["scheduling"],"test_processing_runnables":Q["test_processing_runnables"]}
    rbq = jb.WeightedInserter(q_dict)
    session,engine = dbm.getSessionEngine()
    db_manager = dbm.DatabaseManager(session,engine)

    runnable = rbq.getRunnable("scheduling")

    #Put it back babeh
    rbq.insertRunnable(runnable,"scheduling")
    LID = runnable.getLID()
    sched_factors_before = copy.deepcopy(runnable.getScheduledFactors())
    not_in_list_before = runnable.getCopyNotInsertedTables()
    rbq.processRunnable(runnable,"test_processing_runnables")

    #The time we approximately used to set the next schedule
    approximate_time_ended = lut.getTimeStamp()
    sched_factors_after = copy.deepcopy(runnable.getScheduledFactors())
    not_in_list_after = runnable.getCopyNotInsertedTables()
    job = q_dict["test_processing_runnables"].get()


    """
    
    First we would like to see, whether or not the LID is inserted back into the queue.
    Or whether it has been correctly removed
    
    """
    def test_is_inserted_back(self):

        """

        If the auction is closed and there either exists a final bid, or the only table it hasn't been inserted to is bid;
        Then we can remove it. Since it implies, that the auction ended normally or there were no bids on this lot when it ended.

        """
        if(self.sched_factors_after["is_closed"] and (self.sched_factors_after["has_final_bid"] or (set(self.not_in_list_after) == set(["bid"])))):
            self.assertIsNone(self.job)
        else:
            #Otherwise, the lot should exist in our queue again
            job_lid = self.job.data["lid"]
            self.assertEqual(job_lid,self.LID)

    def test_expected_correctly(self):
        if(self.job is not None):
            #The expected at, that was inserted
            inserted_expected_at = self.job.expected_at.replace(tzinfo=None)
            #There may be some minor differences between the real expected at and the approximate, since there could be a few
            #seconds of difference between approximate_time_ended and the real.
            approx_expected_at = self.rbq.nextProcessingTimestamp(self.runnable.getExpectedClose(),self.approximate_time_ended.replace(tzinfo=None)).replace(tzinfo=None)
            self.assertTrue((approx_expected_at - inserted_expected_at) < datetime.timedelta(minutes=1))



if __name__ == '__main__':
    unittest.main()
