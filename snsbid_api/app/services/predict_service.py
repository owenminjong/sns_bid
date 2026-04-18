from sqlalchemy.orm import Session
from app.models.predict import BidPredict
from datetime import datetime

def calc_predict(req):
    from app.ai.predict import run_predict
    result = run_predict(
        bssamt=req.bssamt,
        Aamt=req.Aamt,
        realAmt=req.realAmt,
        sucsfbidLwltRate=req.sucsfbidLwltRate,
        bidNtceNm=req.bidNtceNm,
    )
    return result

def save_predict(db: Session, req, sfcode: int):
    record = BidPredict(
        bsn       = req.bsn,
        bidNtceNo = req.bidNtceNo,
        bidNtceNm = req.bidNtceNm,
        bssamt    = req.bssamt,
        Aamt      = req.Aamt,
        realAmt   = req.realAmt,
        preamt    = req.preamt,
        preRate   = req.preRate,
        preRate2  = round(req.preRate / 100, 4) if req.preRate else 0,
        urate     = req.urate,
        betc      = req.betc,
        sfcode    = sfcode,
        regdate   = datetime.now(),
    )
    db.add(record)
    db.commit()

def get_predict_list(db: Session, fdate: str, tdate: str, bidNtceNo: str,
                     bidNtceNm: str, page: int, page_size: int):

    query = db.query(BidPredict)

    if fdate:
        query = query.filter(BidPredict.regdate >= fdate)
    if tdate:
        query = query.filter(BidPredict.regdate <= tdate + " 23:59:59")
    if bidNtceNo:
        query = query.filter(BidPredict.bidNtceNo.like(f"%{bidNtceNo}%"))
    if bidNtceNm:
        query = query.filter(BidPredict.bidNtceNm.like(f"%{bidNtceNm}%"))

    total = query.count()
    items = query.order_by(BidPredict.psn.desc()) \
        .offset((page - 1) * page_size) \
        .limit(page_size).all()

    return {
        "data": [
            {
                "psn":        i.psn,
                "bsn":        i.bsn,
                "bidNtceNo":  i.bidNtceNo,
                "bidNtceNm":  i.bidNtceNm,
                "bssamt":     i.bssamt,
                "Aamt":       i.Aamt,
                "realAmt":    i.realAmt,
                "preamt":     i.preamt,
                "preRate":    float(i.preRate) if i.preRate else None,
                "confidence": float(i.confidence) if i.confidence else None,
                "model_used": i.model_used,
                "betc":       i.betc,
                "regdate":    str(i.regdate) if i.regdate else None,
            }
            for i in items
        ],
        "total":       total,
        "page":        page,
        "total_pages": -(-total // page_size),
    }