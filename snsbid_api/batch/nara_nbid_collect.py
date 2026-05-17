# batch/nara_nbid_collect.py

import os
import sys
import json
import requests
import logging
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.nara_nbid import NaraNbid

load_dotenv()

# ─────────────────────────────────────────
# 설정
# ─────────────────────────────────────────
API_KEY = os.getenv("NARA_API_KEY")
REQUEST_DELAY = 0.3
NUM_OF_ROWS = 100
BATCH_SIZE = 100
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "log")
ERROR_LOG_PATH = os.path.join(LOG_DIR, "failed_chunks.json")
COMPLETED_CHUNKS_PATH = os.path.join(LOG_DIR, "completed_chunks.json")

BASE_URL_BID = "https://apis.data.go.kr/1230000/ad/BidPublicInfoService"
BASE_URL_SCSBID = "https://apis.data.go.kr/1230000/as/ScsbidInfoService"

# ─────────────────────────────────────────
# 로거
# ─────────────────────────────────────────
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(
            os.path.join(
                LOG_DIR, f"nara_collect_{datetime.now().strftime('%Y%m%d')}.log"
            ),
            encoding="utf-8",
        ),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────
# 유틸
# ─────────────────────────────────────────
def save_failed_chunk(step: str, chunk_start: str, chunk_end: str, reason):
    entry = {
        "step": step,
        "chunk_start": chunk_start,
        "chunk_end": chunk_end,
        "reason": str(reason)[:500],
        "failed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    try:
        data = []
        if os.path.exists(ERROR_LOG_PATH):
            with open(ERROR_LOG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        data.append(entry)
        with open(ERROR_LOG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.warning(f"  실패 구간 기록됨 → {ERROR_LOG_PATH}")
    except Exception as e:
        logger.error(f"  실패 구간 기록 중 오류: {e}")


def save_completed_chunk(step: str, chunk_start: str, chunk_end: str):
    entry = {"step": step, "chunk_start": chunk_start, "chunk_end": chunk_end}
    try:
        data = []
        if os.path.exists(COMPLETED_CHUNKS_PATH):
            with open(COMPLETED_CHUNKS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        if entry not in data:
            data.append(entry)
        with open(COMPLETED_CHUNKS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"완료 구간 기록 오류: {e}")


def is_completed_chunk(step: str, chunk_start: str, chunk_end: str) -> bool:
    if not os.path.exists(COMPLETED_CHUNKS_PATH):
        return False
    try:
        with open(COMPLETED_CHUNKS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {
            "step": step,
            "chunk_start": chunk_start,
            "chunk_end": chunk_end,
        } in data
    except:
        return False


def parse_openg_dt(val: str):
    if not val:
        return None
    val = val.strip()
    try:
        if len(val) == 8:
            return datetime.strptime(val, "%Y%m%d")
        elif len(val) == 12:
            return datetime.strptime(val, "%Y%m%d%H%M")
        elif len(val) == 13:
            return datetime.strptime(val, "%Y%m%d %H%M")
        elif len(val) == 16:
            return datetime.strptime(val, "%Y-%m-%d %H:%M")
        elif len(val) == 19:
            return datetime.strptime(val, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        pass
    return None


def safe_int(val):
    try:
        v = int(val)
        return v if v > 0 else None
    except (TypeError, ValueError):
        return None


def safe_int_nullable(val):
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def safe_float(val):
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def api_get(url: str, params: dict, retries: int = 3):
    import time

    params["serviceKey"] = API_KEY
    params["type"] = "json"

    for attempt in range(1, retries + 1):
        try:
            res = requests.get(url, params=params, timeout=30)
            res.raise_for_status()
            data = res.json()
            time.sleep(REQUEST_DELAY)
            return data
        except Exception as e:
            logger.warning(f"API 호출 실패 ({attempt}/{retries}): {e}")
            if attempt < retries:
                time.sleep(1)
            else:
                logger.error(f"API 호출 최종 실패: {url}")
                return None


def get_items(data: dict) -> list:
    items = data.get("response", {}).get("body", {}).get("items", [])
    if isinstance(items, dict):
        return [items]
    return items or []


def get_total_count(data: dict) -> int:
    return int(data.get("response", {}).get("body", {}).get("totalCount", 0))


def calc_total_months(start: datetime, end: datetime) -> int:
    return (end.year - start.year) * 12 + (end.month - start.month) + 1


# ─────────────────────────────────────────
# STEP 1: 공고 목록 수집
# ─────────────────────────────────────────
def collect_bid_list(start_dt: str, end_dt: str):
    start = datetime.strptime(start_dt, "%Y%m%d%H%M")
    end = datetime.strptime(end_dt, "%Y%m%d%H%M")
    total_months = calc_total_months(start, end)
    current_month = 0

    logger.info(f"[STEP1] 시작 — 총 {total_months}개월 구간")

    current = start
    while current < end:
        next_month = min(current + relativedelta(months=1), end)
        chunk_start = current.strftime("%Y%m%d%H%M")
        chunk_end = next_month.strftime("%Y%m%d%H%M")
        current_month += 1

        logger.info(
            f"[STEP1] 구간 {current_month}/{total_months}: {chunk_start} ~ {chunk_end}"
        )

        if is_completed_chunk("STEP1", chunk_start, chunk_end):
            logger.info(f"  완료된 구간 SKIP → 다음 구간으로")
            current = next_month
            continue

        db = SessionLocal()
        page = 1
        total = 0
        inserted = 0

        try:
            while True:
                params = {
                    "inqryDiv": "1",
                    "inqryBgnDt": chunk_start,
                    "inqryEndDt": chunk_end,
                    "pageNo": page,
                    "numOfRows": NUM_OF_ROWS,
                }
                data = api_get(f"{BASE_URL_BID}/getBidPblancListInfoCnstwk", params)
                if not data:
                    break

                items = get_items(data)
                if not items:
                    logger.info(f"  데이터 없음 — 구간 종료")
                    break

                for item in items:
                    bid_no = item.get("bidNtceNo", "").strip()
                    bid_ord = item.get("bidNtceOrd", "000").strip()
                    if not bid_no:
                        continue

                    exists = (
                        db.query(NaraNbid)
                        .filter(
                            NaraNbid.bidNtceNo == bid_no,
                            NaraNbid.bidNtceOrd == bid_ord,
                        )
                        .first()
                    )
                    if exists:
                        continue

                    db.add(
                        NaraNbid(
                            bidNtceNo=bid_no,
                            bidNtceOrd=bid_ord,
                            bidNtceNm=item.get("bidNtceNm", "").strip(),
                            dminsttNm=item.get("dminsttNm", "").strip(),
                            cnstrtsiteRgnNm=item.get("cnstrtsiteRgnNm", "").strip()
                            or None,
                            opengDt=parse_openg_dt(item.get("opengDt", "")),
                            bdgtAmt=safe_int(item.get("bdgtAmt")),
                            sucsfbidLwltRate=safe_float(item.get("sucsfbidLwltRate")),
                            daeupcong=item.get("mainCnsttyNm", "").strip() or None,
                        )
                    )
                    inserted += 1

                db.commit()
                total += len(items)
                logger.info(
                    f"  page {page}: {len(items)}건 처리 "
                    f"(누적 {total}건, 신규 {inserted}건)"
                )

                if page * NUM_OF_ROWS >= get_total_count(data):
                    break
                page += 1

            save_completed_chunk("STEP1", chunk_start, chunk_end)

        except Exception as e:
            db.rollback()
            logger.error(f"[STEP1] 구간 오류 ({chunk_start}~{chunk_end}): {e}")
            save_failed_chunk("STEP1", chunk_start, chunk_end, e)
        finally:
            db.close()

        logger.info(f"[STEP1] 구간 완료: 신규 {inserted}건 저장")
        current = next_month

    logger.info(f"[STEP1] 전체 완료")


# ─────────────────────────────────────────
# STEP 2: 기초금액/예가범위 수집
# ─────────────────────────────────────────
def collect_bsis_amount():
    logger.info("[STEP2] 시작")
    updated = 0
    failed = 0

    # 전체 대상 건수 (0=미수집)
    db = SessionLocal()
    try:
        total_cnt = db.query(NaraNbid).filter(NaraNbid.is_collected == 0).count()
    finally:
        db.close()
    logger.info(f"[STEP2] 수집 대상: {total_cnt}건")

    # ✅ 🔴-1 수정: 배치마다 세션 재생성 + 실패 시 is_collected=2 표시 → 무한루프 방지
    while True:
        db = SessionLocal()
        try:
            targets = (
                db.query(NaraNbid)
                .filter(NaraNbid.is_collected == 0)
                .limit(BATCH_SIZE)
                .all()
            )
            if not targets:
                db.close()
                break

            for row in targets:
                params = {
                    "inqryDiv": "2",
                    "bidNtceNo": row.bidNtceNo,
                }
                data = api_get(
                    f"{BASE_URL_BID}/getBidPblancListInfoCnstwkBsisAmount", params
                )
                if not data:
                    failed += 1
                    row.is_collected = 2  # 2 = API 실패
                    db.commit()
                    save_failed_chunk(
                        "STEP2",
                        "N/A",
                        "N/A",
                        f"{row.bidNtceNo}-{row.bidNtceOrd} API 호출 최종 실패",
                    )
                    continue

                items = get_items(data)
                if not items:
                    row.is_collected = 1
                    db.commit()
                    continue

                item = items[0]
                row.bssamt = safe_int(item.get("bssamt"))
                row.bssAmtPurcnstcst = safe_int(item.get("bssAmtPurcnstcst"))
                row.rsrvtnPrceRngBgnRate = (
                    str(item.get("rsrvtnPrceRngBgnRate") or "").strip() or None
                )
                row.rsrvtnPrceRngEndRate = (
                    str(item.get("rsrvtnPrceRngEndRate") or "").strip() or None
                )
                row.is_collected = 1
                db.commit()
                updated += 1

                if updated % 50 == 0:
                    logger.info(
                        f"  진행중: {updated}/{total_cnt}건 완료 / 실패 {failed}건"
                    )

        except Exception as e:
            db.rollback()
            logger.error(f"[STEP2] 배치 오류: {e}")
            save_failed_chunk("STEP2", "N/A", "N/A", e)
        finally:
            db.close()

    logger.info(f"[STEP2] 완료: 성공 {updated}건 / 실패 {failed}건")


# ─────────────────────────────────────────
# STEP 3: 낙찰결과 수집
# ─────────────────────────────────────────
def parse_corp_info(corp_str: str) -> dict:
    """
    opengCorpInfo 파싱
    포맷: 업체명^사업자번호^순위^낙찰금액^낙찰율^...|업체명^...
    첫 번째 행 = 1순위 (낙찰업체)
    """
    result = {
        "bidwinnrNm": "",
        "bidwinnrBizrno": "",
        "sucsfbidAmt": None,
        "sucsfbidRate": None,
    }
    if not corp_str:
        return result

    first_row = corp_str.split("|")[0]
    parts = first_row.split("^")

    if len(parts) >= 5:
        result["bidwinnrNm"] = parts[0].strip()
        result["bidwinnrBizrno"] = parts[1].strip()
        result["sucsfbidAmt"] = safe_int(parts[3])
        result["sucsfbidRate"] = safe_float(parts[4])

    return result


def collect_open_result(start_dt: str, end_dt: str):
    start = datetime.strptime(start_dt, "%Y%m%d%H%M")
    end = datetime.strptime(end_dt, "%Y%m%d%H%M")
    total_months = calc_total_months(start, end)
    current_month = 0

    logger.info(f"[STEP3] 시작 — 총 {total_months}개월 구간")

    current = start
    while current < end:
        next_month = min(current + relativedelta(months=1), end)
        chunk_start = current.strftime("%Y%m%d%H%M")
        chunk_end = next_month.strftime("%Y%m%d%H%M")
        current_month += 1

        logger.info(
            f"[STEP3] 구간 {current_month}/{total_months}: {chunk_start} ~ {chunk_end}"
        )

        if is_completed_chunk("STEP3", chunk_start, chunk_end):
            logger.info(f"  완료된 구간 SKIP → 다음 구간으로")
            current = next_month
            continue

        db = SessionLocal()
        page = 1
        total = 0
        updated = 0
        inserted = 0
        skipped = 0

        try:
            while True:
                params = {
                    "inqryDiv": "1",
                    "inqryBgnDt": chunk_start,
                    "inqryEndDt": chunk_end,
                    "pageNo": page,
                    "numOfRows": NUM_OF_ROWS,
                }
                data = api_get(
                    f"{BASE_URL_SCSBID}/getOpengResultListInfoCnstwk", params
                )
                if not data:
                    break

                items = get_items(data)
                if not items:
                    logger.info(f"  데이터 없음 — 구간 종료")
                    break

                for item in items:
                    bid_no = item.get("bidNtceNo", "").strip()
                    bid_ord = item.get("bidNtceOrd", "000").strip()
                    if not bid_no:
                        continue

                    row = (
                        db.query(NaraNbid)
                        .filter(
                            NaraNbid.bidNtceNo == bid_no,
                            NaraNbid.bidNtceOrd == bid_ord,
                        )
                        .first()
                    )

                    if row and row.is_open == 1:
                        skipped += 1
                        continue

                    if not row:
                        row = NaraNbid(
                            bidNtceNo=bid_no,
                            bidNtceOrd=bid_ord,
                            bidNtceNm=item.get("bidNtceNm", "").strip(),
                            opengDt=parse_openg_dt(item.get("opengDt", "")),
                        )
                        db.add(row)
                        try:
                            db.flush()
                        except Exception as e:
                            # ✅ 🔴-2 수정: rollback 대신 expunge → 이전 커밋 데이터 보호
                            db.expunge(row)
                            logger.warning(f"  중복 SKIP: {bid_no}-{bid_ord} | {e}")
                            skipped += 1
                            continue
                        inserted += 1

                    corp_info = parse_corp_info(item.get("opengCorpInfo", ""))
                    row.bidwinnrNm = corp_info["bidwinnrNm"]
                    row.bidwinnrBizrno = corp_info["bidwinnrBizrno"]
                    row.sucsfbidAmt = corp_info["sucsfbidAmt"]
                    row.sucsfbidRate = corp_info["sucsfbidRate"]
                    row.prtcptCnum = safe_int(item.get("prtcptCnum")) or 0
                    row.progrsDivCdNm = str(item.get("progrsDivCdNm") or "").strip()
                    row.is_open = 1
                    updated += 1

                db.commit()
                total += len(items)
                logger.info(
                    f"  page {page}: {len(items)}건 처리 "
                    f"(누적 {total}건, 신규 {inserted}건, 업데이트 {updated}건, SKIP {skipped}건)"
                )

                if page * NUM_OF_ROWS >= get_total_count(data):
                    break
                page += 1

            save_completed_chunk("STEP3", chunk_start, chunk_end)

        except Exception as e:
            db.rollback()
            logger.error(f"[STEP3] 구간 오류 ({chunk_start}~{chunk_end}): {e}")
            save_failed_chunk("STEP3", chunk_start, chunk_end, e)
        finally:
            db.close()

        logger.info(
            f"[STEP3] 구간 완료: 신규 {inserted}건 / 업데이트 {updated}건 / SKIP {skipped}건"
        )
        current = next_month

    logger.info(f"[STEP3] 전체 완료")


# ─────────────────────────────────────────
# STEP 4: 복수예가 수집
# ─────────────────────────────────────────
def collect_plnprc(start_dt: str, end_dt: str):
    start = datetime.strptime(start_dt, "%Y%m%d%H%M")
    end = datetime.strptime(end_dt, "%Y%m%d%H%M")
    total_months = calc_total_months(start, end)
    current_month = 0

    logger.info(f"[STEP4] 시작 — 총 {total_months}개월 구간")

    current = start
    while current < end:
        next_month = min(current + relativedelta(months=1), end)
        chunk_start = current.strftime("%Y%m%d%H%M")
        chunk_end = next_month.strftime("%Y%m%d%H%M")
        current_month += 1

        logger.info(
            f"[STEP4] 구간 {current_month}/{total_months}: {chunk_start} ~ {chunk_end}"
        )

        if is_completed_chunk("STEP4", chunk_start, chunk_end):
            logger.info(f"  완료된 구간 SKIP → 다음 구간으로")
            current = next_month
            continue

        db = SessionLocal()
        page = 1
        total = 0
        plnprc_map = {}

        try:
            while True:
                params = {
                    "inqryDiv": "1",
                    "inqryBgnDt": chunk_start,
                    "inqryEndDt": chunk_end,
                    "pageNo": page,
                    "numOfRows": NUM_OF_ROWS,
                }
                data = api_get(
                    f"{BASE_URL_SCSBID}/getOpengResultListInfoCnstwkPreparPcDetail",
                    params,
                )
                if not data:
                    break

                items = get_items(data)
                if not items:
                    logger.info(f"  데이터 없음 — 구간 종료")
                    break

                for item in items:
                    bid_no = item.get("bidNtceNo", "").strip()
                    bid_ord = item.get("bidNtceOrd", "000").strip()
                    key = (bid_no, bid_ord)
                    sno = safe_int(item.get("compnoRsrvtnPrceSno"))

                    if not bid_no or not sno:
                        continue

                    if key not in plnprc_map:
                        plnprc_map[key] = {
                            "plnprc": safe_int(item.get("plnprc")),
                            "totRsrvtnPrceNum": safe_int_nullable(
                                item.get("totRsrvtnPrceNum")
                            ),
                            "prices": {},
                        }

                    plnprc_map[key]["prices"][sno] = {
                        "amt": safe_int(item.get("bsisPlnprc")),
                        "drwtNum": safe_int_nullable(item.get("drwtNum")),
                    }

                total += len(items)
                logger.info(
                    f"  page {page}: {len(items)}건 처리 "
                    f"(누적 {total}건, 공고 {len(plnprc_map)}건 집계중)"
                )

                if page * NUM_OF_ROWS >= get_total_count(data):
                    break
                page += 1

            saved = 0
            skipped = 0
            for (bid_no, bid_ord), val in plnprc_map.items():
                row = (
                    db.query(NaraNbid)
                    .filter(
                        NaraNbid.bidNtceNo == bid_no,
                        NaraNbid.bidNtceOrd == bid_ord,
                    )
                    .first()
                )
                if not row or row.is_plnprc == 1:
                    skipped += 1
                    continue

                row.plnprc = val["plnprc"]
                row.totRsrvtnPrceNum = val["totRsrvtnPrceNum"]

                for sno, price in val["prices"].items():
                    if 1 <= sno <= 15:
                        setattr(row, f"rsrvtnPrce{sno}", price["amt"])
                        setattr(row, f"drwtNum{sno}", price["drwtNum"])

                row.is_plnprc = 1
                saved += 1

            db.commit()
            save_completed_chunk("STEP4", chunk_start, chunk_end)
            logger.info(f"[STEP4] 구간 완료: {saved}건 저장 / {skipped}건 SKIP")

        except Exception as e:
            db.rollback()
            logger.error(f"[STEP4] 구간 오류 ({chunk_start}~{chunk_end}): {e}")
            save_failed_chunk("STEP4", chunk_start, chunk_end, e)
        finally:
            db.close()

        current = next_month

    logger.info(f"[STEP4] 전체 완료")


# ─────────────────────────────────────────
# 메인
# ─────────────────────────────────────────
def get_date_range(days_back: int = 7):
    end = datetime.now()
    start = end - timedelta(days=days_back)
    return (start.strftime("%Y%m%d") + "0000", end.strftime("%Y%m%d") + "2359")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="나라장터 건설공사 데이터 수집 배치")
    parser.add_argument("--start", type=str, help="시작일 (예: 202605010000)")
    parser.add_argument("--end", type=str, help="종료일 (예: 202605102359)")
    parser.add_argument(
        "--step",
        type=str,
        default="all",
        help="실행 단계: all / 1(공고) / 2(기초금액) / 3(낙찰결과) / 4(복수예가)",
    )
    args = parser.parse_args()

    if args.start and args.end:
        start_dt, end_dt = args.start, args.end
    else:
        logger.warning(
            "날짜 미지정 — 기본 7일치 수집. 초기 적재 시 --start --end 필수 지정"
        )
        start_dt, end_dt = get_date_range(days_back=7)

    logger.info("======= 나라장터 수집 배치 시작 =======")
    logger.info(f"기간: {start_dt} ~ {end_dt} / STEP: {args.step}")

    if args.step in ("all", "1"):
        collect_bid_list(start_dt, end_dt)

    if args.step in ("all", "2"):
        collect_bsis_amount()

    if args.step in ("all", "3"):
        collect_open_result(start_dt, end_dt)

    if args.step in ("all", "4"):
        if not args.start or not args.end:
            logger.error("STEP4는 --start --end 필수")
        else:
            collect_plnprc(start_dt, end_dt)

    logger.info("======= 배치 종료 =======")
