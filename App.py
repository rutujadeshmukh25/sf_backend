# # App.py 
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi import FastAPI, Body
# from pydantic import BaseModel
# from Connection import connect_to_mysql, connect_to_snowflake, get_mysql_databases, get_mysql_objects

# app = FastAPI()

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],          # allow all origins (React frontend)
#     allow_credentials=True,
#     allow_methods=["*"],          # allow POST, GET, OPTIONS etc.
#     allow_headers=["*"],          # allow all headers
# )


# # Pydantic model to accept JSON body
# class MySQLCredentials(BaseModel):
#     host: str
#     username: str
#     password: str
#     database: str

# @app.post("/connect-mysql")
# async def connect_mysql(
#     host: str | None = None,
#     username: str | None = None,
#     password: str | None = None,
#     database: str | None = None,
#     body: MySQLCredentials | None = None
# ):
#     """
#     Accepts:
#     - Query params OR
#     - JSON body
#     """

#     # If JSON body is provided, override values
#     if body:
#         host = body.host
#         username = body.username
#         password = body.password
#         database = body.database

#     return connect_to_mysql(host, username, password, database)


# @app.get("/connect-sf")
# async def connect_sf():
#     conn = connect_to_snowflake()
#     if conn:
#         print("success")
#         return "success"
#     else:
#         print("fail")
#         return "fail"


# @app.post("/mysql/databases")
# async def list_databases(data: dict = Body(...)):
#     try:
#         conn = mysql.connector.connect(
#             host=data["host"],
#             user=data["username"],
#             password=data["password"]
#         )
#         cursor = conn.cursor()
#         cursor.execute("SHOW DATABASES;")
#         dbs = [db[0] for db in cursor.fetchall()]
#         cursor.close()
#         conn.close()

#         return {"databases": dbs}

#     except Exception as e:
#         return {"error": str(e)}


# @app.post("/mysql/objects")
# async def list_objects(data: dict = Body(...)):
#     try:
#         conn = mysql.connector.connect(
#             host=data["host"],
#             user=data["username"],
#             password=data["password"],
#             database=data["database"]
#         )
#         cursor = conn.cursor()

#         cursor.execute("SHOW FULL TABLES WHERE Table_type = 'BASE TABLE';")
#         tables = [row[0] for row in cursor.fetchall()]

#         cursor.execute("SHOW FULL TABLES WHERE Table_type = 'VIEW';")
#         views = [row[0] for row in cursor.fetchall()]

#         cursor.close()
#         conn.close()

#         return {
#             "tables": tables,
#             "views": views
#         }

#     except Exception as e:
#         return {"error": str(e)}


# @app.post("/mysql/get_ddl")
# async def get_ddl(data: dict = Body(...)):
#     try:
#         conn = mysql.connector.connect(
#             host=data["host"],
#             user=data["username"],
#             password=data["password"],
#             database=data["database"]
#         )
#         cursor = conn.cursor()

#         cursor.execute(f"SHOW CREATE TABLE `{data['object']}`;")
#         ddl = cursor.fetchone()[1]

#         cursor.close()
#         conn.close()

#         return {"ddl": ddl}

#     except Exception as e:
#         return {"error": str(e)}


# App.py
from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
import mysql.connector
import io
import csv
import zipfile
import traceback

from pydantic import BaseModel
from Connection import connect_to_snowflake


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # allow all origins (React frontend)
    allow_credentials=True,
    allow_methods=["*"],          # allow POST, GET, OPTIONS etc.
    allow_headers=["*"],          # allow all headers
)

@app.get("/connect-sf")
async def connect_sf():
    conn = connect_to_snowflake()
    if conn:
        print("success")
        return "success"
    else:
        print("fail")
        return "fail"

def make_mysql_conn(host, user, password, database=None):
    params = {"host": host, "user": user, "password": password}
    if database:
        params["database"] = database
    return mysql.connector.connect(**params)

@app.post("/connect-mysql")
def connect_mysql(data: dict = Body(...)):
    """
    Connect using host/user/password, return list of databases on success.
    """
    try:
        host = data["host"]
        user = data["username"]
        password = data["password"]

        conn = make_mysql_conn(host, user, password)
        cursor = conn.cursor()
        cursor.execute("SHOW DATABASES;")
        databases = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()

        return {"status": "success", "databases": databases, "message": "Connected and databases fetched"}
    except Exception as e:
        return {"status": "error", "databases": [], "message": str(e)}

@app.post("/mysql/objects")
def mysql_objects(data: dict = Body(...)):
    """
    Return tables & views for a selected database.
    Expects: host, username, password, database
    """
    try:
        host = data["host"]
        user = data["username"]
        password = data["password"]
        database = data["database"]

        conn = make_mysql_conn(host, user, password, database)
        cursor = conn.cursor()

        cursor.execute("SHOW FULL TABLES WHERE Table_type = 'BASE TABLE';")
        tables = [row[0] for row in cursor.fetchall()]

        cursor.execute("SHOW FULL TABLES WHERE Table_type = 'VIEW';")
        views = [row[0] for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        return {"status": "success", "tables": tables, "views": views}
    except Exception as e:
        return {"status": "error", "tables": [], "views": [], "message": str(e)}

@app.post("/mysql/get_ddl")
def mysql_get_ddl(data: dict = Body(...)):
    """
    Get DDL for a single object (table/view). Returns text in JSON.
    Expects: host, username, password, database, object (name)
    """
    try:
        host = data["host"]
        user = data["username"]
        password = data["password"]
        database = data["database"]
        obj = data["object"]

        conn = make_mysql_conn(host, user, password, database)
        cursor = conn.cursor()
        # SHOW CREATE TABLE works for tables and views (for views returns CREATE VIEW)
        cursor.execute(f"SHOW CREATE TABLE `{obj}`;")
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if not row:
            return {"status": "error", "message": f"DDL not found for {obj}"}

        ddl = row[1]
        return {"status": "success", "object": obj, "ddl": ddl}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/mysql/download_ddls")
def mysql_download_ddls(data: dict = Body(...)):
    """
    Download DDLs for multiple objects as a zip of .sql files.
    Expects: host, username, password, database, objects: [name,...]
    Returns a StreamingResponse with zip bytes.
    """
    try:
        host = data["host"]
        user = data["username"]
        password = data["password"]
        database = data["database"]
        objects = data.get("objects", [])

        conn = make_mysql_conn(host, user, password, database)
        cursor = conn.cursor()

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for obj in objects:
                try:
                    cursor.execute(f"SHOW CREATE TABLE `{obj}`;")
                    row = cursor.fetchone()
                    if row:
                        ddl = row[1]
                    else:
                        ddl = f"-- Could not fetch DDL for {obj}\n"
                except Exception as e:
                    ddl = f"-- Error fetching DDL for {obj}: {e}\n"

                filename = f"{obj}.sql"
                zf.writestr(filename, ddl)
        cursor.close()
        conn.close()

        zip_buffer.seek(0)
        headers = {
            "Content-Disposition": f"attachment; filename=ddls_{database}.zip"
        }
        return StreamingResponse(zip_buffer, media_type="application/x-zip-compressed", headers=headers)
    except Exception as e:
        traceback.print_exc()
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

@app.post("/mysql/download_data")
def mysql_download_data(data: dict = Body(...)):
    """
    Download data for the selected objects (tables/views).
    If one object -> return single CSV file.
    If multiple -> zip containing CSVs.
    Expects: host, username, password, database, objects: [name,...], limit (optional)
    """
    try:
        host = data["host"]
        user = data["username"]
        password = data["password"]
        database = data["database"]
        objects = data.get("objects", [])
        limit = int(data.get("limit", 0))

        conn = make_mysql_conn(host, user, password, database)
        cursor = conn.cursor()

        # If single object, stream CSV directly
        if len(objects) == 1:
            obj = objects[0]
            query = f"SELECT * FROM `{obj}`"
            if limit > 0:
                query += f" LIMIT {limit}"
            cursor.execute(query)
            cols = [c[0] for c in cursor.description]

            def iter_csv():
                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow(cols)
                yield output.getvalue()
                output.seek(0); output.truncate(0)

                for row in cursor:
                    writer.writerow(list(row))
                    yield output.getvalue()
                    output.seek(0); output.truncate(0)

            return StreamingResponse(iter_csv(), media_type="text/csv", headers={
                "Content-Disposition": f"attachment; filename={obj}.csv"
            })

        # Multiple objects -> create zip of CSVs
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for obj in objects:
                try:
                    q = f"SELECT * FROM `{obj}`"
                    if limit > 0:
                        q += f" LIMIT {limit}"
                    cursor.execute(q)
                    cols = [c[0] for c in cursor.description]
                    csv_buf = io.StringIO()
                    writer = csv.writer(csv_buf)
                    writer.writerow(cols)
                    for row in cursor:
                        writer.writerow(list(row))
                    zf.writestr(f"{obj}.csv", csv_buf.getvalue())
                except Exception as e:
                    zf.writestr(f"{obj}_error.txt", f"Error fetching data for {obj}: {e}\n")
        cursor.close()
        conn.close()

        zip_buffer.seek(0)
        headers = {"Content-Disposition": f"attachment; filename=data_{database}.zip"}
        return StreamingResponse(zip_buffer, media_type="application/x-zip-compressed", headers=headers)

    except Exception as e:
        traceback.print_exc()
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

