import psycopg2 as pg2
from decouple import Config, RepositoryEnv
import threading
from psycopg2.extensions import AsIs

class Psycopg2Connection:

    def __init__(self,usernameEnvName,passwordEnvName,dbnameEnvName):

        self.usernameEnvName = usernameEnvName
        self.passwordEnvName = passwordEnvName
        self.dbnameEnvName = dbnameEnvName

        envFilePath = r"C:\Users\DripTooHard\PycharmProjects\pythonProject1\.env"
        env_conf = Config(RepositoryEnv(envFilePath))

        try:
            self.conn = pg2.connect(f"dbname='{env_conf.get(dbnameEnvName)}' user='{env_conf.get(usernameEnvName)}' host='localhost' password='{env_conf.get(self.passwordEnvName)}'")
        except Exception as e:
            raise Exception(f"I am unable to connect to the database, error occured: {e}")

        self.cur = self.conn.cursor()


    def query(self,query,data):
        self.cur.execute(query,data)

    def fetchone(self):
        self.cur.fetchone()

    def fetchall(self):
        self.cur.fetchall()

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def __del__(self):
        self.conn.close()
        self.cur.close()


class DatabaseManager:

    def __init__(self,usernameEnvName,passwordEnvName,dbnameEnvName):

        self.dbConnection = Psycopg2Connection(usernameEnvName,passwordEnvName,dbnameEnvName)
        self.lotDataQueue = []
        self.running = False

        self.thread = threading.Thread(target=self.workTheQueue)

    def isEmpty(self):
        return len(self.lotDataQueue>0)

    def stop(self):
        self.running = False

    def isRunning(self):
        return self.running

    def start(self):
        self.running = True
        self.thread.start()

    def insertDataRow(self,drowDict,tableName):
        columns = drowDict.keys()
        values = [drowDict[column] for column in columns]

        insert_statement = f'insert into {tableName} (%s) values %s'

        self.dbConnection.query(insert_statement, (AsIs(','.join(columns)), tuple(values)))

    def checkExistence(self,drowDict,tableName,isBid = False):
        try:
            if(isBid):
                query = ("SELECT * FROM {table} WHERE LID = %s AND BID = %s").format(
                    table=tableName
                )
                self.dbConnection.query(query, (str(drowDict["LID"]), str(drowDict["BID"])))
            else:
                query = ("SELECT * FROM {table} WHERE LID = %s").format(
                    table=tableName
                )
                self.dbConnection.query(query, (str(drowDict["LID"]),))
        except Exception as e:
            print(e)

        return self.dbConnection.fetchone() is not None

    def processLotData(self,allLotData):
        for key in allLotData.keys():
            lotData = allLotData[key]

            for drow in lotData:
                alreadyExists = self.checkExistence(drow,key,(key == "bid_data"))

                if not (alreadyExists):
                    self.insertDataRow(drow,key)
                    self.dbConnection.commit()


    def workTheQueue(self):

        if(self.isEmpty()):
            pass
        else:
            currentLotData = self.lotDataQueue.pop()
            self.processLotData(currentLotData)



from LotData.DataRow import ALlLotData
from database.DatabaseManager import DatabaseManager
from CW_Scraper import MagazineOverview
import psycopg2 as pg2
import traceback
import Browser
import re
import time
#%% md
if __name__ == "__main__":
    magOverview = MagazineOverview(599)
    firstPageLIDs = magOverview[0]
    #randomLID = firstPageLIDs[0]
    randomLID = 81889801

    lotData = ALlLotData(randomLID)
    lotData.composeDataRows()


    dbm = DatabaseManager("DBUSER","DBPASS","DBNAME")
    dbm.processLotData(lotData)
    print(lotData)