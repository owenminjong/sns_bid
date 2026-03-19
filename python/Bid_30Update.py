'''
    입찰공고
	30분 주기로
	1. 100억이상 낙찰하한율 Update
	2. 당일 개찰일자의 개찰 시간 Update 
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
    api_key2 = 'IpFyUrZ%2BJhBLmL5gOgjYwipr7VI7NmMSKEinqBcZfCthDoEwtRDG0cv0mYVArvMdRZWPyTFcpwFn6lyG9LFEbw%3D%3D'
    result = [-1, -1, -1]      # 기초금액, 순공사원가, A값
    #http://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoCnstwkBsisAmount?inqryDiv=1&inqryBgnDt=201605010000&inqryEndDt=201605052359&pageNo=1&numOfRows=10&ServiceKey=lLKaCvcFJIih35CZK%2B1QMDTOJJdWEfl5qkzTtRYubhEfDkJY4GbJTp1hA0TuYXIm0gaB%2B1eM32q3ZFBv%2B14qPA%3D%3D
    url = 'http://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoCnstwkBsisAmount?inqryDiv=2&pageNo=1&numOfRows=10&ServiceKey='+api_key2+'&bidNtceNo='+bid_no
    #print('Value API : ', url)
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
    #break

page = 1
#api_key ='lLKaCvcFJIih35CZK%2B1QMDTOJJdWEfl5qkzTtRYubhEfDkJY4GbJTp1hA0TuYXIm0gaB%2B1eM32q3ZFBv%2B14qPA%3D%3D'
api_key ='o4Ur22E710dOJBYYqzBWaSbcXJyaTOaFgawVrRX9TbPyZx6cK4nPgjlI%2B8Yv7mbdkkx0jopil7iPXP3SDPzhSQ%3D%3D'

start_date = ''
sql = "CALL api_bid_30Update_List();"
rows = sql_result(sql)   
if len(rows) > 0 :
    for i in range(0, len(rows)):
        url = 'http://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoCnstwk?inqryDiv=2&numOfRows=1&pageNo=1&ServiceKey='+api_key+'&bidNtceNo='+rows[i]['bidNtceNo']
        #print(url)
        response = requests.get(url)
        if int(response.status_code) == 200:
            soup = BeautifulSoup(response.content, 'lxml-xml')
            if soup.find('totalCount'):
                pageNo = int(soup.find('pageNo').text)
                totalCount = int(soup.find('totalCount').text)
                for item in soup.findAll('item'):
                    print(rows[i]['bidNtceNo'], '낙찰하한율 : ',item.find('sucsfbidLwltRate').text) 
                    print('개찰일시 : ',item.find('opengDt').text)     
                    if item.find('sucsfbidLwltRate').text == '':
                        sucsfbidLwltRate = 0
                    else:
                        sucsfbidLwltRate = float(item.find('sucsfbidLwltRate').text)

                    # 개찰일자-시각 저장
                    sql = "CALL api_bid_update3({}, '{}');".format( \
                                rows[i]['bsn'], item.find('opengDt').text)
                    print(sql)
                    rows2 = sql_result(sql)   

                    # 기초금액, 순공사원가, A값 크롤링
                    craw_result = bid_Crawing(item.find('bidNtceNo').text, item.find('bidNtceOrd').text)
                    if craw_result[0] >= 0:
                        # 크롤링 결과 저장
                        sql = "CALL api_bid_update2({}, {}, {}, {}, {});".format( \
                                 rows[i]['bsn'], craw_result[0], craw_result[1], craw_result[2], sucsfbidLwltRate)
                        print(sql)
                        rows2 = sql_result(sql)   

                    print(sql)
                    rows2 = sql_result(sql)   

mydb.close()




