"""
아이건설넷 입찰공고 수집기 v1.1
====================================
1단계: 입찰 리스트 수집
2단계: 세부페이지 수집 (A값, 순공사원가, 예가범위 등)
3단계: 구글시트 저장

파일경로: snsbid_api/batch/igunsul_collect.py
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

PHPSESSID       = "slfki05famdlia7d1vdikns0ujn9h6ui"
SESSION_IGUNSUL = "2ec6cf8ce208bda03970d942b2701c56"

PART         = "79"
LOCAL        = "6"
RE_DATE1     = "2025-12-30"
RE_DATE2     = "2026-03-30"
IPCHAL_DATE1 = "2026-03-30"
IPCHAL_DATE2 = "2026-04-30"

LIMIT            = 10  # 테스트: 10건
SHEET_ID         = "1dBvLESadURrrt0WWU0-HMBeBOYEl5w0rwZi_wJEo3_Y"
CREDENTIALS_FILE = "batch/service_account.json"
REQUEST_DELAY    = 1.5

# ============================================================
# 컬럼 정의 (순서 고정)
# ============================================================

COLUMNS = [
    # 기본
    "수집일자",
    "bbscode",
    "공고번호",
    "공고차수",
    "공고명",
    "태그",
    # 공고내용
    "종목",
    "대업종",
    "수요기관",
    "지역",
    "지역제한_상세",
    "계약방법",
    "담당자",
    # 금액
    "기초금액",
    "추정가격",
    "투찰률_하한율",
    "A값",
    "순공사원가",
    "낙찰하한가",
    "예가범위",
    # 낙찰방법
    "낙찰방법",
    # 일정
    "공고일",
    "등록마감일",
    "투찰시작일",
    "투찰마감일",
    "개찰일",
]

# ============================================================

BASE_URL = "https://www.igunsul.net"

HEADERS = {
    "Host": "www.igunsul.net",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": BASE_URL,
    "Referer": f"{BASE_URL}/bid/conditional_search",
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
# 세션
# ============================================================

def get_session():
    session = requests.Session()
    session.mount("https://", SSLAdapter())
    session.headers.update(HEADERS)
    session.cookies.set("PHPSESSID",        PHPSESSID,        domain=".igunsul.net")
    session.cookies.set("session_igunsul",  SESSION_IGUNSUL,  domain=".igunsul.net")
    session.cookies.set("junja",            "1",              domain=".igunsul.net")
    session.cookies.set("list_num_session", "500",            domain=".igunsul.net")
    return session


# ============================================================
# 1단계: 리스트 수집
# ============================================================

def fetch_bid_list(session):
    url = f"{BASE_URL}/bid/search_list"
    payload = {
        "bid_search_eum":  "1",
        "part":            PART,
        "part2":           "",
        "part3":           "",
        "local":           LOCAL,
        "detail_local":    "0",
        "ipchal_date1":    IPCHAL_DATE1,
        "ipchal_date2":    IPCHAL_DATE2,
        "ipchal_chkbox":   "2",
        "re_date1":        RE_DATE1,
        "re_date2":        RE_DATE2,
        "nc_sel":          "all",
        "nc_text":         "",
        "order_name":      "",
        "order_name_type": "2",
        "real_org":        "",
        "align":           "1",
        "cost_sel":        "init_cost",
        "cost1":           "",
        "cost2":           "",
        "save_searchInfo": "1",
    }
    print(f"[리스트] POST {url}")
    resp = session.post(url, data=payload, timeout=30, verify=False)
    resp.raise_for_status()
    resp.encoding = "utf-8"
    print(f"[리스트] 응답 {resp.status_code} / {len(resp.text):,}자")
    return resp.text


def clean(text):
    return re.sub(r"\s+", " ", text).strip() if text else ""


def parse_bid_list(html):
    soup = BeautifulSoup(html, "html.parser")
    anchors = soup.find_all("a", class_="list2detailAnchor")
    results = []

    for anchor in anchors:
        tr = anchor.find_parent("tr")
        if not tr:
            continue
        cb = tr.find("input", class_="list_chk")
        if not cb:
            continue
        val = cb.get("value", "").split("/")
        if len(val) < 12:
            continue
        tds = tr.find_all("td")
        if len(tds) < 14:
            continue

        # 공고명
        name_span = anchor.find("span", class_="clipboard_copy_type2")
        if name_span:
            for div in name_span.find_all("div"):
                div.decompose()
            공고명 = clean(name_span.get_text())
        else:
            공고명 = ""

        # 공고번호 + 차수 분리
        no_label = tr.find("label", style=lambda s: s and "5c667b" in s)
        full_no = no_label.get_text(strip=True).strip("[]") if no_label else ""
        # R26BK01430897-000 → 공고번호: R26BK01430897, 차수: 000
        if "-" in full_no:
            공고번호, 공고차수 = full_no.rsplit("-", 1)
        else:
            공고번호, 공고차수 = full_no, ""

        # 기초금액 / 추정가격
        기초div = tds[6].find("div", class_="ta-cost fc_blue_list") if len(tds) > 6 else None
        추정div = tds[6].find("div", class_="ta-cost fc_red_list") if len(tds) > 6 else None
        기초금액 = 기초div.get_text(strip=True).replace(",", "") if 기초div else val[4]
        추정가격 = 추정div.get_text(strip=True).replace(",", "") if 추정div else val[9]

        # 태그
        tags = [t.get_text(strip=True) for t in tr.find_all("label", class_="ij_tag")]

        results.append({
            "수집일자":     "",
            "bbscode":     val[0],
            "공고번호":     공고번호,
            "공고차수":     공고차수,
            "공고명":       공고명,
            "태그":         " ".join(tags),
            "종목":         clean(tds[4].get_text()) if len(tds) > 4 else "",
            "대업종":       clean(tds[5].get_text()) if len(tds) > 5 else "",
            "수요기관":     clean(tds[7].get_text()) if len(tds) > 7 else "",
            "지역":         clean(tds[8].get_text()) if len(tds) > 8 else "",
            "지역제한_상세": "",
            "계약방법":     "",
            "담당자":       "",
            "기초금액":     기초금액,
            "추정가격":     추정가격,
            "투찰률_하한율": val[5],
            "A값":          "",
            "순공사원가":   "",
            "낙찰하한가":   "",
            "예가범위":     "",
            "낙찰방법":     "",
            "공고일":       clean(tds[15].get_text()) if len(tds) > 15 else "",
            "등록마감일":   clean(tds[10].get_text()) if len(tds) > 10 else "",
            "투찰시작일":   clean(tds[12].get_text()) if len(tds) > 12 else "",
            "투찰마감일":   clean(tds[13].get_text()) if len(tds) > 13 else "",
            "개찰일":       val[11],
        })

    return results


# ============================================================
# 2단계: 세부페이지 수집
# ============================================================

def fetch_bid_detail(session, bbscode):
    url = f"{BASE_URL}/detail_bid/index/bid{bbscode}"
    print(f"  [세부] {url}")
    resp = session.get(url, timeout=30, verify=False)
    resp.raise_for_status()
    resp.encoding = "utf-8"
    return resp.text


def parse_bid_detail(html):
    soup = BeautifulSoup(html, "html.parser")
    result = {
        "A값":          "",
        "순공사원가":   "",
        "낙찰하한가":   "",
        "예가범위":     "",
        "낙찰방법":     "",
        "계약방법":     "",
        "지역제한_상세": "",
        "담당자":       "",
    }

    for th in soup.find_all("th"):
        th_text = th.get_text(strip=True)
        td = th.find_next_sibling("td")
        if not td:
            continue
        td_text = clean(td.get_text())

        if th_text == "A값":
            nums = re.findall(r"[\d,]+", td_text)
            result["A값"] = nums[0].replace(",", "") if nums else ""

        elif th_text == "순공사원가":
            nums = re.findall(r"[\d,]+", td_text)
            result["순공사원가"] = nums[0].replace(",", "") if nums else ""

        elif th_text == "낙찰하한가":
            nums = re.findall(r"[\d,]+", td_text)
            result["낙찰하한가"] = nums[0].replace(",", "") if nums else ""

        elif th_text == "예가범위":
            result["예가범위"] = td_text  # +3% ~ -3%

        elif th_text == "낙찰방법":
            result["낙찰방법"] = td_text[:100]

        elif th_text == "계약방법":
            result["계약방법"] = td_text

        elif th_text == "지역제한":
            result["지역제한_상세"] = td_text

        elif th_text in ("담당자(전화번호)", "담당자"):
            result["담당자"] = td_text

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


def get_or_create_sheet(sh, sheet_name):
    try:
        ws = sh.worksheet(sheet_name)
        print(f"  [시트] 기존 시트: {sheet_name}")
    except gspread.exceptions.WorksheetNotFound:
        ws = sh.add_worksheet(title=sheet_name, rows=1000, cols=len(COLUMNS))
        print(f"  [시트] 새 시트 생성: {sheet_name}")
    return ws


def save_to_sheet(ws, rows, today_str):
    existing = ws.get_all_values()

    # 헤더 확인 및 추가
    if not existing or not existing[0] or existing[0][0] != "수집일자":
        ws.insert_row(COLUMNS, 1)
        print(f"  [시트] 헤더 추가")
        existing = ws.get_all_values()

    # 기존 bbscode 목록 (중복 방지)
    existing_bbscodes = set()
    if len(existing) > 1:
        try:
            bbscode_idx = COLUMNS.index("bbscode")
            existing_bbscodes = {
                row[bbscode_idx]
                for row in existing[1:]
                if len(row) > bbscode_idx
            }
        except Exception:
            pass

    added = 0
    skipped = 0
    for row in rows:
        if str(row["bbscode"]) in existing_bbscodes:
            skipped += 1
            continue

        row["수집일자"] = today_str
        data_row = [str(row.get(col, "")) for col in COLUMNS]
        ws.append_row(data_row)
        added += 1
        time.sleep(0.3)

    print(f"  [시트] 추가: {added}건 / 중복스킵: {skipped}건")
    return added


# ============================================================
# 메인
# ============================================================

def main():
    today_str  = datetime.now().strftime("%Y-%m-%d")
    sheet_name = f"입찰공고_{today_str}"

    print("=" * 60)
    print(f"  아이건설넷 입찰공고 수집")
    print(f"  날짜: {today_str} / 테스트: {LIMIT}건")
    print("=" * 60)

    session = get_session()

    # 1단계: 리스트
    print("\n[1단계] 리스트 수집")
    html     = fetch_bid_list(session)
    all_rows = parse_bid_list(html)
    print(f"  → 파싱: {len(all_rows)}건")

    if not all_rows:
        print("  ❌ 데이터 없음. 쿠키 만료 확인")
        return

    target = all_rows[:LIMIT]

    # 2단계: 세부페이지
    print(f"\n[2단계] 세부페이지 수집 ({len(target)}건)")
    for i, row in enumerate(target, 1):
        print(f"  [{i}/{len(target)}] {row['공고명'][:35]}...")
        try:
            detail_html = fetch_bid_detail(session, row["bbscode"])
            detail      = parse_bid_detail(detail_html)
            row.update(detail)
            print(f"    A값:{row['A값']} / 순공사:{row['순공사원가']} / 예가범위:{row['예가범위']} / 계약:{row['계약방법']}")
        except Exception as e:
            print(f"    ❌ 오류: {e}")
        time.sleep(REQUEST_DELAY)

    # 3단계: 구글시트
    print(f"\n[3단계] 구글시트 저장")
    try:
        sh    = get_sheet()
        ws    = get_or_create_sheet(sh, sheet_name)
        added = save_to_sheet(ws, target, today_str)
        print(f"\n✅ 완료! {added}건 → 시트: {sheet_name}")
        print(f"   https://docs.google.com/spreadsheets/d/{SHEET_ID}")
    except Exception as e:
        print(f"\n❌ 구글시트 오류: {e}")
        import traceback
        traceback.print_exc()

    # 콘솔 미리보기
    print("\n" + "=" * 60)
    for i, row in enumerate(target, 1):
        print(f"[{i}] {row['공고명'][:40]}")
        print(f"     공고번호: {row['공고번호']}-{row['공고차수']}")
        print(f"     기초:{row['기초금액']} / A값:{row['A값']} / 순공사:{row['순공사원가']}")
        print(f"     예가범위:{row['예가범위']} / 계약:{row['계약방법']} / 낙찰하한가:{row['낙찰하한가']}")
        print(f"     지역제한:{row['지역제한_상세']} / 담당자:{row['담당자']}")
        print()


if __name__ == "__main__":
    main()