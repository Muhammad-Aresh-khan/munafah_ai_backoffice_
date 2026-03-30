"""
main.py
───────
FastAPI entry point.
Routes grouped by domain — Subscriptions and Payments.
Never put business logic here.
"""

from fastapi import FastAPI, HTTPException, Query
from typing import Optional

from subscriptions import (
    list_plans,
    get_plan_stats,
    list_plan_sellers,
    get_subscription_detail,
)
from payments import (
    get_payment_stats,
    list_payments,
    get_payment_detail,
)


app = FastAPI(
    title="Marketplace Auth & Seller API",
    description="Authentication, OTP Verification, Subscription Management",
    version="2.0",
)


# ══════════════════════════════════════════════════════════════════════════════
# Subscription Routes
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/subscriptions/plans", tags=["Subscriptions"])
def list_plans_api():
    """List all subscription plans."""
    try:
        return list_plans()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Server error: " + str(e))


@app.get("/subscriptions/plans/{plan_id}/stats", tags=["Subscriptions"])
def plan_stats_api(plan_id: int):
    """Summary stats for a plan — drives the 3 header cards."""
    try:
        return get_plan_stats(plan_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Server error: " + str(e))


@app.get("/subscriptions/plans/{plan_id}/sellers", tags=["Subscriptions"])
def plan_sellers_api(
    plan_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, description="Rows per page: 5 | 10 | 20 | 50"),
):
    """Paginated seller table with Paid / Pending / Failed badges."""
    try:
        return list_plan_sellers(plan_id, page, page_size)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Server error: " + str(e))


@app.get("/subscriptions/{subscription_id}", tags=["Subscriptions"])
def subscription_detail_api(subscription_id: int):
    """Full detail for one subscription — eye icon view."""
    try:
        return get_subscription_detail(subscription_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Server error: " + str(e))


# ══════════════════════════════════════════════════════════════════════════════
# Payment Routes
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/payments/stats", tags=["Payments"])
def payment_stats_api():
    """
    4 header cards:
    Total Collected, This Month, Failed Payments count, Pending Payments count.
    """
    try:
        return get_payment_stats()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Server error: " + str(e))


@app.get("/payments", tags=["Payments"])
def list_payments_api(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, description="Rows per page: 5 | 10 | 20 | 50"),
    status: Optional[str] = Query(None, description="Filter: success | failure | pending"),
    country_id: Optional[int] = Query(None, description="Filter by country/region ID"),
):
    """
    Paginated payments table.
    Columns: Transaction ID, Seller, Plan, Amount, Method, Date, Status badge, Invoice.
    Filters: Verification Status dropdown + Region/City dropdown.
    """
    try:
        return list_payments(page, page_size, status, country_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Server error: " + str(e))


@app.get("/payments/{payment_id}", tags=["Payments"])
def payment_detail_api(payment_id: int):
    """Full detail for one payment — eye icon view."""
    try:
        return get_payment_detail(payment_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Server error: " + str(e))

# """
# main.py
# ───────
# FastAPI entry point.
# Routes are grouped by domain — Auth and Subscriptions.
# Add new domains by importing their module and registering routes in the
# relevant section below. Never put business logic here.
# """

# from fastapi import FastAPI, HTTPException, Header, Query
# from typing import Optional

# from subscriptions import (
#     list_plans,
#     get_plan_stats,
#     list_plan_sellers,
#     get_subscription_detail,
# )


# app = FastAPI(
#     title="Marketplace Auth & Seller API",
#     description="Authentication, OTP Verification, Subscription Management",
#     version="2.0",
# )



# # ══════════════════════════════════════════════════════════════════════════════
# # Subscription Routes
# # ══════════════════════════════════════════════════════════════════════════════

# @app.get("/subscriptions/plans", tags=["Subscriptions"])
# def list_plans_api():
#     """
#     List all subscription plans.
#     Used to populate the Plan Name selector / cards.
#     """
#     try:
#         return list_plans()
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail="Server error: " + str(e))


# @app.get("/subscriptions/plans/{plan_id}/stats", tags=["Subscriptions"])
# def plan_stats_api(plan_id: int):
#     """
#     Summary stats for a plan: name, total subscribers,
#     new this month, and monthly revenue.
#     Drives the three header cards in the Figma.
#     """
#     try:
#         return get_plan_stats(plan_id)
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail="Server error: " + str(e))


# @app.get("/subscriptions/plans/{plan_id}/sellers", tags=["Subscriptions"])
# def plan_sellers_api(
#     plan_id: int,
#     page: int = Query(1, ge=1, description="Page number"),
#     page_size: int = Query(10, description="Rows per page: 5 | 10 | 20 | 50"),
# ):
#     """
#     Paginated list of sellers subscribed to a plan.
#     Returns seller name, business, start date, next billing,
#     and latest payment status (Paid / Pending / Failed).
#     """
#     try:
#         return list_plan_sellers(plan_id, page, page_size)
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail="Server error: " + str(e))


# @app.get("/subscriptions/{subscription_id}", tags=["Subscriptions"])
# def subscription_detail_api(subscription_id: int):
#     """
#     Full detail for one subscription — seller info, plan info,
#     and full payment history. Opened via the eye icon in the table.
#     """
#     try:
#         return get_subscription_detail(subscription_id)
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail="Server error: " + str(e))
