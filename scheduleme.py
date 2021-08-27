from os import write
import re
from icecream import ic
from enum import Enum
from bs4 import BeautifulSoup
import request_interception
import time
class Course:
    """
    Object containing the course information we need

    PARAMS:
    Takes classdata as a param
    """
    #TODO: Add a custom print function

    def __init__(self, course_code, term, year): #Remove classdata

        url = self.url_builder(course_code, term, year)
        classdata = request_interception.intercept_request(url)
        self.raw_data = BeautifulSoup(classdata, 'html.parser')

        self.course_info = {
            'campus' : [],
            'url' : url,
            'code' : None,
            'title' : None,
            'coreqs' : None,
            'prereqs' : None,
            'exclusions' : None,
            'registration_notes' : None,
            'description' : None,
            'faculty' : None,
            'term' : None,
            'credits' : None,
            'waiting_list' : None
        }    #Information for the course regardless of section

        self.lectures = []       #A list of different lecture dictionary objects
        self.labs = []           #A list of lab dictionary objects
        self.tutorials = []      #A list of tutorial dictionary objects

        self._time_blocks = []   #List of time block dictionaries for referncing by leccture and labs. Not intended to be acccessed from the outside.
        self._CRN_list = []      #For simplicity, list of CRNs to avoid duplicates. Not intended to be acccessed from the outside.

        self.parse()

    def url_builder(self, course: str, term: str, year: str) -> str:
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
        if course[0] in '0123456789':
            course_dpt = course[:2]
            course_num = course[2:]
        else:
            splitcourse = re.split('(\d+)', course.upper()) #Turns course code AA### into list [AA, ###]
            course_dpt = splitcourse[0]
            course_num = splitcourse[1]
            if len(splitcourse) == 3:
                course_num += splitcourse[2] #Some courses have a letter after the number that is part of the course number.

        url = ("https://scheduleme.wlu.ca/vsb/criteria.jsp?access=1&lang=en&tip=0&page=results&scratch=0"
                "&advice=0&term={}{}&sort=none&filters=iiiiiiiiii&bbs=&ds=&cams=C_K_T_V_W_Z_CC_G_X_Y_MC"
                "&locs=any&isrts=&course_0_0={}-{}&sa_0_0=&cs_0_0=--{}{}_373-374-&cpn_0_0=&csn_0_0=&ca_0_0="
                "&dropdown_0_0=al&ig_0_0=0&rq_0_0=").format(year, term_val, course_dpt, course_num, year, term_val)

        ic(url)
        return url

    def parse(self):
        """"
        Parses the html into the objects

        RETURN:
        Returns 1 on success, -1 on failure

        TODO: Testing
        TODO: Timezones. Make it work. I assume it does
        """
        
        if self.raw_data.error is not None:
            print(self.raw_data.error)
            print("This course may be unavailable this term. Please also ensure your computers timezone is acccurate.")
            return -1

        self._populate_course_info()
        self._populate_all_sections()

        ic(self.course_info)
        ic(self.lectures)
        ic(self.labs)
        ic(self.tutorials)

    def _populate_course_info(self):
        """
        Populates the course_info local variable with necessary information
        """
        #Get information from the course tag
        course_ids = {
            #Format is name_in_html : name_in_object
            'key': 'code',
            'title': 'title',
            'waiting': 'waiting_list',
            'faculty': 'faculty'
        }
        for id in course_ids:
            self.course_info[course_ids[id]] = getattr(self.raw_data, 'course').get(id)

        #These all grab information from different tags, so they need to be handled separately
        for campus in self.raw_data.find_all('campus'):
            self.course_info['campus'].append(campus.get('v')) #Some classess have multiple campuses
        self.course_info['term'] = getattr(self.raw_data, 'term').get('v')
        self.course_info['credits'] = getattr(self.raw_data, 'block').get('credits')
        
        #Extract the prereqs and exclusions from the description.
        self._parse_description()

        return

    def _populate_all_sections(self):
        """
        Populates all sections of the course. Mostly calls on the helper method _populate_section
        """
        self._populate_timeblocks()
        for block in self.raw_data.find_all('block'): 
            if block['key'] in self._CRN_list:      #check for type and CRN to avoid duplicates
                continue
            if block['type'] == 'Lec':
                self.lectures.append(self._populate_section(block))
            elif block['type'] == 'Lab':
                self.labs.append(self._populate_section(block))
            elif block['type'] == "Tut":
                self.tutorials.append(self._populate_section(block))

    def _populate_section(self, block: object) -> dict:
        """
        PARAMS:
        block:      a beautifulsoup object that contains section information

        RETURNS:
        section     a dictionary containing specific information we want
        """
        self._CRN_list.append(block['key'])
        section = {
            'type' : None,
            'CRN' : None,
            'section' : None,
            'open_seats' : None,
            'max_seats' : None,
            'instructor' : None,
            'days' : [],
            'start_time' : [],
            'end_time' : [],
            'location' : None
        }

        section_ids = {
            #Used to iteratively grab all of the html elements i need and store them with more informative names.
            #format - var_name_in_html : var_name_in_this_object
            'type' : 'type',
            'key': 'CRN',
            'secno': 'section',
            'os': 'open_seats', 
            'me': 'max_seats', 
            'teacher': 'instructor',
            'location' : 'location',
        }
        
        for id in section_ids:
            section[section_ids[id]] = block.get(id) #get the section info from the soup object

        timeblocks = [int(x) if x.isdigit() else None for x in block.get('timeblockids').split(',')] #Get the timeblocks for this section

        for x in timeblocks:        #Match the information from the appropriate timeblock to the section dictionary
            if x is not None:
                section['days'].append(self._time_blocks[x]['day'])
                section['start_time'].append(self._time_blocks[x]['t1'])
                section['end_time'].append(self._time_blocks[x]['t2'])
            
        return section

    def _populate_timeblocks(self):
        """
        In the visual scheduled builder times are not directly associated with lecture sections, but instead
        diffferent 'timeblocks' are given, and lecture sections are associated with those timeblocks. This
        grabs the timeblocks into a format that will make it easy to associate a time with a lecture section.
        """
        timeblock_ids = ['id','day','t1','t2']

        self._time_blocks.append(None) #This is to occupy element 0. This means the index in the list will match the time block id!

        for timeblock in self.raw_data.find_all('timeblock'):
            dict_block = { 
                'id' : None,
                'day' : None,
                't1' : None,
                't2' : None
            }
            for id in timeblock_ids:
                dict_block[id] = timeblock.get(id)
            self._time_blocks.append(dict_block)
        return
    
    def _parse_description(self):
        """
        Parses the description into description, prereqs, exclusions, and coreqs
        """
        html_desc = getattr(self.raw_data, 'course').get('desc')
        description = BeautifulSoup(html_desc, 'html.parser').text
        description += " " #litrerally dont even worry about it

        #Does this course have prerequisites? Exclusions? lets find out!
        requisites = {
            'prerequisites' : None,
            'exclusions' : None,
            'co-requisites' : None,
            'registration notes' : None
        }
        included = []

        for req in requisites:
            x = description.lower().find(req)
            if x != -1:
                included.append((req, x, x + len(req))) #Three element tuple containing the term, the position of the first character, and position of the last

        included.sort(key = lambda x: x[1]) #Sorts the requisites by order they appear so we can grab content between them
        
        if len(included) == 0:
            self.course_info['description'] = description
        else:
            included.append((None, -1, -1)) #Will simplify iterating to the end
            self.course_info['description'] = description[:included[0][1]]
            for i in range(len(included) - 1): #Iterate to all but the last item, aka the item we just added.
                requisites[included[i][0]] = (description[included[i][2] : included[i+1][1]]).strip(' .:')#Add it to the dictionary as the substring between the end of its label and ths start of the next label

        #rename these to be easier to work with
        self.course_info['prereqs'] = requisites['prerequisites']
        self.course_info['coreqs'] = requisites['co-requisites']
        self.course_info['registration_notes'] = requisites['registration notes']


class CSV_Helper:
    """
    Helper class that does functions related to course information, but does not hold course information.
    """
    def __init__(self, starting_year):
        self.term_list = [
            ('spring', int(starting_year)),
            ('fall', int(starting_year)),
            ('winter', int(starting_year)+1),
            ('spring', int(starting_year)+1)
        ]

    def _dropdown_url_builder(self, term, year) -> str:
        """
        Builds the URL to get to the dropdown which is used to get the full course list
        """

        term_val = Term[term.upper()].value

        url = ("https://scheduleme.wlu.ca/vsb/criteria.jsp?access=0&lang=en&tip=1&page=criteria&scratch=0"
               "&advice=0&term={}{}&sort=none&filters=iiiiiiiiii&bbs=&ds=&cams=C_K_T_V_W_Z_CC_G_X_Y_MC"
               "&locs=any&isrts=").format(year, term_val)

        return url

    def get_full_course_list(self) -> dict:
        """
        This function gets a list of every course that has/is/will run in at laurier during the four available terms on VSB.

        starting_year: The earliest year that can be seen on the visual schedule builder.
                        So I can see courses in 2021 and 2022 right now, so I'd input 2021.
        """

        print("Getting full course list. \nThis will take 15-20 minutes. Please wait and ensure your computer does not disconnect from the internet.")


        all_courses = [] #Will contain 4 lists, each with the courses frmo that term.

        for term in self.term_list:
            print("Getting courses from {} {}...".format(term[0], term[1]))
            url = self._dropdown_url_builder(term[0], term[1])
            temp_list = request_interception.get_class_list(url)
            temp_list.insert(0, '{} {}'.format(term[0], term[1])) #add the term to the start of the list
            all_courses.append(temp_list)

        return all_courses
    
    def write_course_list_to_text(self, course_list):
        """
        It is necessary to store the course list somewhere since sometimes the program crashes
        """
        for term in course_list:
            txtlist = open(term[0] + '.txt', 'w+') #The first term in the returned course list is 'spring 2021', 'winter 2022' etc.
            txtlist.writelines(course + '\n' for course in term[1:])
            txtlist.close()

    def build_csv(self):
        """
        Build a csv from the course list text tiles, which obviously must already exist
        """
        separator = '@'
        for index, term in enumerate(self.term_list):
            if index == 0:
                continue
            read_file = open("{} {}.txt".format(term[0], term[1]), "r")
            write_file = open("{} {}.csv".format(term[0], term[1]), "w+")
            headers = ["Course Code", "Title", "Campus", "Link", "Description","Remaining Seats", "Locations", "Prerequisites", "Exclusions", "Registration Notes"]
            for i in headers:
                write_file.write(i)
                write_file.write(separator)
            write_file.write('\n')

            write_file.write('{} {} Courses {}{}{} For Other Terms See Other Tabs of Spreadsheet Below'.format(term[0], term[1], separator, separator, separator))
            write_file.write('\n')

            for course_code in read_file.read().splitlines():
                course = Course(course_code, term[0], term[1])
                
                title = course.course_info['title']
                campus = ""
                for campuses in course.course_info['campus']:
                    campus += campuses + ', '
                campus = campus[:-2]

                link = '=HYPERLINK("{}", "LINK")'.format(course.course_info['url']) #must be adjusted to a comma in post
                description = course.course_info['description']

                seats = 0
                locations = ""
                for lecture in course.lectures:
                    seats += int(lecture['open_seats'])
                    if lecture['location'] not in locations:
                        locations += lecture['location']
                        locations += ', '
                locations = locations[:-2]

                prereqs = course.course_info['prereqs']
                exclusions = course.course_info['exclusions']
                registration_notes = course.course_info['registration_notes']

                spreadsheet_list = [course_code, title, campus, link, description, seats, locations, prereqs, exclusions, registration_notes]
                for item in spreadsheet_list:
                    if item == None or item == "":
                        item == "None"
                    write_file.write(str(item))
                    write_file.write(separator)
                time.sleep(3)
                write_file.write('\n')
            read_file.close()
            write_file.close()



class Term(Enum):
    FALL = "09"
    WINTER = "01"
    SPRING = "05"
    SUMMER = "05"
