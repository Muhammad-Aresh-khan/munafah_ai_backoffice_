"""
subscriptions.py
────────────────
Business logic for subscription management (admin-facing).
All table/column names lowercase — PostgreSQL folds unquoted identifiers to lowercase.
"""

from fastapi import HTTPException
from db_connector import conn, cursor


# ── 1. List All Plans ─────────────────────────────────────────────────────────
def list_plans():
    """Return all subscription plans (for plan selector / overview cards)."""
    cursor.execute("""
        SELECT id, name, price, currency, durationmonths,
               createdat, updatedat
        FROM subscriptionplans
        ORDER BY price ASC
    """)
    rows = cursor.fetchall()
    cols = ["id", "name", "price", "currency", "durationMonths",
            "createdAt", "updatedAt"]
    return [dict(zip(cols, row)) for row in rows]


# ── 2. Plan Stats (header cards) ──────────────────────────────────────────────
def get_plan_stats(plan_id: int):
    """
    Returns the three summary cards shown at the top of the Figma:
      - planName, price
      - totalSubscribers, newThisMonth
      - monthlyRevenue
    """
    cursor.execute(
        "SELECT id, name, price, currency FROM subscriptionplans WHERE id=%s",
        (plan_id,)
    )
    plan = cursor.fetchone()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    _, plan_name, price, currency = plan

    # Total active subscribers for this plan
    cursor.execute("""
        SELECT COUNT(*) FROM sellersubscriptions
        WHERE subscriptionplanid=%s AND status='active'
    """, (plan_id,))
    total_subscribers = cursor.fetchone()[0]

    # New this month (started in current calendar month)
    cursor.execute("""
        SELECT COUNT(*) FROM sellersubscriptions
        WHERE subscriptionplanid=%s
          AND status='active'
          AND DATE_TRUNC('month', startdate) = DATE_TRUNC('month', NOW())
    """, (plan_id,))
    new_this_month = cursor.fetchone()[0]

    # Monthly revenue = active subscriber count x plan price
    monthly_revenue = float(total_subscribers) * float(price)

    return {
        "planName": plan_name,
        "price": float(price),
        "currency": currency,
        "billingCycle": "Monthly",
        "totalSubscribers": total_subscribers,
        "newThisMonth": new_this_month,
        "monthlyRevenue": round(monthly_revenue, 2),
    }


# ── 3. List Sellers on a Plan (paginated table) ───────────────────────────────
def list_plan_sellers(plan_id: int, page: int = 1, page_size: int = 10):
    """
    Returns the paginated seller rows shown in the subscription table.
    """
    if page < 1:
        raise HTTPException(status_code=400, detail="page must be >= 1")
    if page_size not in (5, 10, 20, 50):
        raise HTTPException(status_code=400, detail="page_size must be 5, 10, 20, or 50")

    offset = (page - 1) * page_size

    cursor.execute("""
        SELECT COUNT(*) FROM sellersubscriptions
        WHERE subscriptionplanid=%s
    """, (plan_id,))
    total = cursor.fetchone()[0]

    cursor.execute("""
        SELECT
            ss.id                        AS subscriptionid,
            u.name                       AS sellername,
            sel.businessname,
            ss.startdate,
            ss.enddate                   AS nextbilling,
            ss.status                    AS subscriptionstatus,
            (
                SELECT sp.paymentstatus
                FROM subscriptionpayments sp
                WHERE sp.sellersubscriptionid = ss.id
                ORDER BY sp.paymentdate DESC
                LIMIT 1
            )                            AS latestpaymentstatus
        FROM sellersubscriptions ss
        JOIN sellers sel ON sel.id = ss.sellerid
        JOIN users   u   ON u.id  = sel.userid
        WHERE ss.subscriptionplanid = %s
        ORDER BY ss.startdate DESC
        LIMIT %s OFFSET %s
    """, (plan_id, page_size, offset))

    cols = [
        "subscriptionId", "sellerName", "businessName",
        "startDate", "nextBilling", "subscriptionStatus",
        "latestPaymentStatus",
    ]
    rows = [dict(zip(cols, row)) for row in cursor.fetchall()]

    for row in rows:
        # Serialize dates
        for date_col in ("startDate", "nextBilling"):
            if row[date_col]:
                row[date_col] = row[date_col].date().isoformat()

        # Derive badge for Figma: Paid / Pending / Failed
        sub_status = row["subscriptionStatus"]
        pay_status = row["latestPaymentStatus"]  # 'success' | 'failure' | None

        if sub_status == "pending":
            row["badge"] = "Pending"
        elif sub_status == "active" and pay_status == "success":
            row["badge"] = "Paid"
        elif pay_status == "failure":
            row["badge"] = "Failed"
        elif sub_status in ("expired", "cancelled"):
            row["badge"] = sub_status.capitalize()
        else:
            row["badge"] = "Pending"  # fallback: active but no payment yet

    return {
        "data": rows,
        "pagination": {
            "total": total,
            "page": page,
            "pageSize": page_size,
            "totalPages": -(-total // page_size),
        },
    }


# ── 4. Subscription Detail (eye icon) ────────────────────────────────────────
def get_subscription_detail(subscription_id: int):
    """
    Full detail for a single subscription — seller info, plan info,
    and payment history. Shown when admin clicks the eye icon.
    """
    cursor.execute("""
        SELECT
            ss.id, ss.startdate, ss.enddate, ss.status,
            u.name        AS sellername,
            u.email       AS selleremail,
            sel.businessname, sel.companyphone,
            sp.name       AS planname,
            sp.price,     sp.currency,   sp.durationmonths
        FROM sellersubscriptions ss
        JOIN sellers           sel ON sel.id = ss.sellerid
        JOIN users             u   ON u.id  = sel.userid
        JOIN subscriptionplans sp  ON sp.id = ss.subscriptionplanid
        WHERE ss.id = %s
    """, (subscription_id,))

    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Subscription not found")

    (sub_id, start, end, status,
     seller_name, seller_email, biz_name, phone,
     plan_name, price, currency, duration) = row

    # Payment history for this subscription
    cursor.execute("""
        SELECT id, amount, currency, paymentstatus, paymentdate,
               transactionid, paymentmethod
        FROM subscriptionpayments
        WHERE sellersubscriptionid = %s
        ORDER BY paymentdate DESC
    """, (subscription_id,))

    pay_cols = ["id", "amount", "currency", "paymentStatus",
                "paymentDate", "transactionId", "paymentMethod"]
    payments = []
    for p in cursor.fetchall():
        prow = dict(zip(pay_cols, p))
        if prow["paymentDate"]:
            prow["paymentDate"] = prow["paymentDate"].isoformat()
        payments.append(prow)

    return {
        "subscriptionId": sub_id,
        "startDate": start.date().isoformat() if start else None,
        "endDate": end.date().isoformat() if end else None,
        "status": status,
        "seller": {
            "name": seller_name,
            "email": seller_email,
            "businessName": biz_name,
            "phone": phone,
        },
        "plan": {
            "name": plan_name,
            "price": float(price),
            "currency": currency,
            "durationMonths": duration,
        },
        "paymentHistory": payments,
    }
