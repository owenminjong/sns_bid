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
    #break

    '''
    url = "https://www.g2b.go.kr:8081/ep/price/baseamt/selectBaseAmtDtlPopup.do?taskClCd=3&bidno="+bid_no+"&bidseq="+bid_seq
    #print(url)
    result = [-1, -1, -1]      # 기초금액, 순공사원가, A값

    for i in range(1, 10):
        response = requests.get(url)
        기초금액 =0
        A값 = 0
        순공사원가 = 0
        ischk = 0    
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            element = soup.find(class_='section')
            if element is not None:
                element = element.find_all('tr')
                for sub_element in element:
                    if 'A 금액' in str(sub_element):
                        element2 = sub_element.find_all('span')
                        for sub_element2 in element2:
                            if '원' in str(sub_element2):
                                stmp = str(sub_element2)
                                stmp = stmp.replace('<span>','')
                                stmp = stmp.replace('</span>','')
                                stmp = stmp.replace(' ','')
                                stmp = stmp.replace(',','')
                                stmp = stmp.replace('원','')
                                if stmp.isdigit():
                                    # A값 있음 (flag=1)    
                                    ischk = 1
                                    A값 = int(stmp)
                                    #print('A-Value => ', stmp)
                                    #sql = "CALL org_inbid_A_Save('{}', {}, {}, {});".format( \
                                    #            rows[row_idx]['공고번호'], int(rows[row_idx]['공고차수']), int(stmp), 1)
                                    #rows2 = sql_result(sql)   
                                    #print(int(stmp))                
                        break
                    elif  '순공사원가' in str(sub_element):       
                        element2 = sub_element.find_all('td')
                        for sub_element2 in element2:
                            if '원' in str(sub_element2):
                                html_content = str(sub_element2)
                                soup = BeautifulSoup(html_content, 'html.parser')
                                td_text = soup.find('td').get_text(strip=True)
                                price = re.search(r'\d{1,3}(,\d{3})*', str(td_text)).group()
                                #print('Price => ', price)
                                #print(sub_element2)
                                #stmp = str(sub_element2)
                                price = price.replace('<span>','')
                                price = price.replace('</span>','')
                                price = price.replace(' ','')
                                price = price.replace(',','')
                                price = price.replace('원','')
                                if price.isdigit():
                                    # 순공사원가
                                    ischk = 1
                                    순공사원가 = int(price)
                                    #print('순공사원가 => ', price)
                                    #sql = "CALL org_inbid_Cost_Save('{}', {}, {}, {});".format( \
                                    #            rows[row_idx]['공고번호'], int(rows[row_idx]['공고차수']), int(price), 1)
                                    #rows2 = sql_result(sql)   

                    elif  '예비가격 기초금액' in str(sub_element):     
                        element2 = sub_element.find_all('td')
                        for sub_element2 in element2:
                            if '원' in str(sub_element2):
                                html_content = str(sub_element2)
                                soup = BeautifulSoup(html_content, 'html.parser')
                                td_text = soup.find('td').get_text(strip=True)
                                price = re.search(r'\d{1,3}(,\d{3})*', str(td_text)).group()
                                #print('기초금액 : ', price)
                                #print('Price => ', price)
                                #print(sub_element2)
                                #stmp = str(sub_element2)
                                price = price.replace('<span>','')
                                price = price.replace('</span>','')
                                price = price.replace(' ','')
                                price = price.replace(',','')
                                price = price.replace('원','')
                                #print('기초금액 : ', price)
                                if price.isdigit():
                                    # 기초금액
                                    ischk = 1
                                    기초금액 = int(price) 

            result[0] = 기초금액
            result[1] = 순공사원가
            result[2] = A값
            return result
            break
'''

page = 1
#api_key ='lLKaCvcFJIih35CZK%2B1QMDTOJJdWEfl5qkzTtRYubhEfDkJY4GbJTp1hA0TuYXIm0gaB%2B1eM32q3ZFBv%2B14qPA%3D%3D'
api_key ='o4Ur22E710dOJBYYqzBWaSbcXJyaTOaFgawVrRX9TbPyZx6cK4nPgjlI%2B8Yv7mbdkkx0jopil7iPXP3SDPzhSQ%3D%3D'

# 정상적으로 저장된 입찰공고일자의 익일을 조회 
start_date = ''
sql = "CALL svr_batch_Get_bidDate();"
rows = sql_result(sql)   
if len(rows) > 0 :
    start_date = rows[0]['pdate']

if len(start_date) > 0:
    #
    #   입찰 공고 조회 API (기간별)
    #

    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    
    # 현재 날짜
    end_date = datetime.now()
    delta = timedelta(days=1)

    current_date = start_date
    is_error = 0
    print(current_date, end_date)
    while current_date <= end_date:
        pdate = current_date.strftime("%Y%m%d")
        bid_count = 0
        # Batch작업 시작 저장
        ssn = 0
        sql = "CALL svr_batch_Start();"
        rows = sql_result(sql)   
        ssn = rows[0]['ret']

        #
        #   일자별 입찰 공고 조회
        #
        numOfRows = 100  
        page = 1
        pageNo = 0
        totalCount = 0
        while True:
            #if pdate!='20241213':
            #    break

            #Before url = 'http://apis.data.go.kr/1230000/BidPublicInfoService05/getBidPblancListInfoCnstwkPPSSrch02?numOfRows='+str(numOfRows)+'&pageNo='+str(page)+'&ServiceKey=lLKaCvcFJIih35CZK%2B1QMDTOJJdWEfl5qkzTtRYubhEfDkJY4GbJTp1hA0TuYXIm0gaB%2B1eM32q3ZFBv%2B14qPA%3D%3D&inqryDiv=1&inqryBgnDt='+pdate+'0000'+'&inqryEndDt='+pdate+'2359'
            #http://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoCnstwk?inqryDiv=1&inqryBgnDt=201705010000&inqryEndDt=201705012359&pageNo=1&numOfRows=10&ServiceKey=lLKaCvcFJIih35CZK%2B1QMDTOJJdWEfl5qkzTtRYubhEfDkJY4GbJTp1hA0TuYXIm0gaB%2B1eM32q3ZFBv%2B14qPA%3D%3D
            url = 'http://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoCnstwk?numOfRows='+str(numOfRows)+'&pageNo='+str(page)+'&ServiceKey='+api_key+'&inqryDiv=1&inqryBgnDt='+pdate+'0000'+'&inqryEndDt='+pdate+'2359'
            #print(url)
            #print(ssn, '  ', current_date)
            response = requests.get(url)
            if int(response.status_code) == 200:
                soup = BeautifulSoup(response.content, 'lxml-xml')
                if soup.find('totalCount'):
                    pageNo = int(soup.find('pageNo').text)
                    totalCount = int(soup.find('totalCount').text)
                    for item in soup.findAll('item'):
                        #print('공고번호 : ',item.find('bidNtceNo').text, '  ', item.find('ntceKindNm').text)     
                        # 취소여부
                        is_cancel = 0
                        if item.find('ntceKindNm').text=='취소':
                            is_cancel = 1

                        #if is_cancel == 0:    
                        print('공고번호 : ',item.find('bidNtceNo').text, '  ', item.find('ntceKindNm').text)     
                        #print('공고일련 : ',item.find('bidNtceOrd').text)     
                        #print('공고명 : ',item.find('bidNtceNm').text)     
                        #print('개시일자 : ',item.find('bidNtceDt').text)     
                        #print('개찰일시 : ',item.find('opengDt').text)     
                        #print('URL : ',item.find('bidNtceDtlUrl').text)     
                        #print('낙찰하한율 : ',item.find('sucsfbidLwltRate').text)     
                        #print('수요기관 : ',item.find('dminsttNm').text)
                        #print('추정가격 : ',item.find('bdgtAmt').text)

                        bidNtceNm = item.find('bidNtceNm').text 
                        bidNtceNm = bidNtceNm.replace("'","")    
                        if item.find('sucsfbidLwltRate').text == '':
                            sucsfbidLwltRate = 0
                        else:
                            sucsfbidLwltRate = float(item.find('sucsfbidLwltRate').text)
                        if item.find('bdgtAmt').text == '':
                            bdgtAmt = 0
                        else:
                            bdgtAmt = int(item.find('bdgtAmt').text)

                        try:
                            sql = "CALL api_bid_insert('{}', '{}', '{}', '{}', '{}', '{}', {}, '{}', {}, {});".format( \
                                    item.find('bidNtceNo').text, item.find('bidNtceOrd').text, item.find('bidNtceDt').text, \
                                    bidNtceNm, item.find('opengDt').text, item.find('bidNtceDtlUrl').text, \
                                    sucsfbidLwltRate, item.find('dminsttNm').text, bdgtAmt, is_cancel)
                            #print(sql)                  
                            rows = sql_result(sql)   
                            bsn = rows[0]['ret']
                            #print(sql)
                        except:
                            print('SP Error ', sql)
                            bsn = 0
                        
                        if bsn > 0:    
                            # 기초금액, 순공사원가, A값 크롤링
                            craw_result = bid_Crawing(item.find('bidNtceNo').text, item.find('bidNtceOrd').text)
                            if craw_result[0] >= 0:
                                # 크롤링 결과 저장
                                sql = "CALL api_bid_update({}, {}, {}, {});".format( \
                                        bsn, craw_result[0], craw_result[1], craw_result[2])
                                #print(sql)                  
                                rows = sql_result(sql)   
                                
                            
                            bid_count += 1

            else:
                is_error = 1
                print('API Error ', url)
                #print('API 에러['+str(response)+']')

            if (numOfRows*pageNo) > totalCount or totalCount==0:
                break
            else:
                page += 1

        # 작업 결과 저장
        if is_error == 0:
            sql = "CALL svr_batch_Update({}, {}, '{}', '{}');".format( \
                    ssn, 1, current_date.strftime("%Y-%m-%d"), str(bid_count)+'개의 입찰공고를 저장')
            #print(sql)                  
            rows = sql_result(sql)   

        current_date += delta

mydb.close()




