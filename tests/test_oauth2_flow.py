import os
import time
from unittest import skipIf

import undetected_chromedriver as uc    # pylint: disable=import-error
from django.test import LiveServerTestCase  # pylint: disable=import-error
from selenium.common.exceptions import TimeoutException # pylint: disable=import-error
from selenium.webdriver.common.by import By # pylint: disable=import-error
from selenium.webdriver.support import expected_conditions as EC    # pylint: disable=import-error
from selenium.webdriver.support.ui import WebDriverWait # pylint: disable=import-error

from tests import env


class GoogleOAuthTest(LiveServerTestCase):
    """
    Test Oauth2 Flow in Gauth
    """
    host = 'localhost'
    port = 8000
    def setUp(self):    # pylint: disable=invalid-name

        # self.browser = webdriver.Chrome() # Or Firefox, Edge, etc.
        # Create ChromeOptions for undetected_chromedriver
        chrome_options = uc.ChromeOptions()
        # Add any desired arguments, e.g., incognito, disable extensions
        chrome_options.add_argument("--incognito")
        # Initialize the undetected_chromedriver
        self.browser = uc.Chrome(version_main=142, options=chrome_options)
        self.browser.implicitly_wait(10) # Wait for elements to load

    def tearDown(self): # pylint: disable=invalid-name
        print("cleaning...")
        self.browser.quit()

    @skipIf(
        os.environ.get('AUTOMATION', '0') == '0',
        "Skipping resource-intensive test by default."
    )
    def test_google_oauth_login(self):
        """
        Test Successful Login from Gauth Page
        """
        self.browser.get(self.live_server_url + '/gauth/') # Your login URL
        # Click the Google login button (adjust selector as needed)
        google_login_button = self.browser.find_element(By.ID, 'AuthenticateButton')
        google_login_button.click()
        time.sleep(2) # for spoofing browser of not-a-bot
        # Google's login page
        # Input test user credentials (replace with actual test user email/password)
        email_input = self.browser.find_element(By.ID, 'identifierId')
        email_input.send_keys(env.str('TEST_GOOGLE_ACCOUNT'))
        self.browser.find_element(By.ID, 'identifierNext').click()
        time.sleep(2) # for spoofing browser of not-a-bot
        # password_input = self.browser.find_element(By.NAME, 'password')
        password_input = self.browser.find_element(
            By.XPATH,
            "//div[@id='password']//input[@type='password']"
        )
        password_input.send_keys(env.str('TEST_GOOGLE_PASSWORD'))
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

        self.browser.close()
