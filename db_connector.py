import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()


# Database Connection

try:

    conn = psycopg2.connect(

        database=os.getenv("database"),
        user=os.getenv("user"),
        password=os.getenv("password"),
        host=os.getenv("host"),
        port=os.getenv("port")

    )

    cursor = conn.cursor()

    print("Database Connected")


except Exception as e:

    print("Database Connection Error:", e)

    conn = None
    cursor = None