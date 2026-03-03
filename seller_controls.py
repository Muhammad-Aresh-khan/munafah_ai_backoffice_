
from fastapi import HTTPException
from db_connector import conn, cursor


def update_status(seller_id, status):

    try:

        # Update user status using sellerId
        cursor.execute("""
        UPDATE users
        SET status=%s
        FROM sellers
        WHERE sellers.userId = users.id
        AND sellers.id = %s
        """,
        (status, seller_id))


        # If no row updated → seller not found
        if cursor.rowcount == 0:

            raise HTTPException(
                status_code=404,
                detail="Seller not found"
            )


        conn.commit()


        return {
            "success": True,
            "message": f"Seller {seller_id} status updated to {status}"
        }


    except HTTPException:
        raise


    except Exception as e:

        conn.rollback()

        raise HTTPException(
            status_code=500,
            detail="Database error: " + str(e)
        )