import asyncio
from pyppeteer import launch


CHROME_PATH = "/usr/bin/google-chrome"
classdata = ""

def process_webpage(url: str) -> str:
    """Runs the process function without having to worry about asyncio processes"""

    return asyncio.get_event_loop().run_until_complete(_process(url))

async def _process(url: str) -> str:
    """
    PARAMS:
    url:    The url of the visual schedule builder page of the course you want

    RETURNS:
    classdata: The classdata in html format
    """

    browser = await launch(headless=True, devtools=True, executablePath=CHROME_PATH)
    page = await browser.newPage()

    page.on('response', lambda response: asyncio.ensure_future(_intercept_network_response(response)))

    await page.goto(url, waitUntil=["networkidle0", "domcontentloaded"])
    await browser.close()

    return classdata

async def _intercept_network_response(response):
    """Look for the response to the getclassdata.jsp and record it in classdata"""

    if "getclassdata" in response.url:
        global classdata
        classdata = await response.text()