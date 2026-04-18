from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.auth_service import login_user
from pydantic import BaseModel

router = APIRouter()

class LoginRequest(BaseModel):
    sfid: str
    sfpw: str

@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    token = login_user(db, req.sfid, req.sfpw)
    if not token:
        raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 틀렸습니다")
    return {"status": "success", "data": {"access_token": token, "token_type": "bearer"}}