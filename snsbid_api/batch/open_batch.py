'''
    개찰 결과 저장 Batch API Import
    
'''
import os
import sys
import re
import requests
from bs4 import BeautifulSoup
import pymysql
from datetime import datetime, timedelta

exec(open('/python/public_db.py', encoding='utf-8').read())
#exec(open('public_db.py', encoding='utf-8').read())

# DB 접속
mydb = pymysql.connect(host=server_ip, port=3306, db=server_db,
                user=server_user, passwd=server_pass, charset='utf8', autocommit=True)
db_cursor = db_conn()

#api_key ='lLKaCvcFJIih35CZK%2B1QMDTOJJdWEfl5qkzTtRYubhEfDkJY4GbJTp1hA0TuYXIm0gaB%2B1eM32q3ZFBv%2B14qPA%3D%3D'
api_key ='1n3WT%2BGYJGBA7V30qucc26fPsR%2BCVb51GHwG%2BtZFKRtnpYRk3T%2FtbmafOvzkDP%2BAbE867T6jzgYFfeAy51aMSQ%3D%3D'

def api_fixpay(bid_no):
     #
     #  예정 가격 반환
     #
    api_key2 = '1n3WT%2BGYJGBA7V30qucc26fPsR%2BCVb51GHwG%2BtZFKRtnpYRk3T%2FtbmafOvzkDP%2BAbE867T6jzgYFfeAy51aMSQ%3D%3D'
    #Before url = "http://apis.data.go.kr/1230000/ScsbidInfoService01/getOpengResultListInfoCnstwkPreparPcDetail01?numOfRows=100&pageNo=1&ServiceKey="+api_key+"&inqryDiv=2&bidNtceNo="+bid_no
    #http://apis.data.go.kr/1230000/as/ScsbidInfoService/getOpengResultListInfoCnstwkPreparPcDetail?inqryDiv=2&bidNtceNo=20160320372&pageNo=1&numOfRows=15&ServiceKey=lLKaCvcFJIih35CZK%2B1QMDTOJJdWEfl5qkzTtRYubhEfDkJY4GbJTp1hA0TuYXIm0gaB%2B1eM32q3ZFBv%2B14qPA%3D%3D
    url = "http://apis.data.go.kr/1230000/as/ScsbidInfoService/getOpengResultListInfoCnstwkPreparPcDetail?numOfRows=100&pageNo=1&ServiceKey="+api_key2+"&inqryDiv=2&bidNtceNo="+bid_no
    is_error = 0
    plnprc = 0
    try:
        #print("예정가격 "+ url)
        response = requests.get(url)
        if int(response.status_code) == 200:
            soup = BeautifulSoup(response.content, 'lxml-xml')
            if soup.find('totalCount'):
                pageNo = int(soup.find('pageNo').text)
                totalCount = int(soup.find('totalCount').text)
                if totalCount > 0:
                        item_count = 0    
                        for item in soup.findAll('item'):
                            item_count += 1

                            if item_count > 1:
                                    break
                            
                            #print('예정가격 : ',item.find('plnprc').text)     
                            #print('낙찰금액 : ',item.find('sucsfbidAmt').text)     
                            #print('낙찰율 : ',item.find('sucsfbidRate').text)     
                            plnprc = int(float(item.find('plnprc').text))
                            return plnprc 
    except:
        print('Error!!!')
        is_error = 1    


# Batch작업 시작 저장
ssn = 0
sql = "CALL svr_batch_Start();"
rows = sql_result(sql)   
ssn = rows[0]['ret']

open_count = 0
# 미개찰자료 조회 (현재일자 기준)
sql = "CALL svr_api_bid_openDate();"
rows = sql_result(sql)   
if len(rows) > 0 :
    # 일자별 Batch log 처리
    
    for i in range(0, len(rows)):
        # 낙찰 API
        print(rows[i]['bidNtceNo']+' - '+rows[i]['bidNtceOrd'])
        #Before url = "http://apis.data.go.kr/1230000/ScsbidInfoService01/getScsbidListSttusCnstwk01?numOfRows=10&pageNo=1&ServiceKey="+api_key+"&inqryDiv=4&bidNtceNo="+rows[i]['bidNtceNo']
        #http://apis.data.go.kr/1230000/as/ScsbidInfoService/getOpengResultListInfoOpengCompt?bidNtceNo=20160501003&bidNtceOrd=00&bidClsfcNo=0&rbidNo=0&pageNo=1&numOfRows=10&ServiceKey=lLKaCvcFJIih35CZK%2B1QMDTOJJdWEfl5qkzTtRYubhEfDkJY4GbJTp1hA0TuYXIm0gaB%2B1eM32q3ZFBv%2B14qPA%3D%3D
        url ="http://apis.data.go.kr/1230000/as/ScsbidInfoService/getOpengResultListInfoOpengCompt?numOfRows=10&pageNo=1&ServiceKey="+api_key+"&bidNtceNo="+rows[i]['bidNtceNo']+'&bidNtceOrd='+rows[i]['bidNtceOrd']
        print(url)
        is_error = 0
        try:
            response = requests.get(url)
            if int(response.status_code) == 200:
                soup = BeautifulSoup(response.content, 'lxml-xml')
                if soup.find('totalCount'):
                    pageNo = int(soup.find('pageNo').text)
                    totalCount = int(soup.find('totalCount').text)
                    if totalCount > 0:
                            item_count = 0    
                            for item in soup.findAll('item'):
                                item_count += 1

                                if item_count > 1:
                                     break
                                bsn = int(rows[i]['bsn'])
                                print('업체명 : ',item.find('prcbdrNm').text)     
                                print('낙찰금액 : ',item.find('bidprcAmt').text)     
                                #print('낙찰율 : ',item.find('bidprcrt').text)     
                                plnprc = api_fixpay(rows[i]['bidNtceNo'])

                                try:
                                    sql = "CALL api_bid_Openupdate({}, '{}', {}, {}, {});".format( \
                                            bsn, item.find('prcbdrNm').text, item.find('bidprcAmt').text, item.find('bidprcrt').text, plnprc)
                                    print(sql)                  
                                    rows2 = sql_result(sql)   
                                    open_count += 1
                                except:
                                    print('SP Error ', sql)
             
        except:
            print('Error~~')
            is_error = 1    

current_date = datetime.today().strftime("%Y-%m-%d")
sql = "CALL svr_batch_Update({}, {}, '{}', '{}');".format( \
        ssn, 2, current_date , str(open_count)+'개의 개찰정보를 저장')
#print(sql)                  
rows = sql_result(sql)   

