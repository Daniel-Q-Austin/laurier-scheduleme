from enum import Enum
from bs4 import BeautifulSoup
import re
import requests


def url_builder(course, term, year):
    """
    Builds a URL from given parameters

    PARAMS:
    course: String.   The course number you want to access. For example, EC120 or MA129
    term:   String.   Either fall, winter, or spring. Case insensitive.
    year:   String.   Year in format yyyy
    ...

    RETURNS:
    url: String.      Url built from your parameters
    """

    term = term.upper()
    term = Term[term].value #replace string term with appropriate number
    
    course = course.upper()
    splitcourse = re.split('(\d+)', course) #Splits course into a list, letters and numbers

    url = ("https://scheduleme.wlu.ca/vsb/criteria.jsp?access=1&lang=en&tip=0&page=results&scratch=0"
            "&advice=0&term={}{}&sort=none&filters=iiiiiiiiii&bbs=&ds=&cams=C_K_T_V_W_Z_CC_G_X_Y_MC"
            "&locs=any&isrts=&course_0_0={}-{}&sa_0_0=&cs_0_0=--202105_373-374-&cpn_0_0=&csn_0_0=&ca_0_0="
            "&dropdown_0_0=al&ig_0_0=0&rq_0_0=""".format(year, term, splitcourse[0], splitcourse[1]))
        
    return url

def parse(url):
    """
    Parses information from the schedulme url.

    PARAMS:
    ...

    RETURN:
    Returns something

    """
    webpage = requests.get(url)
    soup = BeautifulSoup(webpage.content, 'html.parser')

    print(soup.prettify)

    side_panel = soup.find_all(class_="header_cell")
    print(side_panel)

    None


class Term(Enum):
    FALL = "09"
    WINTER = "01"
    SPRING = "05"