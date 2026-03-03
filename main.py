from fastapi import FastAPI
from sellers import router as seller_router

app = FastAPI(
    title="Admin Backoffice API",
    version="1.0"
)

app.include_router(seller_router)