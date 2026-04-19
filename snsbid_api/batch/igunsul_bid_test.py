"""
이건설 (igunsul.net) 입찰공고 크롤링 테스트
파일 경로: snsbid_api/batch/igunsul_bid_test.py
"""
import requests
import ssl
import urllib3
from requests.adapters import HTTPAdapter
from bs4 import BeautifulSoup
import re
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PHPSESSID       = os.getenv("IGUNSUL_PHPSESSID", "")
SESSION_IGUNSUL = os.getenv("IGUNSUL_SESSION", "")

PART  = "1"
LOCAL = "20"
LIMIT = 5

BASE_URL   = "https://www.igunsul.net"
TARGET_URL = f"{BASE_URL}/bid"

HEADERS = {
    "Host": "www.igunsul.net",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": BASE_URL,
    "Referer": f"{BASE_URL}/bid",
    "Upgrade-Insecure-Requests": "1",
    "Connection": "keep-alive",
}

class SSLAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.set_ciphers("DEFAULT:@SECLEVEL=1")
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        kwargs["ssl_context"] = ctx
        super().init_poolmanager(*args, **kwargs)

def get_session():
    session = requests.Session()
    session.mount("https://", SSLAdapter())
    session.cookies.set("PHPSESSID",       PHPSESSID,       domain=".igunsul.net")
    session.cookies.set("session_igunsul", SESSION_IGUNSUL, domain=".igunsul.net")
    return session

def fetch_page(session):
    payload = {"part": PART, "local": LOCAL}
    print(f"[요청] POST {TARGET_URL} | part={PART} local={LOCAL}")
    resp = session.post(TARGET_URL, data=payload, headers=HEADERS, timeout=30, verify=False)
    resp.raise_for_status()
    resp.encoding = "utf-8"
    print(f"[응답] 상태코드: {resp.status_code}, 크기: {len(resp.text):,}자")
    return resp.text

def parse_con_num(value):
    parts = value.split("/")
    result = {}
    try:
        result["bbscode"]  = parts[0] if len(parts) > 0 else ""
        result["기초금액"] = int(parts[4]) if len(parts) > 4 and parts[4].isdigit() else 0
        result["하한율"]   = float(parts[5]) if len(parts) > 5 and parts[5] else 0.0
        result["추정금액"] = int(parts[9]) if len(parts) > 9 and parts[9].isdigit() else 0
        result["개찰일시"] = parts[11] if len(parts) > 11 else ""
    except Exception:
        pass
    return result

def clean_text(text):
    return re.sub(r"\s+", " ", text).strip() if text else ""

def parse_rows(html):
    soup = BeautifulSoup(html, "html.parser")

    # ★ 디버그
    with open("debug.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("[디버그] debug.html 저장됨")
    print(f"[디버그] '로그인' 포함: {'로그인' in html}")
    print(f"[디버그] 'session_igunsul' 포함: {'session_igunsul' in html}")
    print(f"[디버그] 'con_num' 포함: {'con_num' in html}")
    print(f"[디버그] PHPSESSID: {PHPSESSID[:10] + '...' if PHPSESSID else '비어있음!'}")
    print(f"[디버그] SESSION:   {SESSION_IGUNSUL[:10] + '...' if SESSION_IGUNSUL else '비어있음!'}")

    # 로그인 체크 조건 변경 (con_num 기준)
    if "con_num" not in html:
        print("[경고] 세션 만료 또는 접근 실패. debug.html 확인하세요.")
        return []

    results = []
    rows = soup.select("table tr")

    for row in rows:
        con_input = row.find("input", {"name": "con_num[]"})
        if not con_input:
            continue

        try:
            con_value = con_input.get("value", "")
            parsed    = parse_con_num(con_value)

            notice_no_label = row.find("label", style=lambda s: s and "5c667b" in s)
            notice_no = clean_text(notice_no_label.text) if notice_no_label else ""
            notice_no = notice_no.strip("[]")

            name_span = row.find("span", class_="clipboard_copy_type2")
            notice_name = ""
            if name_span:
                for div in name_span.find_all("div"):
                    div.decompose()
                notice_name = clean_text(name_span.get_text())

            tags = [clean_text(t.text) for t in row.find_all("label", class_="ij_tag")]

            tooltips = row.find_all("div", class_="ij_tooltip")
            license_all  = clean_text(tooltips[0].get_text()) if len(tooltips) > 0 else ""
            license_main = clean_text(tooltips[1].get_text()) if len(tooltips) > 1 else ""

            org_div = row.find("div", class_="left")
            org = clean_text(org_div.get_text()) if org_div else ""

            center_divs = row.find_all("div", class_="center")
            region = clean_text(center_divs[0].get_text()) if center_divs else ""

            results.append({
                "bbscode":   parsed.get("bbscode", ""),
                "공고번호":  notice_no,
                "공고명":    notice_name,
                "태그":      ", ".join(tags),
                "전체면허":  license_all,
                "주면허":    license_main,
                "발주처":    org,
                "지역":      region,
                "기초금액":  parsed.get("기초금액", 0),
                "추정금액":  parsed.get("추정금액", 0),
                "하한율":    parsed.get("하한율", 0.0),
                "개찰일시":  parsed.get("개찰일시", ""),
            })

        except Exception as e:
            print(f"  [파싱 오류] {e}")
            continue

    return results

def print_results(items):
    print()
    print("=" * 80)
    print(f"  수집 결과 ({len(items)}건)")
    print("=" * 80)
    for i, item in enumerate(items, 1):
        print(f"\n[{i}] {item['공고명']}")
        print(f"    공고번호  : {item['공고번호']}")
        print(f"    bbscode   : {item['bbscode']}")
        print(f"    태그      : {item['태그']}")
        print(f"    전체면허  : {item['전체면허']}")
        print(f"    주면허    : {item['주면허']}")
        print(f"    발주처    : {item['발주처']}")
        print(f"    지역      : {item['지역']}")
        print(f"    기초금액  : {item['기초금액']:,}")
        print(f"    추정금액  : {item['추정금액']:,}")
        print(f"    하한율    : {item['하한율']}")
        print(f"    개찰일시  : {item['개찰일시']}")
    print()
    print("=" * 80)

def main():
    print("=" * 80)
    print("  이건설 입찰공고 크롤링 테스트")
    print(f"  공종: 시설 | local={LOCAL} | LIMIT: {LIMIT}건")
    print("=" * 80)

    session  = get_session()
    html     = fetch_page(session)
    all_rows = parse_rows(html)

    print(f"[파싱] {len(all_rows)}건 수집")

    result = all_rows[:LIMIT]
    print_results(result)
    print(f"✅ 완료 - {len(result)}건 출력")

if __name__ == "__main__":
    main()