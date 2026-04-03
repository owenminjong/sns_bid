"""
나라장터 공개API 입찰공고 단건 조회 테스트
==========================================
- API: getBidPblancListInfoCnstwk (공고번호로 단건 조회)
- 기초금액/순공사원가/A값 추가 조회
파일 경로: snsbid_api/batch/nara_bid_test.py
"""

import requests
from bs4 import BeautifulSoup

# ============================================================
# ★ 설정값
# ============================================================

API_KEY = "1n3WT%2BGYJGBA7V30qucc26fPsR%2BCVb51GHwG%2BtZFKRtnpYRk3T%2FtbmafOvzkDP%2BAbE867T6jzgYFfeAy51aMSQ%3D%3D"

# 조회할 공고번호 (-000 제거)
BID_NO = "R25BK00910544"

BASE_URL = "http://apis.data.go.kr/1230000/ad/BidPublicInfoService"

# ============================================================

def fetch_bid_by_no(bid_no):
    """공고번호로 단건 조회"""
    url = (
        f"{BASE_URL}/getBidPblancListInfoCnstwk"
        f"?ServiceKey={API_KEY}"
        f"&inqryDiv=2"
        f"&bidNtceNo={bid_no}"
        f"&pageNo=1"
        f"&numOfRows=10"
    )
    print(f"[요청] 입찰공고 조회")
    print(f"  URL: {url}\n")

    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, "lxml-xml")

    result_code = soup.find("resultCode")
    if result_code and result_code.text != "00":
        result_msg = soup.find("resultMsg")
        print(f"[API 오류] {result_code.text} - {result_msg.text if result_msg else ''}")
        return None

    item = soup.find("item")
    if not item:
        print("[결과 없음] 해당 공고번호가 존재하지 않습니다.")
        return None

    def val(tag):
        el = item.find(tag)
        return el.text.strip() if el and el.text else ""

    try:
        low_rate = float(val("sucsfbidLwltRate")) if val("sucsfbidLwltRate") else 0.0
    except ValueError:
        low_rate = 0.0

    try:
        bdgt_amt = int(val("bdgtAmt")) if val("bdgtAmt") else 0
    except ValueError:
        bdgt_amt = 0

    return {
        "공고번호":   val("bidNtceNo"),
        "공고차수":   val("bidNtceOrd"),
        "공고명":     val("bidNtceNm"),
        "공고종류":   val("ntceKindNm"),
        "공고일자":   val("bidNtceDt"),
        "개찰일자":   val("opengDt"),
        "수요기관":   val("dminsttNm"),
        "추정가격":   bdgt_amt,
        "낙찰하한율": low_rate,
        "취소여부":   1 if val("ntceKindNm") == "취소" else 0,
        "공고URL":    val("bidNtceDtlUrl"),
    }


def fetch_base_amount(bid_no):
    """기초금액 + 순공사원가 + A값 조회"""
    url = (
        f"{BASE_URL}/getBidPblancListInfoCnstwkBsisAmount"
        f"?ServiceKey={API_KEY}"
        f"&inqryDiv=2"
        f"&bidNtceNo={bid_no}"
        f"&pageNo=1"
        f"&numOfRows=10"
    )
    print(f"[요청] 기초금액 조회")
    print(f"  URL: {url}\n")

    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, "lxml-xml")

        result_code = soup.find("resultCode")
        if result_code and result_code.text != "00":
            result_msg = soup.find("resultMsg")
            print(f"[API 오류] {result_code.text} - {result_msg.text if result_msg else ''}")
            return None

        item = soup.find("item")
        if not item:
            print("[기초금액 없음]")
            return None

        def to_int(tag):
            el = item.find(tag)
            try:
                return int(el.text.strip()) if el and el.text.strip() else 0
            except ValueError:
                return 0

        bssamt      = to_int("bssamt")
        purcnstcst  = to_int("bssAmtPurcnstcst")
        npn         = to_int("npnInsrprm")
        health      = to_int("mrfnHealthInsrprm")
        rtr         = to_int("rtrfundNon")
        odsn        = to_int("odsnLngtrmrcprInsrprm")
        sfty        = to_int("sftyMngcst")
        sfty_chck   = to_int("sftyChckMngcst")
        qlty        = to_int("qltyMngcst")
        qlty_yn     = item.find("qltyMngcstAObjYn")
        qlty_yn_val = qlty_yn.text.strip() if qlty_yn else ""

        a_val = npn + health + rtr + odsn + sfty + sfty_chck
        if qlty_yn_val == "Y":
            a_val += qlty

        return {
            "기초금액":   bssamt,
            "순공사원가": purcnstcst,
            "A값":        a_val,
        }

    except Exception as e:
        print(f"[기초금액 조회 오류] {e}")
        return None


def print_result(bid):
    print()
    print("=" * 80)
    print("  조회 결과")
    print("=" * 80)
    fields = [
        ("공고번호",   False),
        ("공고차수",   False),
        ("공고명",     False),
        ("공고종류",   False),
        ("공고일자",   False),
        ("개찰일자",   False),
        ("수요기관",   False),
        ("추정가격",   True),
        ("낙찰하한율", False),
        ("취소여부",   False),
        ("기초금액",   True),
        ("순공사원가", True),
        ("A값",        True),
        ("공고URL",    False),
    ]
    for key, is_number in fields:
        if key not in bid:
            continue
        v = bid[key]
        if is_number and isinstance(v, int):
            print(f"    {key:10}: {v:,}")
        elif key == "취소여부":
            print(f"    {key:10}: {'취소' if v else '정상'}")
        else:
            print(f"    {key:10}: {v}")
    print("=" * 80)


def main():
    print("=" * 80)
    print("  나라장터 API 공고번호 단건 조회 테스트")
    print(f"  공고번호: {BID_NO}")
    print("=" * 80)
    print()

    # 1. 입찰공고 조회
    bid = fetch_bid_by_no(BID_NO)
    if not bid:
        return

    # 2. 기초금액/순공사원가/A값 조회
    base = fetch_base_amount(BID_NO)
    if base:
        bid.update(base)

    # 3. 결과 출력
    print_result(bid)
    print(f"\n✅ 완료")


if __name__ == "__main__":
    main()