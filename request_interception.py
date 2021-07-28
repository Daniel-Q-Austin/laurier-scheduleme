import asyncio
from bs4 import BeautifulSoup
from pyppeteer import launch
from icecream import ic
import string
import time


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

    #Not currently in use
    return
    global course_list
    ic(response.url)
    if "add_suggest.jsp" in response.url:
        html_response = BeautifulSoup(response.text, 'html.parser')
        ic(html_response)
        for course in html_response.find_all('rs'):
            course_list.append(course.get("reason"))

    ic(course_list)



async def _get_dropdown(url : str, class_list : list) -> list:
    """
    Process to click on the search bar, type a letter,
    and return the list that follows
    """
    #TODO: PArse the terms here!!!!
    #TODO: Fucking error handlign for interent time out
    #TODO: Course start with numbers!!!
    #They look like this "<rs id="6" info="(Fall 2021 only)<br/>Optimization" reqId="" reason="TITLE">MA 372</rs>""
    #I can figure out the term frmo the info!!!!
    browser = await launch(headless=False, devtools=False, executablePath=CHROME_PATH)
    page = await browser.newPage()

    letterlist = []
    ordered_list = []
    iterator_key = 'abcdefghijklmnopqrstuvwxyz0123456789'

    binary = False
    #page.on('response', lambda response: ic(response.url))
    page.on('response', lambda response: letterlist.append(response))
    await page.goto(url, waitUntil=["networkidle2", "domcontentloaded"])

    
    for letter in iterator_key:
        await page.click("#code_number")
        await page.keyboard.type(letter, waitUntil=["networkidle2"])
        await page.click("#code_number")
        time.sleep(2)
        for i in range(200): #range must be this long or B courses dont reach the end
            await page.keyboard.press('ArrowDown')
            time.sleep(0.01)
        
        time.sleep(2)
        await page.click("#code_number")
        await page.keyboard.down("Control")
        await page.keyboard.press('a')
        time.sleep(0.1)
        await page.keyboard.up("Control")
        await page.keyboard.press("Backspace")
        time.sleep(0.1)
        ordered_list.append((letter, letterlist)) #Add it to a tuple with teh letter as the first element 
        letterlist = []                            #so we can compare the starting letter of the course code to that letter
                                                
    #ic(ordered_list)
    full_course_list = await _parse_courses(ordered_list)
    ic(full_course_list)
    return(full_course_list)

async def _parse_courses(ordered_list: list) -> list:
    """
    Take the list of tuples containing all of the unparsed courses and puts
    them into a single list of every course at laurier.
    This will ACTUALLLY ONLY GET EVERY COURSE OFFERED THE TERM WE ARE LOOKING AT,
    WHICH IS PROVIDED BY THE ORIGINAL URL. 
    """
    full_course_list = []
    for tupler in ordered_list:
        for response in tupler[1]:
            if "add_suggest" in response.url:
                #ic(response.url)
                response_html = await response.text()
                rs = BeautifulSoup(response_html, 'lxml-xml')
                for course in rs.find_all('rs'):
                    #ic(course.get('info'), course.text)
                    if (' only)' not in course.get('info')) and (course.text != '_more_'): #It is a course, and it is this term
                        if course.text[0].lower() == tupler[0]: #check if the first letter of the course code is the same as the letter typed for that passthrough
                            full_course_list.append(course.text.replace(" ", ""))

    return(full_course_list)


def _add_to_list(response : str, letter : str, response_list : list) -> list:
    """
    Checks the response to see if the dropdown list is showing courses that no longer start with the letter
    """