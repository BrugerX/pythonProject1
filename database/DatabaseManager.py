from decouple import Config, RepositoryEnv
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from database.EnvSettings import environment_information
from psycopg2 import connect
from sqlalchemy import select, and_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import Table, MetaData, inspect, update,delete, insert

def getPredefinedTableNames():
    return ["meta","auction_history","favorite_history","bid","auction","shipping","image","spec"]

def getSessionEngine():
    engine = create_engine('postgresql://postgres:secret123@localhost:5432/postgres')
    Session = sessionmaker(bind=engine)
    session = Session()
    return (session,engine)

def getPsycopg2Settings():
    env_conf = Config(RepositoryEnv(environment_information["filepath"]))
    settings = f"user={env_conf.get(environment_information['database_username'])} password={env_conf.get(environment_information['database_password'])} dbname={env_conf.get(environment_information['database_name'])}"
    del(env_conf)
    return settings

def getPsycopg2Conn():
    settings = getPsycopg2Settings()
    return connect(settings)

def createSessionAndEngine(self,env_info = environment_information):
    env_conf = Config(RepositoryEnv(env_info["filepath"]))
    engine = create_engine(f'postgresql://{env_conf.get(env_info["database_username"])}:{env_conf.get(env_info["database_password"])}@localhost:5432/{env_conf.get(env_info["database_name"])}')
    del(env_conf)
    Session = sessionmaker(bind=self.engine)
    session = Session()
    return (session,engine)

class DatabaseManager:

    def __init__(self,session,engine):
        self.session = session
        self.engine = engine

    def getAllTableNames(self):
        query = f"SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';"
        result = self.session.execute(text(query))
        all_table_names = [name_tuple[0] for name_tuple in result.fetchall()]
        return  all_table_names # or fetch the result as required


    """
    
    @return true if LID is found in table, false if not - fails if the table doesn't have a lid column.
    """
    def exists(self,LID,table):
        query = f"SELECT EXISTS (SELECT 1 FROM {table} WHERE lid = :lid)"

        result = self.session.execute(text(query), {'lid': LID})
        return result.scalar()

    """

    Checks whether or not all tables have the specified LID - returns the tables that do not have that lid

    """

    def tablesWithout(self,LID):
        all_tables = self.getAllTableNames()
        tables_without = [table_name for table_name in all_tables if not self.exists(LID,table_name)]
        return tables_without

    def insert(self,table,dataframe):
        try:
            dataframe.to_sql(table, con=self.engine, if_exists='append', index=False)
            return [dataframe,None]
        except Exception as e:
            return (False,e)

    def update(self,table,lid,column,value):
        try:
            return (self.session.execute(f"UPDATE {table} SET {column} = {value} WHERE {table}.lid = {lid}"),None)
        except Exception as e:
            return (False,e)

    def hasFinalBid(self,LID):
        query = f"SELECT EXISTS (SELECT 1 FROM bid WHERE lid = :lid AND is_final_bid = True)"

        result = self.session.execute(text(query), {'lid': int(LID)})
        return result.scalar()

    def isClosed(self,LID):
        query = f"SELECT EXISTS (SELECT 1 FROM auction_history WHERE lid = :lid AND is_closed = True)"

        result = self.session.execute(text(query), {'lid': int(LID)})
        return result.scalar()

    def getMaxBidAmount(self,LID):
        query = f"SELECT max(amount) FROM bid WHERE lid = :lid GROUP BY lid"

        result = self.session.execute(text(query),{"lid":int(LID)})
        return result.scalar()


    def validateRecordDataframe(self, DF, table_name,unique_constraints):

        # Reflect the table
        metadata = MetaData()
        table = Table(table_name, metadata, autoload_with=self.engine)

        # Initialize an empty list to hold rows to insert
        rows_to_insert = []

        # Iterate over each row in the DataFrame
        for index, row in DF.iterrows():
            # Build the filter condition for the unique constraints
            filter_condition = and_(*[table.c[col] == row[col] for col in unique_constraints])

            # Check if the row already exists
            exists_query = select(table).where(filter_condition)
            result = self.session.execute(exists_query).fetchone()

            # If the row does not exist, add it to the list to insert
            if result is None:
                rows_to_insert.append(row)

        # Convert the rows to insert back to a DataFrame
        rows_to_insert_df = pd.DataFrame(rows_to_insert)

        return rows_to_insert_df

    def getRecordConstraints(self,table_name):
        insepctor = inspect(self.engine)

        if table_name in ["meta","bid","spec","auction"]:
            return insepctor.get_pk_constraint(table_name)["constrained_columns"]

        if table_name in ["shipping","image"]:
            return insepctor.get_unique_constraints(table_name)[0]["column_names"]

        if table_name in ["auction_history","favorite_history"]:
            return []



    def insertRecordDataframe(self, DF, table_name):
        unique_constraints = self.getRecordConstraints(table_name)
        valid_dataframe = self.validateRecordDataframe(DF, table_name, unique_constraints)

        result = self.insert(table_name, valid_dataframe)

        if table_name == "bid":
            LID = int(DF["lid"][0])
            current_max_bid_amount = self.getMaxBidAmount(LID)
            new_max_bid_row = DF[DF["amount"] == current_max_bid_amount]

            # If we do not already have a row with is final bid true, but the latest bid is the final bid, we need to update it
            if not self.hasFinalBid(LID) and new_max_bid_row["amount"].iloc[0] == current_max_bid_amount and \
                    new_max_bid_row["is_final_bid"].iloc[0]:
                # Define the table metadata
                # Reflect the table
                metadata = MetaData()
                table = Table(table_name, metadata, autoload_with=self.engine)

                # Create the delete statement
                delete_stmt = (
                    delete(table).
                    where(table.c.lid == LID).
                    where(table.c.amount == current_max_bid_amount).
                    where(table.c.is_final_bid != True)
                )

                # Execute the delete statement
                with self.engine.connect() as connection:
                    connection.execute(delete_stmt)
                    connection.commit()

                # Prepare the new row data
                new_row_data = new_max_bid_row.iloc[0].to_dict()

                # Create the insert statement
                insert_stmt = insert(table).values(new_row_data)

                # Execute the insert statement
                with self.engine.connect() as connection:
                    connection.execute(insert_stmt)
                    connection.commit()

                result[0] = pd.concat([result[0], new_max_bid_row])


        # Assuming you have a method to get the metadata
        # Make sure to replace `self.metadata` and `self.engine` with the actual SQLAlchemy metadata and engine objects in your class


        return result

    #DO NOT USE - IT IS TOO MESSY
    def automatic_validate_dataframe(self, df: pd.DataFrame, table_name: str) -> pd.DataFrame:
        # Reflect the table from the database
        metadata = MetaData()
        table = Table(table_name, metadata, autoload_with=self.engine)
        inspector = inspect(self.engine)
        unique_constraints = inspector.get_unique_constraints(table_name)

        # List to store indices of invalid rows
        invalid_indices = []

        # Function to check uniqueness in the existing database
        def is_unique_in_db(unique_columns, row):
            query = self.session.query(table)
            for col in unique_columns:
                query = query.filter(getattr(table.c, col) == row[col])
            return self.session.query(query.exists()).scalar()

        # Function to check uniqueness in the dataframe itself
        def is_unique_in_df(unique_columns, row, df_subset):
            subset = df_subset[unique_columns]
            return subset.duplicated().any()

        # Iterate over the DataFrame rows
        for index, row in df.iterrows():
            for constraint in unique_constraints:
                unique_columns = constraint['column_names']
                if is_unique_in_db(unique_columns, row) or is_unique_in_df(unique_columns, row, df[unique_columns]):
                    invalid_indices.append(index)
                    break

        # Drop invalid rows
        df_valid = df.drop(index=invalid_indices)

        return df_valid




"""  
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
"""


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