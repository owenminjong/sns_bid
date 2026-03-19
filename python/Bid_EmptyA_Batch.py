'''
    기초금액, A값 누락 Batch API Import
    
'''
import os
import sys
import re
import requests
from bs4 import BeautifulSoup
import pymysql
from datetime import datetime, timedelta

exec(open('C:\\xampp\\htdocs\\snsbid\\python\\public_db.py', encoding='utf-8').read())
#exec(open('public_db.py', encoding='utf-8').read())

# DB 접속
mydb = pymysql.connect(host=server_ip, port=3306, db=server_db,
                user=server_user, passwd=server_pass, charset='utf8', autocommit=True)
db_cursor = db_conn()

def Str2Int(para):
    if para == '':
        return  0
    else:
        return int(para)

# 기초금액, 순공사원가, A값 API
def bid_Crawing(bid_no, bid_seq):
    api_key2 = '1n3WT%2BGYJGBA7V30qucc26fPsR%2BCVb51GHwG%2BtZFKRtnpYRk3T%2FtbmafOvzkDP%2BAbE867T6jzgYFfeAy51aMSQ%3D%3D'
    result = [-1, -1, -1]      # 기초금액, 순공사원가, A값
    #http://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoCnstwkBsisAmount?inqryDiv=1&inqryBgnDt=201605010000&inqryEndDt=201605052359&pageNo=1&numOfRows=10&ServiceKey=lLKaCvcFJIih35CZK%2B1QMDTOJJdWEfl5qkzTtRYubhEfDkJY4GbJTp1hA0TuYXIm0gaB%2B1eM32q3ZFBv%2B14qPA%3D%3D
    url = 'http://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoCnstwkBsisAmount?inqryDiv=2&pageNo=1&numOfRows=10&ServiceKey='+api_key2+'&bidNtceNo='+bid_no
    print('Value API : ', url)
    response = requests.get(url)
    if int(response.status_code) == 200:
        soup = BeautifulSoup(response.content, 'lxml-xml')
        if soup.find('totalCount'):
            pageNo = int(soup.find('pageNo').text)
            totalCount = int(soup.find('totalCount').text)
            for item in soup.findAll('item'):

                
                print('기초금액 : ',item.find('bssamt').text)     
                print('순공사원가 : ',item.find('bssAmtPurcnstcst').text)    
                '''
                print('국민연금 : ',item.find('npnInsrprm').text)     
                print('건강보험 : ',item.find('mrfnHealthInsrprm').text)     
                print('퇴직공제부금비 : ',item.find('rtrfundNon').text)     
                print('노인장기요양보험 : ',item.find('odsnLngtrmrcprInsrprm').text)     
                print('산업안전보건관리비 : ',item.find('sftyMngcst').text)     
                print('안전관리비 : ',item.find('sftyChckMngcst').text)     
                print('품질관리비 : ',item.find('qltyMngcst').text)     
                print('품질관리비A적용여부 : ',item.find('qltyMngcstAObjYn').text)     
                '''
                
                bssamt = Str2Int(item.find('bssamt').text)
                bssAmtPurcnstcst = Str2Int(item.find('bssAmtPurcnstcst').text)
                npnInsrprm = Str2Int(item.find('npnInsrprm').text)
                mrfnHealthInsrprm = Str2Int(item.find('mrfnHealthInsrprm').text)
                rtrfundNon = Str2Int(item.find('rtrfundNon').text)
                odsnLngtrmrcprInsrprm = Str2Int(item.find('odsnLngtrmrcprInsrprm').text)
                sftyMngcst = Str2Int(item.find('sftyMngcst').text)
                sftyChckMngcst = Str2Int(item.find('sftyChckMngcst').text)
                qltyMngcst = Str2Int(item.find('qltyMngcst').text)

                result[0] = bssamt
                result[1] = bssAmtPurcnstcst
                result[2] = npnInsrprm + mrfnHealthInsrprm + rtrfundNon + odsnLngtrmrcprInsrprm + sftyMngcst + sftyChckMngcst
                if item.find('qltyMngcstAObjYn').text =='Y':
                    result[2] += qltyMngcst

    return result

open_count = 0
# 기초금액, A값 누락 자료 조회 (현재일자 기준)
sql = "CALL svr_api_bid_EmptyA_Date();"
rows = sql_result(sql)   
if len(rows) > 0 :
    # 일자별 Batch log 처리
    
    for i in range(0, len(rows)):
        # 낙찰 API
        print(rows[i]['bidNtceNo']+' - '+rows[i]['bidNtceOrd'])
        craw_result = bid_Crawing(rows[i]['bidNtceNo'], rows[i]['bidNtceOrd'])
        if craw_result[0] >= 0:
            try:
                # 크롤링 결과 저장
                sql = "CALL api_bid_update({}, {}, {}, {});".format( \
                        rows[i]['bsn'], craw_result[0], craw_result[1], craw_result[2])
                print(sql)                  
                rows2 = sql_result(sql)   
            except:             
                print('Error SP :', sql)

