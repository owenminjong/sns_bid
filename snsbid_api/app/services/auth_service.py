from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.models.staff import Staff
from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM  = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_token(data: dict) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    data.update({"exp": expire})
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

def login_user(db: Session, sfid: str, sfpw: str):
    staff = db.query(Staff).filter(
        Staff.sfid == sfid,
        Staff.isuse == 1,
        Staff.isdel == 0
    ).first()

    if not staff:
        return None
    if not verify_password(sfpw, staff.sfpw):
        return None

    token = create_token({
        "sfcode": staff.sfcode,
        "sfid":   staff.sfid,
        "sfname": staff.sfname,
        "issvr":  staff.issvr,
    })
    return token