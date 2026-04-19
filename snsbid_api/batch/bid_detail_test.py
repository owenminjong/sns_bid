import requests, ssl, os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()
import urllib3
from requests.adapters import HTTPAdapter

urllib3.disable_warnings()

PHPSESSID = os.getenv("IGUNSUL_PHPSESSID", "")
SESSION_IGUNSUL = os.getenv("IGUNSUL_SESSION", "")

class SSLAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        import ssl
        ctx = ssl.create_default_context()
        ctx.set_ciphers("DEFAULT:@SECLEVEL=1")
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        kwargs["ssl_context"] = ctx
        super().init_poolmanager(*args, **kwargs)

session = requests.Session()
session.mount("https://", SSLAdapter())
session.cookies.set("PHPSESSID", PHPSESSID, domain=".igunsul.net")
session.cookies.set("session_igunsul", SESSION_IGUNSUL, domain=".igunsul.net")

url = "https://www.igunsul.net/detail_bid/index/bid10010682"
resp = session.get(url, verify=False, timeout=30)
resp.encoding = "utf-8"

with open("debug_bid_detail.html", "w", encoding="utf-8") as f:
    f.write(resp.text)
print("저장완료 - debug_bid_detail.html 열어봐")