"""
숭늉샘B1D - 최종 모델 학습 및 저장
타겟=낙찰율, 피처=비율 기반 / no_a 단일 모델 (XGBoost)
파라미터: params/xgb_no_a_params.json 우선 로드, 없으면 기본값
LabelEncoder: params/le_daeupcong.joblib 로드 (train.py에서 생성)
"""

import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path
from sqlalchemy import text
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import cross_val_score
from xgboost import XGBRegressor

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database import engine

MODEL_DIR  = Path(__file__).parent / "models"
PARAMS_DIR = Path(__file__).parent / "params"
LE_PATH    = PARAMS_DIR / "le_daeupcong.joblib"
MODEL_DIR.mkdir(exist_ok=True)
PARAMS_DIR.mkdir(exist_ok=True)

FEATURES = ["투찰률", "예가범위", "금액대", "참여업체수", "개찰월", "대업종_enc"]
TARGET   = "낙찰율"

# ────────────────────────────────────────────
# 파라미터 로드
# ────────────────────────────────────────────
_params_path = PARAMS_DIR / "xgb_no_a_params.json"

if _params_path.exists():
    with open(_params_path) as f:
        PARAMS = json.load(f)
    print(f"✅ 파라미터 로드: {_params_path}")
    print(json.dumps(PARAMS, indent=2))
else:
    print("⚠️  params.json 없음 → 기본값 사용 (train.py 먼저 실행 권장)")
    PARAMS = {
        "n_estimators":     500,
        "learning_rate":    0.05,
        "max_depth":        6,
        "subsample":        0.8,
        "colsample_bytree": 0.8,
        "random_state":     42,
        "n_jobs":           -1,
        "verbosity":        0,
    }


# ────────────────────────────────────────────
# 1. 데이터 로드
# ────────────────────────────────────────────
def load_data():
    query = text("""
        SELECT
            기초금액, 투찰률, 대업종, 참여업체수, 개찰일,
            예가1,  예가2,  예가3,  예가4,  예가5,
            예가6,  예가7,  예가8,  예가9,  예가10,
            예가11, 예가12, 예가13, 예가14, 예가15,
            낙찰금액
        FROM igunsul_nbid
        WHERE 기초금액 > 0
          AND 낙찰금액 > 0
          AND 낙찰금액 / 기초금액 * 100 BETWEEN 85 AND 91
          AND 예가1 IS NOT NULL
          AND 참여업체수 <= 10000
    """)

    with engine.connect() as conn:
        df = pd.read_sql(query, conn)

    print(f"[데이터 로드] {len(df):,}건")
    return df


# ────────────────────────────────────────────
# 2. LabelEncoder 로드
# ────────────────────────────────────────────
def load_le(df):
    if not LE_PATH.exists():
        raise FileNotFoundError(
            f"le_daeupcong.joblib 없음: {LE_PATH}\n"
            f"→ train.py 먼저 실행하세요."
        )

    le = joblib.load(LE_PATH)

    new_categories = set(df["대업종"].unique()) - set(le.classes_)
    if new_categories:
        print(f"⚠️  새 업종 감지: {new_categories}")
        print(f"   → 모델 전체 재학습 필요 시 le.joblib 삭제 후 train.py 재실행")

    print(f"✅ LabelEncoder 로드: {len(le.classes_)}개 업종")
    return le


# ────────────────────────────────────────────
# 3. 피처 생성
# ────────────────────────────────────────────
def add_features(df, le):
    예가cols = [f"예가{i}" for i in range(1, 16)]
    df["예가범위"] = (df[예가cols].max(axis=1) - df[예가cols].min(axis=1)) / df["기초금액"] * 100
    df = df.drop(columns=예가cols)

    df["금액대"] = pd.cut(
        df["기초금액"],
        bins=[0, 1e9, 3e9, 5e9, float("inf")],
        labels=[1, 2, 3, 4]
    )
    df["금액대"] = pd.to_numeric(df["금액대"], errors="coerce").fillna(1).astype(int)

    df["개찰월"] = pd.to_datetime(df["개찰일"]).dt.month

    df["대업종_enc"] = le.transform(df["대업종"])

    df["낙찰율"] = df["낙찰금액"] / df["기초금액"] * 100

    return df


# ────────────────────────────────────────────
# 4. CV 평가 → 전체 학습 → 저장
# ────────────────────────────────────────────
def train_and_save(df, le):
    X = df[FEATURES].fillna(0)
    y = df[TARGET]

    print(f"\n[XGBoost] CV 평가 시작 (5-Fold)")
    print(f"  데이터: {len(X):,}건 / 피처: {FEATURES}")
    print(f"  파라미터: {PARAMS}")

    cv_scores = cross_val_score(
        XGBRegressor(**PARAMS), X, y,
        cv=5,
        scoring="neg_mean_absolute_error",
        n_jobs=-1,
    )
    cv_mae_pct = float(-cv_scores.mean())
    cv_mae_5억 = int(cv_mae_pct / 100 * 5e8 / 1e4)

    print(f"\n  CV MAE: {cv_mae_pct:.4f}%  (5억 기준 {cv_mae_5억}만원)")

    # 전체 데이터로 최종 학습
    print(f"\n[XGBoost] 전체 데이터 최종 학습 중...")
    model = XGBRegressor(**PARAMS)
    model.fit(X, y)

    importances = pd.Series(model.feature_importances_, index=FEATURES)
    print(f"\n  피처 중요도:")
    for feat, imp in importances.sort_values(ascending=False).items():
        print(f"    {feat}: {imp:.4f}")

    # 저장
    today    = datetime.now().strftime("%Y%m%d")
    filename = f"xgboost_no_a_{today}.joblib"
    filepath = MODEL_DIR / filename

    joblib.dump({
        "model":         model,
        "features":      FEATURES,
        "algo":          "xgboost",
        "model_type":    "no_a",
        "target":        TARGET,
        "trained_at":    datetime.now().isoformat(),
        "train_samples": len(X),
        "label_encoder": le,
        "cv_mae_pct":    cv_mae_pct,
        "cv_mae_5억":    cv_mae_5억,
        "params":        PARAMS,
    }, filepath)

    # latest.joblib 갱신
    latest_path = MODEL_DIR / "latest.joblib"
    if latest_path.exists() or latest_path.is_symlink():
        latest_path.unlink()
    latest_path.symlink_to(filename)

    print(f"\n  💾 저장 완료: {filepath}")
    print(f"  🔗 latest.joblib → {filename}")
    print(f"  CV MAE: {cv_mae_pct:.4f}% / 5억 기준 {cv_mae_5억}만원")
    return filepath


# ────────────────────────────────────────────
# 5. 메인
# ────────────────────────────────────────────
def main():
    print("\n" + "="*60)
    print("  숭늉샘B1D - 최종 모델 학습 및 저장 / no_a 단일")
    print("="*60)

    df   = load_data()
    le   = load_le(df)
    df   = add_features(df, le)
    path = train_and_save(df, le)

    print("\n" + "="*60)
    print("  ✅ 완료")
    print("="*60)
    print(f"  저장 경로: {path}")
    print(f"\n  ▶ 다음: predict.py 개발")
    print()


if __name__ == "__main__":
    main()