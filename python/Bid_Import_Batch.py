'''
    입찰공고 목록 API Import
'''
import os
import sys
import re
import requests
from bs4 import BeautifulSoup
import pymysql
from datetime import datetime, timedelta

exec(open('C:\\xampp\\htdocs\\snsbid\\python\\public_db.py', encoding='utf-8').read())

# DB 접속
mydb = pymysql.connect(host=server_ip, port=3306, db=server_db,
                       user=server_user, passwd=server_pass, charset='utf8', autocommit=True)
db_cursor = db_conn()

def Str2Int(para):
    if para == '' or para is None:
        return 0
    try:
        return int(para)
    except:
        return 0

def safe_text(item, tag, default=''):
    el = item.find(tag)
    if el is None or el.text is None:
        return default
    return el.text.strip()

def safe_date(text, length=10):
    if not text:
        return ''
    return text[:length]

def escape_sql(text):
    if not text:
        return ''
    return text.replace("'", "''")

def get_item_int(item, tag):
    el = item.find(tag)
    if el is None or el.text is None or el.text.strip() == '':
        return 0
    try:
        return int(el.text.strip())
    except:
        return 0

# 기초금액, 순공사원가, A값 API
def bid_Crawing(bid_no, bid_seq):
    api_key2 = '1n3WT%2BGYJGBA7V30qucc26fPsR%2BCVb51GHwG%2BtZFKRtnpYRk3T%2FtbmafOvzkDP%2BAbE867T6jzgYFfeAy51aMSQ%3D%3D'
    result = [-1, -1, -1]
    url = ('http://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoCnstwkBsisAmount'
           '?inqryDiv=2&pageNo=1&numOfRows=10&ServiceKey=' + api_key2 + '&bidNtceNo=' + bid_no)
    print('Value API : ', url)
    try:
        response = requests.get(url, timeout=10)
        if int(response.status_code) == 200:
            soup = BeautifulSoup(response.content, 'lxml-xml')
            if soup.find('totalCount'):
                for item in soup.findAll('item'):
                    bssamt_el = item.find('bssamt')
                    purcnst_el = item.find('bssAmtPurcnstcst')
                    print('기초금액 : ', bssamt_el.text if bssamt_el else '')
                    print('순공사원가 : ', purcnst_el.text if purcnst_el else '')

                    bssamt                = get_item_int(item, 'bssamt')
                    bssAmtPurcnstcst      = get_item_int(item, 'bssAmtPurcnstcst')
                    npnInsrprm            = get_item_int(item, 'npnInsrprm')
                    mrfnHealthInsrprm     = get_item_int(item, 'mrfnHealthInsrprm')
                    rtrfundNon            = get_item_int(item, 'rtrfundNon')
                    odsnLngtrmrcprInsrprm = get_item_int(item, 'odsnLngtrmrcprInsrprm')
                    sftyMngcst            = get_item_int(item, 'sftyMngcst')
                    sftyChckMngcst        = get_item_int(item, 'sftyChckMngcst')
                    qltyMngcst            = get_item_int(item, 'qltyMngcst')

                    result[0] = bssamt
                    result[1] = bssAmtPurcnstcst
                    result[2] = (npnInsrprm + mrfnHealthInsrprm + rtrfundNon +
                                 odsnLngtrmrcprInsrprm + sftyMngcst + sftyChckMngcst)
                    qltyYn = item.find('qltyMngcstAObjYn')
                    if qltyYn and qltyYn.text and qltyYn.text.strip() == 'Y':
                        result[2] += qltyMngcst
    except Exception as e:
        print(f'bid_Crawing 오류: {e}')

    return result


page = 1
api_key = '1n3WT%2BGYJGBA7V30qucc26fPsR%2BCVb51GHwG%2BtZFKRtnpYRk3T%2FtbmafOvzkDP%2BAbE867T6jzgYFfeAy51aMSQ%3D%3D'

# 시작일자 조회
start_date = ''
sql = "CALL svr_batch_Get_bidDate();"
rows = sql_result(sql)
if len(rows) > 0:
    start_date = rows[0]['pdate']

if len(start_date) > 0:
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.now()
    delta = timedelta(days=1)

    current_date = start_date
    is_error = 0
    print(current_date, end_date)

    while current_date <= end_date:
        pdate = current_date.strftime("%Y%m%d")
        bid_count = 0

        # Batch 시작 저장
        ssn = 0
        sql = "CALL svr_batch_Start();"
        rows = sql_result(sql)
        ssn = rows[0]['ret']

        numOfRows = 100
        page = 1
        pageNo = 0
        totalCount = 0

        while True:
            url = ('http://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoCnstwk'
                   '?numOfRows=' + str(numOfRows) +
                   '&pageNo=' + str(page) +
                   '&ServiceKey=' + api_key +
                   '&inqryDiv=1&inqryBgnDt=' + pdate + '0000' +
                   '&inqryEndDt=' + pdate + '2359')

            try:
                response = requests.get(url, timeout=10)
            except Exception as e:
                print(f'API 요청 오류: {e}')
                is_error = 1
                break

            if int(response.status_code) == 200:
                soup = BeautifulSoup(response.content, 'lxml-xml')
                if soup.find('totalCount'):
                    pageNo = int(soup.find('pageNo').text)
                    totalCount = int(soup.find('totalCount').text)

                    for item in soup.findAll('item'):
                        is_cancel = 1 if safe_text(item, 'ntceKindNm') == '취소' else 0
                        print('공고번호 :', safe_text(item, 'bidNtceNo'), ' ', safe_text(item, 'ntceKindNm'))

                        bidNtceNo     = safe_text(item, 'bidNtceNo')
                        bidNtceOrd    = safe_text(item, 'bidNtceOrd')
                        bidNtceDt     = safe_date(safe_text(item, 'bidNtceDt'))
                        bidNtceNm     = escape_sql(safe_text(item, 'bidNtceNm'))
                        opengDt       = safe_date(safe_text(item, 'opengDt'))
                        bidNtceDtlUrl = safe_text(item, 'bidNtceDtlUrl')
                        dminsttNm     = escape_sql(safe_text(item, 'dminsttNm'))

                        lwlt_raw = safe_text(item, 'sucsfbidLwltRate')
                        sucsfbidLwltRate = float(lwlt_raw) if lwlt_raw else 0.0

                        bdgt_raw = safe_text(item, 'bdgtAmt')
                        bdgtAmt = int(bdgt_raw) if bdgt_raw else 0

                        try:
                            sql = ("CALL api_bid_insert('{}', '{}', '{}', '{}', '{}', '{}', {}, '{}', {}, {});".format(
                                bidNtceNo, bidNtceOrd, bidNtceDt,
                                bidNtceNm, opengDt, bidNtceDtlUrl,
                                sucsfbidLwltRate, dminsttNm, bdgtAmt, is_cancel))
                            rows = sql_result(sql)
                            bsn = rows[0]['ret']
                        except Exception as e:
                            print(f'SP Error [{e}]')
                            print(f'SQL: {sql}')
                            bsn = 0

                        if bsn > 0:
                            craw_result = bid_Crawing(bidNtceNo, bidNtceOrd)
                            if craw_result[0] >= 0:
                                try:
                                    sql = "CALL api_bid_update({}, {}, {}, {});".format(
                                        bsn, craw_result[0], craw_result[1], craw_result[2])
                                    rows = sql_result(sql)
                                except Exception as e:
                                    print(f'api_bid_update 오류: {e}')
                            bid_count += 1
                        else:
                            print(f'  → 중복 스킵 (bsn=0)')

            else:
                is_error = 1
                print('API Error ', url)

            if (numOfRows * pageNo) >= totalCount or totalCount == 0:
                break
            else:
                page += 1

        # 작업 결과 저장
        if is_error == 0:
            sql = "CALL svr_batch_Update({}, {}, '{}', '{}');".format(
                ssn, 1, current_date.strftime("%Y-%m-%d"), str(bid_count) + '개의 입찰공고를 저장')
            rows = sql_result(sql)

        current_date += delta

mydb.close()