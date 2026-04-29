"""
숭늉샘B1D - AI 모델 학습
타겟=낙찰율, 피처=비율 기반
XGBoost / LightGBM / RandomForest 5-Fold CV 비교 + XGBoost 튜닝
튜닝 결과 → params/xgb_no_a_params.json 자동 저장
튜닝이 기본값보다 나쁘면 기본값 자동 저장
"""

import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from sqlalchemy import text
from sklearn.base import clone
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database import engine

FEATURES = ["투찰률", "예가범위", "금액대", "참여업체수", "개찰월", "대업종_enc", "log_기초금액"]
TARGET   = "낙찰율"
LE_PATH  = Path(__file__).parent / "params" / "le_daeupcong.joblib"

DEFAULT_PARAMS = {
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

    df["대업종"] = df["대업종"].fillna("기타").replace("", "기타")

    print(f"[데이터 로드] {len(df):,}건")
    return df


# ────────────────────────────────────────────
# 2. LabelEncoder 로드 or 최초 생성
# ────────────────────────────────────────────
def load_or_fit_le(df):
    LE_PATH.parent.mkdir(exist_ok=True)

    if LE_PATH.exists():
        le = joblib.load(LE_PATH)
        new_categories = set(df["대업종"].unique()) - set(le.classes_)
        if new_categories:
            raise ValueError(
                f"새 업종 감지: {new_categories}\n"
                f"→ le_daeupcong.joblib 삭제 후 train.py 재실행하세요."
            )
        print(f"✅ LabelEncoder 로드: {LE_PATH}  ({len(le.classes_)}개 업종)")
    else:
        print(f"[LabelEncoder] 최초 생성 → {LE_PATH}")
        le = LabelEncoder()
        le.fit(df["대업종"])
        joblib.dump(le, LE_PATH)
        print(f"✅ 저장 완료: {len(le.classes_)}개 업종")

    return le


# ────────────────────────────────────────────
# 3. 피처 생성
# ────────────────────────────────────────────
def add_features(df, le):
    예가cols = [f"예가{i}" for i in range(1, 16)]

    # 예가범위: 실제 분산값을 2 or 3으로 분류 (예측 입력과 동일한 스케일)
    df["예가범위_raw"] = (df[예가cols].max(axis=1) - df[예가cols].min(axis=1)) / df["기초금액"] * 100
    df["예가범위"] = df["예가범위_raw"].apply(lambda x: 3 if x > 2.5 else 2)
    df = df.drop(columns=예가cols + ["예가범위_raw"])

    df["금액대"] = pd.cut(
        df["기초금액"],
        bins=[0, 1e9, 3e9, 5e9, float("inf")],
        labels=[1, 2, 3, 4]
    )
    df["금액대"] = pd.to_numeric(df["금액대"], errors="coerce").fillna(1).astype(int)

    df["개찰월"] = pd.to_datetime(df["개찰일"]).dt.month
    df["대업종_enc"] = le.transform(df["대업종"])
    df["낙찰율"] = df["낙찰금액"] / df["기초금액"] * 100
    df["log_기초금액"] = np.log1p(df["기초금액"])

    # 시계열 정렬 (TimeSeriesSplit 전제조건)
    df = df.sort_values("개찰일").reset_index(drop=True)

    print(f"[피처 생성] 낙찰율: {df['낙찰율'].min():.3f} ~ {df['낙찰율'].max():.3f} / 평균: {df['낙찰율'].mean():.3f}")
    print(f"[피처 생성] 예가범위 분포:\n{df['예가범위'].value_counts().sort_index().to_string()}")
    print(f"[피처 생성] 금액대:\n{df['금액대'].value_counts().sort_index().to_string()}")
    print(f"[피처 생성] 개찰일 정렬: {df['개찰일'].min()} ~ {df['개찰일'].max()}")

    return df


def prepare_xy(df):
    X = df[FEATURES].fillna(0)
    y = df[TARGET]
    return X, y


# ────────────────────────────────────────────
# 4. 모델 정의
# ────────────────────────────────────────────
def get_models():
    from xgboost import XGBRegressor
    from lightgbm import LGBMRegressor

    return {
        "xgboost": XGBRegressor(
            n_estimators=500,
            learning_rate=0.05,
            max_depth=6,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=1,
            verbosity=0,
        ),
        "lightgbm": LGBMRegressor(
            n_estimators=500,
            learning_rate=0.05,
            max_depth=6,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=1,
            verbose=-1,
        ),
        "randomforest": RandomForestRegressor(
            n_estimators=500,
            min_samples_leaf=3,
            min_samples_split=10,
            random_state=42,
            n_jobs=1,
        ),
    }


# ────────────────────────────────────────────
# 5. 5-Fold CV 비교
# ────────────────────────────────────────────
def run_cv(X, y):
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.metrics import mean_absolute_error, mean_squared_error

    tscv   = TimeSeriesSplit(n_splits=5)
    models = get_models()

    print(f"\n{'='*60}")
    print(f"  TimeSeriesSplit 5-Fold CV 비교")
    print(f"  전체: {len(X):,}건  (개찰일 기준 정렬)")
    print(f"{'='*60}")

    cv_results = {}

    for name, model in models.items():
        mae_list  = []
        rmse_list = []

        print(f"\n  ▶ {name}", end=" ", flush=True)

        for fold, (train_idx, val_idx) in enumerate(tscv.split(X), 1):
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]

            fold_model = clone(model)
            fold_model.fit(X_train, y_train)
            y_pred = fold_model.predict(X_val)

            mae_list.append(mean_absolute_error(y_val, y_pred))
            rmse_list.append(np.sqrt(mean_squared_error(y_val, y_pred)))
            print(f".", end="", flush=True)

        mae_mean  = np.mean(mae_list)
        rmse_mean = np.mean(rmse_list)
        mae_원    = mae_mean / 100 * 5e8

        print(f" 완료")
        print(f"     MAE  평균: {mae_mean:.4f}%  (5억 기준 {mae_원/1e4:.0f}만원)")
        print(f"     RMSE 평균: {rmse_mean:.4f}%")

        cv_results[name] = {"mae": mae_mean, "rmse": rmse_mean}

    print(f"\n  {'─'*40}")
    print(f"  MAE 기준 순위")
    print(f"  {'─'*40}")
    for rank, (name, res) in enumerate(sorted(cv_results.items(), key=lambda x: x[1]["mae"]), 1):
        mae_원 = res["mae"] / 100 * 5e8
        print(f"  {rank}위 {name}: MAE {res['mae']:.4f}% ({mae_원/1e4:.0f}만원) / RMSE {res['rmse']:.4f}%")

    return cv_results


# ────────────────────────────────────────────
# 6. XGBoost 튜닝
# ────────────────────────────────────────────
def tune_xgboost(X, y):
    from sklearn.model_selection import TimeSeriesSplit, RandomizedSearchCV
    from xgboost import XGBRegressor

    print(f"\n{'='*60}")
    print(f"  [2단계] XGBoost 튜닝")
    print(f"  전체: {len(X):,}건 / n_iter=50 / TimeSeriesSplit 5-Fold")
    print(f"{'='*60}")

    param_dist = {
        "n_estimators":     [300, 500, 800, 1000],
        "learning_rate":    [0.01, 0.03, 0.05, 0.1],
        "max_depth":        [4, 5, 6, 7, 8],
        "subsample":        [0.7, 0.8, 0.9, 1.0],
        "colsample_bytree": [0.6, 0.7, 0.8, 0.9, 1.0],
        "min_child_weight": [1, 3, 5],
    }

    tscv = TimeSeriesSplit(n_splits=5)

    search = RandomizedSearchCV(
        estimator=XGBRegressor(random_state=42, n_jobs=1, verbosity=0),
        param_distributions=param_dist,
        n_iter=50,
        cv=tscv,
        scoring="neg_mean_absolute_error",
        n_jobs=-1,
        random_state=42,
        verbose=1,
    )

    search.fit(X, y)

    best_mae    = -search.best_score_
    best_params = search.best_params_
    mae_원      = best_mae / 100 * 5e8

    print(f"\n  ★ 최적 파라미터:")
    for k, v in best_params.items():
        print(f"     {k}: {v}")
    print(f"\n  ★ 최적 MAE: {best_mae:.4f}%  (5억 기준 {mae_원/1e4:.0f}만원)")

    return best_params, best_mae


# ────────────────────────────────────────────
# 7. params.json 저장
# ────────────────────────────────────────────
def save_params(best_params, best_mae, baseline):
    params_dir  = Path(__file__).parent / "params"
    params_dir.mkdir(exist_ok=True)
    params_path = params_dir / "xgb_no_a_params.json"

    if best_mae > baseline:
        print(f"\n⚠️  튜닝 MAE({best_mae:.4f}%)가 기본값({baseline:.4f}%)보다 나쁨")
        print(f"   → 기본값으로 저장합니다.")
        save = DEFAULT_PARAMS
    else:
        print(f"\n✅ 튜닝 결과가 더 좋음 → 튜닝 파라미터 저장")
        save = {**best_params, "random_state": 42, "n_jobs": -1, "verbosity": 0}

    with open(params_path, "w") as f:
        json.dump(save, f, indent=2, ensure_ascii=False)

    print(f"✅ params.json 저장 완료: {params_path}")
    print(json.dumps(save, indent=2))


# ────────────────────────────────────────────
# 8. 메인
# ────────────────────────────────────────────
def main():
    print("\n" + "="*60)
    print("  숭늉샘B1D AI - 낙찰율 예측 / no_a 단일 모델")
    print("="*60)

    df     = load_data()
    le     = load_or_fit_le(df)
    df     = add_features(df, le)
    X, y   = prepare_xy(df)

    # 1단계: CV 비교
    cv_results = run_cv(X, y)

    print("\n" + "="*60)
    print("  1단계 완료")
    print(f"  베이스라인 (std): 0.8643%  (5억 기준 432만원)")
    print("="*60)

    # 2단계: XGBoost 튜닝
    best_params, best_mae = tune_xgboost(X, y)

    baseline    = cv_results["xgboost"]["mae"]
    improvement = (baseline - best_mae) / baseline * 100
    print(f"\n  기본값 MAE : {baseline:.4f}%")
    print(f"  튜닝 후 MAE: {best_mae:.4f}%")
    print(f"  개선율     : {improvement:.2f}%")

    # 3단계: params.json 저장 (튜닝이 나쁘면 기본값 자동 저장)
    save_params(best_params, best_mae, baseline)

    print("\n" + "="*60)
    print("  최종 요약")
    print("="*60)
    print(f"  베이스라인 std  : 0.8643%  (5억 기준 432만원)")
    print(f"  XGBoost 기본값  : {baseline:.4f}%  (5억 기준 {baseline/100*5e8/1e4:.0f}만원)")
    print(f"  XGBoost 튜닝 후 : {best_mae:.4f}%  (5억 기준 {best_mae/100*5e8/1e4:.0f}만원)")
    print(f"\n  ▶ 다음: python save_model.py 실행")
    print()


if __name__ == "__main__":
    main()