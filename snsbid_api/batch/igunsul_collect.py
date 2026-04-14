"""
아이건설넷 입찰공고 수집기 v1.3
====================================
1단계: 신규 공고 수집 (리스트 + 세부페이지)
2단계: 재확인_대기 시트 처리 (기초금액/A값 없는 것 재수집)
3단계: 구글시트 저장 / 업데이트

시트 구조:
  입찰공고_YYYY-MM-DD  ← 날짜별 수집 데이터
  재확인_대기          ← 기초금액/A값 없는 bbscode 목록

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

LIMIT            = 10   # 테스트: 10건 / 전체: 0 (0이면 전체)
SHEET_ID         = "1dBvLESadURrrt0WWU0-HMBeBOYEl5w0rwZi_wJEo3_Y"
CREDENTIALS_FILE = "batch/service_account.json"
REQUEST_DELAY    = 1.5

# 재확인 대기 시트명
PENDING_SHEET = "재확인_대기"

# ============================================================
# 컬럼 정의
# ============================================================

COLUMNS = [
    "수집일자",
    "bbscode",
    "공고번호",
    "공고차수",
    "공고명",
    "태그",
    "종목",
    "대업종",
    "수요기관",
    "지역",
    "지역제한_상세",
    "계약방법",
    "담당자",
    "기초금액",
    "추정가격",
    "투찰률_하한율",
    "A값",
    "순공사원가",
    "예가범위",
    "낙찰방법",
    "공고일",
    "등록마감일",
    "투찰시작일",
    "투찰마감일",
    "개찰일",
]

AMOUNT_COLUMNS = ["기초금액", "추정가격", "A값", "순공사원가"]

# 재확인 대기 시트 컬럼
PENDING_COLUMNS = [
    "bbscode",
    "원본시트",
    "최초수집일",
    "미확정항목",   # 기초금액/A값 중 없는 것
]

# ============================================================

BASE_URL = "https://www.igunsul.net"

REQ_HEADERS = {
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
# 유틸 함수
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


def has_tag(tags_str, tag):
    """태그 문자열에서 특정 태그 포함 여부"""
    return tag in tags_str


def get_missing_items(row):
    """
    기초금액/A값 중 태그는 있는데 값이 없는 항목 반환
    태그 없으면 원래부터 없는 공고이므로 제외
    """
    missing = []
    tags = row.get("태그", "")

    # 기초금액: 태그 있는데 값 없는 경우
    if has_tag(tags, "기초") and not row.get("기초금액", ""):
        missing.append("기초금액")

    # A값: 태그 있는데 값 없거나 0인 경우
    if has_tag(tags, "A값"):
        a_val = row.get("A값", "")
        a_num = re.sub(r"[^\d]", "", str(a_val))
        if not a_num or int(a_num) == 0:
            missing.append("A값")

    return missing


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

        # 공고번호 + 차수
        no_label = tr.find("label", style=lambda s: s and "5c667b" in s)
        full_no  = no_label.get_text(strip=True).strip("[]") if no_label else ""
        공고번호, 공고차수 = parse_notice_no(full_no)

        # 기초금액 / 추정가격
        기초div  = tds[6].find("div", class_="ta-cost fc_blue_list") if len(tds) > 6 else None
        추정div  = tds[6].find("div", class_="ta-cost fc_red_list")  if len(tds) > 6 else None
        기초금액 = format_amount(기초div.get_text(strip=True).replace(",", "") if 기초div else val[4])
        추정가격 = format_amount(추정div.get_text(strip=True).replace(",", "") if 추정div else val[9])

        # 태그
        tags = [t.get_text(strip=True) for t in tr.find_all("label", class_="ij_tag")]

        results.append({
            "수집일자":      "",
            "bbscode":      val[0],
            "공고번호":      공고번호,
            "공고차수":      공고차수,
            "공고명":        공고명,
            "태그":          " ".join(tags),
            "종목":          clean(tds[4].get_text()) if len(tds) > 4 else "",
            "대업종":        clean(tds[5].get_text()) if len(tds) > 5 else "",
            "수요기관":      clean(tds[7].get_text()) if len(tds) > 7 else "",
            "지역":          clean(tds[8].get_text()) if len(tds) > 8 else "",
            "지역제한_상세": "",
            "계약방법":      "",
            "담당자":        "",
            "기초금액":      기초금액,
            "추정가격":      추정가격,
            "투찰률_하한율": val[5],
            "A값":           "",
            "순공사원가":    "",
            "예가범위":      "",
            "낙찰방법":      "",
            "공고일":        clean(tds[15].get_text()) if len(tds) > 15 else "",
            "등록마감일":    clean(tds[10].get_text()) if len(tds) > 10 else "",
            "투찰시작일":    clean(tds[12].get_text()) if len(tds) > 12 else "",
            "투찰마감일":    clean(tds[13].get_text()) if len(tds) > 13 else "",
            "개찰일":        val[11],
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
        "A값":           "",
        "순공사원가":    "",
        "예가범위":      "",
        "낙찰방법":      "",
        "계약방법":      "",
        "지역제한_상세": "",
        "담당자":        "",
    }

    for th in soup.find_all("th"):
        th_text = th.get_text(strip=True)
        td = th.find_next_sibling("td")
        if not td:
            continue
        td_text = clean(td.get_text())

        if th_text == "A값":
            nums = re.findall(r"[\d,]+", td_text)
            result["A값"] = format_amount(nums[0]) if nums else ""

        elif th_text == "순공사원가":
            nums = re.findall(r"[\d,]+", td_text)
            result["순공사원가"] = format_amount(nums[0]) if nums else ""

        elif th_text == "예가범위":
            result["예가범위"] = td_text

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
# 구글시트 연결
# ============================================================

def get_sheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
    gc    = gspread.authorize(creds)
    return gc.open_by_key(SHEET_ID)


def get_or_create_sheet(sh, sheet_name, cols=None):
    try:
        ws = sh.worksheet(sheet_name)
        print(f"  [시트] 기존 시트: {sheet_name}")
    except gspread.exceptions.WorksheetNotFound:
        col_count = cols if cols else 30
        ws = sh.add_worksheet(title=sheet_name, rows=2000, cols=col_count)
        print(f"  [시트] 새 시트 생성: {sheet_name}")
    return ws


# ============================================================
# 3단계: 입찰공고 시트 저장
# ============================================================

def save_bid_sheet(ws, rows, today_str):
    existing = ws.get_all_values()

    # 헤더 확인 및 추가
    if not existing or not existing[0] or existing[0][0] != "수집일자":
        ws.insert_row(COLUMNS, 1)
        print(f"  [시트] 헤더 추가")
        existing = ws.get_all_values()

    # 기존 bbscode 목록
    existing_bbscodes = {}
    if len(existing) > 1:
        try:
            bbscode_idx = COLUMNS.index("bbscode")
            for row_idx, row in enumerate(existing[1:], start=2):
                if len(row) > bbscode_idx:
                    existing_bbscodes[row[bbscode_idx]] = row_idx
        except Exception:
            pass

    added   = 0
    skipped = 0
    for row in rows:
        bbs = str(row["bbscode"])
        if bbs in existing_bbscodes:
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
# 재확인_대기 시트 처리
# ============================================================

def get_pending_sheet(sh):
    """재확인_대기 시트 가져오기 (없으면 생성)"""
    ws = get_or_create_sheet(sh, PENDING_SHEET, cols=len(PENDING_COLUMNS))
    existing = ws.get_all_values()
    if not existing or not existing[0] or existing[0][0] != "bbscode":
        ws.insert_row(PENDING_COLUMNS, 1)
        print(f"  [대기] 헤더 추가")
    return ws


def add_to_pending(ws_pending, rows, today_str, sheet_name):
    """기초금액/A값 없는 공고를 재확인_대기에 추가"""
    existing = ws_pending.get_all_values()
    existing_bbscodes = set()
    if len(existing) > 1:
        existing_bbscodes = {row[0] for row in existing[1:] if row}

    added = 0
    for row in rows:
        missing = get_missing_items(row)
        if not missing:
            continue

        bbs = str(row["bbscode"])
        if bbs in existing_bbscodes:
            continue

        pending_row = [
            bbs,
            sheet_name,
            today_str,
            "/".join(missing),
        ]
        ws_pending.append_row(pending_row)
        added += 1
        time.sleep(0.3)

    if added:
        print(f"  [대기] 재확인 대기 추가: {added}건")
    return added


def process_pending(session, sh, ws_pending, today_str):
    """
    재확인_대기 처리:
    - 세부페이지 재수집
    - 값 생기면 원본 시트 업데이트 + 대기에서 삭제
    - 값 없으면 유지
    """
    existing = ws_pending.get_all_values()
    if len(existing) <= 1:
        print("  [대기] 재확인 대기 없음")
        return

    pending_rows = existing[1:]
    print(f"  [대기] 재확인 대기: {len(pending_rows)}건")

    # 원본 시트 캐시
    sheet_cache = {}
    completed_indices = []  # 삭제할 행 인덱스 (역순 삭제용)

    for idx, pending in enumerate(pending_rows, start=2):
        if not pending or not pending[0]:
            continue

        bbs         = pending[0]
        origin_name = pending[1]
        missing     = pending[3].split("/") if len(pending) > 3 else []

        print(f"  [{idx-1}/{len(pending_rows)}] bbscode:{bbs} 재확인 중...")

        try:
            # 세부페이지 재수집
            detail_html = fetch_bid_detail(session, bbs)
            detail      = parse_bid_detail(detail_html)
            time.sleep(REQUEST_DELAY)

            # 값이 생겼는지 확인
            resolved = []
            if "기초금액" in missing:
                # 기초금액은 리스트에서 오므로 세부페이지에서 직접 파싱
                # 여기선 A값으로 간접 확인 (기초금액은 리스트 재수집 필요)
                pass
            if "A값" in missing:
                a_val = detail.get("A값", "")
                a_num = re.sub(r"[^\d]", "", str(a_val))
                if a_num and int(a_num) > 0:
                    resolved.append("A값")

            if not resolved and "기초금액" not in missing:
                print(f"    → 아직 미확정")
                continue

            # 원본 시트에서 해당 행 찾아서 업데이트
            if origin_name not in sheet_cache:
                try:
                    sheet_cache[origin_name] = sh.worksheet(origin_name)
                except Exception:
                    print(f"    ❌ 원본 시트 없음: {origin_name}")
                    continue

            ws_origin = sheet_cache[origin_name]
            origin_data = ws_origin.get_all_values()

            # bbscode 컬럼 인덱스
            if not origin_data:
                continue
            try:
                bbs_col_idx = origin_data[0].index("bbscode")
            except ValueError:
                continue

            # 해당 행 찾기
            target_row_idx = None
            for r_idx, r in enumerate(origin_data[1:], start=2):
                if len(r) > bbs_col_idx and r[bbs_col_idx] == bbs:
                    target_row_idx = r_idx
                    break

            if not target_row_idx:
                print(f"    ❌ 원본 시트에서 행 못찾음: bbscode={bbs}")
                continue

            # 업데이트할 컬럼들
            update_map = {}
            if "A값" in resolved:
                update_map["A값"] = detail.get("A값", "")
            if detail.get("순공사원가"):
                update_map["순공사원가"] = detail.get("순공사원가", "")

            for col_name, new_val in update_map.items():
                try:
                    col_idx = origin_data[0].index(col_name) + 1  # 1-based
                    ws_origin.update_cell(target_row_idx, col_idx, new_val)
                    time.sleep(0.2)
                    print(f"    ✅ {col_name} 업데이트: {new_val}")
                except Exception as e:
                    print(f"    ❌ {col_name} 업데이트 실패: {e}")

            # 완전히 해결됐으면 대기 목록에서 삭제 예약
            remaining_missing = [m for m in missing if m not in resolved and m != "기초금액"]
            if not remaining_missing:
                completed_indices.append(idx)
                print(f"    ✅ 재확인 완료 → 대기 목록에서 제거 예약")

        except Exception as e:
            print(f"    ❌ 오류: {e}")

    # 완료된 행 역순으로 삭제 (위에서부터 삭제하면 인덱스 틀어짐)
    for row_idx in sorted(completed_indices, reverse=True):
        try:
            ws_pending.delete_rows(row_idx)
            time.sleep(0.2)
        except Exception as e:
            print(f"  ❌ 대기 행 삭제 오류: {e}")

    if completed_indices:
        print(f"  [대기] {len(completed_indices)}건 재확인 완료 → 대기 목록 삭제")


# ============================================================
# 메인
# ============================================================

def main():
    today_str  = datetime.now().strftime("%Y-%m-%d")
    sheet_name = f"입찰공고_{today_str}"

    print("=" * 60)
    print(f"  아이건설넷 입찰공고 수집")
    print(f"  날짜: {today_str} / 제한: {LIMIT if LIMIT else '전체'}건")
    print("=" * 60)

    session = get_session()
    sh      = get_sheet()

    # ── 재확인_대기 처리 ──────────────────────────────
    print("\n[재확인 처리] 기존 대기 건 확인")
    ws_pending = get_pending_sheet(sh)
    process_pending(session, sh, ws_pending, today_str)

    # ── 신규 공고 수집 ────────────────────────────────
    print("\n[1단계] 리스트 수집")
    html     = fetch_bid_list(session)
    all_rows = parse_bid_list(html)
    print(f"  → 파싱: {len(all_rows)}건")

    if not all_rows:
        print("  ❌ 데이터 없음. 쿠키 만료 확인")
        return

    target = all_rows[:LIMIT] if LIMIT else all_rows

    # ── 세부페이지 수집 ───────────────────────────────
    print(f"\n[2단계] 세부페이지 수집 ({len(target)}건)")
    for i, row in enumerate(target, 1):
        print(f"  [{i}/{len(target)}] {row['공고명'][:35]}...")
        try:
            detail_html = fetch_bid_detail(session, row["bbscode"])
            detail      = parse_bid_detail(detail_html)
            row.update(detail)
            print(f"    A값:{row['A값']} / 순공사:{row['순공사원가']} / 예가:{row['예가범위']}")
        except Exception as e:
            print(f"    ❌ 오류: {e}")
        time.sleep(REQUEST_DELAY)

    # ── 구글시트 저장 ─────────────────────────────────
    print(f"\n[3단계] 구글시트 저장 → {sheet_name}")
    try:
        ws    = get_or_create_sheet(sh, sheet_name, cols=len(COLUMNS))
        added = save_bid_sheet(ws, target, today_str)

        # 재확인 대기 추가
        print(f"\n[4단계] 재확인 대기 등록")
        add_to_pending(ws_pending, target, today_str, sheet_name)

        print(f"\n✅ 완료! {added}건 저장 → {sheet_name}")
        print(f"   https://docs.google.com/spreadsheets/d/{SHEET_ID}")

    except Exception as e:
        print(f"\n❌ 구글시트 오류: {e}")
        import traceback
        traceback.print_exc()

    # ── 콘솔 미리보기 ─────────────────────────────────
    print("\n" + "=" * 60)
    print("  수집 결과 미리보기")
    print("=" * 60)
    for i, row in enumerate(target, 1):
        missing = get_missing_items(row)
        flag    = f" ⚠️ 재확인대기({'/'.join(missing)})" if missing else ""
        print(f"\n[{i}] {row['공고명'][:40]}{flag}")
        print(f"     공고번호  : {row['공고번호']}-{row['공고차수']}")
        print(f"     기초금액  : {row['기초금액']}")
        print(f"     A값       : {row['A값']}")
        print(f"     순공사원가: {row['순공사원가']}")
        print(f"     예가범위  : {row['예가범위']}")
        print(f"     계약방법  : {row['계약방법']}")
        print(f"     개찰일    : {row['개찰일']}")


if __name__ == "__main__":
    main()