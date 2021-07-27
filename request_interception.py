import asyncio
from bs4 import BeautifulSoup
from pyppeteer import launch
from icecream import ic


#CHROME_PATH = "/usr/bin/google-chrome"
CHROME_PATH = "C:\Program Files\Google\Chrome\Application\chrome.exe"
classdata = None
course_list = []

def intercept_request(url: str) -> str:
    """Runs the process function without having to worry about asyncio processes"""

    return asyncio.get_event_loop().run_until_complete(_get_classdata(url))

def click_dropdown(url: str, classlist: list) -> list:
    return asyncio.get_event_loop().run_until_complete(_get_dropdown(url, classlist))

async def _get_classdata(url: str) -> str:
    """
    PARAMS:
    url:    The url of the visual schedule builder page of the course you want

    RETURNS:
    classdata: The classdata in html format
    """

    browser = await launch(headless=True, devtools=False, executablePath=CHROME_PATH)
    page = await browser.newPage()

    page.on('response', lambda response: asyncio.ensure_future(_intercept_network_response(response)))

    await page.goto(url, waitUntil=["networkidle0", "domcontentloaded"])
    await browser.close()

    return classdata

async def _intercept_network_response(response):
    """Look for the response to the getclassdata.jsp and record it in classdata"""
    
    if "getclassdata" in response.url:
        global classdata
        ic(response.url)
        classdata = await response.text()

async def _get_dropdown_response(response, letter) -> list:

    global course_list
    ic(response.url)
    if "add_suggest.jsp" in response.url:
        html_response = BeautifulSoup(response.text, 'html.parser')
        ic(html_response)
        for course in html_response.find_all('rs'):
            course_list.append(course.get("reason"))

    #ic(course_list)



async def _get_dropdown(url : str, class_list : list) -> list:
    """
    Process to click on the search bar, type a letter,
    and return the list that follows
    """
    browser = await launch(headless=False, devtools=False, executablePath=CHROME_PATH)
    page = await browser.newPage()

    page.on('response', lambda response: ic(response.url))
    await page.goto(url, waitUntil=["networkidle2", "domcontentloaded"])

    await page.click("#code_number")
    await page.keyboard.type("a", waitUntil=["networkidle2"])
    await page.click("#code_number")
    for i in range(100):
        await page.keyboard.press('ArrowDown')

    while(1):
        None


def _add_to_list(response : str, letter : str, response_list : list) -> list:
    """
    Checks the response to see if the dropdown list is showing courses that no longer start with the letter
    """