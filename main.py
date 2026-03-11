from fastapi import FastAPI, Depends, HTTPException
from seller_api import (
    get_countries_logic,
    create_or_update_profile_logic,
    get_seller_profile_logic,
    get_uuid_from_token,
    SellerProfile,
    Country
)
from typing import List

app = FastAPI(title="Seller API")


@app.get("/seller/master-data-countries", response_model=List[Country])
def get_countries():
    try:
        return get_countries_logic()
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")


@app.post("/seller/profile")
def create_or_update_profile(profile: SellerProfile, uuid: str = Depends(get_uuid_from_token)):
    try:
        return create_or_update_profile_logic(profile, uuid)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")


@app.get("/seller/profile")
def get_seller_profile(uuid: str = Depends(get_uuid_from_token)):
    try:
        return get_seller_profile_logic(uuid)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")