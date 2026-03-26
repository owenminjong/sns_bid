'''
숭늉샘비드 분석 : 랜덤프레스트 모델
웹 사이트와 연동 예측 결과 반환
2024-12-03
'''
import sys
import pandas as pd
import numpy as np
import datetime
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler
import joblib

def adjust_value(a, b1, b2):
  if a < b1:
    while a < b1:
      a *= 1.002  # 0.2% 증가
    return a
  elif a > b2:
    while a > b2:
      a *= 0.998  # 0.2% 감소
    return a
  else:
    return a  # a가 b1과 b2 사이에 있는 경우 변경 없음


# 외부 인자 
기초금액 = int(sys.argv[1])
A값 = int(sys.argv[2])
하한율 = float(sys.argv[3])
순공사원가 = int(sys.argv[4])

if 순공사원가 > 0:
    data = {
            '공고번호': '00000001', '기초금액': 기초금액, '하한율': 하한율, 'A값': A값, '순공사원가':순공사원가
        }
else:
    data = {
            '공고번호': '00000001', '기초금액': 기초금액, '하한율': 하한율, 'A값': A값
        }
    # DataFrame 생성
df = pd.DataFrame(data,index=[0])
df = df.set_index('공고번호')   

# 모델 불러오기
if 순공사원가 > 0:
    loaded_model = joblib.load('../../../python/sns_random_sun.joblib')
else:
    if 기초금액<=1000000000:
        loaded_model = joblib.load('../../../python/sns_random_10.joblib')
    elif 기초금액<=3000000000:
        loaded_model = joblib.load('../../../python/sns_random_30.joblib')
    elif 기초금액<=5000000000:
        loaded_model = joblib.load('../../../python/sns_random_50.joblib')
    else:
        loaded_model = joblib.load('../../../python/sns_random_50up.joblib')

# 테스트 데이터에 대한 예측 수행
predictions = loaded_model.predict(df)
rst = int(predictions[0])

# 예측금액은 기초금액의 87~89% 내에 있어야 함.
rst = adjust_value(rst, int(기초금액*0.87), int(기초금액*0.89))

print(int(rst))
