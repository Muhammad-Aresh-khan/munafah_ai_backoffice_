import uuid
import bcrypt
from fastapi import HTTPException
from db_connector import conn, cursor
from email_utils import generate_otp, send_otp_email, verify_otp
from jwt_utils import create_jwt, blacklist_token, extract_token


# ── 1. Signup ─────────────────────────────────────────────────────────────────
def signup(name: str, email: str, password: str):
    # Check duplicate email
    cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
    if cursor.fetchone():
        raise HTTPException(status_code=409, detail="Email already registered")

    user_uuid    = str(uuid.uuid4())
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    try:
        cursor.execute("""
            INSERT INTO users (uuid, name, email, passwordHash, role, status)
            VALUES (%s, %s, %s, %s, 'seller', 'inactive')
        """, (user_uuid, name, email, password_hash))

        # Create linked sellers row
        cursor.execute("SELECT id FROM users WHERE uuid=%s", (user_uuid,))
        user_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO sellers (userId, isEmailVerified, profileComplete)
            VALUES (%s, FALSE, FALSE)
        """, (user_id,))

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail="Database error: " + str(e))

    # Generate & send OTP (after commit so user exists)
    try:
        otp = generate_otp(email)
        send_otp_email(email, otp, purpose="verification")
    except Exception as e:
        # User created but email failed — still return success, frontend can resend
        return {
            "success": True,
            "message": "Account created. OTP email failed — please request a new OTP.",
            "warning": str(e),
        }

    return {
        "success": True,
        "message": "Account created. Please verify your email with the OTP sent.",
    }


# ── 2. OTP Verification ───────────────────────────────────────────────────────
def verify_email(email: str, otp: str):
    if not verify_otp(email, otp):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    try:
        # Activate user
        cursor.execute("""
            UPDATE users SET status='active', updatedAt=NOW()
            WHERE email=%s
        """, (email,))

        # Mark seller email verified
        cursor.execute("""
            UPDATE sellers SET isEmailVerified=TRUE, updatedAt=NOW()
            FROM users
            WHERE sellers.userId = users.id
            AND users.email = %s
        """, (email,))

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail="Database error: " + str(e))

    return {"success": True, "message": "Email verified. You can now log in."}


# ── 3. Login ──────────────────────────────────────────────────────────────────
def login(email: str, password: str):
    cursor.execute("""
        SELECT id, uuid, passwordHash, status, role
        FROM users WHERE email=%s
    """, (email,))
    row = cursor.fetchone()

    if not row:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user_id, user_uuid, password_hash, status, role = row

    if not bcrypt.checkpw(password.encode(), password_hash.encode()):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if status != "active":
        raise HTTPException(status_code=403, detail="Account not active. Please verify your email.")

    # Check seller subscription expiry and deactivate if expired
    _deactivate_expired_subscriptions(user_id)

    token = create_jwt(user_uuid, role)

    return {
        "success": True,
        "message": "Login successful",
        "token": token,
        "role": role,
    }


# ── 4. Logout ─────────────────────────────────────────────────────────────────
def logout(authorization: str):
    token = extract_token(authorization)
    blacklist_token(token)
    return {"success": True, "message": "Logged out successfully"}


# ── 5a. Request Password Reset ────────────────────────────────────────────────
def request_password_reset(email: str):
    cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
    if not cursor.fetchone():
        # Don't reveal whether email exists
        return {"success": True, "message": "If that email exists, an OTP has been sent."}

    try:
        otp = generate_otp(email)
        send_otp_email(email, otp, purpose="password_reset")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to send OTP: " + str(e))

    return {"success": True, "message": "Password reset OTP sent to your email."}


# ── 5b. Reset Password ────────────────────────────────────────────────────────
def reset_password(email: str, otp: str, new_password: str):
    if not verify_otp(email, otp):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    new_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()

    try:
        cursor.execute("""
            UPDATE users SET passwordHash=%s, updatedAt=NOW()
            WHERE email=%s
        """, (new_hash, email))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail="Database error: " + str(e))

    return {"success": True, "message": "Password reset successfully. You can now log in."}


# ── Helper: deactivate expired subscriptions ──────────────────────────────────
def _deactivate_expired_subscriptions(user_id: int):
    try:
        cursor.execute("""
            UPDATE sellerSubscriptions
            SET status='expired', updatedAt=NOW()
            FROM sellers
            WHERE sellerSubscriptions.sellerId = sellers.id
            AND sellers.userId = %s
            AND sellerSubscriptions.status = 'active'
            AND sellerSubscriptions.endDate < NOW()
        """, (user_id,))
        conn.commit()
    except Exception:
        conn.rollback()  # Non-fatal — don't block login
