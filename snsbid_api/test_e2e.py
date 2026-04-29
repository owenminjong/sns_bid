"""
E2E 테스트 스크립트
실행: python test_e2e.py
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api"
TOKEN = None  # 로그인 후 자동 세팅

# ── 색상 출력 헬퍼 ──────────────────────────────────────────
def ok(msg):   print(f"  ✅ {msg}")
def fail(msg): print(f"  ❌ {msg}")
def info(msg): print(f"  ℹ️  {msg}")
def sep(title): print(f"\n{'='*55}\n  {title}\n{'='*55}")

def pprint(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))

# ── 공통 요청 헬퍼 ──────────────────────────────────────────
def get(path, params=None, auth=True):
    headers = {"Authorization": f"Bearer {TOKEN}"} if auth and TOKEN else {}
    r = requests.get(f"{BASE_URL}{path}", params=params, headers=headers)
    return r

def post(path, body, auth=True):
    headers = {"Authorization": f"Bearer {TOKEN}"} if auth and TOKEN else {}
    r = requests.post(f"{BASE_URL}{path}", json=body, headers=headers)
    return r

# ════════════════════════════════════════════════════════════
# TEST 1: 서버 헬스체크
# ════════════════════════════════════════════════════════════
sep("TEST 1: 서버 헬스체크")
try:
    r = requests.get("http://localhost:8000/")
    if r.status_code == 200:
        ok(f"서버 응답 정상 (status={r.status_code})")
        pprint(r.json())
    else:
        fail(f"서버 응답 이상 (status={r.status_code})")
except Exception as e:
    fail(f"서버 연결 실패: {e}")
    print("\n⛔ uvicorn이 실행 중인지 확인하세요.")
    exit(1)

# ════════════════════════════════════════════════════════════
# TEST 2: 로그인 → JWT 발급
# ════════════════════════════════════════════════════════════
sep("TEST 2: 로그인 (JWT 발급)")

# ★ 실제 계정으로 수정하세요
LOGIN_ID = "admin"
LOGIN_PW = "123!@#"

r = post("/auth/login", {"sfid": LOGIN_ID, "sfpw": LOGIN_PW}, auth=False)
print(f"  status: {r.status_code}")
data = r.json()
pprint(data)

if r.status_code == 200 and data.get("status") == "success":
    TOKEN = data["data"]["access_token"]
    ok(f"JWT 발급 성공 (token 앞 20자: {TOKEN[:20]}...)")
else:
    fail("로그인 실패 — sfid/sfpw 확인 필요")
    print("  ⚠️  TOKEN 없이 이후 인증 API 테스트는 실패합니다.")

# ════════════════════════════════════════════════════════════
# TEST 3: 업종 목록 (인증 불필요)
# ════════════════════════════════════════════════════════════
sep("TEST 3: GET /api/predict/daeupcong (업종 목록)")

r = get("/predict/daeupcong", auth=False)
print(f"  status: {r.status_code}")
data = r.json()

if r.status_code == 200 and data.get("status") == "success":
    items = data["data"]
    ok(f"업종 {len(items)}개 반환")
    info(f"첫 3개: {items[:3]}")
else:
    fail("업종 목록 실패")
    pprint(data)

# ════════════════════════════════════════════════════════════
# TEST 4: 입찰공고 목록
# ════════════════════════════════════════════════════════════
sep("TEST 4: GET /api/bids (입찰공고 목록)")

r = get("/bids", params={"page": 1, "page_size": 5})
print(f"  status: {r.status_code}")
data = r.json()

sample_bid = None
if r.status_code == 200 and data.get("status") == "success":
    items = data["data"]
    total = data.get("total", "?")
    ok(f"공고 {len(items)}건 반환 (전체 {total}건)")
    if items:
        sample_bid = items[0]
        info(f"샘플 공고: [{sample_bid.get('id')}] {sample_bid.get('공고명','')[:30]}")
        info(f"  기초금액={sample_bid.get('기초금액')}, 예가범위={sample_bid.get('예가범위')}")
        info(f"  대업종={sample_bid.get('대업종')}, 개찰일={sample_bid.get('개찰일')}")
else:
    fail("입찰공고 목록 실패")
    pprint(data)

# ════════════════════════════════════════════════════════════
# TEST 5: 예측 실행
# ════════════════════════════════════════════════════════════
sep("TEST 5: POST /api/predict (예측 실행)")

# 샘플 bid에서 값 추출, 없으면 기본값
bssamt      = sample_bid.get("기초금액", 500_000_000) if sample_bid else 500_000_000
yegarim     = sample_bid.get("예가범위", "+3% ~ -3%")  if sample_bid else "+3% ~ -3%"
daeupcong   = sample_bid.get("대업종", "토목")          if sample_bid else "토목"
gaechal_day = sample_bid.get("개찰일", "2025-06-15")   if sample_bid else "2025-06-15"
# 개찰일 datetime → 날짜 문자열 정리
if gaechal_day and "T" in str(gaechal_day):
    gaechal_day = str(gaechal_day)[:10]

PREDICT_BODY = {
    "투찰률":   87.745,
    "bssamt":   int(bssamt) if bssamt else 500_000_000,
    "참여업체수": 15,
    "대업종":   daeupcong,
    "예가범위":  yegarim,
    "개찰일자":  str(gaechal_day)[:10],
}
info(f"요청 바디: {PREDICT_BODY}")

r = post("/predict", PREDICT_BODY)
print(f"  status: {r.status_code}")
data = r.json()
pprint(data)

predict_result = None
if r.status_code == 200 and data.get("status") == "success":
    predict_result = data["data"]
    ok(f"예측 성공!")
    ok(f"  predict_rate : {predict_result.get('predict_rate')}%")
    ok(f"  predict_amt  : {predict_result.get('predict_amt'):,}원")
    ok(f"  model_mae_pct: {predict_result.get('model_mae_pct')}%")
    ok(f"  range        : {predict_result.get('range')}")
    if predict_result.get("warning"):
        info(f"  warning      : {predict_result.get('warning')}")
else:
    fail("예측 실패")
    pprint(data)

# ════════════════════════════════════════════════════════════
# TEST 6: 예측 저장
# ════════════════════════════════════════════════════════════
sep("TEST 6: POST /api/predict/save (예측 저장)")

if predict_result and sample_bid:
    SAVE_BODY = {
        "bbscode":   str(sample_bid.get("bbscode", "")),
        "bidNtceNo": str(sample_bid.get("공고번호", "TEST-0001")),
        "bidNtceNm": str(sample_bid.get("공고명", "E2E 테스트 공고"))[:50],
        "bssamt":    int(bssamt) if bssamt else 500_000_000,
        "Aamt":      int(sample_bid.get("A값", 0) or 0),
        "urate":     PREDICT_BODY["투찰률"],
        "preamt":    predict_result["predict_amt"],
        "preRate":   predict_result["predict_rate"],
        "preRate2":  predict_result["model_mae_pct"],
    }
    info(f"요청 바디: {SAVE_BODY}")

    r = post("/predict/save", SAVE_BODY)
    print(f"  status: {r.status_code}")
    data = r.json()
    pprint(data)

    if r.status_code == 200 and data.get("status") == "success":
        ok(f"저장 성공! psn={data['data'].get('psn')}")
    else:
        fail("저장 실패")
else:
    info("예측 결과 또는 샘플 공고 없어서 저장 테스트 스킵")
    # 더미로 테스트
    SAVE_BODY = {
        "bbscode":   "TEST",
        "bidNtceNo": "20250001",
        "bidNtceNm": "E2E 테스트 공고",
        "bssamt":    500_000_000,
        "Aamt":      0,
        "urate":     87.745,
        "preamt":    441_000_000,
        "preRate":   88.2,
        "preRate2":  0.64,
    }
    r = post("/predict/save", SAVE_BODY)
    print(f"  status: {r.status_code}")
    pprint(r.json())
    if r.status_code == 200:
        ok("더미 저장 성공")
    else:
        fail("더미 저장 실패")

# ════════════════════════════════════════════════════════════
# TEST 7: 예측 목록 조회
# ════════════════════════════════════════════════════════════
sep("TEST 7: GET /api/predict/list (예측 목록)")

today = datetime.now().strftime("%Y-%m-%d")
r = get("/predict/list", params={
    "fdate": "2024-01-01",
    "tdate": today,
    "page": 1,
    "page_size": 5,
})
print(f"  status: {r.status_code}")
data = r.json()

if r.status_code == 200 and data.get("status") == "success":
    items = data["data"]
    total = data.get("total", "?")
    ok(f"예측 목록 {len(items)}건 반환 (전체 {total}건)")
    if items:
        info(f"최신 예측: {items[0]}")
else:
    fail("예측 목록 실패")
    pprint(data)

# ════════════════════════════════════════════════════════════
# 최종 결과 요약
# ════════════════════════════════════════════════════════════
sep("E2E 테스트 완료")
print("  위 결과 확인 후 ❌ 항목 위주로 수정 진행하세요.")
print()