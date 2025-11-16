# App.py 
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from pydantic import BaseModel
from Connection import connect_to_mysql
from Connection import connect_to_snowflake

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # allow all origins (React frontend)
    allow_credentials=True,
    allow_methods=["*"],          # allow POST, GET, OPTIONS etc.
    allow_headers=["*"],          # allow all headers
)


# Pydantic model to accept JSON body
class MySQLCredentials(BaseModel):
    host: str
    username: str
    password: str
    database: str

@app.post("/connect-mysql")
async def connect_mysql(
    host: str | None = None,
    username: str | None = None,
    password: str | None = None,
    database: str | None = None,
    body: MySQLCredentials | None = None
):
    """
    Accepts:
    - Query params OR
    - JSON body
    """

    # If JSON body is provided, override values
    if body:
        host = body.host
        username = body.username
        password = body.password
        database = body.database

    return connect_to_mysql(host, username, password, database)


@app.get("/connect-sf")
async def connect_sf():
    conn = connect_to_snowflake()
    if conn:
        print("success")
        return "success"
    else:
        print("fail")
        return "fail"
