'''
    입찰공고 목록 API - A값 Upate
    
'''
import os
import sys
import re
import requests
from bs4 import BeautifulSoup
import pymysql
from datetime import datetime, timedelta

exec(open('/home/snsbid/python/public_db.py', encoding='utf-8').read())
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

#api_key ='lLKaCvcFJIih35CZK%2B1QMDTOJJdWEfl5qkzTtRYubhEfDkJY4GbJTp1hA0TuYXIm0gaB%2B1eM32q3ZFBv%2B14qPA%3D%3D'
api_key ='o4Ur22E710dOJBYYqzBWaSbcXJyaTOaFgawVrRX9TbPyZx6cK4nPgjlI%2B8Yv7mbdkkx0jopil7iPXP3SDPzhSQ%3D%3D'

# 기초금액, 순공사원가, A값 크롤링 함수 (최대 10회 크롤링)
def bid_Crawing(bid_no, bid_seq):
    result = [-1, -1, -1]      # 기초금액, 순공사원가, A값
    #http://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoCnstwkBsisAmount?inqryDiv=1&inqryBgnDt=201605010000&inqryEndDt=201605052359&pageNo=1&numOfRows=10&ServiceKey=lLKaCvcFJIih35CZK%2B1QMDTOJJdWEfl5qkzTtRYubhEfDkJY4GbJTp1hA0TuYXIm0gaB%2B1eM32q3ZFBv%2B14qPA%3D%3D
    url = 'http://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoCnstwkBsisAmount?inqryDiv=2&pageNo=1&numOfRows=10&ServiceKey='+api_key+'&bidNtceNo='+bid_no
    response = requests.get(url)
    if int(response.status_code) == 200:
        soup = BeautifulSoup(response.content, 'lxml-xml')
        if soup.find('totalCount'):
            pageNo = int(soup.find('pageNo').text)
            totalCount = int(soup.find('totalCount').text)
            for item in soup.findAll('item'):
                '''
                print('기초금액 : ',item.find('bssamt').text)     
                print('순공사원가 : ',item.find('bssAmtPurcnstcst').text)     
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
    #break

sql = "CALL api_bid_A_List();"
rows = sql_result(sql)   
if len(rows) > 0 :
    # 일자별 Batch log 처리
    #print('length :', len(rows))
    for ii in range(0, len(rows)):
        #print('ii :', ii)
        print( rows[ii]['bidNtceNo']+' - '+rows[ii]['bidNtceOrd'])
        bsn = int(rows[ii]['bsn'])
        craw_result = bid_Crawing(rows[ii]['bidNtceNo'], rows[ii]['bidNtceOrd'])
        if craw_result[0] >= 0:
            # 크롤링 결과 저장
            try:
                sql = "CALL api_bid_update({}, {}, {}, {});".format( \
                        bsn, craw_result[0], craw_result[1], craw_result[2])
                #print(sql)                  
                rows2 = sql_result(sql)   
                print(bsn, craw_result[0], craw_result[1], craw_result[2])
            except:
                print('SP Error ', sql)
                

mydb.close()




