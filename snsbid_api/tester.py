python -c "
import requests
from dotenv import load_dotenv
import os
load_dotenv()
API_KEY = os.getenv('NARA_API_KEY')
params = {
    'serviceKey': API_KEY,
    'type': 'json',
    'inqryDiv': '1',
    'inqryBgnDt': '202501010000',
    'inqryEndDt': '202503312359',
    'pageNo': 1,
    'numOfRows': 5,
}
res = requests.get('https://apis.data.go.kr/1230000/as/ScsbidInfoService/getOpengResultListInfoCnstwk', params=params)
print(res.status_code)
print(res.text[:3000])
"
