from selenium import webdriver
from selenium import *
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import pandas as pd

#------GLOBAL-------#
DRIVER_PATH = 'C:/Users/Astro/Downloads/selen/chromedriver.exe' #Change to wherever your driver is located
DOCKET_PATH = "https://comments.ustr.gov/s/docket?docketNumber=USTR-2022-0014"
LINK_PATH = "links.txt"
options = Options()
options.headless = True
driver = webdriver.Chrome(options=options ,executable_path=DRIVER_PATH)

submitter_columns = ["Submission ID", "submitting on behalf of an organization or industry?","Organization Name", "Third Party Organizational Type",
                        "Commenter First Name","Third Party Firm, Association Name","Commenter Last Name","Third Party Representative",
                        "Does your business meet the size standards for a U.S", "number of employees"
                        ]
#---END OF GLOBAL---#

class DocketScrapper:
    def __init__(self) -> None:
        driver.get(DOCKET_PATH)
        self.link_list = []

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

    def scrap_submission(self, link) -> list:
        '''Iterates through links and collects necessary information'''
        driver.get(link)
        #loops the page until the driver collects the elements
        while(True):
            time.sleep(.2) #Delay give the page time to load
            submission_title = driver.find_elements(by=By.XPATH, value="//c-ustrfb-public-details-review-content-row//c-ustrfb-public-details-review-content-field/div[(contains(@class, 'slds-form-element slds-form-element_readonly') and not (contains(@class, 'is-horizontal')))]/span[contains(@class,'slds-form-element__label')]" )
            submission_contents = driver.find_elements(by=By.XPATH, value="//c-ustrfb-public-details-review-content-row//div/div/div[contains(@class, slds-form-element__static)]")

            if(submission_contents == [] or submission_title == []):
                continue
            else:
                break
        submitter_list = []
        
        content_length = len(submission_title)
        #Since submitter info has different lengths we check how many titles we found and only collect contents within that range
        for i in range(0, content_length):
            submitter_list.append(submission_contents[i].text)

        #Since contents containing 10 submitter info elements have a different format we have to insert whitespace into
        #the smaller lengths submiiter info to keep consistent formating in the dataframe.
        if(content_length < 10):
            submitter_list.insert(3, ' ')
            submitter_list.insert(5, ' ')
            submitter_list.insert(7, ' ')

        return submitter_list

    def collect_submissions(self, limit = 0) -> list:
        submit_list = []
        count = 0
        #scraps each link inside the URL while keeping count
        for i in self.link_list:
            try:
                submit_list.append(self.scrap_submission(i))
            
            except Exception as e:
                print(e)
            count += 1
            if(count > limit and limit > 0):
                break
            print(count)
        
        return submit_list
    def scrap_contents(self):
        pass

#Commonly used xpath's
#all submitter content
#//c-ustrfb-public-details-review-content-row//div/div[contains(@class, "slds-size_1-of-2")]//div//div[contains(@class, slds-form-element__static)]/div 
# titles
#//c-ustrfb-public-details-review-content-row//span 
#Only submiiter title info
#//c-ustrfb-public-details-review-content-row//c-ustrfb-public-details-review-content-field/div[(contains(@class, "slds-form-element slds-form-element_readonly") and not (contains(@class, "is-horizontal")))]/span[contains(@class,"slds-form-element__label")]
#scraps information up to additional comments
#//c-ustrfb-public-details-review-content-row//div/div//div/div/div
#scaps titles up to additional comments
#//c-ustrfb-public-details-review-content-row//span
#scraps information inside additional comments
#//c-ustrfb-display-repeating-records//c-ustrfb-public-details-review-content-field/div/div/div
#scraps titles inside additional comments
#//c-ustrfb-display-repeating-records//c-ustrfb-public-details-review-content-field/div/span
docket_scraper = DocketScrapper()

#Continues to loop until a link list is loaded or produced.
while(True):
    if(not docket_scraper.load_link_list()):
        if(docket_scraper.create_link_list()):
            print("Successfully created list")
            break
    else:
        print(len(docket_scraper.link_list))
        break
list_of_submissions = docket_scraper.collect_submissions(10)
submitter_df = pd.DataFrame(list_of_submissions, columns= submitter_columns)

submitter_df.to_excel('ustr_submit.xlsx')
print('done')
driver.quit()