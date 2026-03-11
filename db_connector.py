import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)

def get_cursor():
    return conn.cursor()