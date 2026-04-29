from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.bid_service import get_bid_list
from app.deps import get_current_staff

router = APIRouter()


@router.get("")
def bid_list(
        fdate:   str = Query(default=""),
        tdate:   str = Query(default=""),
        공고번호: str = Query(default=""),
        공고명:   str = Query(default=""),
        isopen:  int = Query(default=-1),
        famt:    int = Query(default=0),
        tamt:    int = Query(default=0),
        page:     int = Query(default=1),
        page_size: int = Query(default=20),
        db: Session = Depends(get_db),
        _: dict = Depends(get_current_staff)
):
    result = get_bid_list(db, fdate, tdate, 공고번호, 공고명, isopen, famt, tamt, page, page_size)
    return {"status": "success", **result}