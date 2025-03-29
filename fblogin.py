import random
import requests
import base64
import json
from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# Setup Chrome options to automatically allow notifications
chrome_options = Options()

# Automatically allow notifications for the website
prefs = {
    "profile.default_content_setting_values.notifications": 1
}
chrome_options.add_experimental_option("prefs", prefs)

# API Key for CAPTCHA
API_KEY_CAPTCHA = 'point_3d0bd505d511c336b6279f4815057b9a'
PAGE_REDIRECT_URL = "https://www.facebook.com/DCDarkLegion"

def image_to_base64(image_url):
    """Convert an image URL to base64."""
    response = requests.get(image_url)
    return base64.b64encode(response.content).decode('utf-8')

def solve_captcha(image_url):
    """Solve CAPTCHA by sending the base64 image to the CAPTCHA API."""
    base64_image = image_to_base64(image_url)
    payload = {
        'key': API_KEY_CAPTCHA,
        'type_captcha': 'Default v.1',
        'method': 'base64',
        'body': base64_image
    }
    response = requests.post('https://captcha69.com/in.php', data=payload)
    return response.text

def get_captcha_result(captcha_id):
    """Fetch CAPTCHA result using the provided captcha_id."""
    payload = {
        'key': API_KEY_CAPTCHA,
        'action': 'get',
        'id': captcha_id
    }
    response = requests.post('https://captcha69.com/res.php', data=payload)
    return response.text.split('|')[1]


def login_facebook(username, password):
    """Login to Facebook using Selenium."""
    service = Service(executable_path="./chromedriver.exe")
    browser = webdriver.Chrome(service=service, options=chrome_options)
    browser.get("https://facebook.com")
    WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.ID, "email")))

    browser.find_element(By.ID, "email").send_keys(username)
    browser.find_element(By.ID, "pass").send_keys(password)
    browser.find_element(By.ID, "pass").send_keys(Keys.ENTER)
    
    # Wait for Facebook to respond
    WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.TAG_NAME, "img")))
    return browser

def get_captcha_image(browser):
    """Retrieve CAPTCHA image if present on Facebook login page."""
    img_tags = browser.find_elements(By.TAG_NAME, "img")
    for img in img_tags:
        src = img.get_attribute("src")
        if src and "captcha" in src:
            return img
    return None


def submit_captcha(browser):
    """Click the 'Continue' button after entering the CAPTCHA text."""
    try:
        # Locate the div with role="button" and containing a span with the text "Continue"
        continue_button = WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@role='button']//span[text()='Continue']"))
        )
        continue_button.click()
    except Exception as e:
        print(f"Error locating or clicking the 'Continue' button: {e}")
        
        
def wait_for_redirect(browser, expected_url):
    """Wait for the page to redirect to the expected URL."""
    try:
        # Wait for URL to contain the expected part
        browser.get(expected_url)
        print(f"Page has been redirected to: {browser.current_url}")
    except Exception as e:
        print(f"Error: Page did not redirect to {expected_url}. Current URL: {browser.current_url}")
        print(f"Error details: {e}")

def wait_for_page_load(browser):
    """Wait for the page to load after submitting the CAPTCHA."""
    # Print the current URL after clicking the 'Continue' button
    print(f"Current URL before redirect: {browser.current_url}")
    WebDriverWait(browser, 30).until(
        EC.url_changes(browser.current_url)  # Wait until the URL changes
    )
    print(f"Page has been redirected to: {browser.current_url}")


def main():
    # List of Facebook accounts
    accounts = [
        ("0399988593", "p6+p7N&r%M$#B5b"),
        # Add more accounts if needed
    ]

    # Choose a random account
    username, password = random.choice(accounts)

    # Login to Facebook
    browser = login_facebook(username, password)

    # Retrieve CAPTCHA image
    captcha_img = get_captcha_image(browser)
    if captcha_img:
        captcha_img_url = captcha_img.get_attribute("src")
        print(f"Found CAPTCHA image: {captcha_img_url}")

        # Solve CAPTCHA
        captcha_id = solve_captcha(captcha_img_url).split('|')[1]
        captcha_text = get_captcha_result(captcha_id)

        print(f"Captcha Text: {captcha_text}")

        # Enter CAPTCHA in the input field
        captcha_input = browser.find_element(By.TAG_NAME, "input")
        captcha_input.send_keys(captcha_text)
        

        # Click the "Continue" button
        submit_captcha(browser)
        
        # Wait for the page to load and redirect to the expected URL
        wait_for_page_load(browser)

        # Check if we are on the expected page
        wait_for_redirect(browser, PAGE_REDIRECT_URL)
    else:
        print("No CAPTCHA image found.")

    # Wait to observe result and then close the browser
    sleep(30)
    browser.quit()

if __name__ == "__main__":
    main()
