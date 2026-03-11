

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, EmailStr, constr
from typing import Literal, Optional

from auth import signup, verify_email, login, logout, request_password_reset, reset_password


app = FastAPI(
    title="Marketplace Auth & Seller API",
    description="Authentication, OTP Verification",
    version="2.0",
)

class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: constr(min_length=8)

class OTPVerifyRequest(BaseModel):
    email: EmailStr
    otp: constr(min_length=6, max_length=6)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    email: EmailStr
    otp: constr(min_length=6, max_length=6)
    new_password: constr(min_length=8)

# ══════════════════════════════════════════════════════════════════════════════
# Auth Routes
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/auth/signup", tags=["Auth"])
def signup_api(body: SignupRequest):
    """Register a new seller account and send OTP."""
    try:
        return signup(body.name, body.email, body.password)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Server error: " + str(e))


@app.post("/auth/verify", tags=["Auth"])
def verify_api(body: OTPVerifyRequest):
    """Verify OTP to activate account."""
    try:
        return verify_email(body.email, body.otp)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Server error: " + str(e))


@app.post("/auth/login", tags=["Auth"])
def login_api(body: LoginRequest):
    """Login with email + password. Returns JWT."""
    try:
        return login(body.email, body.password)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Server error: " + str(e))


@app.post("/auth/logout", tags=["Auth"])
def logout_api(authorization: Optional[str] = Header(None)):
    """Invalidate JWT token (logout)."""
    try:
        return logout(authorization)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Server error: " + str(e))


@app.post("/auth/password-reset/request", tags=["Auth"])
def password_reset_request_api(body: PasswordResetRequest):
    """Send OTP to email for password reset."""
    try:
        return request_password_reset(body.email)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Server error: " + str(e))


@app.post("/auth/password-reset/confirm", tags=["Auth"])
def password_reset_confirm_api(body: PasswordResetConfirm):
    """Verify OTP and set new password."""
    try:
        return reset_password(body.email, body.otp, body.new_password)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Server error: " + str(e))

