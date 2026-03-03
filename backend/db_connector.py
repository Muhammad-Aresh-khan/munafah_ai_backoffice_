import os, psycopg2
from dotenv import load_dotenv
current_dir=os.path.dirname(os.path.abspath(__file__))
project_root=os.path.abspath(os.path.join(current_dir,'..'))
load_dotenv()

# CONNECTION TO POSTGRESQL DATABASE
try:
    conn=psycopg2.connect(
        host=os.getenv('host'),
        port=os.getenv('port'),
        database=os.getenv('database'),
        user=os.getenv('user'),
        password=os.getenv('password')
    )
    if conn:
        print("Database connection established successfully.")

except Exception as e:
    print(f"Error connecting to database: {e}")
    conn=None


def get_cursor():
    if conn:
        return conn.cursor()
    return None