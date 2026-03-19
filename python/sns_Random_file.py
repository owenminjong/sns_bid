'''
숭늉샘비드 : 랜덤 프레스트 모델 파일 생성 
'''
import pandas as pd
import numpy as np
import datetime
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler
import joblib

# 학습 Data Load
data_csv = pd.read_csv('sns_train_sun.csv', engine='python', encoding='utf-8')
print('학습 Data Load....')
# 테스트 Data Load
# test_csv = pd.read_csv('sns_train_24_10_A.csv', engine='python', encoding='utf-8')

data_csv['공고번호']=data_csv['공고번호'].apply(lambda x:str(x))
data_csv=data_csv.set_index('공고번호')

#test_csv['공고번호']=test_csv['공고번호'].apply(lambda x:str(x))
#test_csv=test_csv.set_index('공고번호')

train_data = data_csv.drop(['개시일자','예가1','예가2','예가2','예정가격','추정가격','참가수','순위투찰율','사정율','낙찰하한가'],axis=1)
data_y = train_data['순위금액']
data_x = train_data.drop('순위금액',axis=1)

#test_data = test_csv.drop(['개시일자','예가1','예가2','예가2','예정가격','추정가격','참가수','순위투찰율','사정율','낙찰하한가'],axis=1)
#test_y = test_data['순위금액']
#test_x = test_data.drop('순위금액',axis=1)

# train 데이터와 validation 데이터로 분류
from sklearn.model_selection import train_test_split
x_train, x_test, y_train, y_test = train_test_split(data_x,data_y,test_size=0.000001,random_state=1004)
print('train 데이터와 validation 데이터로 분류....')

# 랜덤포레스트 모델 사용
rf = RandomForestRegressor(n_estimators=500,min_samples_leaf=3,min_samples_split=10, n_jobs=-1, random_state=1002, criterion='squared_error')
rf.fit(x_train,y_train)
pred_Y=rf.predict(x_test)
print('오차(log-MSE) : ',np.sum((np.log(pred_Y)-np.log(y_test))**2)/len(x_test))
print('랜덤포레스트 모델 생성....')

# 모델 저장
joblib.dump(rf, 'sns_random_sun.joblib')
print('모델 저장 완료 !!!')
