# dbconnection.py
import os
from dotenv import load_dotenv
import snowflake.connector
import mysql.connector

load_dotenv()

# Snowflake connection
def connect_to_snowflake():
    try:
        conn = snowflake.connector.connect(
            account=os.getenv('SNOWFLAKE_ACCOUNT'),
            user=os.getenv('SNOWFLAKE_USERNAME'),
            password=os.getenv('SNOWFLAKE_PASSWORD'),
            database=os.getenv('SNOWFLAKE_DATABASE'),
            schema=os.getenv('SNOWFLAKE_SCHEMA'),
            warehouse=os.getenv('SNOWFLAKE_WHAREHOUSE'),
            role=os.getenv('SNOWFLAKE_ROLE'),
        )
        print('Connected to Snowflake')
        return conn
    except Exception as e:
        print(f'Error connecting to Snowflake: {e}')

# MySQL connection
def connect_to_mysql(host, username, password, database):
    try:
        conn = mysql.connector.connect(
            host=host,
            user=username,
            password=password,
            database=database,
        )
        print('Connected to MySQL')
        return {'message': 'Connection succeeded'}
    except Exception as e:
        print(f'Error connecting to MySQL: {e}')
        return {'message': 'Connection failed'}
