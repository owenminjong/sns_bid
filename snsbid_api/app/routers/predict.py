from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.predict_service import calc_predict, save_predict, get_predict_list
from app.routers.deps import get_current_staff
from pydantic import BaseModel

router = APIRouter()

class PredictRequest(BaseModel):
    bsn:              int
    bssamt:           int
    Aamt:             int
    realAmt:          int
    sucsfbidLwltRate: float = 0
    bidNtceNo:        str
    bidNtceNm:        str

class SaveRequest(BaseModel):
    bsn:       int
    bidNtceNo: str
    bidNtceNm: str
    bssamt:    int
    Aamt:      int
    realAmt:   int
    preamt:    int
    preRate:   float
    urate:     float = 0
    betc:      str = ""

@router.post("")
def predict(req: PredictRequest, db: Session = Depends(get_db), staff: dict = Depends(get_current_staff)):
    result = calc_predict(req)
    return {"status": "success", "data": result}

@router.post("/save")
def predict_save(req: SaveRequest, db: Session = Depends(get_db), staff: dict = Depends(get_current_staff)):
    save_predict(db, req, staff["sfcode"])
    return {"status": "success"}

@router.get("/list")
def predict_list(
        fdate:     str = Query(default=""),
        tdate:     str = Query(default=""),
        bidNtceNo: str = Query(default=""),
        bidNtceNm: str = Query(default=""),
        page:      int = Query(default=1),
        page_size: int = Query(default=20),
        db: Session = Depends(get_db),
        _: dict = Depends(get_current_staff)
):
    result = get_predict_list(db, fdate, tdate, bidNtceNo, bidNtceNm, page, page_size)
    return {"status": "success", **result}