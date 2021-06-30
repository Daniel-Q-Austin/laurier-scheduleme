import re
from icecream import ic
from enum import Enum
from bs4 import BeautifulSoup

#TODO: Begin parsing class data. All the data is there. I need to struccture and parse that bitch.
#TODO: Put it all in the object

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

class Term(Enum):
    FALL = "09"
    WINTER = "01"
    SPRING = "05"

class Course:
    """
    Object containing the course information we need

    PARAMS:
    Takes classdata as a param
    """
    course_tag = 'course'
    course_ids = {
        'key': 'code',
        'title': 'title',
        'cores': 'coreqs',
        'desc': 'description',
        'waiting': 'waiting_list',
        'faculty': 'faculty'
        }

    section_tag = 'block'
    section_ids = {
        'type' : 'type',
        'key': 'CRN',
        'secno': 'section_number',
        'os': 'open_seats', #ALMOST CERTAIN
        'me': 'max_seats', #UNSURE
        'nres': 'remaining_seats', #REALLY JUST A GUESS
        'teacher': 'instructor',
        'timeblockids': 'time_block'
        }

    def __init__(self, classdata: str):
        self.raw_data = BeautifulSoup(classdata, 'html.parser')
        self.course_info = {}   #Information for the course regardless of section
        self.lectures = []      #A list of different lecture dictionary objects
        self.labs = []          #A list of lab dictionary objects

        self._CRN_list = []      #For simplicity, list of CRNs to avoid duplicates. Not intended to be acccessed from the outside.

    def parse(self):
        """"
        ...

        RETURN:
        Returns something

        Parses information from the schedulme url.
        TODO: If it returns an error, shut her down!!!
        TODO: Add prereqs and shit? Parse desc
        TODO: Fucking add time blocks
        TODO: Get credits in course info, not in block as it currently is
        TODO: Parsee BLOCKS you feel me g. PRse the many many many bloccks that im gonna have here.
        """


        self._add_course_element('campus', 'v', 'campus')
        self._add_course_element('term', 'v', 'term')
        for id in self.course_ids:
            self._add_course_element(self.course_tag, id, self.course_ids[id])

        for block in self.raw_data.find_all(self.section_tag): #check for type and CRN to avoid duplicates
            if block['key'] in self._CRN_list:
                continue

            if block['type'] == 'Lec':
                self.lectures.append(self._populate_section(block))
            elif block['type'] == 'Lab':
                self.labs.append(self._populate_section(block))
            
        ic(self.course_info)
        ic(self.lectures)
        ic(self.labs)
        

    def _add_course_element(self, tag: str, id: str, name: str): 
        self.course_info[name] = eval("self.raw_data.{}['{}']".format(tag, id)) #change to getattr
        return
    

    def _populate_section(self, block: object) -> dict:
        """
        PARAMS:
        block:      a beautifulsoup object that contains section information

        RETURNS:
        section     a dictionary containing specific information we want
        """
        section = {}
        self._CRN_list.append(block['key'])
        for id in self.section_ids:
            section[self.section_ids[id]] = block.get(id)
        return section


        