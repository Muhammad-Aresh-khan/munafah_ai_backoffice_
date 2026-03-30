

from fastapi import HTTPException
from db_connector import conn, cursor


# ── 1. Payment Stats (4 header cards) ────────────────────────────────────────
def get_payment_stats():
    """
    Returns the four summary cards shown at the top of the Figma:
      - totalCollected   → all successful payments ever
      - thisMonth        → successful payments in current month
      - failedPayments   → count of failure payments
      - pendingPayments  → count of subscriptions with status='pending'
    """

    # Total collected (all successful payments)
    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM subscriptionpayments
        WHERE paymentstatus = 'success'
    """)
    total_collected = float(cursor.fetchone()[0])

    # This month collected
    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM subscriptionpayments
        WHERE paymentstatus = 'success'
          AND DATE_TRUNC('month', paymentdate) = DATE_TRUNC('month', NOW())
    """)
    this_month = float(cursor.fetchone()[0])

    # Failed payments count
    cursor.execute("""
        SELECT COUNT(*)
        FROM subscriptionpayments
        WHERE paymentstatus = 'failure'
    """)
    failed_payments = cursor.fetchone()[0]

    # Pending payments = subscriptions with status='pending'
    cursor.execute("""
        SELECT COUNT(*)
        FROM sellersubscriptions
        WHERE status = 'pending'
    """)
    pending_payments = cursor.fetchone()[0]

    return {
        "totalCollected": total_collected,
        "thisMonth": this_month,
        "failedPayments": failed_payments,
        "pendingPayments": pending_payments,
    }


# ── 2. Payments Table (paginated + filters) ───────────────────────────────────
def list_payments(
    page: int = 1,
    page_size: int = 10,
    status: str = None,        # 'success' | 'failure' | 'pending'
    country_id: int = None,    # Region/City filter → maps to seller's country
):
    """
    Returns paginated payment rows for the table:
      transactionId, seller name, business name, plan name,
      amount, paymentMethod, paymentDate, status (badge), invoice number.

    Filters:
      - status     → Verification Status dropdown in Figma
      - country_id → Region/City dropdown in Figma
    """
    if page < 1:
        raise HTTPException(status_code=400, detail="page must be >= 1")
    if page_size not in (5, 10, 20, 50):
        raise HTTPException(status_code=400, detail="page_size must be 5, 10, 20, or 50")

    offset = (page - 1) * page_size

    # Build dynamic WHERE clauses
    filters = []
    params = []

    if status == "pending":
        # Pending = subscription status pending (no payment row yet)
        # Handled separately below — skip payment table filter
        pass
    elif status == "success":
        filters.append("sp.paymentstatus = 'success'")
    elif status == "failure":
        filters.append("sp.paymentstatus = 'failure'")

    if country_id:
        filters.append("sel.countryoforigin = %s")
        params.append(country_id)

    where_clause = ("WHERE " + " AND ".join(filters)) if filters else ""

    # Count query
    cursor.execute(f"""
        SELECT COUNT(*)
        FROM subscriptionpayments sp
        JOIN sellersubscriptions ss  ON ss.id  = sp.sellersubscriptionid
        JOIN sellers             sel ON sel.id = ss.sellerid
        JOIN users               u   ON u.id   = sel.userid
        JOIN subscriptionplans   pl  ON pl.id  = ss.subscriptionplanid
        {where_clause}
    """, params)
    total = cursor.fetchone()[0]

    # Data query
    cursor.execute(f"""
        SELECT
            sp.id                AS paymentid,
            sp.transactionid,
            u.name               AS sellername,
            sel.businessname,
            pl.name              AS planname,
            sp.amount,
            sp.paymentmethod,
            sp.paymentdate,
            sp.paymentstatus,
            -- Invoice number derived from payment id
            CONCAT('INV-', LPAD(sp.id::TEXT, 3, '0')) AS invoicenumber
        FROM subscriptionpayments sp
        JOIN sellersubscriptions ss  ON ss.id  = sp.sellersubscriptionid
        JOIN sellers             sel ON sel.id = ss.sellerid
        JOIN users               u   ON u.id   = sel.userid
        JOIN subscriptionplans   pl  ON pl.id  = ss.subscriptionplanid
        {where_clause}
        ORDER BY sp.paymentdate DESC
        LIMIT %s OFFSET %s
    """, params + [page_size, offset])

    cols = [
        "paymentId", "transactionId", "sellerName", "businessName",
        "planName", "amount", "paymentMethod", "paymentDate",
        "paymentStatus", "invoiceNumber",
    ]
    rows = [dict(zip(cols, row)) for row in cursor.fetchall()]

    for row in rows:
        if row["paymentDate"]:
            row["paymentDate"] = row["paymentDate"].date().isoformat()
        if row["amount"] is not None:
            row["amount"] = float(row["amount"])

        # Badge mapping for Figma
        row["badge"] = "Completed" if row["paymentStatus"] == "success" else "Failed"

    return {
        "data": rows,
        "pagination": {
            "total": total,
            "page": page,
            "pageSize": page_size,
            "totalPages": -(-total // page_size),
        },
    }


# ── 3. Payment Detail (eye icon) ──────────────────────────────────────────────
def get_payment_detail(payment_id: int):
    """
    Full detail for a single payment transaction.
    Shown when admin clicks the eye icon in the table.
    """
    cursor.execute("""
        SELECT
            sp.id,
            sp.transactionid,
            sp.amount,
            sp.currency,
            sp.paymentstatus,
            sp.paymentdate,
            sp.paymentmethod,
            u.name          AS sellername,
            u.email         AS selleremail,
            sel.businessname,
            sel.companyphone,
            pl.name         AS planname,
            pl.price        AS planprice,
            ss.startdate,
            ss.enddate,
            CONCAT('INV-', LPAD(sp.id::TEXT, 3, '0')) AS invoicenumber
        FROM subscriptionpayments sp
        JOIN sellersubscriptions ss  ON ss.id  = sp.sellersubscriptionid
        JOIN sellers             sel ON sel.id = ss.sellerid
        JOIN users               u   ON u.id   = sel.userid
        JOIN subscriptionplans   pl  ON pl.id  = ss.subscriptionplanid
        WHERE sp.id = %s
    """, (payment_id,))

    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Payment not found")

    (pay_id, txn_id, amount, currency, pay_status, pay_date,
     pay_method, seller_name, seller_email, biz_name, phone,
     plan_name, plan_price, start_date, end_date, invoice_no) = row

    return {
        "paymentId": pay_id,
        "transactionId": txn_id,
        "amount": float(amount) if amount else None,
        "currency": currency,
        "paymentStatus": pay_status,
        "badge": "Completed" if pay_status == "success" else "Failed",
        "paymentDate": pay_date.date().isoformat() if pay_date else None,
        "paymentMethod": pay_method,
        "invoiceNumber": invoice_no,
        "seller": {
            "name": seller_name,
            "email": seller_email,
            "businessName": biz_name,
            "phone": phone,
        },
        "plan": {
            "name": plan_name,
            "price": float(plan_price) if plan_price else None,
            "startDate": start_date.date().isoformat() if start_date else None,
            "endDate": end_date.date().isoformat() if end_date else None,
        },
    }
