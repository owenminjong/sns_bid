"""
아이건설넷 낙찰결과 수집기 v1.5
====================================
수정내역 v1.5:
  - validate_row() 추가: 수집 데이터 품질 검증
    검증 항목: 필수값 누락 / 산식1 오차 / 사정률 오차 / 낙찰금액 역전 / 낙찰율 오차 / 추첨번호 형식
  - 이슈 있는 행 → 재확인_대기 시트 자동 분류
  - 정상 행만 낙찰결과 시트에 저장

파일경로: snsbid_api/batch/igunsul_nbid_collect.py
"""

import requests
import ssl
import urllib3
import time
import re
from bs4 import BeautifulSoup
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================
# ★ 설정값
# ============================================================

PHPSESSID       = "3v5laqmiapb6svr4f8095rrabvn8v51m"
SESSION_IGUNSUL = "b2dd3b225f00b7d8b5d25122acf54b61"

PART         = "79"
LOCAL        = "6"
IPCHAL_DATE1 = "2025-12-30"
IPCHAL_DATE2 = "2026-03-30"

LIMIT            = 10
SHEET_ID         = "1dBvLESadURrrt0WWU0-HMBeBOYEl5w0rwZi_wJEo3_Y"
CREDENTIALS_FILE = "batch/service_account.json"
REQUEST_DELAY    = 1.5

# ============================================================
# 컬럼 정의
# ============================================================

COLUMNS = [
    "수집일자", "nbbscode", "bbscode", "공고번호", "공고차수", "공고명", "태그",
    "종목", "대업종", "수요기관", "지역",
    "기초금액", "추정가격",
    "투찰률",
    "A값", "순공사원가",
    "예정가격", "사정률",
    "낙찰하한가", "낙찰하한가_순공사", "낙찰하한가_실제",
    "낙찰금액", "낙찰율", "낙찰업체", "낙찰업체_추첨번호", "가격점수", "참여업체수",
    "선택복수예가", "복수예가_평균율",
    "예가1","예가2","예가3","예가4","예가5",
    "예가6","예가7","예가8","예가9","예가10",
    "예가11","예가12","예가13","예가14","예가15",
    "추첨1","추첨2","추첨3","추첨4","추첨5",
    "추첨6","추첨7","추첨8","추첨9","추첨10",
    "추첨11","추첨12","추첨13","추첨14","추첨15",
    "개찰일",
]

# 재확인_대기 시트: COLUMNS + 이슈내용 컬럼 추가
RECHECK_COLUMNS = COLUMNS + ["이슈내용"]

CIRCLE_MAP = {
    '①':1,'②':2,'③':3,'④':4,'⑤':5,
    '⑥':6,'⑦':7,'⑧':8,'⑨':9,'⑩':10,
    '⑪':11,'⑫':12,'⑬':13,'⑭':14,'⑮':15
}

BASE_URL = "https://www.igunsul.net"

REQ_HEADERS = {
    "Host": "www.igunsul.net",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": BASE_URL,
    "Referer": f"{BASE_URL}/nbid/conditional_search",
}


# ============================================================
# SSL 우회
# ============================================================

class SSLAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.set_ciphers("DEFAULT:@SECLEVEL=1")
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        kwargs["ssl_context"] = ctx
        super().init_poolmanager(*args, **kwargs)


# ============================================================
# 유틸
# ============================================================

def clean(text):
    return re.sub(r"\s+", " ", text).strip() if text else ""

def n(s):
    return int(re.sub(r"[^\d]", "", str(s))) if s else 0

def format_amount(value):
    if not value: return ""
    nums = re.sub(r"[^\d]", "", str(value))
    if not nums: return ""
    try: return f"{int(nums):,}"
    except: return str(value)

def parse_notice_no(full_no):
    match = re.match(r'^(.+)-(\d{3})$', full_no)
    if match: return match.group(1), match.group(2)
    return full_no, ""

def parse_date(raw: str) -> str:
    if not raw: return ""
    s = raw.strip()
    m = re.match(r'^(\d{2})/(\d{2})/(\d{2})(\d{2}):(\d{2})$', s)
    if m: return f"20{m.group(1)}-{m.group(2)}-{m.group(3)} {m.group(4)}:{m.group(5)}"
    m = re.match(r'^(\d{2})/(\d{2})/(\d{2})\s+(\d{2}):(\d{2})$', s)
    if m: return f"20{m.group(1)}-{m.group(2)}-{m.group(3)} {m.group(4)}:{m.group(5)}"
    m = re.match(r'^(\d{4})/(\d{2})/(\d{2})\s+(\d{2}):(\d{2})$', s)
    if m: return f"{m.group(1)}-{m.group(2)}-{m.group(3)} {m.group(4)}:{m.group(5)}"
    m = re.match(r'^(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2})$', s)
    if m: return s
    print(f"    ⚠ 개찰일 파싱 실패: '{raw}'")
    return raw

def parse_chum_no(raw: str) -> str:
    if not raw: return ""
    nums = re.findall(r'\d+', raw)
    valid = [str(int(x)) for x in nums if 1 <= int(x) <= 15]
    if len(valid) == 2: return f"{valid[0]} {valid[1]}"
    return ""

def parse_hanga(val: str):
    """
    낙찰하한가 raw → (산식1, 산식2, 실제기준)
    패턴A: '430,752,527원(예정가격 중 순공사원가 X 0.98 =388,105,586원)'
    패턴B: '92,737,805원'
    """
    m1 = re.match(r'([\d,]+)원', val)
    h1 = m1.group(1) if m1 else ""
    m2 = re.search(r'=\s*([\d,]+)원', val)
    h2 = m2.group(1) if m2 else ""
    if h1 and h2:
        실제 = h1 if int(h1.replace(',','')) >= int(h2.replace(',','')) else h2
    else:
        실제 = h1
    return h1, h2, 실제


# ============================================================
# ★ 데이터 품질 검증
# ============================================================

def validate_row(row) -> list:
    """
    수집 데이터 품질 검증
    이슈 있으면 리스트 반환, 없으면 빈 리스트
    """
    issues = []

    # 1. 필수값 누락
    필수 = [
        '기초금액', '추정가격', '투찰률', 'A값',
        '예정가격', '사정률', '낙찰하한가', '낙찰금액',
        '낙찰율', '낙찰업체', '참여업체수', '개찰일'
    ]
    for col in 필수:
        if not row.get(col):
            issues.append(f'{col}_누락')

    # 2. 산식1 오차 > 1000원: (예정-A) × 투찰률 + A
    try:
        yega     = n(row['예정가격'])
        A        = n(row['A값'])
        rate     = float(row['투찰률']) / 100
        h1_calc  = int((yega - A) * rate + A)
        h1_coll  = n(row['낙찰하한가'])
        if abs(h1_calc - h1_coll) > 1000:
            issues.append(f'낙찰하한가_오차_{h1_calc - h1_coll:+,}원')
    except Exception as e:
        issues.append(f'낙찰하한가_계산오류')

    # 3. 사정률 오차 > 0.01: (예정/기초 × 100) - 100
    try:
        기초         = n(row['기초금액'])
        예정         = n(row['예정가격'])
        사정률_calc  = round(예정 / 기초 * 100 - 100, 3)
        사정률_coll  = float(row['사정률'])
        if abs(사정률_calc - 사정률_coll) > 0.01:
            issues.append(f'사정률_오차_{사정률_calc}')
    except Exception as e:
        issues.append(f'사정률_계산오류')

    # 4. 낙찰금액 < 낙찰하한가_실제 역전
    try:
        if row.get('낙찰하한가_실제') and n(row['낙찰금액']) < n(row['낙찰하한가_실제']):
            issues.append('낙찰금액_역전')
    except: pass

    # 5. 낙찰율 오차 > 0.01: 낙찰금액/기초 × 100
    try:
        기초        = n(row['기초금액'])
        낙찰        = n(row['낙찰금액'])
        낙찰율_calc = round(낙찰 / 기초 * 100, 3)
        낙찰율_coll = float(row['낙찰율'])
        if abs(낙찰율_calc - 낙찰율_coll) > 0.01:
            issues.append(f'낙찰율_오차_{낙찰율_calc}')
    except Exception as e:
        issues.append(f'낙찰율_계산오류')

    # 6. 추첨번호 형식: 1~15 숫자 2개
    추첨 = row.get('낙찰업체_추첨번호', '')
    if 추첨:
        nums = re.findall(r'\d+', 추첨)
        valid = [int(x) for x in nums if 1 <= int(x) <= 15]
        if len(valid) != 2:
            issues.append(f'추첨번호_형식오류_{추첨}')

    return issues


# ============================================================
# 세션
# ============================================================

def get_session():
    session = requests.Session()
    session.mount("https://", SSLAdapter())
    session.headers.update(REQ_HEADERS)
    session.cookies.set("PHPSESSID",        PHPSESSID,        domain=".igunsul.net")
    session.cookies.set("session_igunsul",  SESSION_IGUNSUL,  domain=".igunsul.net")
    session.cookies.set("junja",            "1",              domain=".igunsul.net")
    session.cookies.set("list_num_session", "500",            domain=".igunsul.net")
    return session


# ============================================================
# 1단계: 낙찰 리스트 수집
# ============================================================

def fetch_nbid_list(session):
    url = f"{BASE_URL}/nbid/search_list"
    payload = {
        "bid_search_eum":  "1",
        "part":            PART,
        "part2":           "",
        "part3":           "",
        "local":           LOCAL,
        "detail_local":    "0",
        "ipchal_date1":    IPCHAL_DATE1,
        "ipchal_date2":    IPCHAL_DATE2,
        "nc_sel":          "all",
        "nc_text":         "",
        "order_name":      "",
        "order_name_type": "2",
        "real_org":        "",
        "g2b_yega_range":  "1",
        "first_com":       "",
        "cost_sel":        "init_cost",
        "cost1":           "",
        "cost2":           "",
        "align":           "1",
        "save_searchInfo": "1",
    }
    print(f"[리스트] POST {url}")
    resp = session.post(url, data=payload, timeout=30, verify=False)
    resp.raise_for_status()
    resp.encoding = "utf-8"
    print(f"[리스트] 응답 {resp.status_code} / {len(resp.text):,}자")
    return resp.text


def parse_nbid_list(html):
    soup = BeautifulSoup(html, "html.parser")
    anchors = soup.find_all("a", class_="list2detailAnchor")
    results = []

    for anchor in anchors:
        tr = anchor.find_parent("tr")
        if not tr: continue
        tds = tr.find_all("td")
        if len(tds) < 14: continue

        nbbscode = anchor.get("nbbscode", "")
        bbscode  = anchor.get("bbscode", "")
        if not nbbscode: continue

        name_span = anchor.find("span", class_="clipboard_copy_type2")
        if name_span:
            for div in name_span.find_all("div"): div.decompose()
            공고명 = clean(name_span.get_text())
        else:
            공고명 = ""

        no_label = tr.find("label", style=lambda s: s and "5c667b" in s)
        full_no  = no_label.get_text(strip=True).strip("[]") if no_label else ""
        공고번호, 공고차수 = parse_notice_no(full_no)

        tags = [t.get_text(strip=True) for t in tr.find_all("label", class_="ij_tag")]

        기초div = tds[6].find("div", class_="ta-cost fc_blue_list") if len(tds) > 6 else None
        추정div = tds[6].find("div", class_="ta-cost fc_red_list")  if len(tds) > 6 else None
        기초금액 = format_amount(기초div.get_text(strip=True).replace(",","") if 기초div else "")
        추정가격 = format_amount(추정div.get_text(strip=True).replace(",","") if 추정div else "")

        참여업체수_raw = clean(tds[13].get_text()) if len(tds) > 13 else ""
        nums_only = re.sub(r"[^\d]", "", 참여업체수_raw)
        참여업체수 = str(int(nums_only)) if nums_only else ""

        개찰일 = parse_date(clean(tds[14].get_text()) if len(tds) > 14 else "")

        results.append({
            "수집일자": "", "nbbscode": nbbscode, "bbscode": bbscode,
            "공고번호": 공고번호, "공고차수": 공고차수, "공고명": 공고명,
            "태그": " ".join(tags),
            "종목":     clean(tds[2].get_text()) if len(tds) > 2 else "",
            "대업종":   clean(tds[3].get_text()) if len(tds) > 3 else "",
            "수요기관": clean(tds[4].get_text()) if len(tds) > 4 else "",
            "지역":     clean(tds[5].get_text()) if len(tds) > 5 else "",
            "기초금액": 기초금액, "추정가격": 추정가격,
            "투찰률": "", "A값": "", "순공사원가": "",
            "예정가격": format_amount(clean(tds[7].get_text()).replace(",","")) if len(tds) > 7 else "",
            "사정률":   clean(tds[8].get_text()) if len(tds) > 8 else "",
            "낙찰하한가": "", "낙찰하한가_순공사": "", "낙찰하한가_실제": "",
            "낙찰금액": format_amount(clean(tds[9].get_text()).replace(",","")) if len(tds) > 9 else "",
            "낙찰율":   clean(tds[10].get_text()) if len(tds) > 10 else "",
            "낙찰업체": clean(tds[12].get_text()) if len(tds) > 12 else "",
            "낙찰업체_추첨번호": "", "가격점수": "",
            "참여업체수": 참여업체수,
            "선택복수예가": "", "복수예가_평균율": "",
            **{f"예가{i}": "" for i in range(1, 16)},
            **{f"추첨{i}": "" for i in range(1, 16)},
            "개찰일": 개찰일,
        })

    return results


# ============================================================
# 2단계: 낙찰 세부페이지 수집
# ============================================================

def fetch_nbid_detail(session, nbbscode):
    url = f"{BASE_URL}/detail_nbid/index/nbid{nbbscode}"
    print(f"  [세부] {url}")
    resp = session.get(url, timeout=30, verify=False)
    resp.raise_for_status()
    resp.encoding = "utf-8"
    return resp.text


def parse_nbid_detail(html):
    soup = BeautifulSoup(html, "html.parser")
    result = {
        "투찰률": "", "A값": "", "순공사원가": "",
        "낙찰하한가": "", "낙찰하한가_순공사": "", "낙찰하한가_실제": "",
        "선택복수예가": "", "복수예가_평균율": "",
        "낙찰업체_추첨번호": "", "가격점수": "",
        **{f"예가{i}": "" for i in range(1, 16)},
        **{f"추첨{i}": "" for i in range(1, 16)},
    }
    sections = soup.find_all("section")

    # 0. 공고개요
    for sec in sections:
        h5 = sec.find("h5")
        if not (h5 and "공고개요" in h5.get_text()): continue
        for row in sec.find_all("tr"):
            cells = row.find_all(["th", "td"])
            for i in range(0, len(cells) - 1, 2):
                key = cells[i].get_text(strip=True)
                val = cells[i+1].get_text(strip=True) if i+1 < len(cells) else ""
                if "투찰률" in key:
                    m = re.search(r"([\d.]+)", val)
                    if m: result["투찰률"] = m.group(1)
                elif key == "A값":
                    result["A값"] = format_amount(val)
                elif "순공사원가" in key:
                    result["순공사원가"] = format_amount(val)
                elif "낙찰하한가" in key:
                    h1, h2, 실제 = parse_hanga(val)
                    result["낙찰하한가"]        = h1
                    result["낙찰하한가_순공사"]  = h2
                    result["낙찰하한가_실제"]    = 실제
        break

    # 1. 선택복수예가 + 평균율
    top_numbers = soup.find_all("span", class_="top-number")
    if top_numbers:
        text = top_numbers[0].get_text(strip=True)
        nums = [str(CIRCLE_MAP[c]) for c in text if c in CIRCLE_MAP]
        result["선택복수예가"] = " ".join(nums)
        parent = top_numbers[0].find_parent()
        if parent:
            avg_match = re.search(r"복수예비가격 평균율\s*:\s*([-\d.]+)", clean(parent.get_text()))
            if avg_match: result["복수예가_평균율"] = avg_match.group(1)

    # 2. 복수예가 15개
    for sec in sections:
        h5 = sec.find("h5")
        if not (h5 and "개찰결과" in h5.get_text()): continue
        tables = sec.find_all("table")
        if tables:
            for row in tables[0].find_all("tr")[1:]:
                cells = row.find_all("td")
                for col_start in [0, 5, 10]:
                    if col_start + 3 >= len(cells): break
                    num_cell = cells[col_start].get_text(strip=True)
                    if num_cell not in CIRCLE_MAP: continue
                    num = CIRCLE_MAP[num_cell]
                    result[f"예가{num}"] = format_amount(cells[col_start+1].get_text(strip=True).replace(",",""))
                    result[f"추첨{num}"] = cells[col_start+3].get_text(strip=True)
        break

    # 3. 낙찰업체 추첨번호 + 가격점수
    for sec in sections:
        h5 = sec.find("h5")
        if not (h5 and "참여업체" in h5.get_text()): continue
        rows = sec.find_all("tr")
        if len(rows) < 2: break
        header = [c.get_text(strip=True) for c in rows[0].find_all(["th","td"])]
        chum_idx  = next((i for i,h in enumerate(header) if "추첨번호" in h), None)
        score_idx = next((i for i,h in enumerate(header) if "가격점수" in h), None)
        winner_row = None
        for row in rows[1:]:
            cells = row.find_all("td")
            if not cells: continue
            if "최종낙찰" in (cells[2].get_text(strip=True) if len(cells) > 2 else ""):
                winner_row = cells; break
            if cells[0].get_text(strip=True) == "1":
                winner_row = cells; break
        if winner_row:
            if chum_idx is not None and chum_idx < len(winner_row):
                result["낙찰업체_추첨번호"] = parse_chum_no(clean(winner_row[chum_idx].get_text()))
            if score_idx is not None and score_idx < len(winner_row):
                m = re.match(r"^([\d.]+)", clean(winner_row[score_idx].get_text()))
                if m: result["가격점수"] = m.group(1)
        break

    return result


# ============================================================
# 3단계: 구글시트 저장
# ============================================================

def get_sheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
    gc = gspread.authorize(creds)
    return gc.open_by_key(SHEET_ID)

def get_or_create_sheet(sh, sheet_name, columns):
    try:
        ws = sh.worksheet(sheet_name)
        print(f"  [시트] 기존: {sheet_name}")
    except gspread.exceptions.WorksheetNotFound:
        ws = sh.add_worksheet(title=sheet_name, rows=2000, cols=len(columns))
        print(f"  [시트] 신규: {sheet_name}")
    return ws

def ensure_header(ws, columns):
    existing = ws.get_all_values()
    if not existing or not existing[0] or existing[0][0] != columns[0]:
        ws.insert_row(columns, 1)
        print(f"  [시트] 헤더 추가")
        return []
    return existing[1:]  # 헤더 제외 데이터

def get_existing_nbbscodes(rows, col_idx):
    return {row[col_idx] for row in rows if len(row) > col_idx}

def save_rows(ws, rows, columns, existing_nbbscodes, today_str):
    nbb_idx = columns.index("nbbscode")
    added = skipped = 0
    for row in rows:
        nbb = str(row.get("nbbscode", ""))
        if nbb in existing_nbbscodes:
            skipped += 1
            continue
        row["수집일자"] = today_str
        ws.append_row([str(row.get(col, "")) for col in columns])
        added += 1
        time.sleep(0.3)
    return added, skipped


# ============================================================
# 메인
# ============================================================

def main():
    today_str  = datetime.now().strftime("%Y-%m-%d")
    sheet_name = f"낙찰결과_{today_str}"
    recheck_name = "재확인_대기"

    print("=" * 60)
    print(f"  아이건설넷 낙찰결과 수집  |  {today_str}  |  테스트 {LIMIT}건")
    print("=" * 60)

    session = get_session()

    # 1단계
    print("\n[1단계] 낙찰 리스트 수집")
    html     = fetch_nbid_list(session)
    all_rows = parse_nbid_list(html)
    print(f"  → 파싱: {len(all_rows)}건")
    if not all_rows:
        print("  ❌ 데이터 없음. 쿠키 만료 확인")
        return

    target = all_rows[:LIMIT]

    # 2단계
    print(f"\n[2단계] 세부페이지 수집 ({len(target)}건)")
    for i, row in enumerate(target, 1):
        print(f"  [{i}/{len(target)}] {row['공고명'][:35]}...")
        try:
            detail = parse_nbid_detail(fetch_nbid_detail(session, row["nbbscode"]))
            row.update(detail)
            print(f"    하한가:{row['낙찰하한가']} / 순공사:{row['낙찰하한가_순공사']} / 실제:{row['낙찰하한가_실제']}")
            print(f"    선택예가:{row['선택복수예가']} / 추첨:{row['낙찰업체_추첨번호']} / 점수:{row['가격점수']}")
        except Exception as e:
            print(f"    ❌ 오류: {e}")
        time.sleep(REQUEST_DELAY)

    # 품질 검증 & 분류
    print(f"\n[품질검증] {len(target)}건 검증 중...")
    ok_rows     = []
    recheck_rows = []

    for row in target:
        issues = validate_row(row)
        if issues:
            row["이슈내용"] = " | ".join(issues)
            recheck_rows.append(row)
            print(f"  ⚠️  {row['공고명'][:30]} → {issues}")
        else:
            ok_rows.append(row)
            print(f"  ✅ {row['공고명'][:30]}")

    print(f"  → 정상: {len(ok_rows)}건 / 재확인: {len(recheck_rows)}건")

    # 3단계: 구글시트 저장
    print(f"\n[3단계] 구글시트 저장")
    try:
        sh = get_sheet()

        # 정상 데이터 → 낙찰결과 시트
        if ok_rows:
            ws_ok = get_or_create_sheet(sh, sheet_name, COLUMNS)
            existing = ensure_header(ws_ok, COLUMNS)
            existing_nbb = get_existing_nbbscodes(existing, COLUMNS.index("nbbscode"))
            added, skipped = save_rows(ws_ok, ok_rows, COLUMNS, existing_nbb, today_str)
            print(f"  낙찰결과_{today_str}: 추가 {added}건 / 중복스킵 {skipped}건")

        # 재확인 데이터 → 재확인_대기 시트
        if recheck_rows:
            ws_re = get_or_create_sheet(sh, recheck_name, RECHECK_COLUMNS)
            existing_re = ensure_header(ws_re, RECHECK_COLUMNS)
            existing_nbb_re = get_existing_nbbscodes(existing_re, RECHECK_COLUMNS.index("nbbscode"))
            added_re, skipped_re = save_rows(ws_re, recheck_rows, RECHECK_COLUMNS, existing_nbb_re, today_str)
            print(f"  재확인_대기: 추가 {added_re}건 / 중복스킵 {skipped_re}건")

        print(f"\n✅ 완료!")
        print(f"   https://docs.google.com/spreadsheets/d/{SHEET_ID}")

    except Exception as e:
        print(f"\n❌ 구글시트 오류: {e}")
        import traceback; traceback.print_exc()

    # 콘솔 미리보기
    print("\n" + "=" * 60)
    print("  수집 결과 미리보기")
    print("=" * 60)
    for i, row in enumerate(target, 1):
        status = "✅" if row not in recheck_rows else f"⚠️  이슈: {row.get('이슈내용','')}"
        print(f"\n[{i}] {status}")
        print(f"  공고명    : {row['공고명'][:40]}")
        print(f"  기초/추정 : {row['기초금액']} / {row['추정가격']}")
        print(f"  투찰률    : {row['투찰률']}% / A값: {row['A값']} / 순공사: {row['순공사원가']}")
        print(f"  예정가격  : {row['예정가격']} / 사정률: {row['사정률']}")
        print(f"  하한가    : {row['낙찰하한가']} / 순공사기준: {row['낙찰하한가_순공사']} / 실제: {row['낙찰하한가_실제']}")
        print(f"  낙찰      : {row['낙찰금액']} ({row['낙찰율']}%) / {row['낙찰업체']}")
        print(f"  추첨/점수 : {row['낙찰업체_추첨번호']} / {row['가격점수']} / 참여: {row['참여업체수']}업체")
        print(f"  선택예가  : {row['선택복수예가']} / 평균율: {row['복수예가_평균율']}")
        print(f"  개찰일    : {row['개찰일']}")


if __name__ == "__main__":
    main()