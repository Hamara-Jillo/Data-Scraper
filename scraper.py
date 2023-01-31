import email_validator
from mailchimp3 import MailChimp
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from bs4 import BeautifulSoup
import time

pword = " "
user_name = " "
linkedin_url = "https://www.linkedin.com/uas/login"
service = ChromeService(executable_path=ChromeDriverManager().install())

location = ""
#  default positions
positions = {
    "First": "network-F",
    "Second": "network-S",
    "Third": "network-O"
}
position = positions[""]
company = ""
prospect_links = []
email_links = [] 
validated_emails = []
MAILCHIMP_API_KEY = ''
MAILCHIMP_USERNAME = ''


driver = webdriver.Chrome(service=service)
driver.get(linkedin_url)
# There maybe a capture program waiting for your response here
time.sleep(40)

# Logs in the user


def linkedin_auth(user_name, pword):
    username = driver.find_element(By.ID, "username")
    username.send_keys(user_name)
    pwd = driver.find_element(By.ID, "password")
    pwd.send_keys(pword)
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    
# Go to my connections and apply appropriate filters

def filter_page():
    
    try:
        connections = "https://www.linkedin.com/mynetwork/invite-connect/connections/"
        driver.get(connections)
    except :
        print("Page {} is not connected".format(connections))

    time.sleep(20)
    driver.find_element(By.LINK_TEXT, "Search with filters").click()
    


def apply_filter(location,position,company):
    # Finds position button and applies the appropriate position
    position_button = WebDriverWait(driver,20).until(
        EC.element_to_be_clickable((By.XPATH, "//button[@type='button'][@aria-label='Connections filter. 1st filter is currently applied. Clicking this button displays all Connections filter options.']"))
    )
    position_button.click()
    if position == "network-F" or "":
        # Since it's chosen by default on the linked in page we pass
        pass
    else:
        uncheck_position_1 = driver.find_element(By.XPATH, "//label[@for = 'network-F']")
        uncheck_position_1.click()
        position_check = driver.find_element(By.XPATH, "//label[@for = '"+ position +"']")
        position_check.click()
        # Finds location button and clicks it to apply setting on the first filter
        location_button = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, "//button[@type='button'][@aria-label='Locations filter. Clicking this button displays all Locations filter options.']"))
        )
        location_button.click()
    # Finds location button and clicks it to open the location filter
    location_button = WebDriverWait(driver, 20).until(
    EC.element_to_be_clickable((By.XPATH, "//button[@type='button'][@aria-label='Locations filter. Clicking this button displays all Locations filter options.']"))
    )
    location_button.click()
    # Find's location input field and inputs the desired location
    input_location = driver.find_element(By.XPATH, "//input[@aria-label='Add a location']")
    input_location.send_keys(location)
    time.sleep(3)
    input_location.send_keys(Keys.ARROW_DOWN)
    time.sleep(2)
    input_location.send_keys(Keys.ENTER)
    time.sleep(2)
    # Find's the company button and clicks it to apply changes to the location input
    company_button = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, "//button[@type='button'][@aria-label='Current company filter. Clicking this button displays all Current company filter options.']"))
        )
    company_button.click()
    # Click it again to open the Company filter menu
    company_button.click()
    time.sleep(2)
    # Find's company input field and inputs the desired company
    input_company = driver.find_element(By.XPATH, "//input[@aria-label='Add a company']")
    input_company.send_keys(company)
    time.sleep(2)
    input_company.send_keys(Keys.ARROW_DOWN)
    time.sleep(2)
    input_company.send_keys(Keys.ENTER)
    time.sleep(2)
    # Finds and clicks the show results button
    show_results = driver.find_elements(By.XPATH,"//button[@type='button'][@aria-label='Apply current filter to show results']" )
    show_results[2].click()

def prospects_list():
    
    next = True
    prospect_list = driver.find_elements(By.CSS_SELECTOR, 'div.entity-result')

    # Finds desired prospect list
    while next:
        for list in prospect_list:
            # Get the span element
            span = list.find_element(By.CSS_SELECTOR, 'button>span')
            # Check if the span has text 'message' to mean you and the prospects are connected
            # I can only scrap emails from prospects you are connected with
            if span.text == 'Message':
                # Get the link element inside the div
                link = list.find_element(By.CSS_SELECTOR,'a.app-aware-link').get_attribute('href')
                prospect_links.append(link)
        next_button  = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//button[@aria-label="Next"]')))
        if next_button == False:
            next = False
        else:
            next_button.click()
            
def scrape_emails(prospect_links):
    
    for link in prospect_links:
        driver.get(link)
        wait = WebDriverWait(driver, 20)
        contact_link = wait.until(EC.element_to_be_clickable((By.XPATH, '//a[@id="top-card-text-details-contact-info"]')))
        contact_link.click()
        time.sleep(3)
        modal = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@data-test-modal-container]')))
        email_section = modal.find_element(By.CSS_SELECTOR, 'section.pv-contact-info__contact-type.ci-email')
        em = email_section.find_element(By.CSS_SELECTOR, 'a')
        email_links.append(em)

def clean_validate_emails():
    for email_link in email_links:
        # Clean email
        email = email_link.replace("mailto:", "")
        
        try:
            validated_email = email_validator.validate_email(email)
            email = validated_email['email']
            validated_emails.append(email)
        except email_validator.EmailNotValidError as e:
            print("The {} address is not valid".format)

def mail_chimp_process(API_KEY, USERNAME):
    client = MailChimp(mc_api=API_KEY, mc_user=USERNAME)

    # Get the id for the list in Mailchimp.
    list_id = client.lists.all()['list'][0]['id']
    # Construct a payload for request.
    for email in validated_emails:
        client.lists.members.create(list_id=list_id, data={'email_address': email, 'status': 'subscribed'})
        

        campaign_data = {
            "type": "regular",
            "recipients": {
                "list_id": list_id
            },
            "settings": {
                "subject_line": "Example Campaign",
                "from_name": "John Doe",
                "reply_to": "johndoe@example.com"
            },
            "content": {
                "html": "<p>Hello, this is an example campaign.</p>"
            }
        }

        client.campaigns.create(data=campaign_data)
        campaign_id = client.campaigns.get(campaign_id='<CAMPAIGN_ID>')
        client.campaigns.actions.send(campaign_id=campaign_id)
        
linkedin_auth(user_name=user_name, pword=pword)
time.sleep(3)
filter_page()
time.sleep(3)
apply_filter(position=position, location=location, company=company)
prospects_list()
time.sleep(2)
scrape_emails(prospect_links=prospect_links)
time.sleep(5)
clean_validate_emails()
mail_chimp_process(API_KEY=MAILCHIMP_API_KEY, USERNAME=MAILCHIMP_USERNAME)