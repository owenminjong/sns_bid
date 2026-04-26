# 숭늉샘BID (snsbid)

> 공공 입찰 낙찰가 AI 예측 B2B 웹 서비스

나라장터 API로 수집한 서울시 공공입찰 데이터를 기반으로,  
낙찰 가능성이 높은 투찰 금액을 AI로 예측합니다.

---

## 기술 스택

| 구분 | 기술 |
|---|---|
| 백엔드 | FastAPI (Python) |
| 프론트엔드 | React |
| DB | MariaDB 11.1 |
| AI | XGBoost · LightGBM · RandomForest |
| 배치 | Python · APScheduler |
| 배포 | 로컬(XAMPP) → 클라우드 예정 |

---

## 주요 기능

- 나라장터 API 기반 입찰공고 자동 수집 배치
- AI 모델 학습 및 낙찰율 예측 (낙찰금액 역산)
- 입찰공고 목록 + 예측 팝업 화면
- 예측 결과 저장 및 이력 관리
- JWT 인증 기반 직원 관리

---

## 프로젝트 배경

공공 입찰에서 낙찰 확률을 높이기 위해 직접 설계하고 개발한 프로젝트입니다.

예정가격이 랜덤으로 결정되는 구조상 완벽한 예측은 불가능하지만,
과거 낙찰 패턴을 AI로 학습해 확률적으로 유리한 투찰 금액을 제시합니다.

---

## AI 모델 설계

### 낙찰 메커니즘

```
기초금액 ±2~3% 범위에서 복수예비가격 15개 생성
→ 업체들이 각 2개 번호 선택
→ 가장 많이 선택된 상위 4개 평균 = 예정가격 (랜덤)
→ 예정가격 이하 & 낙찰하한가 이상 중 최저가 업체 낙찰
→ 예정가격이 랜덤이므로 완벽한 예측 불가
→ 과거 낙찰 패턴으로 확률을 높이는 방식
```

### 모델 전략

```
1단계: XGBoost · LightGBM · RandomForest 5-Fold CV 비교
       → MAE · RMSE 기준 최적 모델 채택 (XGBoost)

2단계: 튜닝
       RandomizedSearchCV → params/xgb_no_a_params.json 저장
       → save_model.py에서 자동 로드

3단계: 전체 데이터 최종 학습 + CV MAE 실측 저장
       → models/latest.joblib
```

### 학습 데이터

| 항목 | 내용 |
|---|---|
| 소스 | igunsul_nbid (서울 공공입찰 2020~2025) |
| 건수 | 35,712건 |
| 필터 | 낙찰율 85~91%, 예가1 IS NOT NULL, 참여업체수 ≤ 10,000 |
| 타겟 | 낙찰율 (낙찰금액 / 기초금액 × 100) |

### 피처

| 피처 | 설명 |
|---|---|
| 투찰률 | 86.745 / 87.745 / 89.745 (사실상 3개 카테고리) |
| 예가범위 | (예가 MAX - MIN) / 기초금액 × 100 |
| 금액대 | 1(~10억) / 2(~30억) / 3(~50억) / 4(50억+) |
| 참여업체수 | 실수값 |
| 개찰월 | 1~12 |
| 대업종_enc | LabelEncoder (le_daeupcong.joblib 고정) |

### 성능

| 지표 | 값 |
|---|---|
| CV MAE | 0.6415% |
| 5억 기준 오차 | ±321만원 |
| 베이스라인(std) | 0.8643% |

---

## 프로젝트 구조

```
snsbid/
├── main.py
├── .env
├── requirements.txt
├── app/
│   ├── database.py
│   ├── models/              # SQLAlchemy 모델
│   ├── routers/             # FastAPI 라우터
│   │   ├── auth.py
│   │   ├── bid.py
│   │   ├── predict.py       # GET /daeupcong, POST /, POST /save, GET /list
│   │   ├── staff.py
│   │   └── batch.py
│   ├── services/            # 비즈니스 로직
│   │   ├── auth_service.py
│   │   ├── bid_service.py
│   │   └── predict_service.py
│   └── ai/
│       ├── train.py         # CV 비교 + 튜닝 (실험용)
│       ├── save_model.py    # 최종 학습 + 저장 (운영용)
│       ├── predict.py       # 예측 실행
│       ├── params/
│       │   ├── xgb_no_a_params.json   # 튜닝 결과
│       │   └── le_daeupcong.joblib    # 업종 인코더 (고정)
│       └── models/
│           ├── xgboost_no_a_날짜.joblib
│           └── latest.joblib
├── batch/
│   ├── igunsul_bid_collect.py
│   └── igunsul_nbid_collect.py
└── frontend/
    └── src/
        ├── pages/
        │   ├── Login.jsx
        │   ├── TenderNotice.jsx      # 입찰공고 목록 + 예측 팝업
        │   └── PredictionList.jsx   # 예측 결과 이력
        ├── components/
        │   └── PredictModal.jsx     # 예측 팝업 (투찰률 선택 → 예측 → 저장)
        └── api/
            └── index.js             # axios 인스턴스 (JWT 자동 주입)
```

---

## 예측 API 흐름

```
POST /api/predict
  입력: 투찰률, 기초금액, 참여업체수, 대업종, 예가범위, 개찰일자
  출력: 예측낙찰율(%), 예측낙찰금액(원), ±MAE 범위, warning

POST /api/predict/save
  입력: 공고정보 + 예측결과 (JWT에서 sfcode 자동 추출)
  저장: bid_predict 테이블 INSERT

GET /api/predict/list
  필터: 날짜, 공고번호, 공고명, 페이지
  출력: 예측 이력 목록

GET /api/predict/daeupcong
  출력: LabelEncoder 업종 목록 227개 (인증 불필요)
```

---

## 재학습 흐름

```
# 튜닝이 필요할 때 (가끔)
python app/ai/train.py
→ params/xgb_no_a_params.json 자동 저장
→ python app/ai/save_model.py

# 재학습만 할 때 (자주)
python app/ai/save_model.py
→ params.json 그대로 재사용, latest.joblib 갱신
```

---

## 화면 구성

1. 로그인
2. 입찰공고 목록 + 예측 팝업 (메인)
3. 예측 결과 목록

---

## 개발 현황

- [x] 기존 시스템 분석 및 문제점 파악
- [x] DB 구조 설계
- [x] FastAPI 프로젝트 구조 + DB 연결
- [x] 라우터 · 서비스 레이어 구성 (auth, bid, batch, staff)
- [x] 나라장터 API 배치 수집 파이프라인
- [x] 5-Fold CV 다중 모델 비교 학습
- [x] XGBoost 튜닝 + params.json 자동 저장
- [x] LabelEncoder 고정 관리 (le_daeupcong.joblib)
- [x] predict.py — 모델 로드/예측/업종 폴백(warning)
- [x] routers/predict.py · services/predict_service.py
- [x] React 프론트엔드 (TenderNotice, PredictModal, PredictionList)
- [ ] E2E 통합 테스트
- [ ] 클라우드 배포

---

## 환경변수 (.env)

```
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=sns_bid
DB_USER=root
DB_PASS=

NARA_API_KEY=
ANTHROPIC_API_KEY=

SECRET_KEY=
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

---

## 참고 논문

- 황대현 외, KNN을 이용한 입찰가격예측 (2019)
- 황대현 외, MLP·ANFIS를 이용한 입찰가격예측 (2020)
- 엄상훈 외, 다중선형회귀 기반 예정가격 예측 (2022)