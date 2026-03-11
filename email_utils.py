from dotenv import load_dotenv
load_dotenv()
import random
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from db_connector import conn, cursor

# ── Config ────────────────────────────────────────────────────────────────────
SMTP_HOST     = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT     = int(os.getenv("SMTP_PORT", 587))
SMTP_USER     = os.getenv("SMTP_USER", "your_email@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "your_app_password")   # Gmail App Password
OTP_EXPIRE_MINUTES = int(os.getenv("OTP_EXPIRE_MINUTES", 10))


# ── Generate & store OTP ──────────────────────────────────────────────────────
def generate_otp(email: str) -> str:
    otp = str(random.randint(100000, 999999))
    expires_at = datetime.utcnow() + timedelta(minutes=OTP_EXPIRE_MINUTES)

    # Upsert: one active OTP per email
    cursor.execute("""
        INSERT INTO otpStore (email, otp, expiresAt, used)
        VALUES (%s, %s, %s, FALSE)
        ON CONFLICT (email)
        DO UPDATE SET otp=%s, expiresAt=%s, used=FALSE
    """, (email, otp, expires_at, otp, expires_at))
    conn.commit()

    return otp


# ── Verify OTP ────────────────────────────────────────────────────────────────
def verify_otp(email: str, otp: str) -> bool:
    cursor.execute("""
        SELECT otp, expiresAt, used
        FROM otpStore
        WHERE email = %s
    """, (email,))
    row = cursor.fetchone()

    if not row:
        return False

    stored_otp, expires_at, used = row

    if used:
        return False
    if datetime.utcnow() > expires_at:
        return False
    if stored_otp != otp:
        return False

    # Mark as used
    cursor.execute("""
        UPDATE otpStore SET used=TRUE WHERE email=%s
    """, (email,))
    conn.commit()

    return True


# ── Send OTP email ────────────────────────────────────────────────────────────
def send_otp_email(recipient_email: str, otp: str, purpose: str = "verification") -> None:
    subject_map = {
        "verification": "Your Email Verification Code",
        "password_reset": "Your Password Reset Code",
    }
    subject = subject_map.get(purpose, "Your OTP Code")

    body = f"""
    <html><body>
    <h2>Your OTP Code</h2>
    <p>Use the code below to complete your {purpose.replace('_', ' ')}:</p>
    <h1 style="letter-spacing:6px;">{otp}</h1>
    <p>This code expires in <strong>{OTP_EXPIRE_MINUTES} minutes</strong>.</p>
    <p>If you did not request this, please ignore this email.</p>
    </body></html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = SMTP_USER
    msg["To"]      = recipient_email
    msg.attach(MIMEText(body, "html"))

    # with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:


    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
        server.ehlo()
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, recipient_email, msg.as_string())
