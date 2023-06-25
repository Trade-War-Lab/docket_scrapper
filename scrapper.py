import os
import pandas as pd
from selenium import webdriver
from selenium import *
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

id_columns = ["Question ID", "Question"]
question_dict = {
    1: "Submission ID"
}
DOCKET_PATH = "https://comments.ustr.gov/s/docket?docketNumber=USTR-2022-0014" #main docket
LINK_PATH = "links.txt"
SUBMISSION_PATH = "fr/" #

DOWNLOAD_PATH = SUBMISSION_PATH + "download/"
INFO_PATH = SUBMISSION_PATH + "info/"
DRIVER_PATH = 'C:/Users/Astro/Downloads/selen/chromedriver.exe' #Change to wherever your driver is located

path = os.path.abspath(DOWNLOAD_PATH)
prefs = {"download.default_directory":path}
options = Options()
options.add_experimental_option("prefs", prefs)
options.headless = False
driver = webdriver.Chrome(options=options ,executable_path=DRIVER_PATH)
#-----------


class DocketScrapper:
    def __init__(self) -> None:
        driver.get(DOCKET_PATH)
        self.create_directories(DOWNLOAD_PATH)
        self.create_directories(INFO_PATH)

        self.link_list = []
    def check_dict_dups(self, value_list):
        for i in value_list:
            if(i in question_dict.values()):
                print("already in questions")
            else:
                last_value = list(question_dict.keys())
                question_dict[last_value[-1] + 1] = i
        
        ids_df = pd.DataFrame(question_dict.items(), columns=id_columns)
        ids_df.to_excel("questions_ids.xlsx")

    def load_link_list(self)-> bool:
        '''Loads the text file containing docket links. Returns true if successful.'''
        if(os.path.exists(LINK_PATH)):
            with open(LINK_PATH, "r") as f:
                self.link_list = f.readlines()

        if(len(self.link_list) is not 0):
            print("loaded links")
            return True
        else:
            print("failed to load links")
            return False

    def save_link_list(self) -> None:
        '''Saves the list of links to a text file.'''
        with open(LINK_PATH, 'w') as f:
            for link in self.link_list:
                f.write(str(link))
                f.write('\n')

    def check_duplicate_links(self, list) -> bool:
        ''''
        Checks that the links collected contains any duplicates. Returns False if 
        all links are unique.
        '''
        if(len(list) == len(set(list))):
            return False
        else: 
            return True
     
    def create_link_list(self) -> bool:
        '''
        Scraps, checks, and saves all the docket submission links to iterate over later to simplfy things. 
        Returns True if successfully collected all unique submission links. 
        '''
        a_elements = []
        temp_link_list = []
        page_count = 0
        record_count = 0
        scraping = True
        while(scraping):
            time.sleep(1) #Waits one second for the page to load. Probably not the best way to do this but it works for now.

            #Collects all hyperlink tags inside the table element, should be 50 per page except on the last page which should be 47. 
            a_elements = driver.find_elements(by=By.XPATH, value="//table[contains(@class,'slds-table')]/tbody//tr//lightning-formatted-url/a")

            #iterates through the hyperlink list and extracts the href elements, saving them to a temporary list.
            docket_link_list = []
            for i in range(len(a_elements)):
                try:
                    docket_link_list.append(a_elements[i].get_attribute('href'))
                except Exception as e:
                    print(e)
                    continue
            for i in docket_link_list:
                temp_link_list.append(i)
                print(i)
            
            #keeps track of scrapping progress
            record_count += len(a_elements)
            page_count += 1
            print(f"Elements collected this iter: {len(a_elements)}")
            print(f"Total records collected: {record_count}")
            print(f"Pages Scraped {page_count}")
            #Finds and clicks the next page button, continues until the next page button is no longer clickable which breaks the loop.  
            try:
                driver.find_element(by=By.XPATH, value="//lightning-layout-item[contains(@class, 'slds-p-right_x-small')]//button").click()
            except:
                print("No longer clickable")
                scraping = False
        
        #Checks for any duplicates indicating something went wrong, if no issues are found saves the collected list to a .txt file
        if(self.check_duplicate_links(temp_link_list)):
            print("duplicates found")
        else:
            self.link_list = temp_link_list
            self.save_link_list()
            return True
        
        return False

    def scrap_contents(self, limit = 0) -> list:
        '''This function is called to scrap submission info and addtional comments then returns a list of only submission info.'''
        submit_list = []

        count = 0
        for i in self.link_list:
            try:
                self.scrap_to_additional(i)
                #submit_list.append(self.scrap_submission(i))
            except Exception as e:
                print(e)
            count += 1
            if(count > limit and limit > 0):
                break
            print(count)
        return submit_list

    def create_directories(self, path) -> None:
        if not os.path.exists(path):
            os.makedirs(path)
    
    def scrap_to_additional(self,link) -> None:
        driver.get(link)
        content_title = []
        content_contents = []
        content_add_title = []
        content_add = []
        download_buttons = []
        #loops the page until the driver collects the elements
        while(True):
            time.sleep(2) #Delay give the page time to load
            content_title = driver.find_elements(by=By.XPATH, value="//c-ustrfb-public-details-review-content-row//span" ) 
            content_add = driver.find_elements(by=By.XPATH, value="//c-ustrfb-display-repeating-records//c-ustrfb-public-details-review-content-field/div/div/div")
            content_contents = driver.find_elements(by=By.XPATH, value="//c-ustrfb-public-details-review-content-row//div/div//div/div/div") 
            content_add_title = driver.find_elements(by=By.XPATH, value="//c-ustrfb-display-repeating-records//c-ustrfb-public-details-review-content-field/div/span" )
            download_buttons =  driver.find_elements(by=By.XPATH, value="//c-ustr-public-docket-attachment-tile//a" )
            
            if(content_title == [] or content_contents == []):
                continue
            else:
                break
            
        contents = []
        titles = []
        additional_content_title= []
        additional_content = []
        #Extracts string from webdriver elements
        for i in content_title:
            titles.append(i.text)
        for i in content_contents:
            contents.append(i.text)
        for i in content_add_title:
            additional_content_title.append(i.text)
        for i in content_add:
            additional_content.append(i.text)
        #Combines submission info and additional info
        combined_content = contents + additional_content
        combined_titles = titles + additional_content_title
        self.check_dict_dups(combined_titles)

        content_df = pd.DataFrame([combined_content], columns=combined_titles)

        #clicks download files button if it exists
        if(download_buttons != []):
            for i in download_buttons:
                i.click()


docket_scraper = DocketScrapper()

while(True):
    if(not docket_scraper.load_link_list()):
        pass
    else:
        print(len(docket_scraper.link_list))
        break

list_of_submissions = docket_scraper.scrap_contents(10)
