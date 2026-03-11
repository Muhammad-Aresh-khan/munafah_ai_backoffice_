from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List
from db_connector import conn, get_cursor
from jose import jwt

# Constants
SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"

# Pydantic Models
class SellerProfile(BaseModel):
    businessName: str
    companyEmail: str
    companyPhone: str
    companyWebsite: str
    countryOfOrigin: int

class Country(BaseModel):
    id: int
    name: str

# Security Dependency
security = HTTPBearer()

def get_uuid_from_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        uuid = payload.get("uuid")
        if uuid is None:
            raise HTTPException(status_code=401, detail="Invalid token: UUID missing")
        return uuid
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


# API Logic Functions

def get_countries_logic() -> List[Country]:
    cursor = get_cursor()
    try:
        cursor.execute("SELECT id, name FROM countries ORDER BY name")
        rows = cursor.fetchall()
        return [{"id": r[0], "name": r[1]} for r in rows]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error while fetching countries: {e}")
    finally:
        cursor.close()


def create_or_update_profile_logic(profile: SellerProfile, uuid: str):
    cursor = get_cursor()
    try:
        # Get user
        cursor.execute("SELECT id, status FROM users WHERE uuid=%s", (uuid,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if user[1] != "active":
            raise HTTPException(status_code=403, detail="User not active")
        user_id = user[0]

        # Check seller existence
        cursor.execute("SELECT id FROM sellers WHERE userId=%s", (user_id,))
        seller = cursor.fetchone()

        if seller:
            cursor.execute("""
                UPDATE sellers
                SET businessName=%s,
                    companyEmail=%s,
                    companyPhone=%s,
                    companyWebsite=%s,
                    countryOfOrigin=%s,
                    profileComplete=true,
                    updatedAt=NOW()
                WHERE userId=%s
            """, (
                profile.businessName,
                profile.companyEmail,
                profile.companyPhone,
                profile.companyWebsite,
                profile.countryOfOrigin,
                user_id
            ))
        else:
            cursor.execute("""
                INSERT INTO sellers
                (userId, businessName, companyEmail, companyPhone, companyWebsite, countryOfOrigin, profileComplete)
                VALUES (%s,%s,%s,%s,%s,%s,true)
            """, (
                user_id,
                profile.businessName,
                profile.companyEmail,
                profile.companyPhone,
                profile.companyWebsite,
                profile.countryOfOrigin
            ))

        conn.commit()
        return {"message": "Seller profile saved successfully"}

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error while saving profile: {e}")
    finally:
        cursor.close()


def get_seller_profile_logic(uuid: str):
    cursor = get_cursor()
    try:
        # Get user
        cursor.execute("SELECT id, status FROM users WHERE uuid=%s", (uuid,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if user[1] != "active":
            raise HTTPException(status_code=403, detail="User not active")
        user_id = user[0]

        # Get seller profile
        cursor.execute("""
            SELECT s.businessName, s.companyEmail, s.companyPhone, s.companyWebsite, c.name
            FROM sellers s
            JOIN countries c ON s.countryOfOrigin = c.id
            WHERE s.userId=%s
        """, (user_id,))
        seller = cursor.fetchone()
        if not seller:
            raise HTTPException(status_code=404, detail="Seller profile not found")

        return {
            "businessName": seller[0],
            "companyEmail": seller[1],
            "companyPhone": seller[2],
            "companyWebsite": seller[3],
            "country": seller[4]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error while fetching profile: {e}")
    finally:
        cursor.close()