from fastapi import APIRouter, HTTPException, Query
from db_connector import get_connection

router = APIRouter(prefix="/admin", tags=["Seller Listing"])


# GET ALL SELLERS (with pagination, sequential by userId)
@router.get("/sellers")
def get_all_sellers(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1)
):
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        offset = (page - 1) * limit
        cursor = conn.cursor()

        query = """
            SELECT
                u.id AS user_id,
                s.id AS seller_profile_id,
                u.name,
                u.email,
                u.status,
                s.businessName,
                c.name AS country
            FROM sellers s
            JOIN users u ON s.userId = u.id
            LEFT JOIN countries c ON s.countryOfOrigin = c.id
            WHERE u.role = 'seller'
            ORDER BY u.id ASC
            LIMIT %s OFFSET %s;
        """

        cursor.execute(query, (limit, offset))
        rows = cursor.fetchall()

        columns = [desc[0] for desc in cursor.description]
        sellers = [dict(zip(columns, row)) for row in rows]

        return {
            "page": page,
            "limit": limit,
            "data": sellers
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        conn.close()


# ✅ GET SINGLE SELLER PROFILE BY user_id
@router.get("/sellers/{user_id}")
def get_seller_by_user_id(user_id: int):
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor()

        query = """
            SELECT
                u.id AS user_id,
                s.id AS seller_profile_id,
                u.name,
                u.email,
                u.status,
                s.businessName,
                s.companyEmail,
                s.companyPhone,
                s.companyWebsite,
                s.socialLink,
                s.profileComplete,
                c.name AS country,
                ss.status AS subscription_status,
                sp.paymentStatus
            FROM sellers s
            JOIN users u ON s.userId = u.id
            LEFT JOIN countries c ON s.countryOfOrigin = c.id
            LEFT JOIN sellerSubscriptions ss ON ss.sellerId = s.id
            LEFT JOIN subscriptionPayments sp
                ON sp.sellerSubscriptionId = ss.id
            WHERE u.id = %s;
        """

        cursor.execute(query, (user_id,))
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Seller not found")

        columns = [desc[0] for desc in cursor.description]
        seller = dict(zip(columns, row))

        return seller

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        conn.close()