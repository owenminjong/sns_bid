'''
    숭늉샘비드
    예측 데이터 생성 -> 예측 모델 생성 Batch
'''
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import pymysql
import os
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler
import joblib

exec(open('public_db.py', encoding='utf-8').read())
# DB 접속
mydb = pymysql.connect(host=server_ip, port=3306, db=server_db,
                user=server_user, passwd=server_pass, charset='utf8', autocommit=True)
db_cursor = db_conn()

# Batch작업 시작 저장
ssn = 0
sql = "CALL svr_batch_Start();"
rows = sql_result(sql)   
ssn = rows[0]['ret']

# 10억미만 
if os.path.exists('sns_train_10.csv'):
    os.remove('sns_train_10.csv')
sql = "call api_bid_train('00000000', '99999999', 1, 1000000000, 0);"
rows = sql_result(sql)   
df = pd.DataFrame(rows)
df.to_csv('sns_train_10.csv', index=False)

# 10억~30억미만 
if os.path.exists('sns_train_30.csv'):
    os.remove('sns_train_30.csv')
sql = "call api_bid_train('00000000', '99999999', 1000000001, 3000000000, 0);"
rows = sql_result(sql)   
df = pd.DataFrame(rows)
df.to_csv('sns_train_30.csv', index=False)

# 30억~50억미만 
if os.path.exists('sns_train_50.csv'):
    os.remove('sns_train_50.csv')
sql = "call api_bid_train('00000000', '99999999', 3000000001, 5000000000, 0);"
rows = sql_result(sql)   
df = pd.DataFrame(rows)
df.to_csv('sns_train_50.csv', index=False)

# 50억초과 
if os.path.exists('sns_train_50up.csv'):
    os.remove('sns_train_50up.csv')
sql = "call api_bid_train('00000000', '99999999', 5000000001, 5000000000000000, 0);"
rows = sql_result(sql)   
df = pd.DataFrame(rows)
df.to_csv('sns_train_50up.csv', index=False)

# 순공사원가 포함
if os.path.exists('sns_train_sun.csv'):
    os.remove('sns_train_sun.csv')
sql = "call api_bid_train('00000000', '99999999', 1, 5000000000000000, 1);"
rows = sql_result(sql)   
df = pd.DataFrame(rows)
df.to_csv('sns_train_sun.csv', index=False)


# 10억미만 모델 생성
data_csv = pd.read_csv('sns_train_10.csv', engine='python', encoding='utf-8')
data_csv['공고번호']=data_csv['공고번호'].apply(lambda x:str(x))
data_csv=data_csv.set_index('공고번호')
train_data = data_csv.drop(['예정가격','순위투찰율'],axis=1)
data_y = train_data['순위금액']
data_x = train_data.drop('순위금액',axis=1)
from sklearn.model_selection import train_test_split
x_train, x_test, y_train, y_test = train_test_split(data_x,data_y,test_size=0.000001,random_state=1004)
rf = RandomForestRegressor(n_estimators=500,min_samples_leaf=3,min_samples_split=10, n_jobs=-1, random_state=1002, criterion='squared_error')
rf.fit(x_train,y_train)
pred_Y=rf.predict(x_test)
joblib.dump(rf, 'sns_random_10.joblib')

# 10~30억미만 모델 생성
data_csv = pd.read_csv('sns_train_30.csv', engine='python', encoding='utf-8')
data_csv['공고번호']=data_csv['공고번호'].apply(lambda x:str(x))
data_csv=data_csv.set_index('공고번호')
train_data = data_csv.drop(['예정가격','순위투찰율'],axis=1)
data_y = train_data['순위금액']
data_x = train_data.drop('순위금액',axis=1)
from sklearn.model_selection import train_test_split
x_train, x_test, y_train, y_test = train_test_split(data_x,data_y,test_size=0.000001,random_state=1004)
rf = RandomForestRegressor(n_estimators=500,min_samples_leaf=3,min_samples_split=10, n_jobs=-1, random_state=1002, criterion='squared_error')
rf.fit(x_train,y_train)
pred_Y=rf.predict(x_test)
joblib.dump(rf, 'sns_random_30.joblib')

# 30~50억미만 모델 생성
data_csv = pd.read_csv('sns_train_50.csv', engine='python', encoding='utf-8')
data_csv['공고번호']=data_csv['공고번호'].apply(lambda x:str(x))
data_csv=data_csv.set_index('공고번호')
train_data = data_csv.drop(['예정가격','순위투찰율'],axis=1)
data_y = train_data['순위금액']
data_x = train_data.drop('순위금액',axis=1)
from sklearn.model_selection import train_test_split
x_train, x_test, y_train, y_test = train_test_split(data_x,data_y,test_size=0.000001,random_state=1004)
rf = RandomForestRegressor(n_estimators=500,min_samples_leaf=3,min_samples_split=10, n_jobs=-1, random_state=1002, criterion='squared_error')
rf.fit(x_train,y_train)
pred_Y=rf.predict(x_test)
joblib.dump(rf, 'sns_random_50.joblib')

# 50억이상 모델 생성
data_csv = pd.read_csv('sns_train_50up.csv', engine='python', encoding='utf-8')
data_csv['공고번호']=data_csv['공고번호'].apply(lambda x:str(x))
data_csv=data_csv.set_index('공고번호')
train_data = data_csv.drop(['예정가격','순위투찰율'],axis=1)
data_y = train_data['순위금액']
data_x = train_data.drop('순위금액',axis=1)
from sklearn.model_selection import train_test_split
x_train, x_test, y_train, y_test = train_test_split(data_x,data_y,test_size=0.000001,random_state=1004)
rf = RandomForestRegressor(n_estimators=500,min_samples_leaf=3,min_samples_split=10, n_jobs=-1, random_state=1002, criterion='squared_error')
rf.fit(x_train,y_train)
pred_Y=rf.predict(x_test)
joblib.dump(rf, 'sns_random_50up.joblib')

# 순공사원가 포함 모델 생성
data_csv = pd.read_csv('sns_train_sun.csv', engine='python', encoding='utf-8')
data_csv['공고번호']=data_csv['공고번호'].apply(lambda x:str(x))
data_csv=data_csv.set_index('공고번호')
train_data = data_csv.drop(['예정가격','순위투찰율'],axis=1)
data_y = train_data['순위금액']
data_x = train_data.drop('순위금액',axis=1)
from sklearn.model_selection import train_test_split
x_train, x_test, y_train, y_test = train_test_split(data_x,data_y,test_size=0.000001,random_state=1004)
rf = RandomForestRegressor(n_estimators=500,min_samples_leaf=3,min_samples_split=10, n_jobs=-1, random_state=1002, criterion='squared_error')
rf.fit(x_train,y_train)
pred_Y=rf.predict(x_test)
joblib.dump(rf, 'sns_random_sun.joblib')

#작업 결과 저장 
current_date = datetime.today().strftime("%Y-%m-%d")
sql = "CALL svr_batch_Update({}, {}, '{}', '{}');".format( \
        ssn, 3, current_date , '예측 모델 파일 생성')
#print(sql)                  
rows = sql_result(sql)   


