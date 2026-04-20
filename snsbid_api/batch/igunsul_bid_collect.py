"""
아이건설넷 입찰공고 수집기
파일경로: snsbid_api/batch/igunsul_bid_collect.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import ssl
import urllib3
import time
import re
from bs4 import BeautifulSoup
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.bid import IgunsulBid
from app.models.batch import IgunsulBatch

load_dotenv()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================
# 설정값
# ============================================================

PHPSESSID       = os.getenv("IGUNSUL_PHPSESSID", "")
SESSION_IGUNSUL = os.getenv("IGUNSUL_SESSION", "")

PART          = "79"    # 시설공사
LOCAL         = "6"   # 서울
LIMIT         = 0    # 테스트: 10 / 전체: 0
REQUEST_DELAY = 1.5

BASE_URL   = "https://www.igunsul.net"
LIST_URL = f"{BASE_URL}/bid"
DETAIL_URL = f"{BASE_URL}/detail_bid/index/bid"

HEADERS = {
    "Host": "www.igunsul.net",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": BASE_URL,
    "Referer": LIST_URL,
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

def to_int(s):
    if s is None:
        return None
    nums = re.sub(r"[^\d]", "", str(s))
    if not nums:
        return None
    val = int(nums)
    if val > 9223372036854775807:
        return None
    return val

def to_float(s):
    if s is None:
        return None
    try:
        return float(str(s).replace(",", "").strip())
    except Exception:
        return None

def parse_schedule_date(text):
    """'2026/04/22 18:00' → '2026-04-22 18:00'"""
    m = re.search(r"(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2})", text)
    if m:
        return m.group(1).replace("/", "-")
    return ""

def parse_notice_no(full_no):
    m = re.match(r'^(.+)-(\d{3})$', full_no.strip())
    if m:
        return m.group(1), m.group(2)
    return full_no.strip(), "000"


# ============================================================
# 세션
# ============================================================

def get_session():
    session = requests.Session()
    session.mount("https://", SSLAdapter())
    session.cookies.set("PHPSESSID",       PHPSESSID,       domain=".igunsul.net")
    session.cookies.set("session_igunsul", SESSION_IGUNSUL, domain=".igunsul.net")
    return session


# ============================================================
# 1단계: 리스트 수집
# ============================================================

def fetch_list(session):
    today_str = datetime.now().strftime("%Y-%m-%d")
    date2 = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

    payload = {
        "bid_search_eum":  "1",
        "part":            "79",
        "part2":           "",
        "part3":           "",
        "local":           "6",
        "detail_local":    "0",
        "ipchal_date1":    today_str,
        "ipchal_date2":    date2,
        "ipchal_chkbox":   "2",
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

    resp = session.post(
        f"{BASE_URL}/bid",
        data=payload,
        headers={**HEADERS, "Referer": f"{BASE_URL}/bid/conditional_search"},
        timeout=30,
        verify=False
    )
    resp.raise_for_status()
    resp.encoding = "utf-8"
    return resp.text

def parse_con_num(value):
    parts = value.split("/")
    result = {}
    try:
        result["bbscode"]  = parts[0] if len(parts) > 0 else ""
        result["기초금액"] = int(parts[4]) if len(parts) > 4 and parts[4].isdigit() else None
        result["투찰률"]   = to_float(parts[5]) if len(parts) > 5 and parts[5] else None
        result["추정가격"] = int(parts[9]) if len(parts) > 9 and parts[9].isdigit() else None
        result["개찰일시"] = parts[11] if len(parts) > 11 else ""
    except Exception:
        pass
    return result

def parse_list(html):
    soup = BeautifulSoup(html, "html.parser")

    # 디버그
    with open("debug_bid_list.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[디버그] 응답크기: {len(html):,}자")
    print(f"[디버그] 'con_num' 포함: {'con_num' in html}")
    print(f"[디버그] 'list2detailAnchor' 포함: {'list2detailAnchor' in html}")

    if "con_num" not in html:
        print("[경고] 세션 만료. 쿠키를 갱신하세요.")
        return []

    results = []
    for row in soup.select("table tr"):
        con_input = row.find("input", {"name": "con_num[]"})
        if not con_input:
            continue
        try:
            parsed = parse_con_num(con_input.get("value", ""))
            bbscode = parsed.get("bbscode", "")
            if not bbscode:
                continue

            no_label = row.find("label", style=lambda s: s and "5c667b" in s)
            full_no  = clean(no_label.text).strip("[]") if no_label else ""
            공고번호, 공고차수 = parse_notice_no(full_no)

            name_span = row.find("span", class_="clipboard_copy_type2")
            공고명 = ""
            if name_span:
                for div in name_span.find_all("div"):
                    div.decompose()
                공고명 = clean(name_span.get_text())

            tags = [clean(t.text) for t in row.find_all("label", class_="ij_tag")]

            tooltips = row.find_all("div", class_="ij_tooltip")
            종목 = clean(tooltips[0].get_text()) if tooltips else ""

            org_div = row.find("div", class_="left")
            수요기관 = clean(org_div.get_text()) if org_div else ""

            center_divs = row.find_all("div", class_="center")
            지역 = clean(center_divs[0].get_text()) if center_divs else ""

            results.append({
                "bbscode":  bbscode,
                "공고번호": 공고번호,
                "공고차수": 공고차수,
                "공고명":   공고명,
                "태그":     ", ".join(tags),
                "종목":     종목,
                "수요기관": 수요기관,
                "지역":     지역,
                "기초금액": parsed.get("기초금액"),
                "추정가격": parsed.get("추정가격"),
                "투찰률":   parsed.get("투찰률"),
                "개찰일_원본": parsed.get("개찰일시", ""),
            })
        except Exception as e:
            print(f"  [파싱 오류] {e}")
            continue

    return results


# ============================================================
# 2단계: 세부페이지 수집
# ============================================================

def fetch_detail(session, bbscode):
    url = f"{DETAIL_URL}{bbscode}"
    resp = session.get(url, timeout=30, verify=False)
    resp.raise_for_status()
    resp.encoding = "utf-8"
    return resp.text

def parse_detail(html):
    soup = BeautifulSoup(html, "html.parser")
    result = {
        "기초금액": None, "추정가격": None, "투찰률": None,
        "A값": None, "순공사원가": None,
        "예가범위": "", "낙찰방법": "", "계약방법": "", "지역제한_상세": "",
        "등록마감일": "", "투찰시작일": "", "투찰마감일": "", "개찰일": None,
    }

    # 공고개요 테이블 파싱
    for row in soup.find_all("tr"):
        cells = row.find_all(["th", "td"])
        for i in range(len(cells) - 1):
            key = clean(cells[i].get_text())
            val = clean(cells[i+1].get_text()) if i+1 < len(cells) else ""

            if key == "기초금액":
                result["기초금액"] = to_int(val)
            elif key == "추정가격":
                result["추정가격"] = to_int(val)
            elif "투찰률" in key:
                m = re.search(r"([\d.]+)", val)
                if m:
                    rate = to_float(m.group(1))
                    if rate and 50 <= rate <= 100:  # ★ 범위 체크
                        result["투찰률"] = rate
            elif "A값" in key:
                result["A값"] = to_int(val)
            elif "순공사원가" in key:
                result["순공사원가"] = to_int(val)
            elif key == "예가범위":
                result["예가범위"] = val
            elif key == "낙찰방법":
                result["낙찰방법"] = val[:200]
            elif key == "계약방법":
                result["계약방법"] = val
            elif key == "지역제한":
                result["지역제한_상세"] = val

    # 입찰일정 파싱
    schedule_div = soup.find("div", id="schedule_div")
    if schedule_div:
        items = schedule_div.find_all("li")
        for item in items:
            text = clean(item.get_text())
            if "등록마감일" in text:
                result["등록마감일"] = parse_schedule_date(text)
            elif "투찰시작일" in text:
                result["투찰시작일"] = parse_schedule_date(text)
            elif "투찰마감일" in text:
                result["투찰마감일"] = parse_schedule_date(text)
            elif "개찰일" in text:
                d = parse_schedule_date(text)
                if d:
                    try:
                        result["개찰일"] = datetime.strptime(d, "%Y-%m-%d %H:%M")
                    except Exception:
                        pass

    return result


# ============================================================
# DB 저장
# ============================================================

def save_to_db(db: Session, rows: list, today: date):
    added = skipped = 0

    for row in rows:
        exists = db.query(IgunsulBid).filter(
            IgunsulBid.bbscode == row["bbscode"]
        ).first()
        if exists:
            skipped += 1
            continue

        bid = IgunsulBid(
            bbscode       = row["bbscode"],
            공고번호      = (row.get("공고번호", "") or "")[:20],
            공고차수      = (row.get("공고차수", "") or "")[:3],
            공고명        = (row.get("공고명", "") or "")[:200],
            태그          = (row.get("태그", "") or "")[:200],
            종목          = (row.get("종목", "") or "")[:100],
            수요기관      = (row.get("수요기관", "") or "")[:100],
            지역          = (row.get("지역", "") or "")[:50],
            지역제한_상세 = (row.get("지역제한_상세", "") or "")[:100],
            계약방법      = (row.get("계약방법", "") or "")[:50],
            낙찰방법      = (row.get("낙찰방법", "") or "")[:200],
            예가범위      = (row.get("예가범위", "") or "")[:10],
            기초금액      = row.get("기초금액"),
            추정가격      = row.get("추정가격"),
            투찰률        = row.get("투찰률"),
            A값           = row.get("A값"),
            순공사원가    = row.get("순공사원가"),
            등록마감일    = (row.get("등록마감일", "") or "")[:20],
            투찰시작일    = (row.get("투찰시작일", "") or "")[:20],
            투찰마감일    = (row.get("투찰마감일", "") or "")[:20],
            개찰일        = row.get("개찰일"),
            개찰일_원본   = (row.get("개찰일_원본", "") or "")[:30],
            수집일자      = today,
        )
        db.add(bid)
        added += 1
        print(f"  ✅ 저장: {row['공고명'][:35]}")

    db.commit()
    return added, skipped


# ============================================================
# 배치 로그
# ============================================================

def batch_start(db):
    b = IgunsulBatch(batch_type="bid", status=0)
    db.add(b)
    db.commit()
    db.refresh(b)
    return b

def batch_end(db, b, status, total, ok, skip, error, msg=""):
    b.status    = status
    b.ended_at  = datetime.now()
    b.total_cnt = total
    b.ok_cnt    = ok
    b.skip_cnt  = skip
    b.error_cnt = error
    b.message   = msg
    db.commit()


# ============================================================
# 메인
# ============================================================

def main():
    today = date.today()
    print("=" * 60)
    print(f"  아이건설넷 입찰공고 수집  |  {today}  |  {'테스트 '+str(LIMIT)+'건' if LIMIT else '전체'}")
    print("=" * 60)

    db      = SessionLocal()
    batch   = batch_start(db)
    session = get_session()

    try:
        # 1단계: 리스트
        print("\n[1단계] 입찰공고 리스트 수집")
        html     = fetch_list(session)
        all_rows = parse_list(html)
        print(f"  → 파싱: {len(all_rows)}건")

        if not all_rows:
            print("  ❌ 데이터 없음. 쿠키 만료 확인")
            batch_end(db, batch, 2, 0, 0, 0, 0, "데이터 없음")
            return

        target = all_rows[:LIMIT] if LIMIT else all_rows

        # 2단계: 세부페이지
        print(f"\n[2단계] 세부페이지 수집 ({len(target)}건)")
        errors = 0
        for i, row in enumerate(target, 1):
            print(f"  [{i}/{len(target)}] {row['공고명'][:35]}...")
            try:
                detail = parse_detail(fetch_detail(session, row["bbscode"]))
                # 세부페이지 값 우선 (기초금액 0이면 세부에서 덮어쓰기)
                for k, v in detail.items():
                    if v is not None and v != "" and v != 0:
                        row[k] = v
            except Exception as e:
                print(f"    ❌ 세부 오류: {e}")
                errors += 1
            time.sleep(REQUEST_DELAY)

        # 3단계: DB 저장
        print(f"\n[3단계] DB 저장")
        added, skipped = save_to_db(db, target, today)
        print(f"  → 저장: {added}건 / 중복스킵: {skipped}건")

        batch_end(db, batch, 1, len(target), added, skipped, errors)
        print(f"\n✅ 완료!")

    except Exception as e:
        import traceback
        msg = str(e)
        print(f"\n❌ 오류: {msg}")
        traceback.print_exc()
        batch_end(db, batch, 2, 0, 0, 0, 1, msg)

    finally:
        db.close()


if __name__ == "__main__":
    main()