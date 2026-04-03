"""
dsbid 입찰공고 목록 크롤링 테스트
==================================
- 공종: 시설(sPart=1) 고정
- 게시기관: 전체 (sSite= 비워둠)
- 테스트: 5건만 콘솔 출력
파일 경로: snsbid_api/batch/dsbid_bid_test.py
"""

import requests
import ssl
import urllib3
from requests.adapters import HTTPAdapter
from bs4 import BeautifulSoup
import re

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================
# ★ 설정값
# ============================================================

PHPSESSID  = "0a43a8542018041d306b242f90db3715"

START_DATE = "2026/03/27"
END_DATE   = "2026/03/27"

SEARCH_CATE = "noticeNumber"
SEARCH_TEXT = ""
SITE_CODE   = ""               # 비우면 전체, 1=나라장터, 2=국방부...
CONTRACT    = ""
STAT        = "Y"
DATE_TYPE   = "noticeTime"     # noticeTime / bidCloseTime / bidOpenTime / regCloseTime
PART        = "1"              # 1=시설 고정
LIMIT       = 5

# ============================================================

BASE_URL   = "https://admin.dsbid.co.kr"
TARGET_URL = f"{BASE_URL}/outline.php"

HEADERS = {
    "Host": "admin.dsbid.co.kr",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Upgrade-Insecure-Requests": "1",
    "Connection": "keep-alive",
}

SITE_CODE_MAP = {
    "": "전체", "1": "나라장터", "2": "국방부", "3": "한국전력",
    "4": "주택공사", "5": "도로공사", "6": "마사회", "7": "수자원공사",
    "8": "수력원자력", "9": "인천국제공항공사", "10": "국가철도공단",
    "11": "한국석유공사", "12": "한국가스공사", "13": "한국지역난방공사",
    "14": "학교장터", "15": "기타기관", "16": "한국철도공사", "17": "학교급식전자조달",
}


# ============================================================
# SSL 우회 어댑터 (구형 서버 DH키 문제)
# ============================================================

class SSLAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.set_ciphers("DEFAULT:@SECLEVEL=1")
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        kwargs["ssl_context"] = ctx
        super().init_poolmanager(*args, **kwargs)


# ============================================================
# 함수
# ============================================================

def get_session():
    session = requests.Session()
    session.mount("https://", SSLAdapter())
    session.cookies.set("PHPSESSID", PHPSESSID, domain="admin.dsbid.co.kr")
    return session


def build_params(page=1):
    return {
        "navi": "",
        "cate": "./bid/index.php",
        "bidMode": "search",
        "sCate": SEARCH_CATE,
        "sText": SEARCH_TEXT,
        "sSite": SITE_CODE,
        "sContract": CONTRACT,
        "sPart": PART,
        "sStat": STAT,
        "sDate": DATE_TYPE,
        "startDate": START_DATE,
        "endDate": END_DATE,
        "startpage": str(page),
    }


def fetch_page(session, page=1):
    params = build_params(page)
    print(f"[요청] GET page={page} | {START_DATE} ~ {END_DATE} | 공종=시설")
    resp = session.get(TARGET_URL, params=params, headers=HEADERS, timeout=30, verify=False)
    resp.raise_for_status()
    resp.encoding = "utf-8"
    print(f"[응답] 상태코드: {resp.status_code}, 크기: {len(resp.text):,}자")
    return resp.text


def clean_number(text):
    if not text:
        return 0
    cleaned = re.sub(r"[,\s\xa0]", "", text.strip())
    try:
        return int(cleaned)
    except ValueError:
        return 0


def parse_rows(html):
    soup = BeautifulSoup(html, "html.parser")

    if soup.find("form", {"name": "searchForm"}) is None:
        print("[경고] 세션 만료 또는 접근 불가. PHPSESSID를 갱신하세요.")
        return [], 0

    rows = soup.select("tr.result_tr2")

    # 전체 페이지 수
    total_pages = 1
    page_div = soup.find("div", class_="page_div")
    if page_div:
        for a in page_div.find_all("a"):
            m = re.search(r"startpage=(\d+)", a.get("href", ""))
            if m:
                total_pages = max(total_pages, int(m.group(1)))

    results = []
    for row in rows:
        tds = row.find_all("td")
        if len(tds) < 14:
            continue
        try:
            # 공고명 + idx
            name_a = tds[2].find("a", class_="noticeName")
            notice_name = name_a.get_text(strip=True) if name_a else tds[2].get_text(strip=True)
            idx = ""
            if name_a:
                m = re.search(r"idx=(\d+)", name_a.get("href", ""))
                if m:
                    idx = m.group(1)

            # 공고번호 + 사이트코드
            notice_no_a = tds[3].find("a")
            notice_no = notice_no_a.get_text(strip=True) if notice_no_a else tds[3].get_text(strip=True)
            site_code = ""
            if notice_no_a:
                m = re.search(r"orgNoticeGo\('(\d+)'", notice_no_a.get("onclick", ""))
                if m:
                    site_code = m.group(1)

            # 면허 br 처리
            for br in tds[5].find_all("br"):
                br.replace_with(", ")
            license_text = tds[5].get_text(strip=True).strip(", ")

            # 하한율
            try:
                low_rate = float(tds[11].get_text(strip=True))
            except ValueError:
                low_rate = 0.0

            results.append({
                "번호":     tds[0].get_text(strip=True),
                "공종":     tds[1].get_text(strip=True),
                "공고명":   notice_name,
                "공고번호": notice_no,
                "게시기관": SITE_CODE_MAP.get(site_code, site_code),
                "idx":      idx,
                "지역":     tds[4].get_text(strip=True),
                "면허":     license_text,
                "등록마감": tds[6].get_text(strip=True),
                "투찰마감": tds[7].get_text(strip=True),
                "개찰일시": tds[8].get_text(strip=True),
                "기초금액": clean_number(tds[9].get_text(strip=True)),
                "추정금액": clean_number(tds[10].get_text(strip=True)),
                "하한율":   low_rate,
                "예가범위": tds[12].get_text(strip=True),
            })
        except Exception as e:
            print(f"  [파싱 오류] {e}")
            continue

    return results, total_pages


def print_results(items):
    print()
    print("=" * 80)
    print(f"  수집 결과 ({len(items)}건)")
    print("=" * 80)
    for i, item in enumerate(items, 1):
        print(f"\n[{i}] {item['공고명']}")
        print(f"    공고번호  : {item['공고번호']}")
        print(f"    게시기관  : {item['게시기관']}")
        print(f"    공종/면허 : {item['공종']} / {item['면허']}")
        print(f"    지역      : {item['지역']}")
        print(f"    기초금액  : {item['기초금액']:,}")
        print(f"    추정금액  : {item['추정금액']:,}")
        print(f"    하한율    : {item['하한율']}")
        print(f"    예가범위  : {item['예가범위']}")
        print(f"    투찰마감  : {item['투찰마감']}")
        print(f"    개찰일시  : {item['개찰일시']}")
    print()
    print("=" * 80)


def main():
    print("=" * 80)
    print("  dsbid 입찰공고 목록 크롤러 (테스트)")
    print(f"  기간: {START_DATE} ~ {END_DATE} | 공종: 시설 | LIMIT: {LIMIT}건")
    print("=" * 80)

    session = get_session()
    html = fetch_page(session, page=1)
    all_rows, total_pages = parse_rows(html)

    print(f"[파싱] 1페이지 {len(all_rows)}건 / 전체 {total_pages}페이지")

    result = all_rows[:LIMIT]
    print_results(result)
    print(f"✅ 완료 - {len(result)}건 출력")


if __name__ == "__main__":
    main()