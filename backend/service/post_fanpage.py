import os
import random
import pickle
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from backend.utils.index import decrypt_string

from backend.utils.captcha_solver import solve_captcha, get_captcha_result
from backend.constants import (
    FB_DEFAULT_URL, 
    EDITOR_ACCOUNT_FACEBOOK,
    logger
)


def init_browser(is_ubuntu=False):
    """Initialize Chrome browser with required options."""
    chrome_options = Options()

    # Common options
    prefs = {
        "profile.default_content_setting_values.notifications": 1
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    # Remove the "Chrome is being controlled by automated test software" message
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    if is_ubuntu:
        # Ubuntu-specific options
        chrome_options.binary_location = "/usr/bin/chromium"
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        service = Service("/usr/bin/chromedriver")
    else:
        # Windows-specific options
        service = Service(executable_path="./chromedriver.exe")

    browser = webdriver.Chrome(service=service, options=chrome_options)
    
    # Additional step to modify navigator.webdriver property
    browser.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return browser

def login_facebook(username, password, is_ubuntu=False, use_cookies=True, cookies_path=None):
    """Login to Facebook using Selenium with option to use saved cookies."""
    browser = init_browser(is_ubuntu)
    
    # Set default cookies path if not provided
    if not cookies_path:
        cookies_dir = os.path.join(os.getcwd(), "facebook_cookies")
        if not os.path.exists(cookies_dir):
            os.makedirs(cookies_dir)
        cookies_path = os.path.join(cookies_dir, f"{username}_cookies.pkl")
    
    if use_cookies and os.path.exists(cookies_path):
        # Load cookies if available
        browser.get(FB_DEFAULT_URL)
        try:
            logger.info(f"Attempting to login using cookies from {cookies_path}")
            with open(cookies_path, 'rb') as cookiesfile:
                cookies = pickle.load(cookiesfile)
                for cookie in cookies:
                    browser.add_cookie(cookie)
            
            # Refresh page to apply cookies
            browser.refresh()
            sleep(random.randint(3, 6))
            
            # Check if login was successful
            if is_logged_in(browser):
                logger.info(f"Successfully logged in using cookies for {username}")
                return browser
            else:
                logger.info("Cookie login failed, proceeding with normal login")
        except Exception as e:
            logger.error(f"Error loading cookies: {e}")
    
    # Normal login if cookies not available or failed
    browser.get(FB_DEFAULT_URL)
    sleep(random.randint(6, 12))
    
    # Wait for login elements and enter credentials
    WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.ID, "email")))
    browser.find_element(By.ID, "email").send_keys(username)
    browser.find_element(By.ID, "pass").send_keys(password)
    browser.find_element(By.ID, "pass").send_keys(Keys.ENTER)

    # Wait for Facebook to respond after login
    sleep(random.randint(5, 10))

    # Check if login was successful and save cookies
    if is_logged_in(browser):
        logger.info(f"Successfully logged in with credentials for {username}")
        save_cookies(browser, username, cookies_path)
    else:
        logger.warning(f"Login may have failed for {username}")

        # Check for CAPTCHA or other verification
        if "checkpoint" in browser.current_url or "captcha" in browser.page_source.lower():
            logger.warning("Detected security checkpoint or CAPTCHA")
            # Handle CAPTCHA if present
            if handle_captcha_if_present(browser, username, password):
                # After handling CAPTCHA, check login again and save cookies
                if is_logged_in(browser):
                    logger.info("Successfully logged in after CAPTCHA verification")
                    save_cookies(browser, username, cookies_path)

    return browser

def is_logged_in(browser):
    """Check if the user is logged in to Facebook."""
    try:
        # Look for elements that indicate a successful login
        # This could be a profile picture, notifications icon, etc.
        WebDriverWait(browser, 5).until(
            EC.presence_of_element_located((By.XPATH, "//div[@aria-label='Your profile' or @aria-label='Account' or contains(@class, 'x1qhmfi1')]"))
        )
        logger.info("Login verification successful - user is logged in")
        return True
    except:
        logger.warning("Login verification failed - user is not logged in")
        return False

def save_cookies(browser, username, cookies_path=None):
    """Save browser cookies to a file."""
    if not cookies_path:
        # Create cookies directory if it doesn't exist
        cookies_dir = os.path.join(os.getcwd(), "facebook_cookies")
        if not os.path.exists(cookies_dir):
            os.makedirs(cookies_dir)
        cookies_path = os.path.join(cookies_dir, f"{username}_cookies.pkl")
    
    # Save cookies
    try:
        cookies = browser.get_cookies()
        with open(cookies_path, 'wb') as file:
            pickle.dump(cookies, file)
        logger.info(f"Cookies saved successfully to {cookies_path}")
        
        # Verify cookie file was created
        if os.path.exists(cookies_path) and os.path.getsize(cookies_path) > 0:
            logger.info(f"Cookie file verified: {os.path.getsize(cookies_path)} bytes")
        else:
            logger.warning("Cookie file may be empty or not created properly")
    except Exception as e:
        logger.error(f"Error saving cookies: {e}")


def login_facebook_ubuntu(username, password, use_cookies=True):
    """Convenience function for Ubuntu login."""
    cookies_path = os.path.join(os.getcwd(), "facebook_cookies", f"{username}_cookies.pkl")
    return login_facebook(username, password, is_ubuntu=True, use_cookies=use_cookies, cookies_path=cookies_path)



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


def scroll_down(browser):
    """Scroll down the page to load more posts."""
    browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    sleep(random.randint(5, 9))  # Wait for content to load


def get_captcha_image(browser):
    """Retrieve CAPTCHA image if present on Facebook login page."""
    img_tags = browser.find_elements(By.TAG_NAME, "img")
    for img in img_tags:
        src = img.get_attribute("src")
        if src and "captcha" in src:
            return img
    return None


def handle_captcha_if_present(browser, username, password):
    """
    This function handles CAPTCHA challenges that may appear during the login process.
    If a CAPTCHA is detected, it solves the CAPTCHA, re-enters login credentials if necessary,
    and continues the browsing session.

    Args:
        browser (webdriver.Chrome): The browser instance used for Selenium automation.
        username (str): The username (email) for logging into Facebook.
        password (str): The password for logging into Facebook.

    Returns:
        bool: Returns True if CAPTCHA was detected and handled, False otherwise.
    """
    try:
        # Look for CAPTCHA image on the page
        captcha_img = get_captcha_image(browser)
        if captcha_img:
            captcha_img_url = captcha_img.get_attribute("src")
            print(f"Found CAPTCHA image: {captcha_img_url}")

            # Solve the CAPTCHA and get the solution
            captcha_id = solve_captcha(captcha_img_url).split('|')[1]
            captcha_text = get_captcha_result(captcha_id)
            print(f"Captcha Response: {captcha_text}")

            # Enter the CAPTCHA solution in the input field and submit it
            captcha_input = browser.find_element(By.TAG_NAME, "input")
            captcha_input.send_keys(captcha_text)

            # Click the "Continue" button to proceed
            submit_captcha(browser)
            sleep(random.randint(5, 9))

            # Try to re-login if necessary
            try:
                WebDriverWait(browser, 10).until(
                    EC.presence_of_element_located((By.ID, "email"))
                )
                # Re-enter login credentials and submit
                browser.find_element(By.ID, "email").send_keys(username)
                browser.find_element(By.ID, "pass").send_keys(password + Keys.ENTER)
            except Exception:
                print("Re-login not required or already logged in.")
            
            return True  # CAPTCHA was handled successfully
        else:
            print("No CAPTCHA image found, continuing process.")

    except Exception as e:
        print(f"Error while handling CAPTCHA: {e}")
        

def run_post_fanpage_with_editor_role(use_cookies=True):
    """
    Run Facebook scraper for multiple fanpages using a single browser session
    
    Args:
        all_game_fanpages (list): List of game URLs to scrape
        use_cookies (bool): Whether to use saved cookies for login
        
    Returns:
        bool: True if scraping completed successfully, False otherwise
    """
    try:
        # Choose a random account and login
        username, password = random.choice(EDITOR_ACCOUNT_FACEBOOK)
        username_decrypted = decrypt_string(username)
        password_decrypted = decrypt_string(password)
        cookies_path = os.path.join(os.getcwd(), "facebook_cookies", f"{username_decrypted}_cookies.pkl")
        browser = login_facebook(username_decrypted, password_decrypted, use_cookies=use_cookies, cookies_path=cookies_path)

        current_url = browser.current_url
        if current_url.startswith(f"{FB_DEFAULT_URL}/two_step_verification/authentication"):
            if not handle_captcha_if_present(browser, username_decrypted, password_decrypted):
                print("CAPTCHA handling failed, exiting.")
                return False

        sleep_time = random.randint(3, 8)
        logger.info(f":::::: Sleeping for {sleep_time} seconds after scraping all games...")
        sleep(sleep_time)
            
        return True

    except Exception as e:
        print(f"Error in main scraper: {e}")
        return False

    finally:
        try:
            browser.quit()
            print("Browser closed successfully.")
        except Exception as e:
            print(f"Error closing browser: {e}")
