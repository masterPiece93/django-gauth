import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from django.test import LiveServerTestCase
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
from unittest import skipIf


import time
from selenium.common.exceptions import TimeoutException

class GoogleOAuthTest(LiveServerTestCase):
    host = 'localhost'
    port = 8000 
    def setUp(self):

        # self.browser = webdriver.Chrome() # Or Firefox, Edge, etc.
        # Create ChromeOptions for undetected_chromedriver
        chrome_options = uc.ChromeOptions()
        # Add any desired arguments, e.g., incognito, disable extensions
        chrome_options.add_argument("--incognito") 
        # Initialize the undetected_chromedriver
        self.browser = uc.Chrome(version_main=142, options=chrome_options)
        self.browser.implicitly_wait(10) # Wait for elements to load

    def tearDown(self):
        self.browser.quit()

    @skipIf(os.environ.get('NOX', '0') == '1', "Skipping resource-intensive test in NOX testing.")
    def test_google_oauth_login(self):
        
        self.browser.get(self.live_server_url + '/gauth/') # Your login URL
        
        # Click the Google login button (adjust selector as needed)
        google_login_button = self.browser.find_element(By.ID, 'AuthenticateButton') 
        google_login_button.click()

        time.sleep(2) # for spoofing browser of not-a-bot

        # Google's login page
        # Input test user credentials (replace with actual test user email/password)
        email_input = self.browser.find_element(By.ID, 'identifierId')
        email_input.send_keys(os.environ.get('TEST_GOOGLE_ACCOUNT'))
        self.browser.find_element(By.ID, 'identifierNext').click()

        time.sleep(2) # for spoofing browser of not-a-bot

        # password_input = self.browser.find_element(By.NAME, 'password')
        password_input = self.browser.find_element(By.XPATH, "//div[@id='password']//input[@type='password']")
        password_input.send_keys(os.environ.get('TEST_GOOGLE_PASSWORD'))
        self.browser.find_element(By.ID, 'passwordNext').click()

        
        time.sleep(2) # for spoofing browser of not-a-bot

        continue_button_xpath = "//button[contains(span, 'Continue')]"
        try:
            WebDriverWait(self.browser, 20).until(
                EC.element_to_be_clickable((By.XPATH, continue_button_xpath))
            ).click()
        except TimeoutException:
            print("Continue button not found or not clickable")

        # Wait for a maximum of 10 seconds
        try:
            WebDriverWait(self.browser, 10).until(EC.url_to_be("http://localhost:8000/gauth/"))
        except TimeoutException:
            print("http://localhost:8000/gauth/ not redirected")

        self.assertIn('gauth', self.browser.current_url) # Or another expected URL
        self.assertIn('Authenticated', self.browser.page_source) # Or another indicator