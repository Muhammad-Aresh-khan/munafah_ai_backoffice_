from db_connector import conn, get_cursor

def active_sellers_count():
    cursor = get_cursor()
    if not cursor:
        return 0
    try:
        sql = sql = """
                SELECT COUNT(*)
                FROM sellers s
                JOIN users u ON s.userId = u.id
                WHERE u.role = 'seller'
                AND u.status = 'active';
                """
        cursor.execute(sql)
        result = cursor.fetchone()
        return result[0] if result else 0

    except Exception:
        conn.rollback()
        return 0

    finally:
        cursor.close()