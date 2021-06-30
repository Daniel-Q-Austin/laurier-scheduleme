import scheduleme   
import request_interception
from icecream import ic

def test_url_builder() -> str: 
    url = scheduleme.url_builder("MA201", "fall", "2021")
    #ic(url)
    return url

def test_intercept_request(url: str) -> str:
    data = request_interception.intercept_request(url)
    #ic(data)
    return data

def main():
    url = test_url_builder()
    data = test_intercept_request(url)
    tester = scheduleme.Course(data)
    tester.parse()
    
main()