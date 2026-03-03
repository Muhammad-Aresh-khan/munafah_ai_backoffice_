from inactive_sellers import inactive_sellers_count
from active_sellers import active_sellers_count
from total_sellers import total_sellers_count
from db_connector import get_cursor
from fastapi import FastAPI
app=FastAPI()

@app.get("/admin/dashboard/summary")
def get_summary_of_sellers():
    try:
        return{
            "total_sellers": total_sellers_count(),
            "active_sellers": active_sellers_count(),
            "inactive_sellers": inactive_sellers_count()
        }
    except Exception as e:
        return {"Error":"counts fetch failed:"+str(e)}
    