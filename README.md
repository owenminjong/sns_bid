# 숭늉샘BID (snsbid)

> 공공 입찰 낙찰가 AI 예측 B2B 웹 서비스

나라장터 API로 수집한 26만 건의 입찰 데이터를 기반으로,  
낙찰 가능성이 높은 투찰 금액을 AI로 예측합니다.

---

## 기술 스택

| 구분 | 기술 |
|---|---|
| 백엔드 | FastAPI (Python) |
| 프론트엔드 | React |
| DB | MariaDB |
| AI | XGBoost · LightGBM · RandomForest · MLP |
| 텍스트 분석 | Claude API |
| 배치 | Python · APScheduler |
| 배포 | Docker · AWS (예정) |

---

## 주요 기능

- 나라장터 API 기반 입찰공고 자동 수집 배치
- 금액대별 AI 모델 학습 및 낙찰가 예측
- Claude API 공고명·수요기관 텍스트 분석 앙상블
- 입찰공고 목록 + 예측 팝업 화면
- 예측 결과 저장 및 이력 관리

---

## 프로젝트 배경

공공 입찰 낙찰가 예측 시스템을 직접 설계·구축하면서,  
기존 접근 방식의 한계를 확인하고 아래 문제점을 개선했습니다.

- `test_size=0.000001` — 사실상 검증 없는 학습
- `adjust_value()` — 예측값을 87~89%로 강제 보정 (모델 무의미)
- MAE · RMSE · R² 등 성능 평가 지표 전무
- PHP → exec(Python) 연동 구조 (느림, 에러 처리 불가)

---

## AI 모델 전략

논문 기반으로 설계한 다중 모델 비교 구조입니다.
```text
1단계: XGBoost · LightGBM · RandomForest · MLP 비교 학습
       → MAE · RMSE · R² 기준 최적 모델 채택

2단계: 입력변수 확장
       bssamt · sucsfbidLwltRate · Aamt · realAmt
       + 금액대 구간 · 월/분기 · 지역코드 (파생변수)

3단계: Claude API 앙상블
       공고명 · 수요기관 텍스트 분석 → 수치 모델 보정
       → 예측금액 + 신뢰도 반환
```

참고 논문:
- 황대현 외, KNN을 이용한 입찰가격예측 (2019)
- 황대현 외, MLP·ANFIS를 이용한 입찰가격예측 (2020)
- 엄상훈 외, 다중선형회귀 기반 예정가격 예측 (2022)

---

## 프로젝트 구조
```text
snsbid/
├── main.py
├── .env
├── app/
│   ├── database.py
│   ├── models/
│   ├── routers/
│   ├── services/
│   └── ai/
│       ├── train.py
│       ├── predict.py
│       └── evaluate.py
├── batch/
│   ├── import_batch.py
│   └── open_batch.py
└── frontend/
    └── src/
```

---

## 데이터 현황

| 항목 | 수치 |
|---|---|
| 전체 수집 건수 | 130만 건 |
| AI 학습 가능 건수 | 26만 건 |
| 수집 기간 | 2014년 ~ 현재 |
| 핵심 컬럼 | bssamt · sucsfbidLwltRate · Aamt · realAmt · sucsfbidRate |

---

## 화면 구성

1. 로그인
2. 입찰공고 목록 + 예측 팝업 (메인)
3. 예측 결과 목록

---

## 개발 현황

- [x] 나라장터 API 배치 수집 파이프라인
- [x] 기존 시스템 분석 및 문제점 파악
- [x] DB 구조 설계 및 프로시저 정비
- [ ] FastAPI 재구축
- [ ] 다중 AI 모델 비교 학습
- [ ] Claude API 앙상블
- [ ] React 프론트엔드
- [ ] 클라우드 배포