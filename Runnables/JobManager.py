from datetime import datetime,timedelta,timezone

import pandas as pd

import utility.LoggingUtility as lut
from CW_Scraper import MagazineOverview
import LotDataPackage.LotData as ld
import LotDataPackage.ExtractorsAndTables as ent
import numpy as np
import json
import database.DatabaseManager as dbm
import pq.python.pq.Queue as q
import argparse
import threading
import time

class RunnableQueuer:

    def __init__(self,queues):
        self.Qs = queues

    def insertRunnable(self,runnable,q_name,schedule_at = None,expected_at = None):
        self.Qs[q_name].put(runnable.getScheduledFactors(),schedule_at=schedule_at,expected_at=expected_at)

    def getRunnable(self,q_name,check_scheduling_factors=False):
        job = self.Qs[q_name].get()
        if(job is not None):
            scheduled_factors = job.data
            timestamp = scheduled_factors["scraped_timestamp"]
            #Let the ints in this stay as strings, since it might fuck the rest of the code up :(
            #TODO: Maybe make a sched_factor object that does this conversion stuff automatically...?
            meta_data = ent.MetadataExtractor(scheduled_factors["lid"],timestamp,scheduled_factors["cat_int"],scheduled_factors["cat_name"])
            session,engine = dbm.getSessionEngine()
            return ld.RunnableInsertion(session,engine,meta_data,scheduled_factors,check_scheduling_factors=check_scheduling_factors)
        else:
            raise RuntimeError (f"Tried to get runnable insertiong, but queue {q_name} was empty!")

class WeightedInserter(RunnableQueuer):

    def __init__(self, queues, v = 0 ,idle_time=10):
        super().__init__(queues)
        self.idle_time = idle_time
        self.verbosity = v
        self.stop_event = threading.Event()

    def print(self, text):
        if self.verbosity > 0:
            print(text)


    def insertRunnable(self,runnable,q_name,schedule_at = None,expected_at = None):
        self.Qs[q_name].put(runnable.getScheduledFactors(), schedule_at=schedule_at, expected_at=expected_at)

    def processRunnable(self,runnable: ld.RunnableInsertion,q_name):
        #First we get the latest times for closing and favorite count
        if(not ( runnable.getIsClosed() or runnable.queryUpdateHasFinalBid() )):
            for record_key in ["auction_history_record","favorite_history_record"]:
                runnable.insert(record_key)

            not_inserted = runnable.getCopyNotInsertedTables()

            #If we get auction_history we also get latest_bid, which will make it faster to insert the two records below
            if("spec" in not_inserted or "auction" in not_inserted):
                runnable.insert("spec_record")
                runnable.insert("auction_record")

        #We now check to see if the auction has finished - we may only discover that after we scrape the latest auction_history
        no_bids = False
        if(runnable.getIsClosed()):

            for record_key in ["shipping_record", "image_record", "bid_record"]:

                try:
                    runnable.insert(record_key)
                #This just means, that there were no bids to the auction
                except KeyError as e:
                    if(record_key == "bid_record"):
                        no_bids = True
                    else:
                        raise KeyError(f"Failed to process runnable with LID {runnable.getLID()} for record_key {record_key} got error {e} when trying to insert the record")

        #The auction has to be closed; But sometimes the auction will close without any bids.
        if(runnable.getIsClosed() and (runnable.getHasFinalBid() or no_bids)):
            return True
        else:
            self.insertRunnable(runnable,q_name,expected_at=self.nextProcessingTimestamp(runnable.getExpectedClose()))
            return False

    # We should be getting our timestamps from the queue in UTC time
    def nextProcessingTimestamp(self,expected_close_timestamp, current_timestamp = lut.getTimeStamp().replace(tzinfo=None)):


        time_to_close = expected_close_timestamp - current_timestamp
        if time_to_close <= timedelta(minutes=10):
            return current_timestamp + timedelta(minutes=1)
        elif time_to_close <= timedelta(minutes=30):
            return current_timestamp + timedelta(minutes=2)
        elif time_to_close <= timedelta(hours=1):
            return current_timestamp + timedelta(minutes=5)
        elif time_to_close <= timedelta(hours=2):
            return current_timestamp + timedelta(minutes=15)
        elif time_to_close <= timedelta(hours=4):
            return current_timestamp + timedelta(minutes=30)
        elif time_to_close <= timedelta(hours=7):
            return current_timestamp + timedelta(hours=1)
        elif time_to_close <= timedelta(days=1):
            return current_timestamp + timedelta(hours=2)
        else:
            return current_timestamp + timedelta(hours=6)

    def main(self,main_q_name):
        while not self.stop_event.is_set():
            runnable = self.getRunnable(main_q_name)

            if runnable is None:
                self.print(f"{self.__class__} sleeping for: {self.idle_time} seconds")
                time.sleep(self.idle_time)
            else:
                self.print(f"Processing runnable with LID: {runnable.getLID()} not being in {runnable.getCopyNotInsertedTables()}")
                self.processRunnable(runnable,main_q_name)
                self.print(f"Finished processing runnable with LID: {runnable.getLID()} should not be in {runnable.getCopyNotInsertedTables()} \t is closed: {runnable.getIsClosed()} \t final bid: {runnable.getHasFinalBid()}")
    def stop(self):
        self.stop_event.set()


#TODO: Add an object that can track statistics and such of JobManager
class JobManager:
    def __init__(self, jq, sq, session, engine, idle_time=10):
        self.jq = jq
        self.sq = sq
        self.session = session
        self.engine = engine
        self.idle_time = idle_time
        self.stop_event = threading.Event()
        self.db_manager = dbm.DatabaseManager(session,engine)

    def main(self):
        while not self.stop_event.is_set():
            new_job = self.jq.get()

            if new_job is None:
                #print(f"Job manager sleeping for: {self.idle_time} seconds")
                time.sleep(self.idle_time)
                continue

            new_job_data = json.loads(new_job.data)

            match new_job_data["task_type"]:

                case "get_new_lids":
                    categories_of_interest = new_job_data["categories_of_interest"]
                    print(f"Getting new lids in categories: {categories_of_interest}")
                    self.jobGetNewLids(categories_of_interest)
                    print(f"Finished getting new lids in categories: {categories_of_interest}")

    def stop(self):
        self.stop_event.set()


    #Lid isn't already in the processing queue
    def isNewLid(self,LID):
        return not (self.db_manager.exists(LID,"processing") or self.db_manager.exists(LID,"meta"))


    def recordNewLIDInMain(self,runnable,exceptions_log):
        LID = runnable.getLID()
        cat_int = runnable.download_manager.getData("meta_data").getCategoryInt()
        cat_name = runnable.download_manager.getData("meta_data").getCategoryName()

        for record_key in ["meta_record", "favorite_history_record", "auction_history_record"]:
            table = record_key.replace("_record", "")

            if not (self.db_manager.exists(LID, table)):
                try:
                    runnable.insert(record_key)
                except Exception as e:
                    exceptions_log += [(LID, cat_int, cat_name, e, record_key, lut.getTimeStamp())]
                    raise e

    def recordNewLidInProcessingQ(self, runnable, exception_log):
        LID = runnable.getLID()
        (res,err) = self.db_manager.insert("processing",pd.DataFrame.from_dict([{"lid":LID,"first_added_timestamp":lut.getTimeStamp(),"finished_timestamp":None}]))
        if(res is None):
            exception_log += [err]
            raise RuntimeError(f"Did not manage to insert new lid into processing queue. LID: {LID}, error: {err}")

    def scheduleNewLidToSchedulingQ(self, runnable, exception_log):
        scheduling_factors = runnable.getScheduledFactors()
        self.sq.put(scheduling_factors,expected_at=self.nextProcessingTimestamp(runnable.getExpectedClose()))

    def jobGetNewLids(self,categories_of_interest):
        exceptions_log = []
        scraping_start_timestamp = lut.getTimeStamp()
        logging_columns = ['LID', 'Category Int', 'Category Name', 'Exception', 'Record Key', 'Timestamp']

        # First we create our list of reached pages
        scraped_tracker = dict()
        for (cat_int) in categories_of_interest.keys():
            magazine_overview = MagazineOverview(cat_int)
            magazine_overview.set_active_nr_pages()
            scraped_tracker[cat_int] = (magazine_overview, 0, magazine_overview.nrActivePages)


        # We iterate over each category, such that we scrape one page at a time from each
        nr_active_pages = [nr_active_pages for (_, _, nr_active_pages) in scraped_tracker.values()]
        for i in range(np.max(nr_active_pages)):

            for (cat_int, cat_name) in categories_of_interest.items():
                (mag_overview, page_reached, max_pages) = scraped_tracker[cat_int]

                if (page_reached < max_pages):
                    #print(f"At page: {page_reached} out of {max_pages} pages for category {cat_name}")

                    for LID in mag_overview[page_reached]:

                        if(self.isNewLid(LID)):

                            meta_data = ent.MetadataExtractor(LID, lut.getTimeStamp(), cat_int, cat_name)
                            runnable = ld.RunnableInsertion(self.session,self.engine,meta_data,)

                            self.recordNewLIDInMain(runnable,exceptions_log)
                            #TODO: Add a check, such that we only add to the processing queue, if we succesfully record it in the main DB
                            self.recordNewLidInProcessingQ(runnable, exceptions_log)
                            self.scheduleNewLidToSchedulingQ(runnable, exceptions_log)

                    scraped_tracker[cat_int] = (mag_overview, page_reached + 1, max_pages)

            lut.logExceptionsToCsv(exceptions_log, scraping_start_timestamp, logging_columns,r'C:\Users\DripTooHard\PycharmProjects\pythonProject1\Runnables\LIDLogs')
    def nextProcessingTimestamp(self,expected_close_timestamp, current_timestamp = lut.getTimeStamp().replace(tzinfo=None)):


        time_to_close = expected_close_timestamp - current_timestamp
        if time_to_close <= timedelta(minutes=10):
            return current_timestamp + timedelta(minutes=1)
        elif time_to_close <= timedelta(minutes=30):
            return current_timestamp + timedelta(minutes=2)
        elif time_to_close <= timedelta(hours=1):
            return current_timestamp + timedelta(minutes=5)
        elif time_to_close <= timedelta(hours=2):
            return current_timestamp + timedelta(minutes=15)
        elif time_to_close <= timedelta(hours=4):
            return current_timestamp + timedelta(minutes=30)
        elif time_to_close <= timedelta(hours=7):
            return current_timestamp + timedelta(hours=1)
        elif time_to_close <= timedelta(days=1):
            return current_timestamp + timedelta(hours=2)
        else:
            return current_timestamp + timedelta(hours=6)

def run_job_manager():
    conn = dbm.getPsycopg2Conn()
    Q = q.PQ(conn)
    jq = Q["job"]
    sq = Q["scheduling"]
    session, engine = dbm.getSessionEngine()
    jb_man = JobManager(jq, sq, session, engine)
    jb_man.main()

if __name__ == "__main__":
    # List to keep track of threads and job managers
    threads = []
    job_managers = []

    parser = argparse.ArgumentParser(description="Run job managers in multiple threads.")
    parser.add_argument(
        "--num-threads",
        type=int,
        default=3,
        help="Number of threads to run (default: 3)"
    )

    args = parser.parse_args()

    # Number of threads to run
    num_threads = args.num_threads

    for _ in range(num_threads):
        # Initialize and start a new thread
        thread = threading.Thread(target=run_job_manager)
        thread.start()
        threads.append(thread)

    # Keep the main application running until interrupted
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")

        # Stop all job managers
        for job_manager in job_managers:
            job_manager.stop()

        # Join all threads
        for thread in threads:
            thread.join()

        print("Application stopped.")
