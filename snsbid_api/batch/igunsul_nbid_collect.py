"""
아이건설넷 낙찰결과 수집기 v3.0 (페이징 + 기간 분할)
파일경로: snsbid_api/batch/igunsul_nbid_collect.py
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
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.nbid import IgunsulNbid
from app.models.recheck import IgunsulRecheck
from app.models.batch import IgunsulBatch

load_dotenv()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================
# 설정값
# ============================================================

PHPSESSID       = os.getenv("IGUNSUL_PHPSESSID", "")
SESSION_IGUNSUL = os.getenv("IGUNSUL_SESSION", "")

PART          = "79"
LOCAL         = "6"
START_DATE = date(2020, 7, 1)
REQUEST_DELAY = 1.5

BASE_URL = "https://www.igunsul.net"

REQ_HEADERS = {
    "Host": "www.igunsul.net",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": BASE_URL,
    "Referer": f"{BASE_URL}/nbid/search_list",
}

CIRCLE_MAP = {
    '①':1,'②':2,'③':3,'④':4,'⑤':5,
    '⑥':6,'⑦':7,'⑧':8,'⑨':9,'⑩':10,
    '⑪':11,'⑫':12,'⑬':13,'⑭':14,'⑮':15
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

def parse_notice_no(full_no):
    match = re.match(r'^(.+)-(\d{3})$', full_no)
    if match:
        return match.group(1), match.group(2)
    return full_no, ""

def parse_date(raw: str):
    if not raw:
        return None
    s = raw.strip()
    patterns = [
        r'^(\d{2})/(\d{2})/(\d{2})(\d{2}):(\d{2})$',
        r'^(\d{2})/(\d{2})/(\d{2})\s+(\d{2}):(\d{2})$',
    ]
    for p in patterns:
        m = re.match(p, s)
        if m:
            try:
                return datetime.strptime(
                    f"20{m.group(1)}-{m.group(2)}-{m.group(3)} {m.group(4)}:{m.group(5)}",
                    "%Y-%m-%d %H:%M"
                )
            except Exception:
                pass
    m = re.match(r'^(\d{4})[/-](\d{2})[/-](\d{2})\s+(\d{2}):(\d{2})$', s)
    if m:
        try:
            return datetime.strptime(
                f"{m.group(1)}-{m.group(2)}-{m.group(3)} {m.group(4)}:{m.group(5)}",
                "%Y-%m-%d %H:%M"
            )
        except Exception:
            pass
    return None

def parse_chum_no(raw: str) -> str:
    if not raw:
        return ""
    nums = re.findall(r'\d+', raw)
    valid = [str(int(x)) for x in nums if 1 <= int(x) <= 15]
    if len(valid) == 2:
        return f"{valid[0]} {valid[1]}"
    return ""

def parse_hanga(val: str):
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
# 검증
# ============================================================

def validate_row(row: dict) -> list:
    issues = []

    # 무조건 필수
    필수 = ['기초금액', '낙찰금액', '낙찰율', '낙찰업체', '개찰일']
    for col in 필수:
        if not row.get(col):
            issues.append(f'{col}_누락')

    # A값 있을 때만 낙찰하한가 검증
    if row.get('A값') and row.get('예정가격') and row.get('투찰률'):
        try:
            yega    = to_int(row['예정가격'])
            A       = to_int(row['A값'])
            rate    = to_float(row['투찰률']) / 100
            h1_calc = int((yega - A) * rate + A)
            h1_coll = to_int(row['낙찰하한가'])
            if h1_coll and abs(h1_calc - h1_coll) > 1000:
                issues.append(f'낙찰하한가_오차_{h1_calc - h1_coll:+,}원')
        except Exception:
            pass

    # 낙찰율 검증
    try:
        기초        = to_int(row['기초금액'])
        낙찰        = to_int(row['낙찰금액'])
        낙찰율_calc = round(낙찰 / 기초 * 100, 3)
        낙찰율_coll = to_float(row['낙찰율'])
        if 낙찰율_coll is not None and abs(낙찰율_calc - 낙찰율_coll) > 0.01:
            issues.append(f'낙찰율_오차_{낙찰율_calc}')
    except Exception:
        pass

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
# 1단계: 리스트 수집
# ============================================================

def fetch_nbid_list(session, date1, date2, page=1):
    url = f"{BASE_URL}/nbid/search_list"
    payload = {
        "page_num":        str(page),
        "part":            PART,
        "part2":           "",
        "part3":           "",
        "local":           LOCAL,
        "search_code":     "",
        "search_text":     "",
        "part_section":    "1",
        "common":          "",
        "level":           "",
        "list_num":        "500",
        "align":           "1",
        "search_tag":      "",
        "detail_local":    "0",
        "ipchal_date1":    date1,
        "ipchal_date2":    date2,
        "con_named":       "",
        "n_num":           "",
        "order_name":      "",
        "order_name_type": "2",
        "g2b_code":        "",
        "yega_range":      "",
        "real_org":        "",
        "sj_rate":         "",
        "first_com":       "",
        "cost_eum":        "",
        "cost_eum2":       "",
        "cost":            "",
        "init_exp_cost1":  "",
        "init_exp_cost2":  "",
        "nc_sel":          "all",
        "nc_text":         "",
        "cost1":           "",
        "cost2":           "",
        "g2b_yega_range":  "1",
        "show_yega_range": "",
        "cost_sel":        "init_cost",
    }
    resp = session.post(url, data=payload, timeout=30, verify=False)
    resp.raise_for_status()
    resp.encoding = "utf-8"
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
        bbscode  = anchor.get("bbscode", "") or None
        if not nbbscode:
            continue

        name_span = anchor.find("span", class_="clipboard_copy_type2")
        if name_span:
            for div in name_span.find_all("div"):
                div.decompose()
            공고명 = clean(name_span.get_text())
        else:
            공고명 = ""

        no_label = tr.find("label", style=lambda s: s and "5c667b" in s)
        full_no  = no_label.get_text(strip=True).strip("[]") if no_label else ""
        공고번호, 공고차수 = parse_notice_no(full_no)

        tags = [t.get_text(strip=True) for t in tr.find_all("label", class_="ij_tag")]

        기초div  = tds[6].find("div", class_="ta-cost fc_blue_list") if len(tds) > 6 else None
        추정div  = tds[6].find("div", class_="ta-cost fc_red_list")  if len(tds) > 6 else None
        기초금액 = to_int(기초div.get_text(strip=True).replace(",","") if 기초div else None)
        추정가격 = to_int(추정div.get_text(strip=True).replace(",","") if 추정div else None)

        참여업체수_raw = clean(tds[13].get_text()) if len(tds) > 13 else ""
        참여업체수 = to_int(re.sub(r"[^\d]", "", 참여업체수_raw)) or 0

        개찰일 = parse_date(clean(tds[14].get_text()) if len(tds) > 14 else "")

        results.append({
            "nbbscode":          nbbscode,
            "bbscode":           bbscode,
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
            "투찰률":            None,
            "A값":               None,
            "순공사원가":        None,
            "예정가격":          to_int(clean(tds[7].get_text()).replace(",","")) if len(tds) > 7 else None,
            "사정률":            to_float(clean(tds[8].get_text())) if len(tds) > 8 else None,
            "낙찰하한가":        None,
            "낙찰하한가_순공사": None,
            "낙찰하한가_실제":   None,
            "낙찰금액":          to_int(clean(tds[9].get_text()).replace(",","")) if len(tds) > 9 else None,
            "낙찰율":            to_float(clean(tds[10].get_text())) if len(tds) > 10 else None,
            "낙찰업체":          clean(tds[12].get_text()) if len(tds) > 12 else "",
            "낙찰업체_추첨번호": "",
            "가격점수":          None,
            "참여업체수":        참여업체수,
            "선택복수예가":      "",
            "복수예가_평균율":   None,
            **{f"예가{i}": None for i in range(1, 16)},
            **{f"추첨{i}": None for i in range(1, 16)},
            "개찰일":            개찰일,
        })

    return results


# ============================================================
# 2단계: 세부페이지 수집
# ============================================================

def fetch_nbid_detail(session, nbbscode):
    url = f"{BASE_URL}/detail_nbid/index/nbid{nbbscode}"
    resp = session.get(url, timeout=30, verify=False)
    resp.raise_for_status()
    resp.encoding = "utf-8"
    return resp.text


def parse_nbid_detail(html):
    soup = BeautifulSoup(html, "html.parser")
    result = {
        "투찰률": None, "A값": None, "순공사원가": None,
        "낙찰하한가": None, "낙찰하한가_순공사": None, "낙찰하한가_실제": None,
        "선택복수예가": "", "복수예가_평균율": None,
        "낙찰업체_추첨번호": "", "가격점수": None,
        **{f"예가{i}": None for i in range(1, 16)},
        **{f"추첨{i}": None for i in range(1, 16)},
    }
    sections = soup.find_all("section")

    for sec in sections:
        h5 = sec.find("h5")
        if not (h5 and "공고개요" in h5.get_text()):
            continue
        for row in sec.find_all("tr"):
            cells = row.find_all(["th", "td"])
            for i in range(0, len(cells) - 1, 2):
                key = cells[i].get_text(strip=True)
                val = cells[i+1].get_text(strip=True) if i+1 < len(cells) else ""
                if "투찰률" in key:
                    m = re.search(r"([\d.]+)", val)
                    if m:
                        result["투찰률"] = to_float(m.group(1))
                elif key == "A값":
                    result["A값"] = to_int(re.sub(r"[^\d]", "", val))
                elif "순공사원가" in key:
                    result["순공사원가"] = to_int(re.sub(r"[^\d]", "", val))
                elif "낙찰하한가" in key:
                    h1, h2, 실제 = parse_hanga(val)
                    result["낙찰하한가"]       = to_int(h1)
                    result["낙찰하한가_순공사"] = to_int(h2) if h2 else None
                    result["낙찰하한가_실제"]   = to_int(실제)
        break

    top_numbers = soup.find_all("span", class_="top-number")
    if top_numbers:
        text = top_numbers[0].get_text(strip=True)
        nums = [str(CIRCLE_MAP[c]) for c in text if c in CIRCLE_MAP]
        result["선택복수예가"] = " ".join(nums)
        parent = top_numbers[0].find_parent()
        if parent:
            avg_match = re.search(r"복수예비가격 평균율\s*:\s*([-\d.]+)", clean(parent.get_text()))
            if avg_match:
                result["복수예가_평균율"] = to_float(avg_match.group(1))

    for sec in sections:
        h5 = sec.find("h5")
        if not (h5 and "개찰결과" in h5.get_text()):
            continue
        tables = sec.find_all("table")
        if tables:
            for row in tables[0].find_all("tr")[1:]:
                cells = row.find_all("td")
                for col_start in [0, 5, 10]:
                    if col_start + 3 >= len(cells):
                        break
                    num_cell = cells[col_start].get_text(strip=True)
                    if num_cell not in CIRCLE_MAP:
                        continue
                    num = CIRCLE_MAP[num_cell]
                    result[f"예가{num}"] = to_int(cells[col_start+1].get_text(strip=True).replace(",",""))
                    result[f"추첨{num}"] = to_int(cells[col_start+3].get_text(strip=True))
        break

    for sec in sections:
        h5 = sec.find("h5")
        if not (h5 and "참여업체" in h5.get_text()):
            continue
        rows = sec.find_all("tr")
        if len(rows) < 2:
            break
        header = [c.get_text(strip=True) for c in rows[0].find_all(["th","td"])]
        chum_idx  = next((i for i, h in enumerate(header) if "추첨번호" in h), None)
        score_idx = next((i for i, h in enumerate(header) if "가격점수" in h), None)
        winner_row = None
        for row in rows[1:]:
            cells = row.find_all("td")
            if not cells:
                continue
            if "최종낙찰" in (cells[2].get_text(strip=True) if len(cells) > 2 else ""):
                winner_row = cells
                break
            if cells[0].get_text(strip=True) == "1":
                winner_row = cells
                break
        if winner_row:
            if chum_idx is not None and chum_idx < len(winner_row):
                result["낙찰업체_추첨번호"] = parse_chum_no(clean(winner_row[chum_idx].get_text()))
            if score_idx is not None and score_idx < len(winner_row):
                m = re.match(r"^([\d.]+)", clean(winner_row[score_idx].get_text()))
                if m:
                    result["가격점수"] = to_float(m.group(1))
        break

    return result


# ============================================================
# DB 저장
# ============================================================

def save_to_db(db: Session, rows: list, today: date) -> tuple:
    added = skipped = recheck = 0

    for row in rows:
        exists = db.query(IgunsulNbid).filter(
            IgunsulNbid.nbbscode == row["nbbscode"]
        ).first()
        if exists:
            skipped += 1
            continue

        issues = validate_row(row)

        if issues:
            rc = IgunsulRecheck(
                nbbscode = row["nbbscode"],
                bbscode  = row.get("bbscode") or "",
                공고명   = row.get("공고명", ""),
                수집일자 = today,
                이슈내용 = " | ".join(issues),
            )
            db.add(rc)
            recheck += 1
            print(f"  ⚠️  재확인: {row['공고명'][:30]} → {issues}")
        else:
            nbid = IgunsulNbid(
                nbbscode = row["nbbscode"],
                bbscode  = row.get("bbscode"),
                **{k: row.get(k) for k in [
                    "공고번호","공고차수","공고명","태그","종목","대업종","수요기관","지역",
                    "기초금액","추정가격","투찰률","A값","순공사원가","예정가격","사정률",
                    "낙찰하한가","낙찰하한가_순공사","낙찰하한가_실제",
                    "낙찰금액","낙찰율","낙찰업체","낙찰업체_추첨번호","가격점수","참여업체수",
                    "선택복수예가","복수예가_평균율",
                    *[f"예가{i}" for i in range(1,16)],
                    *[f"추첨{i}" for i in range(1,16)],
                    "개찰일",
                ]},
                수집일자 = today,
            )
            db.add(nbid)
            added += 1
            print(f"  ✅ 저장: {row['공고명'][:30]}")

    db.commit()
    return added, skipped, recheck


# ============================================================
# 배치 로그
# ============================================================

def batch_start(db):
    b = IgunsulBatch(batch_type="nbid", status=0)
    db.add(b)
    db.commit()
    db.refresh(b)
    return b

def batch_end(db, b, status, total, ok, recheck, skip, error, msg=""):
    b.status      = status
    b.ended_at    = datetime.now()
    b.total_cnt   = total
    b.ok_cnt      = ok
    b.recheck_cnt = recheck
    b.skip_cnt    = skip
    b.error_cnt   = error
    b.message     = msg
    db.commit()


# ============================================================
# 메인
# ============================================================

def main():
    today   = date.today()
    db      = SessionLocal()
    batch   = batch_start(db)
    session = get_session()

    total_added = total_recheck = total_skip = total_error = 0

    print("=" * 60)
    print(f"  아이건설넷 낙찰결과 수집  |  {today}")
    print(f"  기간: {START_DATE} ~ {today}  (반년씩 분할)")
    print("=" * 60)

    try:
        current = START_DATE
        while current < today:
            next_period = min(current + relativedelta(months=6) - timedelta(days=1), today)
            date1 = current.strftime("%Y-%m-%d")
            date2 = next_period.strftime("%Y-%m-%d")

            print(f"\n{'='*60}")
            print(f"  기간: {date1} ~ {date2}")
            print(f"{'='*60}")

            page = 1
            while True:
                print(f"\n  [페이지 {page}] 수집 중...")
                html     = fetch_nbid_list(session, date1, date2, page)
                all_rows = parse_nbid_list(html)
                print(f"  → 파싱: {len(all_rows)}건")

                if not all_rows:
                    print("  → 데이터 없음. 다음 기간으로.")
                    break

                # 세부페이지 수집
                for i, row in enumerate(all_rows, 1):
                    print(f"    [{i}/{len(all_rows)}] {row['공고명'][:35]}...")
                    try:
                        detail = parse_nbid_detail(fetch_nbid_detail(session, row["nbbscode"]))
                        row.update(detail)
                    except Exception as e:
                        print(f"      ❌ 세부 오류: {e}")
                        total_error += 1
                    time.sleep(REQUEST_DELAY)

                # DB 저장
                added, skipped, recheck = save_to_db(db, all_rows, today)
                total_added   += added
                total_recheck += recheck
                total_skip    += skipped
                print(f"  → 저장: {added}건 / 재확인: {recheck}건 / 중복: {skipped}건")

                if len(all_rows) < 500:
                    break

                page += 1
                time.sleep(REQUEST_DELAY)

            current = next_period + timedelta(days=1)

        batch_end(db, batch, 1, total_added + total_recheck + total_skip,
                  total_added, total_recheck, total_skip, total_error)
        print(f"\n✅ 전체 완료! 저장: {total_added}건 / 재확인: {total_recheck}건 / 중복: {total_skip}건")

    except Exception as e:
        import traceback
        print(f"\n❌ 오류: {e}")
        traceback.print_exc()
        db.rollback()
        batch_end(db, batch, 2, 0, 0, 0, 0, 1, str(e))

    finally:
        db.close()


if __name__ == "__main__":
    main()