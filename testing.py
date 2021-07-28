import scheduleme   
import request_interception
from icecream import ic

def test_url_builder() -> str: 
    helper = scheduleme.Helper()
    url = helper.url_builder("20333W", "winter", "2022")
    #ic(url)
    return url

def test_intercept_request(url: str) -> str:
    data = request_interception.intercept_request(url)
    #ic(data)
    return data

def test_dropdown(url: str) -> list:
    testlist = request_interception.click_dropdown(url, [])
    return testlist

def main():
    url = test_url_builder()
    #TODO: This url needs to be gotten programatiicaly
    #testlist = test_dropdown("https://scheduleme.wlu.ca/vsb/criteria.jsp?access=0&lang=en&tip=1&page=criteria&scratch=0&advice=0&term=202105&sort=none&filters=iiiiiiiiii&bbs=&ds=&cams=C_K_T_V_W_Z_CC_G_X_Y_MC&locs=any&isrts=")
    data = test_intercept_request(url)
    tester = scheduleme.Course(data)
    tester.parse()
    
main()