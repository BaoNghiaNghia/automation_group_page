import os
import re
import random
import shutil
import pickle
import tempfile
import requests
from time import sleep
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from backend.utils.captcha_solver import solve_captcha, get_captcha_result
from backend.utils.index import get_all_game_fanpages
from backend.constants import (
    SCRAPER_FB_ACCOUNT_LIST, 
    FB_DEFAULT_URL,
    logger,
    ENV_CONFIG
)

def clear_uc_driver_cache():
    cache_dir = os.path.expandvars(r'%APPDATA%\undetected_chromedriver')
    if os.path.exists(cache_dir):
        try:
            shutil.rmtree(cache_dir)
            logger.info(f"Deleted undetected-chromedriver cache folder: {cache_dir}")
        except Exception as e:
            logger.warning(f"Failed to delete cache folder {cache_dir}: {e}")
    else:
        logger.info(f"No undetected-chromedriver cache folder found at {cache_dir}")


def init_browser(is_ubuntu=False):
    """Initialize Chrome browser with undetected-chromedriver options."""
    options = uc.ChromeOptions()

    # Common options
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-software-rasterizer')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-logging')
    options.add_argument('--log-level=3')
    options.add_argument('--silent')

    options.add_argument("--disable-session-crashed-bubble")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")

    prefs = {
        "profile.default_content_setting_values.notifications": 1,
        "profile.default_content_setting_values.media_stream_camera": 1,
        "profile.default_content_setting_values.media_stream_mic": 1,
        "profile.default_content_setting_values.geolocation": 1,
        "profile.managed_default_content_settings.javascript": 1,
        "profile.default_content_settings.cookies": 1
    }
    options.add_experimental_option("prefs", prefs)

    options.add_argument("--disable-blink-features=AutomationControlled")

    if is_ubuntu:
        options.binary_location = "/usr/bin/chromium"
        options.add_argument("--headless")
        browser = uc.Chrome(options=options, browser_executable_path="/usr/bin/chromium", headless=True, version_main=136)
    else:
        browser = uc.Chrome(options=options, version_main=136)

    # Set user agent
    browser.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })

    # Set window position and size
    screen_width = browser.execute_script("return window.screen.width")
    screen_height = browser.execute_script("return window.screen.height")
    window_width = int(screen_width * 0.5)
    window_height = int(screen_height * 1)
    browser.set_window_position(0, screen_height - window_height)
    browser.set_window_size(window_width, window_height)

    # Modify navigator.webdriver property
    browser.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    return browser


def login_facebook(username, password, is_ubuntu=False, use_cookies=True, cookies_path=None):
    """Login to Facebook using undetected-chromedriver with option to use saved cookies."""
    browser = init_browser(is_ubuntu)
    
    if not cookies_path:
        cookies_dir = os.path.join(os.getcwd(), "facebook_cookies")
        if not os.path.exists(cookies_dir):
            os.makedirs(cookies_dir)
        cookies_path = os.path.join(cookies_dir, f"{username}_cookies.pkl")
    
    if use_cookies and os.path.exists(cookies_path):
        browser.get(FB_DEFAULT_URL)
        try:
            logger.info(f"Attempting to login using cookies from {cookies_path}")
            with open(cookies_path, 'rb') as cookiesfile:
                cookies = pickle.load(cookiesfile)
                for cookie in cookies:
                    browser.add_cookie(cookie)
            browser.refresh()
            sleep(random.randint(3, 6))
            if is_logged_in(browser):
                logger.info(f"Successfully logged in using cookies for {username}")
                return browser
            else:
                logger.info("Cookie login failed, proceeding with normal login")
        except Exception as e:
            logger.error(f"Error loading cookies: {e}")

    browser.get(FB_DEFAULT_URL)
    sleep(random.randint(6, 12))
    WebDriverWait(browser, 3).until(EC.presence_of_element_located((By.ID, "email")))
    browser.find_element(By.ID, "email").send_keys(username)
    browser.find_element(By.ID, "pass").send_keys(password)
    browser.find_element(By.ID, "pass").send_keys(Keys.ENTER)
    sleep(random.randint(5, 10))

    if is_logged_in(browser):
        logger.info(f"Successfully logged in with credentials for {username}")
        save_cookies(browser, username, cookies_path)
    else:
        logger.warning(f"Login may have failed for {username}")
        if "checkpoint" in browser.current_url or "captcha" in browser.page_source.lower():
            logger.warning("Detected security checkpoint or CAPTCHA")
            if handle_captcha_if_present(browser, username, password):
                if is_logged_in(browser):
                    logger.info("Successfully logged in after CAPTCHA verification")
                    save_cookies(browser, username, cookies_path)
    return browser


def is_logged_in(browser):
    """Check if the user is logged in to Facebook."""
    try:
        WebDriverWait(browser, 5).until(
            EC.presence_of_element_located((By.XPATH, "//div[@aria-label='Your profile' or @aria-label='Account' or contains(@class, 'x1qhmfi1')]") )
        )
        logger.info("Login verification successful - user is logged in")
        return True
    except:
        logger.warning("Login verification failed - user is not logged in")
        return False


def save_cookies(browser, username, cookies_path=None):
    """Save browser cookies to a file."""
    if not cookies_path:
        cookies_dir = os.path.join(os.getcwd(), "facebook_cookies")
        if not os.path.exists(cookies_dir):
            os.makedirs(cookies_dir)
        cookies_path = os.path.join(cookies_dir, f"{username}_cookies.pkl")
    try:
        cookies = browser.get_cookies()
        with open(cookies_path, 'wb') as file:
            pickle.dump(cookies, file)
        logger.info(f"Cookies saved successfully to {cookies_path}")
        if os.path.exists(cookies_path) and os.path.getsize(cookies_path) > 0:
            logger.info(f"Cookie file verified: {os.path.getsize(cookies_path)} bytes")
        else:
            logger.warning("Cookie file may be empty or not created properly")
    except Exception as e:
        logger.error(f"Error saving cookies: {e}")


def submit_captcha(browser):
    """Click the 'Continue' button after entering the CAPTCHA text."""
    try:
        # Locate the div with role="button" and containing a span with the text "Continue"
        continue_button = WebDriverWait(browser, 3).until(
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
                WebDriverWait(browser, 3).until(
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


def run_sync_metadata_group(environment, use_cookies=True):
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
        username, password = random.choice(SCRAPER_FB_ACCOUNT_LIST)
        cookies_path = os.path.join(os.getcwd(), "facebook_cookies", f"{username}_cookies.pkl")
        browser = login_facebook(username, password, use_cookies=use_cookies, cookies_path=cookies_path)

        current_url = browser.current_url
        if current_url.startswith(f"{FB_DEFAULT_URL}/two_step_verification/authentication"):
            if not handle_captcha_if_present(browser, username, password):
                print("CAPTCHA handling failed, exiting.")
                return False  # Exit if CAPTCHA handling fails

        sleep_time = random.randint(3, 8)
        logger.info(f":::::: Sleeping for {sleep_time} seconds sync metadata of group...")
        
        # ----------------------- Scraper fanpages ----------------------- #
        list_game_fanpages = get_all_game_fanpages(environment)
        for idx, game in enumerate(list_game_fanpages, 1):
            try:
                if not game.get('my_group'):
                    logger.warning(f"No group URL found for game {idx}")
                    continue
                    
                group_url = game['my_group'].strip()
                if not group_url:
                    logger.warning(f"Empty group URL for game {idx}")
                    continue
                    
                browser.get('https://' + group_url)
                
                sleep(5)
                
                try:
                    # Check if we need to go to the news feed
                    news_feed_element = WebDriverWait(browser, 3).until(
                        EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div/div/div[1]/div[3]/a/div/div[1]/div/span/span"))
                    )
                    if news_feed_element.text == "Đi tới Bảng tin":
                        continue
                except Exception as e:
                    logger.error(f"Error navigating to news feed")
                
                try:
                    # Try first XPath
                    try:
                        group_name_element = WebDriverWait(browser, 3).until(
                            EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div[1]/div[2]/div/div/div/div/div[1]/div/div/div/div/div/div[1]/h1/span/a"))
                        )
                    except:
                        # If first XPath fails, try second XPath
                        group_name_element = WebDriverWait(browser, 3).until(
                            EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div/div[2]/div/div/div[1]/div[2]/div/div/div/div/div[1]/div/div/div/div/div/div[1]/h1/span/a"))
                        )
                    
                    group_name = group_name_element.text
                    logger.info(f"Group name: {group_name}")
                except Exception as e:
                    logger.error(f"Error getting group name: {e}")

                try:
                    # Try first XPath
                    try:
                        group_members_element = WebDriverWait(browser, 3).until(
                            EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div[1]/div[2]/div/div/div/div/div[1]/div/div/div/div/div/div[2]/span/div/div/span/div/div[3]/a"))
                        )
                    except:
                        # If first XPath fails, try second XPath
                        group_members_element = WebDriverWait(browser, 3).until(
                            EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div/div[2]/div/div/div[1]/div[2]/div/div/div/div/div[1]/div/div/div/div/div/div[2]/span/div/div/span/div/div[3]/a"))
                        )
                    
                    group_members = group_members_element.text
                    logger.info(f"Group members: {group_members}")
                except Exception as e:
                    logger.error(f"Error getting group members: {e}")
                    
                # Try to get group image
                try:
                    # Try first XPath
                    group_image_element = WebDriverWait(browser, 3).until(
                        EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div/div[2]/div/div/div[1]/div[1]/div/div/div/div/div[2]/div/a/div[1]/div/div/div/div/img"))
                    )
                except:
                    # If first XPath fails, try second XPath
                    group_image_element = WebDriverWait(browser, 3).until(
                        EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div/div[2]/div/div/div[1]/div[1]/div/div/div/div/div[2]/div/a/div[1]/div/div/div/img"))
                    )
                image_url = group_image_element.get_attribute('src')
                
                logger.info(f"Image URL: {image_url}")
                if image_url:
                    # Download the image
                    response = requests.get(image_url)
                    if response.status_code == 200:
                        cleaned_group_name = group_name.encode('ascii', 'ignore').decode('ascii')
                        cleaned_group_name = re.sub(r'[^\w\s]', '', cleaned_group_name)  # Remove special characters
                        cleaned_group_name = re.sub(r'\s+', '_', cleaned_group_name.strip())  # Replace spaces with underscores
                        
                        # Create a temporary file to store the image with cleaned group name
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg', prefix=f"{cleaned_group_name}_") as temp_file:
                            temp_file.write(response.content)
                            temp_file_path = temp_file.name
                        
                        try:
                            # Upload the image using the API
                            with open(temp_file_path, 'rb') as file:
                                files = {'file': file}
                                upload_response = requests.post(
                                    f'{ENV_CONFIG[environment]["SERVICE_URL"]}/game_fanpages/upload-image',
                                    files=files
                                )
                            
                            if upload_response.status_code == 200:
                                logger.info(f"Successfully uploaded image for game {game['id']}")
                                logger.info(f"Temporary file path: {os.path.basename(temp_file_path)}")
                                # Update screenshot_path after successful upload
                                update_data = {
                                    "screenshot_path": os.path.basename(temp_file_path)
                                }
                                update_response = requests.patch(
                                    f'{ENV_CONFIG[environment]["SERVICE_URL"]}/game_fanpages/update/{game["id"]}',
                                    headers={'Content-Type': 'application/json'},
                                    json=update_data
                                )
                                
                                if update_response.status_code == 200:
                                    logger.info(f"Successfully updated screenshot_path for game {game['id']}")
                                else:
                                    logger.error(f"Failed to update screenshot_path for game {game['id']}. Status code: {update_response.status_code}")
                            else:
                                logger.error(f"Failed to upload image for game {game['id']}. Status code: {upload_response.status_code}")
                        finally:
                            # Clean up the temporary file
                            try:
                                os.unlink(temp_file_path)
                            except Exception as e:
                                logger.error(f"Error cleaning up temporary file: {e}")
                
                try:
                    # Prepare data for API update
                    update_data = {
                        "name_of_game": group_name or "",
                        "group_search_name": group_members or ""
                    }
                    # Make API request to update game fanpage
                    response = requests.patch(
                        f'{ENV_CONFIG[environment]["SERVICE_URL"]}/game_fanpages/update/{game["id"]}',
                        headers={'Content-Type': 'application/json'},
                        json=update_data
                    )
                    
                    if response.status_code == 200:
                        logger.info(f"Successfully updated metadata for game {game['id']}")
                    else:
                        logger.error(f"Failed to update metadata for game {game['id']}. Status code: {response.status_code}")
                        
                except Exception as e:
                    logger.error(f"Error updating metadata for game {game['id']}: {e}")
                
                sleep(random.randint(6, 9))
                
            except Exception as e:
                logger.error(f"Error redirecting to group URL")
                continue
        
        return True

    except Exception as e:
        print(f"Error in main scraper: {e}")
        return False  # Exit if an error occurs during the main scraper execution

    finally:
        # Close browser after processing all games
        try:
            browser.quit()
            print("Browser closed successfully.")
        except Exception as e:
            print(f"Error closing browser: {e}")

