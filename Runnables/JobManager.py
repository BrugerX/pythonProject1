import pandas as pd

import utility.LoggingUtility as lut
from CW_Scraper import MagazineOverview
import LotData.LotData as ld
from RunningSettings import wanted_categories
import LotData.ExtractorsAndTables as ent
from utility import webscrapingUtil as wut
from sqlalchemy import create_engine
import numpy as np
import database.DatabaseManager as dbm
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
import pq.python.pq.Queue as q
import csv
import os
import time
import threading
import time

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
                print(f"Job manager sleeping for: {self.idle_time} seconds")
                time.sleep(self.idle_time)
                continue

            new_job_data = new_job.data

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
        self.sq.put(scheduling_factors)

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
                    print(f"At page: {page_reached} out of {max_pages} pages for category {cat_name}")

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

def run_lid_get():
    lid_get.main()

if __name__ == "__main__":
    conn = dbm.getPsycopg2Conn()
    Q = q.PQ(conn)
    jq = Q["job"]
    sq = Q["scheduling"]
    session,engine = dbm.getSessionEngine()
    jq.put({"task_type":"get_new_lids","categories_of_interest":{333:"watches"}})
    lid_get = JobManager(jq, sq, session, engine)


    # Create a Thread object with the target function
    thread = threading.Thread(target=run_lid_get)

    # Start the thread
    thread.start()

    # Keep the main application running until interrupted
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
        lid_get.stop()
        thread.join()
        print("Application stopped.")
