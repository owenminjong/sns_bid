"""
app/routers/predict.py
예측 관련 API 라우터
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from app.database import get_db
from app.deps import get_current_staff
from app.services import predict_service

router = APIRouter(tags=["predict"])  # prefix 제거 — main.py에서 "/api/predict" 관리


# ── Pydantic 모델 ─────────────────────────────────────────────────────────────
class PredictRequest(BaseModel):
    투찰률:    float
    bssamt:   int
    참여업체수: int
    대업종:   str
    예가범위:  str
    개찰일자:  str          # "YYYY-MM-DD" 또는 "YYYYMMDD"


class SavePredictRequest(BaseModel):
    bbscode:   str       # betc에 저장 — 공고 역추적용
    bidNtceNo: str
    bidNtceNm: str
    bssamt:    int
    Aamt:      int
    urate:     float
    preamt:    int
    preRate:   float
    preRate2:  float
    # bsn 제거 — NULL 저장
    # realAmt 제거 — 0 고정
    # sfcode 제거 — JWT에서 추출


# ── 엔드포인트 ────────────────────────────────────────────────────────────────
@router.get("/daeupcong")
def get_daeupcong():
    """
    업종 목록 반환
    [인증 예외] 05_개발_규칙 "모든 API 인증 필수" 원칙의 의도적 예외.
    드롭다운 초기화용 정적 참조 데이터로 보안 민감 정보 아님.
    """
    return predict_service.get_daeupcong()


@router.post("")
def run_predict(
        req: PredictRequest,
        current_staff=Depends(get_current_staff),
):
    """낙찰율 예측 실행"""
    return predict_service.run_predict(
        투찰률=req.투찰률,
        bssamt=req.bssamt,
        참여업체수=req.참여업체수,
        대업종=req.대업종,
        예가범위=req.예가범위,
        개찰일자=req.개찰일자,
    )


@router.post("/save")
def save_predict(
        req: SavePredictRequest,
        current_staff=Depends(get_current_staff),
        db: Session = Depends(get_db),
):
    """예측 결과 저장"""
    return predict_service.save_predict(
        db=db,
        sfcode=current_staff["sfcode"],   # JWT에서 추출
        bbscode=req.bbscode,
        bidNtceNo=req.bidNtceNo,
        bidNtceNm=req.bidNtceNm,
        bssamt=req.bssamt,
        Aamt=req.Aamt,
        urate=req.urate,
        preamt=req.preamt,
        preRate=req.preRate,
        preRate2=req.preRate2,
    )


@router.get("/list")
def get_predict_list(
        current_staff=Depends(get_current_staff),
        db: Session = Depends(get_db),
        fdate:     Optional[str] = Query(None),
        tdate:     Optional[str] = Query(None),
        bidNtceNo: Optional[str] = Query(None),
        bidNtceNm: Optional[str] = Query(None),
        page:      int           = Query(1,  ge=1),
        page_size: int           = Query(20, ge=1, le=100),
):
    """예측 결과 목록 조회"""
    return predict_service.get_predict_list(
        db=db,
        fdate=fdate,
        tdate=tdate,
        bidNtceNo=bidNtceNo,
        bidNtceNm=bidNtceNm,
        page=page,
        page_size=page_size,
    )