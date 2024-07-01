from psycopg2 import connect
from decouple import Config, RepositoryEnv
import pandas as pd

environment_information = {"database_username": "DBUSER", "database_password": "DBPASS", "database_name": "DBNAME",
                               "filepath": r"C:\Users\DripTooHard\PycharmProjects\pythonProject1\.env"}


