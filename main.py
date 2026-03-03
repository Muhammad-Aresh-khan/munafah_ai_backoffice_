from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Literal

from seller_controls import update_status


app = FastAPI(
    title="Seller Controls API",
    description="Admin Seller Control System",
    version="1.0"
)


class UpdateStatus(BaseModel):

    status: Literal[
        "active",
        "inactive"
    ]


@app.patch("/admin/sellers/{seller_id}/status")

def status_api(
        seller_id: int,
        update: UpdateStatus):

    try:

        return update_status(
            seller_id,
            update.status
        )

    # If seller_controls already raised HTTPException
    except HTTPException as e:

        raise e

    # Unexpected errors
    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail="Server Error: " + str(e)
        )