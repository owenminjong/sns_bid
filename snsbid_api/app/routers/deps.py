from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.auth_service import verify_token

bearer = HTTPBearer()

def get_current_staff(credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="인증이 필요합니다")
    return payload