import unittest
import Runnables.JobManager as jb
import LotDataPackage.LotDataSettings as lds
import database.DatabaseManager as dbm
import pq.python.pq.Queue as q
import time
import numpy as np

class MyTestCase(unittest.TestCase):
    t_start = time.time()
    conn = dbm.getPsycopg2Conn()
    Q = q.PQ(conn)
    q_dict = {"scheduling": Q["scheduling"]}
    rbq = jb.RunnableQueuer(q_dict)
    session,engine = dbm.getSessionEngine()
    db_manager = dbm.DatabaseManager(session,engine)

    def test_not_inserted_follows_reality_random(self):

            for x in range(10):
                runnable = self.rbq.getRunnable("scheduling",True)
                LID = runnable.getLID()
                not_in_start = runnable.getCopyNotInsertedTables()
                try:
                    for table in not_in_start:

                        try:
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

if __name__ == '__main__':
    unittest.main()
