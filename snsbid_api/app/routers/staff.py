from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.deps import get_current_staff
from app.models.staff import Staff

router = APIRouter()

@router.get("")
def staff_list(db: Session = Depends(get_db), _: dict = Depends(get_current_staff)):
    staffs = db.query(Staff).filter(Staff.isdel == 0).all()
    return {"status": "success", "data": [
        {
            "sfcode": s.sfcode,
            "sfname": s.sfname,
            "sfid":   s.sfid,
            "tel":    s.tel,
            "isuse":  s.isuse,
            "issvr":  s.issvr,
        } for s in staffs
    ]}