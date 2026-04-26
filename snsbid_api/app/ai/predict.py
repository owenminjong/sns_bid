"""
app/ai/predict.py
XGBoost 낙찰율 예측 모듈

모델 입력 피처:
    투찰률    - 사용자 입력 (%)
    예가범위  - 지방계약법=3, 국가계약법=2
    금액대    - 1:10억이하 / 2:10~30억 / 3:30~50억 / 4:50억초과  (파생)
    참여업체수 - 개찰 참여 업체 수
    개찰월    - 개찰일자에서 추출 (파생)
    대업종_enc - LabelEncoder 변환된 정수

예측 타겟: 낙찰율 (%)  →  낙찰금액 = 기초금액 × 낙찰율 / 100
"""

import joblib
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Optional

# ── 경로 설정 ─────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "models" / "latest.joblib"

# ── 금액대 구간 정의 (train.py pd.cut bins/labels와 반드시 동일) ───────────────
# pd.cut(right=True) 기본값 → (0, 10억] (10억, 30억] (30억, 50억] (50억, ∞)
AMT_BINS   = [0, 1_000_000_000, 3_000_000_000, 5_000_000_000, float("inf")]
AMT_LABELS = [1, 2, 3, 4]

# ── 모델 싱글톤 ────────────────────────────────────────────────────────────────
_bundle: Optional[dict] = None


def load_model() -> dict:
    """
    모델 번들을 로드하고 캐싱한다.
    반환 dict 키: model, features, label_encoder, cv_mae_pct, params 등
    """
    global _bundle
    if _bundle is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"모델 파일을 찾을 수 없습니다: {MODEL_PATH}")
        _bundle = joblib.load(MODEL_PATH)
    return _bundle


def _resolve_금액대(bssamt: int) -> int:
    """
    기초금액(bssamt)으로 금액대 구간 정수를 반환한다.
    pd.cut(right=True) 기본값과 일치하도록 <= 조건 사용.
    """
    for i, boundary in enumerate(AMT_BINS[1:]):
        if bssamt <= boundary:
            return AMT_LABELS[i]
    return AMT_LABELS[-1]


def _encode_대업종(label_encoder, 대업종: str) -> tuple[int, bool]:
    """
    LabelEncoder로 대업종명을 정수로 변환한다.
    미지 클래스(학습 시 없던 업종) → ValueError → '기타' 폴백

    Returns:
        (enc_value, fallback_used)
        fallback_used=True 이면 호출자가 warning을 생성해야 함
    """
    try:
        return int(label_encoder.transform([대업종])[0]), False
    except ValueError:
        try:
            return int(label_encoder.transform(["기타"])[0]), True
        except ValueError:
            # '기타'도 없는 극단적 상황 — 방어 코드
            return 0, True


def get_대업종_classes() -> list[str]:
    """
    LabelEncoder에 등록된 전체 업종 목록을 반환한다.
    GET /api/predict/daeupcong 엔드포인트에서 호출.
    """
    bundle = load_model()
    return list(bundle["label_encoder"].classes_)


def predict(
        투찰률: float,
        bssamt: int,
        참여업체수: int,
        대업종: str,
        예가범위: int,
        개찰일자: str,           # "YYYY-MM-DD" 또는 "YYYYMMDD"
) -> dict:
    """
    낙찰율 및 낙찰예상금액을 예측한다.

    Args:
        투찰률:     사용자가 입찰 시 쓰려는 투찰율 (%)  ex) 88.5
        bssamt:    기초금액 (원)                        ex) 500_000_000
        참여업체수: 개찰 참여 업체 수                   ex) 15
        대업종:    대업종명 문자열                       ex) "철콘"
        예가범위:  2(국가계약법) 또는 3(지방계약법)      ex) 2
        개찰일자:  개찰 예정일                           ex) "2026-04-30"

    Returns:
        {
            "predict_rate": float,   # 예측 낙찰율 (%)
            "predict_amt": int,      # 예측 낙찰금액 (원)
            "warning": str | None,   # 업종 폴백 시 경고 메시지, 정상이면 None
            "model_mae_pct": float,  # 모델 CV MAE (%)
            "model_mae_amt": int,    # 모델 CV MAE 금액 환산 (원)
            "range": {               # 예측 ± MAE 범위
                "min": int,
                "max": int,
            },
            "meta": {
                "금액대": int,
                "개찰월": int,
                "대업종_enc": int,
                "model_trained_at": str,
                "train_samples": int,
            }
        }

    Raises:
        FileNotFoundError: 모델 파일 없음
        ValueError: 입력값 범위 오류
    """
    # ── 입력 유효성 검사 ──────────────────────────────────────────────────────
    if not (50.0 <= 투찰률 <= 110.0):
        raise ValueError(f"투찰률은 50~110 사이여야 합니다. 입력값: {투찰률}")
    if bssamt <= 0:
        raise ValueError(f"기초금액은 0보다 커야 합니다. 입력값: {bssamt}")
    if 참여업체수 <= 0:
        raise ValueError(f"참여업체수는 0보다 커야 합니다. 입력값: {참여업체수}")
    if 예가범위 not in (2, 3):
        raise ValueError(f"예가범위는 2(국가계약법) 또는 3(지방계약법)이어야 합니다. 입력값: {예가범위}")

    # ── 개찰일자 파싱 ─────────────────────────────────────────────────────────
    개찰일자 = 개찰일자.replace("-", "").replace("/", "")
    try:
        dt = datetime.strptime(개찰일자, "%Y%m%d")
    except ValueError:
        raise ValueError(f"개찰일자 형식이 올바르지 않습니다: {개찰일자} (YYYY-MM-DD 또는 YYYYMMDD)")
    개찰월 = dt.month

    # ── 파생 변수 계산 ────────────────────────────────────────────────────────
    bundle = load_model()
    금액대 = _resolve_금액대(bssamt)
    대업종_enc, fallback_used = _encode_대업종(bundle["label_encoder"], 대업종)
    warning = (
        f"등록되지 않은 업종('{대업종}')이 입력되어 '기타'로 처리되었습니다."
        if fallback_used else None
    )

    # ── 입력 DataFrame 구성 (학습 피처 순서 고정) ─────────────────────────────
    features = bundle["features"]   # ['투찰률', '예가범위', '금액대', '참여업체수', '개찰월', '대업종_enc']
    row = {
        "투찰률": 투찰률,
        "예가범위": 예가범위,
        "금액대": 금액대,
        "참여업체수": 참여업체수,
        "개찰월": 개찰월,
        "대업종_enc": 대업종_enc,
    }
    X = pd.DataFrame([row], columns=features)

    # ── 예측 ─────────────────────────────────────────────────────────────────
    model = bundle["model"]
    predict_rate = float(model.predict(X)[0])

    # ── 결과 계산 ─────────────────────────────────────────────────────────────
    predict_amt = int(bssamt * predict_rate / 100)
    mae_pct = bundle["cv_mae_pct"]
    mae_amt = int(bssamt * mae_pct / 100)

    return {
        "predict_rate": round(predict_rate, 3),
        "predict_amt": predict_amt,
        "warning": warning,
        "model_mae_pct": round(mae_pct, 4),
        "model_mae_amt": mae_amt,
        "range": {
            "min": int(bssamt * (predict_rate - mae_pct) / 100),
            "max": int(bssamt * (predict_rate + mae_pct) / 100),
        },
        "meta": {
            "금액대": 금액대,
            "개찰월": 개찰월,
            "대업종_enc": 대업종_enc,
            "model_trained_at": bundle.get("trained_at", ""),
            "train_samples": bundle.get("train_samples", 0),
        },
    }