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

# Fetch list of databases
def get_mysql_databases(host, username, password):
    try:
        conn = mysql.connector.connect(
            host=host,
            user=username,
            password=password
        )
        cursor = conn.cursor()
        cursor.execute("SHOW DATABASES;")
        dbs = [db[0] for db in cursor.fetchall()]
        return {"databases": dbs}
    except Exception as e:
        return {"error": str(e)}

# Fetch tables and views
def get_mysql_objects(host, username, password, database):
    try:
        conn = mysql.connector.connect(
            host=host,
            user=username,
            password=password,
            database=database
        )
        cursor = conn.cursor()

        cursor.execute("SHOW FULL TABLES WHERE Table_type='BASE TABLE';")
        tables = [t[0] for t in cursor.fetchall()]

        cursor.execute("SHOW FULL TABLES WHERE Table_type='VIEW';")
        views = [v[0] for v in cursor.fetchall()]

        return {"tables": tables, "views": views}
    except Exception as e:
        return {"error": str(e)}

