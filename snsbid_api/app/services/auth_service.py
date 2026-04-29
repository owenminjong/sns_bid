import os
import bcrypt
from datetime import datetime, timedelta
from jose import jwt
from sqlalchemy.orm import Session
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "changeme")
ALGORITHM  = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440))


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def create_access_token(data: dict) -> str:
    payload = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload.update({"exp": expire})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def login_user(db: Session, sfid: str, sfpw: str) -> str | None:
    from app.models.staff import Staff
    staff = db.query(Staff).filter(Staff.sfid == sfid).first()
    if not staff:
        return None
    if not verify_password(sfpw, staff.sfpw):
        return None
    token = create_access_token({
        "sfcode": staff.sfcode,
        "sfid":   staff.sfid,
        "sfname": staff.sfname,
        "issvr":  staff.issvr,
    })
    return token
