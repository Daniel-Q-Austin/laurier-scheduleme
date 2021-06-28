import re
from icecream import ic
from enum import Enum
from bs4 import BeautifulSoup

#TODO: Begin parsing class data. All the data is there. I need to struccture and parse that bitch.

def url_builder(course: str, term: str, year: str) -> str:
    """
    PARAMS:
    course: The course number you want to access. For example, EC120 or MA129
    term:   Either fall, winter, or spring. Case insensitive.
    year:   Year in format yyyy
    ...

    RETURNS:
    url:    Url built from your parameters

    Builds a URL from given parameters
    """

    term_val = Term[term.upper()].value #replace string term with appropriate number
    splitcourse = re.split('(\d+)', course.upper()) #Splits course into a list, letters and numbers

    url = ("https://scheduleme.wlu.ca/vsb/criteria.jsp?access=1&lang=en&tip=0&page=results&scratch=0"
            "&advice=0&term={}{}&sort=none&filters=iiiiiiiiii&bbs=&ds=&cams=C_K_T_V_W_Z_CC_G_X_Y_MC"
            "&locs=any&isrts=&course_0_0={}-{}&sa_0_0=&cs_0_0=--202105_373-374-&cpn_0_0=&csn_0_0=&ca_0_0="
            "&dropdown_0_0=al&ig_0_0=0&rq_0_0=""".format(year, term_val, splitcourse[0], splitcourse[1]))

    ic(url)
    return url

def parse(classdata: str) -> str:
    """
    PARAMS:
    classdata: ALl of the class data in HTML format
    ...

    RETURN:
    Returns something

    Parses information from the schedulme url.
    """
    soup = BeautifulSoup(classdata, 'html.parser')
    #if it returns an error shut it down

    #print(soup.prettify)
    ic(soup.campus)


    None

class Term(Enum):
    FALL = "09"
    WINTER = "01"
    SPRING = "05"