import requests
import urllib
from bs4 import BeautifulSoup
DEBUG=False
def request(endpoint, params = None):
    headers = {}
    domain = "http://10.72.66.197:9081"
    path = "/wso2wsas/services/IVRService/"
    url = f"{domain}{path}{endpoint}"
    if params:
        url += f"?{urllib.parse.urlencode(params)}"
    response = requests.get(url,headers=headers)
    if DEBUG:
        print(f"{response.request.method} -- {response.url}\n",f"{response.text}")
    bs = BeautifulSoup(response.text, features="lxml")
    obj = bs.find("ns:return")
    if obj:
        result = bs.find("ns:return").text
        return result
    else:
        return False

def query(endpoint='users', cert_no=None, phone_no=None):
    if cert_no:
        result = request(endpoint, {"tel": cert_no})
    else:
        result = request(endpoint, {"tel": phone_no})
    if DEBUG:
        print(f"\n{result}")
    return result
    
# def query(endpoint='users', cert_no=None, phone_no=None):
#     if cert_no == "长沙县" or phone_no == "长沙县":
#         return False
#     if cert_no == "15012345678" or phone_no == "15012345678":
#         return False
#     return f"{endpoint} cert_no={cert_no}, phone_no={phone_no}"

if __name__ == "__main__":
    DEBUG=True
    query("custInformation", 87971551)
    query("orderInfoQuery", 87971551)
    query("custMgrQuery", 87971551)
    query("custInfoQuery", 87971551)
