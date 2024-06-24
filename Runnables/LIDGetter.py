import utility.LoggingUtility as lut
from CW_Scraper import MagazineOverview
import LotData.LotData as ld
from RunningSettings import wanted_categories
import LotData.ExtractorsAndTables as ent
from utility import webscrapingUtil as wut
from sqlalchemy import create_engine
import numpy as np
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
import csv
import os




if __name__ == '__main__':
    lut.getTimeStamp()
    exceptions = []
    scraping_start_timestamp = lut.getTimeStamp()
    logging_columns = ['LID', 'Category Int', 'Category Name', 'Exception', 'Record Key', 'Timestamp']

    #First we create our list of reached pages
    scraped_tracker = dict()
    for (cat_int) in wanted_categories.keys():
        magazine_overview = MagazineOverview(cat_int)
        magazine_overview.set_active_nr_pages()
        scraped_tracker[cat_int] = (magazine_overview,0,magazine_overview.nrActivePages)

    nr_categories = len(wanted_categories)

    #instantiate engine
    engine = create_engine('postgresql://postgres:secret123@localhost:5432/postgres')
    Session = sessionmaker(bind=engine)
    session = Session()

    #We iterate over each category, such that we scrape one page at a time from each
    nr_active_pages = [nr_active_pages for (_,_,nr_active_pages) in scraped_tracker.values()]
    for i in range(np.max(nr_active_pages)):

        for (cat_int,cat_name) in wanted_categories.items():
            (mag_overview,page_reached,max_pages) = scraped_tracker[cat_int]

            if(page_reached < max_pages):
                #print(f"At page: {page_reached} out of {max_pages} pages for category {cat_name}")

                for LID in mag_overview[page_reached]:
                    meta_data = ent.MetadataExtractor(LID, lut.getTimeStamp(), cat_int, cat_name)
                    l_data = ld.LotData(meta_data)

                    for record_key in ["meta_record","favorite_history_record","auction_history_record"]:
                        table = record_key.replace("_record","")
                        query = f"SELECT EXISTS (SELECT 1 FROM {table} WHERE lid = :lid)"

                        result = session.execute(text(query), {'lid': LID})
                        exists = result.scalar()  # or fetch the result as required
                        if(not exists):
                            try:
                                df = l_data[record_key]

                                if(record_key == "meta_record"):
                                    df["status"] = "new"
                                df.to_sql(table, con=engine, if_exists='append', index=False)

                            except Exception as e:
                                exceptions += [(LID,cat_int,cat_name,e,record_key,lut.getTimeStamp())]

                scraped_tracker[cat_int] = (mag_overview,page_reached + 1, max_pages)

    lut.logExceptionsToCsv(exceptions,scraping_start_timestamp,logging_columns,r'C:\Users\DripTooHard\PycharmProjects\pythonProject1\Runnables\LIDLogs')

