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
    #TODO: I believe all of theese dicts and tags can be moved to more appropriate places
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
        'os': 'open_seats', 
        'me': 'max_seats', 
        'nres': 'remaining_seats',
        'teacher': 'instructor',
        #'timeblockids': 'time_block' MUST BE HANDLED DIFFERENTLY
        #DAYS
        #START TIME
        #END TIME 
        }

    timeblock_ids = {
        'id' : 'id',
        'day' : 'day',
        't1' : 'start_time',
        't2' : 'end_time'
    }

    def __init__(self, classdata: str):
        self.raw_data = BeautifulSoup(classdata, 'html.parser')
        self.course_info = {}   #Information for the course regardless of section
        self.lectures = []      #A list of different lecture dictionary objects
        self.labs = []          #A list of lab dictionary objects

        self._time_blocks = []   #List of time block dictionaries for referncing by leccture and labs
        self._CRN_list = []      #For simplicity, list of CRNs to avoid duplicates. Not intended to be acccessed from the outside.

    def parse(self):
        """"
        ...

        RETURN:
        Returns something

        Parses information from the schedulme url.
        TODO: If it returns an error, shut her down!!!
        TODO: Add prereqs and shit? Parse desc
        TODO: Change this dumb 'course_tag' 'section_tag stuff. it doesnt make sense here
        #TODO: MAke it work in cases of ONLINE LEARNING or MIXED ONLINE AND IN PERSON. See CH110, has a MIX
            Can look for SECNO and go from there. 
        #TODO: All things considered she works pretty well. More testing, shit that is here. Need to make sure I exaplin shit when
                I upload to github. Like how does timeblocks work. The structure of the thing. etc.
        """

        #Populate course info. Can be made into new function
        self._add_course_element('campus', 'v', 'campus')
        self._add_course_element('term', 'v', 'term')
        self._add_course_element('block', 'credits', 'credits')
        for id in self.course_ids:
            self._add_course_element(self.course_tag, id, self.course_ids[id])

        self._populate_timeblocks()

        #Populate section info. Can be made into new function
        for block in self.raw_data.find_all(self.section_tag): #check for type and CRN to avoid duplicates
            if block['key'] in self._CRN_list:
                continue
            if block['type'] == 'Lec':
                self.lectures.append(self._populate_section(block))
            elif block['type'] == 'Lab':
                self.labs.append(self._populate_section(block))
            
        #Console shit
        ic(self.course_info)
        ic(self.lectures)
        ic(self.labs)
        

    def _add_course_element(self, tag: str, id: str, name: str): 
        self.course_info[name] = getattr(self.raw_data, tag).get(id)
        return

    def _populate_section(self, block: object) -> dict:
        """
        PARAMS:
        block:      a beautifulsoup object that contains section information

        RETURNS:
        section     a dictionary containing specific information we want
        """

        self._CRN_list.append(block['key'])
        section = {}
        
        for id in self.section_ids:
            section[self.section_ids[id]] = block.get(id)

        timeblocks = [int(x) if x.isdigit() else None for x in block.get('timeblockids').split(',')]
        section['days'] = []
        section['start_time'] = []
        section['end_time'] = []

        for x in timeblocks:
            if x is not None:
                section['days'].append(self._time_blocks[x]['day'])
                section['start_time'].append(self._time_blocks[x]['start_time'])
                section['end_time'].append(self._time_blocks[x]['end_time'])
            
        return section

    def _populate_timeblocks(self):
        """
        Get the time blocks into the time block list for easy access
        """

        self._time_blocks.append(None) #This is to occupy element 0. This means the index in the list will match the time block id!
        for timeblock in self.raw_data.find_all('timeblock'):
            dict_block = {}
            for id in self.timeblock_ids:
                dict_block[self.timeblock_ids[id]] = timeblock.get(id)
            self._time_blocks.append(dict_block)


        