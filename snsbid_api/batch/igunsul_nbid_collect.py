"""
아이건설넷 낙찰결과 수집기 v1.0
====================================
1단계: 낙찰 리스트 수집
2단계: 세부페이지 수집 (복수예가 15개, 선택번호 등)
3단계: 구글시트 저장

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

PHPSESSID       = "slfki05famdlia7d1vdikns0ujn9h6ui"
SESSION_IGUNSUL = "2ec6cf8ce208bda03970d942b2701c56"

PART         = "79"
LOCAL        = "6"
IPCHAL_DATE1 = "2025-12-30"   # 개찰일 시작
IPCHAL_DATE2 = "2026-03-30"   # 개찰일 종료

LIMIT            = 10
SHEET_ID         = "1dBvLESadURrrt0WWU0-HMBeBOYEl5w0rwZi_wJEo3_Y"
CREDENTIALS_FILE = "batch/service_account.json"
REQUEST_DELAY    = 1.5

# ============================================================
# 컬럼 정의
# ============================================================

# 낙찰 리스트 + 세부페이지 컬럼
COLUMNS = [
    # 기본
    "수집일자",
    "nbbscode",
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
    # 금액
    "기초금액",
    "추정가격",
    "예정가격",
    "사정률",
    # 낙찰결과
    "낙찰금액",
    "낙찰율",
    "낙찰업체",
    "낙찰업체_추첨번호",
    "가격점수",
    "참여업체수",
    # 복수예가
    "선택복수예가",      # 예: 2 7 8 10
    "복수예가_평균율",
    # 복수예가 15개 (금액)
    "예가1","예가2","예가3","예가4","예가5",
    "예가6","예가7","예가8","예가9","예가10",
    "예가11","예가12","예가13","예가14","예가15",
    # 복수예가 15개 (추첨수)
    "추첨1","추첨2","추첨3","추첨4","추첨5",
    "추첨6","추첨7","추첨8","추첨9","추첨10",
    "추첨11","추첨12","추첨13","추첨14","추첨15",
    # 일정
    "개찰일",
]

AMOUNT_COLUMNS = [
    "기초금액", "추정가격", "예정가격",
    "낙찰금액",
    "예가1","예가2","예가3","예가4","예가5",
    "예가6","예가7","예가8","예가9","예가10",
    "예가11","예가12","예가13","예가14","예가15",
]

# 원문자 → 숫자
CIRCLE_MAP = {
    '①':1,'②':2,'③':3,'④':4,'⑤':5,
    '⑥':6,'⑦':7,'⑧':8,'⑨':9,'⑩':10,
    '⑪':11,'⑫':12,'⑬':13,'⑭':14,'⑮':15
}

# ============================================================

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


def format_amount(value):
    if not value:
        return ""
    nums = re.sub(r"[^\d]", "", str(value))
    if not nums:
        return ""
    try:
        return f"{int(nums):,}"
    except Exception:
        return str(value)


def parse_notice_no(full_no):
    match = re.match(r'^(.+)-(\d{3})$', full_no)
    if match:
        return match.group(1), match.group(2)
    return full_no, ""


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
        if not tr:
            continue
        tds = tr.find_all("td")
        if len(tds) < 14:
            continue

        nbbscode = anchor.get("nbbscode", "")
        bbscode  = anchor.get("bbscode", "")
        if not nbbscode:
            continue

        # 공고명
        name_span = anchor.find("span", class_="clipboard_copy_type2")
        if name_span:
            for div in name_span.find_all("div"):
                div.decompose()
            공고명 = clean(name_span.get_text())
        else:
            공고명 = ""

        # 공고번호 + 차수
        no_label = tr.find("label", style=lambda s: s and "5c667b" in s)
        full_no  = no_label.get_text(strip=True).strip("[]") if no_label else ""
        공고번호, 공고차수 = parse_notice_no(full_no)

        # 태그
        tags = [t.get_text(strip=True) for t in tr.find_all("label", class_="ij_tag")]

        # 기초금액 / 추정가격 (td[6])
        기초div  = tds[6].find("div", class_="ta-cost fc_blue_list") if len(tds) > 6 else None
        추정div  = tds[6].find("div", class_="ta-cost fc_red_list")  if len(tds) > 6 else None
        기초금액 = format_amount(기초div.get_text(strip=True).replace(",","") if 기초div else "")
        추정가격 = format_amount(추정div.get_text(strip=True).replace(",","") if 추정div else "")

        # 개찰일 파싱 (td[14]: "26/03/3017:20" → "2026-03-30 17:20")
        개찰일_raw = clean(tds[14].get_text()) if len(tds) > 14 else ""
        개찰일 = ""
        if 개찰일_raw:
            m = re.match(r'(\d{2})/(\d{2})/(\d{2})(\d{2}):(\d{2})', 개찰일_raw)
            if m:
                개찰일 = f"20{m.group(1)}-{m.group(2)}-{m.group(3)} {m.group(4)}:{m.group(5)}"
            else:
                개찰일 = 개찰일_raw

        results.append({
            "수집일자":          "",
            "nbbscode":         nbbscode,
            "bbscode":          bbscode,
            "공고번호":          공고번호,
            "공고차수":          공고차수,
            "공고명":            공고명,
            "태그":              " ".join(tags),
            "종목":              clean(tds[2].get_text()) if len(tds) > 2 else "",
            "대업종":            clean(tds[3].get_text()) if len(tds) > 3 else "",
            "수요기관":          clean(tds[4].get_text()) if len(tds) > 4 else "",
            "지역":              clean(tds[5].get_text()) if len(tds) > 5 else "",
            "기초금액":          기초금액,
            "추정가격":          추정가격,
            "예정가격":          format_amount(clean(tds[7].get_text()).replace(",","")) if len(tds) > 7 else "",
            "사정률":            clean(tds[8].get_text())  if len(tds) > 8  else "",
            "낙찰금액":          format_amount(clean(tds[9].get_text()).replace(",",""))  if len(tds) > 9  else "",
            "낙찰율":            clean(tds[10].get_text()) if len(tds) > 10 else "",
            "낙찰업체":          clean(tds[12].get_text()) if len(tds) > 12 else "",
            "낙찰업체_추첨번호": "",
            "가격점수":          "",
            "참여업체수":        clean(tds[13].get_text()) if len(tds) > 13 else "",
            "선택복수예가":      "",
            "복수예가_평균율":   "",
            **{f"예가{i}":  "" for i in range(1, 16)},
            **{f"추첨{i}":  "" for i in range(1, 16)},
            "개찰일":            개찰일,
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
        "선택복수예가":      "",
        "복수예가_평균율":   "",
        "낙찰업체_추첨번호": "",
        "가격점수":          "",
        **{f"예가{i}":  "" for i in range(1, 16)},
        **{f"추첨{i}": "" for i in range(1, 16)},
    }

    # 1. 선택복수예가 번호 + 평균율
    top_numbers = soup.find_all("span", class_="top-number")
    if top_numbers:
        # 첫번째 세트만 사용
        text = top_numbers[0].get_text(strip=True)
        nums = [str(CIRCLE_MAP[c]) for c in text if c in CIRCLE_MAP]
        result["선택복수예가"] = " ".join(nums)

        # 평균율
        parent = top_numbers[0].find_parent()
        if parent:
            avg_text = clean(parent.get_text())
            avg_match = re.search(r'복수예비가격 평균율\s*:\s*([-\d.]+)', avg_text)
            if avg_match:
                result["복수예가_평균율"] = avg_match.group(1)

    # 2. 복수예가 15개 파싱 (번호순 테이블)
    sections = soup.find_all("section")
    yega_section = None
    for sec in sections:
        h5 = sec.find("h5")
        if h5 and "개찰결과" in h5.get_text():
            yega_section = sec
            break

    if yega_section:
        tables = yega_section.find_all("table")
        if tables:
            table = tables[0]  # 번호순 테이블
            rows  = table.find_all("tr")
            for row in rows[1:]:
                cells = row.find_all("td")
                # 3열 구조 (5칸씩)
                for col_start in [0, 5, 10]:
                    if col_start + 3 >= len(cells):
                        break
                    num_cell = cells[col_start].get_text(strip=True)
                    if num_cell not in CIRCLE_MAP:
                        continue
                    num      = CIRCLE_MAP[num_cell]
                    amount   = cells[col_start+1].get_text(strip=True).replace(",","")
                    chum     = cells[col_start+3].get_text(strip=True)

                    result[f"예가{num}"]  = format_amount(amount)
                    result[f"추첨{num}"] = chum

    # 3. 낙찰업체 추첨번호 + 가격점수 (참여업체 리스트 1순위)
    for sec in sections:
        rows = sec.find_all("tr")
        for row in rows:
            cells = row.find_all("td")
            if not cells:
                continue
            # 1순위 행 찾기 (첫번째 td가 '1' 이고 최종낙찰 포함)
            if cells[0].get_text(strip=True) == "1":
                row_text = row.get_text()
                if "최종낙찰" in row_text or "낙찰" in row_text:
                    # 추첨번호
                    if len(cells) > 10:
                        result["낙찰업체_추첨번호"] = clean(cells[10].get_text())
                    # 가격점수
                    if len(cells) > 6:
                        score_text = clean(cells[6].get_text())
                        score_match = re.search(r'(\d+\.?\d*)\s*점?', score_text)
                        if score_match:
                            result["가격점수"] = score_match.group(1)
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
    gc    = gspread.authorize(creds)
    return gc.open_by_key(SHEET_ID)


def get_or_create_sheet(sh, sheet_name):
    try:
        ws = sh.worksheet(sheet_name)
        print(f"  [시트] 기존 시트: {sheet_name}")
    except gspread.exceptions.WorksheetNotFound:
        ws = sh.add_worksheet(title=sheet_name, rows=2000, cols=len(COLUMNS))
        print(f"  [시트] 새 시트 생성: {sheet_name}")
    return ws


def save_nbid_sheet(ws, rows, today_str):
    existing = ws.get_all_values()

    # 헤더 확인 및 추가
    if not existing or not existing[0] or existing[0][0] != "수집일자":
        ws.insert_row(COLUMNS, 1)
        print(f"  [시트] 헤더 추가")
        existing = ws.get_all_values()

    # 기존 nbbscode 중복 체크
    existing_nbbscodes = set()
    if len(existing) > 1:
        try:
            nbb_idx = COLUMNS.index("nbbscode")
            existing_nbbscodes = {
                row[nbb_idx]
                for row in existing[1:]
                if len(row) > nbb_idx
            }
        except Exception:
            pass

    added   = 0
    skipped = 0
    for row in rows:
        nbb = str(row["nbbscode"])
        if nbb in existing_nbbscodes:
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
    sheet_name = f"낙찰결과_{today_str}"

    print("=" * 60)
    print(f"  아이건설넷 낙찰결과 수집")
    print(f"  날짜: {today_str} / 테스트: {LIMIT}건")
    print("=" * 60)

    session = get_session()

    # 1단계: 리스트
    print("\n[1단계] 낙찰 리스트 수집")
    html     = fetch_nbid_list(session)
    all_rows = parse_nbid_list(html)
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
            detail_html = fetch_nbid_detail(session, row["nbbscode"])
            detail      = parse_nbid_detail(detail_html)
            row.update(detail)
            print(f"    선택예가:{row['선택복수예가']} / 평균율:{row['복수예가_평균율']} / 낙찰추첨:{row['낙찰업체_추첨번호']}")
        except Exception as e:
            print(f"    ❌ 오류: {e}")
        time.sleep(REQUEST_DELAY)

    # 3단계: 구글시트 저장
    print(f"\n[3단계] 구글시트 저장 → {sheet_name}")
    try:
        sh    = get_sheet()
        ws    = get_or_create_sheet(sh, sheet_name)
        added = save_nbid_sheet(ws, target, today_str)
        print(f"\n✅ 완료! {added}건 → {sheet_name}")
        print(f"   https://docs.google.com/spreadsheets/d/{SHEET_ID}")
    except Exception as e:
        print(f"\n❌ 구글시트 오류: {e}")
        import traceback
        traceback.print_exc()

    # 콘솔 미리보기
    print("\n" + "=" * 60)
    print("  수집 결과 미리보기")
    print("=" * 60)
    for i, row in enumerate(target, 1):
        print(f"\n[{i}] {row['공고명'][:40]}")
        print(f"     nbbscode  : {row['nbbscode']}")
        print(f"     bbscode   : {row['bbscode']}")
        print(f"     예정가격  : {row['예정가격']}")
        print(f"     사정률    : {row['사정률']}")
        print(f"     낙찰금액  : {row['낙찰금액']}")
        print(f"     낙찰업체  : {row['낙찰업체']}")
        print(f"     참여업체수: {row['참여업체수']}")
        print(f"     선택예가  : {row['선택복수예가']}")
        print(f"     평균율    : {row['복수예가_평균율']}")
        print(f"     낙찰추첨  : {row['낙찰업체_추첨번호']}")
        print(f"     가격점수  : {row['가격점수']}")


if __name__ == "__main__":
    main()