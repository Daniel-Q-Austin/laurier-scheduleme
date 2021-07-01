import re
from icecream import ic
from enum import Enum
from bs4 import BeautifulSoup

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
    #TODO: rawdata and class data should be switched lol. like the var names.
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
        TODO: Change this dumb 'course_tag' 'section_tag stuff. it doesnt make sense here
        #TODO: All things considered she works pretty well. More testing, shit that is here. Need to make sure I exaplin shit when
                I upload to github. Like how does timeblocks work. The structure of the thing. etc.
        #TODO: Timezones. Make it work
        #TODO: Make it dect the chrome path automatically.
        """
        
        if self.raw_data.error is not None:
            print(self.raw_data.error)
            print("This course may be unavailable this term. Please also ensure your computers timezone is acccurate.")
            return

        self._populate_course_info()
        self._populate_timeblocks()
        self._populate_all_sections()

        ic(self.course_info)
        ic(self.lectures)
        ic(self.labs)
        

    def _add_course_element(self, tag: str, id: str, name: str): 
        #Not currently in use
        self.course_info[name] = getattr(self.raw_data, tag).get(id)
        return

    def _populate_course_info(self):
        """
        Populates the course_info local variable with necessary information
        """
        course_tag = 'course'
        course_ids = {
            #Used to iteratively grab all of the html elements i need and store them with more informative names.
            #If you want to grab more variables from the html block just add them here
            #format:   var_name_in_html : var_name_in_this_object
            'key': 'code',
            'title': 'title',
            'cores': 'coreqs', #Never seen this used once.
            'desc': 'description',
            'waiting': 'waiting_list',
            'faculty': 'faculty'
        }

        self.course_info['campus'] = []

        #These all grab information from different tags, so they need to be handled separately
        for campus in self.raw_data.find_all('campus'):
            self.course_info['campus'].append(campus.get('v'))
        self.course_info['term'] = getattr(self.raw_data, 'term').get('v')
        self.course_info['credits'] = getattr(self.raw_data, 'block').get('credits')

        #Get information from the course tag
        for id in course_ids:
            self.course_info[course_ids[id]] = getattr(self.raw_data, course_tag).get(id)
        
        #Extract the prereqs and exclusions from the description. Sorry for the long lines.
        description = self.course_info['description']
        self.course_info['prereqs'] = description[description.rfind('Prerequisites: </font>') + len('Prerequisites: </font>') : description.find('<br><font color="crimson">Exclusions:') - 1].strip(' .:')
        self.course_info['exclusions'] = description[description.rfind('Exclusions: </font>') + len('Exclusions: </font>') : description.rfind('<br><font') - 1].strip(' .:')
        
        return

    def _populate_all_sections(self):
        """
        Populates all sections of the course. Mostly calls on the helper method _populate section
        """
        for block in self.raw_data.find_all('block'): 
            if block['key'] in self._CRN_list:      #check for type and CRN to avoid duplicates
                continue
            if block['type'] == 'Lec':
                self.lectures.append(self._populate_section(block))
            elif block['type'] == 'Lab':
                self.labs.append(self._populate_section(block))

    def _populate_section(self, block: object) -> dict:
        """
        PARAMS:
        block:      a beautifulsoup object that contains section information

        RETURNS:
        section     a dictionary containing specific information we want
        """
        section_tag = 'block'
        section_ids = {
            #Used to iteratively grab all of the html elements i need and store them with more informative names.
            #If you want to grab more variables from the html block just add them here
            #format - var_name_in_html : var_name_in_this_object
            'type' : 'type',
            'key': 'CRN',
            'secno': 'section',
            'os': 'open_seats', 
            'me': 'max_seats', 
            'nres': 'remaining_seats', #Isnt this the same as open seats?
            'teacher': 'instructor',
        }

        self._CRN_list.append(block['key'])
        section = {}
        
        for id in section_ids:
            section[section_ids[id]] = block.get(id) #get the section info from the soup object

        timeblocks = [int(x) if x.isdigit() else None for x in block.get('timeblockids').split(',')] #Get the timeblocks for this section

        section['days'] = []        #Create the categories for day, start time, end time, in the dictionary for this section
        section['start_time'] = []
        section['end_time'] = []

        for x in timeblocks:        #Match the information from the appropriate timeblock to the section dictionary
            if x is not None:
                section['days'].append(self._time_blocks[x]['day'])
                section['start_time'].append(self._time_blocks[x]['start_time'])
                section['end_time'].append(self._time_blocks[x]['end_time'])
            
        return section

    def _populate_timeblocks(self):
        """
        Get the time blocks into the time block list for easy access
        """
        timeblock_ids = {
            'id' : 'id',
            'day' : 'day',
            't1' : 'start_time',
            't2' : 'end_time'
        }

        self._time_blocks.append(None) #This is to occupy element 0. This means the index in the list will match the time block id!

        for timeblock in self.raw_data.find_all('timeblock'):
            dict_block = {}
            for id in timeblock_ids:
                dict_block[timeblock_ids[id]] = timeblock.get(id)
            self._time_blocks.append(dict_block)
        return


        