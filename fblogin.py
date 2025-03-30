import random
from urllib.parse import urlparse, parse_qs
import requests
import base64
from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from constants import FB_ACCOUNT_LIST, FB_DEFAULT_URL, GAME_NAME_URL, API_KEY_CAPTCHA

# API Key for CAPTCHA





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
    # Setup Chrome options to automatically allow notifications
    chrome_options = Options()

    # Automatically allow notifications for the website
    prefs = {
        "profile.default_content_setting_values.notifications": 1
    }
    chrome_options.add_experimental_option("prefs", prefs)

    service = Service(executable_path="./chromedriver.exe")
    browser = webdriver.Chrome(service=service, options=chrome_options)
    browser.get(FB_DEFAULT_URL)
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


def extract_post_id_from_url(url):
    """Extract post ID from a Facebook post URL."""
    try:
        path = urlparse(url).path
        if "/posts/" in path:
            post_id = path.split("/posts/")[1].split("?")[0]
            return post_id
    except Exception as e:
        print(f"Failed to extract post ID from {url}: {e}")
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


def get_posts_by_attribute(browser):
    posts = []
    try:
        post_links = browser.find_elements(By.XPATH, "//a[starts-with(@href, 'https://www.facebook.com/DCDarkLegion/posts')]")
        for link in post_links:
            href = link.get_attribute('href')
            post_id = extract_post_id_from_url(href)
            if post_id and post_id not in posts:
                posts.append(post_id)
    except Exception as e:
        print(f"Error retrieving posts: {e}")
    return posts



def scroll_down(browser):
    browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    sleep(5)  # Wait for content to load



def main():
    # Choose a random account
    username, password = random.choice(FB_ACCOUNT_LIST)

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
        wait_for_redirect(browser, FB_DEFAULT_URL + GAME_NAME_URL)
        
        all_posts = set()
        for i in range(7):
            print(f"\n[Scraping Round {i + 1}]")
            new_posts = get_posts_by_attribute(browser)
            for post in new_posts:
                if post not in all_posts:
                    all_posts.add(post)
                    print(post)
            scroll_down(browser)

        print(f"\nTotal unique posts collected: {len(all_posts)}")
        
        # Save to file
        with open(f"facebook_{GAME_NAME_URL}_post_ids.txt", "w", encoding="utf-8") as f:
            for post_id in sorted(all_posts):
                f.write(post_id + "\n")
        print(f"Post IDs saved to facebook_{GAME_NAME_URL}_post_ids.txt")
    else:
        print("No CAPTCHA image found.")

    # Wait to observe result and then close the browser
    sleep(500)
    browser.quit()

if __name__ == "__main__":
    main()
