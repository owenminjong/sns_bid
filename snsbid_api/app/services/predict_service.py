"""
app/services/predict_service.py
예측 관련 비즈니스 로직
"""

from typing import Optional
from sqlalchemy import text
from fastapi import HTTPException

from app.ai.predict import predict, get_대업종_classes


# ────────────────────────────────────────────
# 1. 업종 목록
# ────────────────────────────────────────────
def get_daeupcong() -> dict:
    try:
        classes = get_대업종_classes()
        return {
            "status": "success",
            "data":   classes,
            "total":  len(classes),
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))


# ────────────────────────────────────────────
# 2. 예측 실행
# ────────────────────────────────────────────
def run_predict(
        투찰률: float,
        bssamt: int,
        참여업체수: int,
        대업종: str,
        예가범위: int,
        개찰일자: str,
) -> dict:
    try:
        result = predict(
            투찰률=투찰률,
            bssamt=bssamt,
            참여업체수=참여업체수,
            대업종=대업종,
            예가범위=예가범위,
            개찰일자=개찰일자,
        )
        return {"status": "success", "data": result}

    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


# ────────────────────────────────────────────
# 3. 예측 저장
# ────────────────────────────────────────────
def save_predict(
        db,
        sfcode: int,        # router에서 current_staff["sfcode"] 로 전달
        bbscode: str,       # betc 컬럼에 저장 — 공고 역추적용 (betc 용도 불명으로 임시 활용)
        bidNtceNo: str,
        bidNtceNm: str,
        bssamt: int,
        Aamt: int,
        urate: float,
        preamt: int,
        preRate: float,
        preRate2: float,
) -> dict:
    try:
        sql = text("""
            INSERT INTO bid_predict (
                bsn, bidNtceNo, bidNtceNm,
                bssamt, Aamt, realAmt,
                urate, preamt, preRate, preRate2,
                confidence, model_used, betc, sfcode, regdate
            ) VALUES (
                NULL, :bidNtceNo, :bidNtceNm,
                :bssamt, :Aamt, 0,
                :urate, :preamt, :preRate, :preRate2,
                NULL, 'xgboost', :betc, :sfcode, NOW()
            )
        """)

        result = db.execute(sql, {
            "bidNtceNo": bidNtceNo,
            "bidNtceNm": bidNtceNm,
            "bssamt":    bssamt,
            "Aamt":      Aamt,
            "urate":     urate,
            "preamt":    preamt,
            "preRate":   preRate,
            "preRate2":  preRate2,
            "betc":      bbscode,   # bbscode → betc 컬럼에 저장
            "sfcode":    sfcode,
        })
        db.commit()

        return {
            "status": "success",
            "data":   {"psn": result.lastrowid},
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"저장 실패: {str(e)}")


# ────────────────────────────────────────────
# 4. 예측 목록 조회
# ────────────────────────────────────────────
def get_predict_list(
        db,
        fdate: Optional[str] = None,
        tdate: Optional[str] = None,
        bidNtceNo: Optional[str] = None,
        bidNtceNm: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
) -> dict:
    try:
        # where_clause 조각은 전부 하드코딩 문자열 + SQLAlchemy 바인딩 파라미터만 사용
        # 사용자 입력이 직접 문자열에 삽입되지 않으므로 SQL injection 위험 없음
        where = ["1=1"]
        params: dict = {}

        if fdate:
            where.append("DATE(regdate) >= :fdate")
            params["fdate"] = fdate
        if tdate:
            where.append("DATE(regdate) <= :tdate")
            params["tdate"] = tdate
        if bidNtceNo:
            where.append("bidNtceNo LIKE :bidNtceNo")
            params["bidNtceNo"] = f"%{bidNtceNo}%"
        if bidNtceNm:
            where.append("bidNtceNm LIKE :bidNtceNm")
            params["bidNtceNm"] = f"%{bidNtceNm}%"

        where_clause = " AND ".join(where)
        offset = (page - 1) * page_size

        # count용 params 분리 — list용 limit/offset 키가 섞이면
        # SQLAlchemy가 "unexpected bind parameter" 에러를 낼 수 있음
        count_params = {k: v for k, v in params.items()}
        count_sql = text(f"SELECT COUNT(*) FROM bid_predict WHERE {where_clause}")
        total = db.execute(count_sql, count_params).scalar()

        params["limit"]  = page_size
        params["offset"] = offset

        list_sql = text(f"""
            SELECT
                psn, bsn, bidNtceNo, bidNtceNm,
                bssamt, Aamt, realAmt, urate,
                preamt, preRate, preRate2,
                confidence, model_used, sfcode,
                DATE_FORMAT(regdate, '%Y-%m-%d %H:%i') AS regdate
            FROM bid_predict
            WHERE {where_clause}
            ORDER BY psn DESC
            LIMIT :limit OFFSET :offset
        """)

        rows = db.execute(list_sql, params).mappings().all()

        return {
            "status":      "success",
            "data":        [dict(r) for r in rows],
            "total":       total,
            "page":        page,
            "total_pages": -(-total // page_size),  # ceiling division
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"목록 조회 실패: {str(e)}")