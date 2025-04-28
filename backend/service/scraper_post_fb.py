import os
import time
import random
import pickle
import requests
from PIL import Image
from io import BytesIO
from time import sleep
from selenium import webdriver
from urllib.parse import urlparse
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from backend.utils.captcha_solver import solve_captcha, get_captcha_result
from backend.utils.index import get_all_game_fanpages
from backend.constants import FB_ACCOUNT_LIST, FB_DEFAULT_URL, FOLDER_PATH_DATA_CRAWLER, LIMIT_POST_PER_DAY, FOLDER_PATH_POST_ID_CRAWLER, FB_DEFAULT_URL, ENV_CONFIG, SHARE_COMMENT_IN_POST, logger


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


def extract_post_id_from_url(url):
    try:
        path = urlparse(url).path
        if "/posts/" in path:
            return path.split("/posts/")[1].split("?")[0]
        elif "/permalink/" in path:
            return path.split("/permalink/")[1].split("?")[0]
        elif "story_fbid=" in url:
            return url.split("story_fbid=")[1].split("&")[0]
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


def get_posts_by_attribute(browser, game_name):
    posts = []
    try:
        # Concatenate the URL parts before using them in the XPath
        base_url = f"{FB_DEFAULT_URL}/{game_name}/posts"
        post_links = browser.find_elements(By.XPATH, f"//a[starts-with(@href, '{base_url}')]")
        
        for link in post_links:
            href = link.get_attribute('href')
            post_id = extract_post_id_from_url(href)
            if post_id and post_id not in posts:
                posts.append(post_id)

                print(f"Post ID found: {post_id}")
    except Exception as e:
        print(f"Error retrieving posts: {e}")
    return posts

def scroll_down(browser):
    browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    sleep(random.randint(5, 9))  # Wait for content to load


def clonePostContent(driver, postId):
    try:
        driver.get(f"{FB_DEFAULT_URL}/{str(postId)}")
        
        # Find the content element containing all the text
        contentElement = driver.find_elements(By.XPATH, "/html/body/div[1]/div/div[1]/div/div[5]/div/div/div[2]/div/div/div/div/div/div/div/div[2]/div[2]/div/div/div/div/div/div/div/div/div/div/div/div/div[13]/div/div/div[3]/div[1]")
        
        content = ""
        # Get all text from contentElement
        if len(contentElement):
            content = " ".join([elem.text for elem in contentElement])  # Concatenate text from all elements
        

        # Get all image links inside the specific path provided
        linksArr = []

        image_links = driver.find_elements(By.XPATH, "/html/body/div[1]/div/div[1]/div/div[5]/div/div/div[2]/div/div/div/div/div/div/div/div[2]/div[2]/div/div/div/div/div/div/div/div/div/div/div/div/div[13]/div/div/div[3]/div[2]/div//a//img")
        
        for img in image_links:
            linkImage = img.get_attribute('src')
            if linkImage:
                linksArr.append(linkImage)

        postData = {"post_id": postId, "content": content, "images": linksArr}

        return postData
    except Exception as e:
        print(f"Error in clonePostContent: {e}")
        return False

# Function to download image and save with the correct extension
def download_image_file(image_url, file_number, post_id, folder_path="/data_crawl/", game_name=""):
    try:
        # Create the folder for the post if it doesn't exist
        post_path = os.path.join(os.getcwd(), folder_path.strip("/\\"), f"{game_name}_{str(post_id)}")
        if not os.path.exists(post_path):
            os.makedirs(post_path)

        # Extract the file name from the URL (or use a default name)
        image_name = image_url.split("/")[-1]

        # Get the file extension (jpeg, png, etc.) from the URL
        file_extension = os.path.splitext(image_name)[1]

        # If no file extension is found in the URL, request the file to get the content type
        if not file_extension:
            response = requests.get(image_url, stream=True)
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                if 'image/jpeg' in content_type:
                    file_extension = '.jpg'
                elif 'image/png' in content_type:
                    file_extension = '.png'
                elif 'image/gif' in content_type:
                    file_extension = '.gif'
                else:
                    print(f"Unknown image format for URL: {image_url}")
                    return
            else:
                print(f"Failed to fetch image headers, Status code: {response.status_code}")
                return

        # Check image dimensions before downloading
        response = requests.get(image_url, stream=True)
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            width, height = img.size
            
            # Only download if width or height is greater than 100px
            if width <= 100 and height <= 100:
                return
            
            # Update the image name with the correct file extension
            image_name = f"{post_id}_{file_number}.png"
            
            # Save the image
            with open(os.path.join(post_path, image_name), 'wb') as handler:
                handler.write(response.content)
            
            print(f"Image saved as {image_name} in {post_path} (dimensions: {width}x{height})")
        else:
            print(f"Failed to fetch image, Status code: {response.status_code}")
            
    except Exception as e:
        print(f"Error downloading image from {image_url}: {e}")


def crawlPostData(driver, postIds, game_name, environment, list_game_fanpages):
    empty_post_count = 0  # Counter for empty posts
    written_post_count = 0  # Counter for posts written to file


    # Create a mapping of game fanpage URLs to their IDs
    game_fanpages_id_map = {}
    for item in list_game_fanpages:
        # Extract the last part of the fanpage URL (after the last slash)
        fanpage_key = item['fanpage'].rstrip('/').split('/')[-1]
        game_fanpages_id_map[fanpage_key] = item['id']
    
    # Get the game_fanpage_id for the current game
    game_fanpage_id = game_fanpages_id_map.get(game_name)

    for id in postIds:
        try:
            dataPost = clonePostContent(driver, id)
            if dataPost:
                postId = str(dataPost['post_id'])
                postContent = str(dataPost['content'])

                # Check if postContent is not empty
                if postContent.strip() == "":
                    empty_post_count += 1
                    print(f"Skipping post with ID {postId} because content is empty.")
                    continue  # Skip this post and move to the next one
                else:
                    # Save post content to file
                    writeFileTxtPost('content.txt', postContent, postId, FOLDER_PATH_DATA_CRAWLER, game_name)
                    written_post_count += 1
                    print("----------------------------------------")
                    print(f"Post ID: {postId} - Content: {postContent[:50]}{'...' if len(postContent) > 50 else ''}")

                stt = 0
                for img in dataPost["images"]:
                    stt += 1
                    download_image_file(img, str(stt), postId, FOLDER_PATH_DATA_CRAWLER, game_name)
                    
            # Click on the specified element (like button or reaction)
            try:
                # Wait for a random time before clicking to simulate human behavior
                sleep(random.uniform(1.5, 3.0))
                
                # Find and click the specified element
                like_button = driver.find_element(By.XPATH, 
                    "/html/body/div[1]/div/div[1]/div/div[5]/div/div/div[2]/div/div/div/div/div/div/div/div[2]/div[2]/div/div/div/div/div/div/div/div/div/div/div/div/div[13]/div/div/div[4]/div/div/div[1]/div/div[1]/div/div[1]/div/span/div/span[2]")
                
                
                # Scroll element into view
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", like_button)
                
                # Wait a moment after scrolling
                sleep(random.uniform(0.8, 1.5))
                
                # Click the element
                like_button.click()
                print(f"Clicked on reaction element for post ID: {id}")
                
                # Wait for about 7 seconds after clicking like button
                sleep_time = random.uniform(6.5, 9.5)
                print(f"Waiting for {sleep_time:.2f} seconds after clicking like button...")
                sleep(sleep_time)
                
                # Call the function to handle reaction panel
                handle_get_friend_reaction_post_panel(driver, game_fanpage_id, environment)

                
                # Wait a moment after clicking
                sleep(random.uniform(1.0, 2.0))
            except Exception as e:
                print(f"Could not click on reaction element: {e}")

            sleep(random.randint(12, 14))
        except Exception as e:
            print(f"Error in crawlPostData: {e}")

    # Print total counts after processing
    print(f"\nTotal empty posts skipped: {empty_post_count}")
    print(f"Total posts written to file: {written_post_count}")

# Function to handle reaction panel scrolling and profile extraction
def handle_get_friend_reaction_post_panel(driver, game_fanpage_id, environment):
    try:
        # Define reaction panel xpath as a constant
        REACTION_PANEL_XPATH_OPTION_1 = "/html/body/div[7]/div[1]/div/div[2]/div/div/div"
        REACTION_PANEL_XPATH_OPTION_2 = "/html/body/div[5]/div[1]/div/div[2]/div/div/div"
        REACTION_PANEL_XPATH_OPTION_3 = "/html/body/div[6]/div[1]/div/div[2]/div/div/div"
        
        # Try all xpath options in sequence
        reaction_panel = None
        panel_xpath_used = None
        
        xpath_options = [
            (REACTION_PANEL_XPATH_OPTION_1, "OPTION_1"),
            (REACTION_PANEL_XPATH_OPTION_2, "OPTION_2"),
            (REACTION_PANEL_XPATH_OPTION_3, "OPTION_3")
        ]
        
        for xpath, option_name in xpath_options:
            try:
                reaction_panel = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, xpath))
                )
                panel_xpath_used = xpath
                print(f"Found reaction panel with {option_name}")
                break
            except Exception as e:
                print(f"Could not find reaction panel with {option_name}: {e}")

        # Only proceed if we found a reaction panel
        if reaction_panel:
            # Add a random sleep to ensure the panel is fully loaded
            sleep(random.uniform(1.0, 2.0))

            try:
                panel_container = driver.find_element(By.XPATH, f"{panel_xpath_used}/div/div/div/div[2]/div[2]/div/div/div[2]")

                drag_element = driver.find_element(By.XPATH, f"{panel_xpath_used}/div/div/div/div[2]/div[2]/div/div/div[3]")
                
                # Get positions and dimensions
                panel_container_rect = driver.execute_script("return arguments[0].getBoundingClientRect();", panel_container)
                drag_element_rect = driver.execute_script("return arguments[0].getBoundingClientRect();", drag_element)
                
                panel_bottom = panel_container_rect['bottom']
                drag_bottom = drag_element_rect['bottom']

                # Calculate how many scrolls needed to align bottoms
                scroll_rounds = 0
                current_bottom_diff = abs(panel_bottom - drag_bottom)
                
                # Continue scrolling until bottoms are aligned or very close
                while current_bottom_diff > 5 and scroll_rounds < 25:
                    action = ActionChains(driver)
                    action.click_and_hold(drag_element)
                    sleep(random.uniform(1, 3))  # Hold for a moment
                    
                    # Adjust scroll distance based on difference
                    scroll_distance = min(100, current_bottom_diff)
                    action.move_by_offset(0, scroll_distance)
                    action.release()
                    action.perform()
                    
                    sleep(random.uniform(1, 3))
                    scroll_rounds += 1
                    
                    # Update positions after scrolling
                    panel_container_rect = driver.execute_script("return arguments[0].getBoundingClientRect();", panel_container)
                    drag_element_rect = driver.execute_script("return arguments[0].getBoundingClientRect();", drag_element)
                    panel_bottom = panel_container_rect['bottom']
                    drag_bottom = drag_element_rect['bottom']
                    current_bottom_diff = abs(panel_bottom - drag_bottom)
                    
                    print(f"Completed scroll round {scroll_rounds}, bottom difference: {current_bottom_diff}px")
                
                print(f"Finished scrolling after {scroll_rounds} rounds, final bottom difference: {current_bottom_diff}px")
                
                # Click on panel container to finish interaction
                ActionChains(driver).move_to_element(panel_container).click().perform()
                sleep(random.uniform(0.3, 0.7))
                
            except Exception as scroll_error:
                print(f"Error during scroll attempt: {str(scroll_error)}")
                
            # Extract reaction links after scrolling
            try:
                reaction_links = reaction_panel.find_elements(By.CSS_SELECTOR, "a[role='link'][tabindex='0']")
                
                if reaction_links:
                    unique_profile_ids = set()
                    for i, link in enumerate(reaction_links):
                        href = link.get_attribute("href")
                        profile_id = None
                        # Skip Facebook stories links
                        if "facebook.com/stories" in href:
                            continue
                        # Extract profile ID from href
                        if "profile.php?id=" in href:
                            profile_id = href.split("profile.php?id=")[1].split("&")[0]
                        elif "facebook.com/" in href:
                            profile_id = href.split("facebook.com/")[1].split("?")[0].split("&")[0]
                        
                        if profile_id:
                            unique_profile_ids.add(profile_id)
                    print(f"Found {len(unique_profile_ids)} unique profile IDs:")
                    for idx, profile_id in enumerate(unique_profile_ids):
                        print(f"  Unique Profile {idx+1}: {profile_id}")
                        
                    # Save profile IDs to API in batches of 10
                    if unique_profile_ids:
                        try:                                 
                            # Process in batches of 10
                            profile_list = list(unique_profile_ids)
                            batch_size = 20
                            
                            for i in range(0, len(profile_list), batch_size):
                                batch = profile_list[i:i+batch_size]
                                payload = []
                                
                                for profile_id in batch:
                                    payload.append({
                                        "profile_id": profile_id,
                                        "game_fanpages_id": game_fanpage_id
                                    })
                                
                                # Make API request
                                import requests
                                import json
                                
                                headers = {'Content-Type': 'application/json'}
                                api_url = f'{ENV_CONFIG[environment]["SERVICE_URL"]}/friend_list_group_game/insert-batch'
                                
                                response = requests.post(api_url, headers=headers, data=json.dumps(payload))
                                
                                if response.status_code == 200:
                                    print(f"Successfully sent batch of {len(batch)} profile IDs to API")
                                else:
                                    print(f"API request failed with status code {response.status_code}: {response.text}")
                                    
                        except Exception as api_error:
                            print(f"Error sending profile IDs to API: {str(api_error)}")
                else:
                    print("No reaction links found in the panel")
            except Exception as e:
                print(f"Error extracting reaction links: {e}")

            print("Completed scrolling through the reaction panel")
        else:
            print("No reaction panel found with any XPATH option, skipping panel interaction")

    except Exception as e:
        print(f"Could not scroll through reaction panel: {e}")

# Function to save content to a file
def writeFileTxtPost(fileName, content, idPost, pathImg="/img/", game_name=""):
    # Normalize and build the path properly
    post_path = os.path.join(os.getcwd(), pathImg.strip("/\\"), f"{game_name}_{str(idPost)}")

    if not os.path.exists(post_path):
        os.makedirs(post_path)

    file_path = os.path.join(post_path, fileName)

    try:
        with open(file_path, 'a', encoding="utf-8") as f1:
            f1.write(content + os.linesep)
        print(f"Content written to {file_path}")
    except Exception as e:
        print(f"Error writing to file {file_path}: {e}")


# Read Post IDs from file (assumed function)
def readData(fileName):
    with open(fileName, 'r', encoding="utf-8") as f:
        return [line.strip() for line in f.readlines()]
    
    
def run_fb_scraper_single_fanpage_posts(game_name, use_cookies=True):
    try:
        # Choose a random account and login
        username, password = random.choice(FB_ACCOUNT_LIST)
        cookies_path = os.path.join(os.getcwd(), "facebook_cookies", f"{username}_cookies.pkl")
        browser = login_facebook(username, password, use_cookies=use_cookies, cookies_path=cookies_path)

        sleep(random.randint(2, 5))

        # Handle CAPTCHA if present
        if handle_captcha_if_present(browser, username, password):
            # Save cookies again after CAPTCHA handling
            if is_logged_in(browser):
                save_cookies(browser, username, cookies_path)
                
            # Wait for redirect to the game page
            wait_for_redirect(browser, f"{FB_DEFAULT_URL}/{game_name}")

            all_posts = set()
            last_height = browser.execute_script("return document.body.scrollHeight")

            # Scroll and collect posts, with a maximum number of attempts
            for attempt in range(50):
                print(f"\n[Scrolling Attempt {attempt + 1}]")
                current_posts = get_posts_by_attribute(browser, game_name)
                all_posts.update(current_posts)

                if len(all_posts) >= LIMIT_POST_PER_DAY:
                    print("Limit of posts reached.")
                    break

                # Check if no posts found after 3 attempts
                if attempt >= 3 and len(all_posts) == 0:
                    print("No posts found after 3 attempts, exiting.")
                    sleep(random.randint(10, 15))
                    browser.quit()
                    return

                # Scroll down smoothly to load more posts
                scheight = 1.0
                while scheight < 10.0:
                    browser.execute_script("window.scrollTo(0, document.body.scrollHeight/%s);" % scheight)
                    scheight += 0.01
                    sleep(0.01)  # Small pause between scroll increments
                
                # Add a small pause after smooth scrolling
                sleep(random.uniform(1.0, 2.0))
                
                new_height = browser.execute_script("return document.body.scrollHeight")

                # If no new content is loaded, stop scrolling
                if new_height == last_height:
                    print("Reached the end of the page, stopping scroll.")
                    break

                last_height = new_height

                if attempt == 49:
                    print("Too many scroll attempts, exiting.")

            # Output the number of posts collected
            print(f"\nTotal unique posts collected: {len(all_posts)}")

            # Save the post IDs to a file
            post_id_file_path = os.path.join(os.getcwd(), FOLDER_PATH_POST_ID_CRAWLER.strip("/\\"))
            if not os.path.exists(post_id_file_path):
                os.makedirs(post_id_file_path)

            post_id_file_name = f"facebook_{game_name}_post_ids.txt"
            post_id_full_path = os.path.join(post_id_file_path, post_id_file_name)

            with open(post_id_full_path, "w", encoding="utf-8") as f:
                f.write("\n".join(sorted(all_posts)))

            # Crawl and download post data
            crawlPostData(browser, readData(post_id_full_path), game_name)

            print(f"----- Done {all_posts} posts: Game {game_name} -----")

        else:
            print("No CAPTCHA image found or failed to handle CAPTCHA.")

    except Exception as e:
        print(f"Error in main: {e}")

    finally:
        # Ensure the browser is closed properly
        try:
            browser.quit()
            print("Browser closed successfully.")
        except Exception as e:
            print(f"Error closing browser: {e}")
    
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
        

# Simulate human behavior between scraping games
def simulate_human_behavior_when_scraping_game(browser, environment):
    try:
        logger.info("Simulating human behavior...")
        
        game_fanpages = get_all_game_fanpages(environment)
        if not game_fanpages:
            logger.error("No game URLs found from get_game_fanpages")
            raise Exception("No game URLs found from get_game_fanpages")
        
        group_search_names = [game["group_search_name"] for game in game_fanpages if "group_search_name" in game]
        
        # Navigate to Facebook Watch
        logger.info("Navigating to Facebook Watch...")
        browser.get(f"{FB_DEFAULT_URL}/watch")
        
        # Scroll on Watch page for 2-3 minutes
        watch_duration = random.randint(150, 210)  # 2-3 minutes
        logger.info(f"Scrolling on Watch page for {watch_duration} seconds...")
        start_time = time.time()
        
        # Use more natural scrolling patterns with variable speeds and distances
        while time.time() - start_time < watch_duration:
            # Natural scrolling with acceleration and deceleration
            scroll_pattern = random.choice(["smooth", "quick", "pause_heavy"])
            
            if scroll_pattern == "smooth":
                # Smooth scrolling with gradual acceleration
                for i in range(3, 8):
                    scroll_amount = i * 100  # Gradually increasing scroll amount
                    browser.execute_script(f"window.scrollBy(0, {scroll_amount});")
                    time.sleep(random.uniform(0.3, 0.7))
            elif scroll_pattern == "quick":
                # Quick scroll followed by pause (like finding something interesting)
                scroll_amount = random.randint(500, 1200)
                browser.execute_script(f"window.scrollBy(0, {scroll_amount});")
            else:  # pause_heavy
                # Small scroll with longer pause (like reading content)
                scroll_amount = random.randint(200, 400)
                browser.execute_script(f"window.scrollBy(0, {scroll_amount});")
            
            # Variable pauses between scrolling actions
            if random.random() < 0.7:  # 70% chance for normal pause
                time.sleep(random.uniform(2.0, 5.5))
            else:  # 30% chance for longer engagement
                engagement_time = random.uniform(8.0, 18.0)
                logger.info(f"Engaging with content for {engagement_time:.1f} seconds...")
                time.sleep(engagement_time)
                
                # SHARE A POST
                if random.random() < 0.4:  # 15% chance to share a post
                    try:
                        logger.info("Attempting to share a post...")
                        # Find share buttons using multiple possible selectors
                        share_buttons = browser.find_elements(By.XPATH, 
                            "//div[@aria-label='Share' or contains(@aria-label, 'share') or contains(@role, 'button')][.//span[text()='Share' or contains(text(), 'Share')]]")
                        
                        if share_buttons:
                            share_button = random.choice(share_buttons)
                            # Scroll to make the share button visible
                            browser.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", share_button)
                            time.sleep(random.uniform(0.8, 1.5))
                            
                            # Click the share button
                            share_button.click()
                            logger.info("Clicked share button")
                            time.sleep(random.uniform(2.0, 3.5))
                            
                            # Handle the share dialog
                            try:
                                # Look for "Share now" option
                                share_options = WebDriverWait(browser, 5).until(
                                    EC.presence_of_element_located((By.XPATH, "//div[@role='dialog']//div[text()='Share now' or contains(text(), 'Share now')]"))
                                )
                                share_options.click()
                                logger.info("Shared post using 'Share now' option")
                                time.sleep(random.uniform(3.0, 5.0))
                            except Exception as e:
                                logger.info(f"Could not find 'Share now' option: {str(e)}")
                                # Try to close the share dialog
                                try:
                                    close_buttons = browser.find_elements(By.XPATH, "//div[@aria-label='Close' or @role='button'][.//i]")
                                    if close_buttons:
                                        close_buttons[0].click()
                                        logger.info("Closed share dialog")
                                except Exception as close_error:
                                    logger.info(f"Could not close share dialog: {str(close_error)}")
                    except Exception as share_error:
                        logger.info(f"Error while attempting to share post: {str(share_error)}")
                
                # Simulate reactions during longer engagement (like, comment hover)
                if random.random() < 0.4:  # 40% chance to interact
                    try:
                        reaction_buttons = browser.find_elements(By.XPATH, "//div[@aria-label='Like' or @aria-label='React' or contains(@aria-label, 'reaction')]")
                        if reaction_buttons:
                            button = random.choice(reaction_buttons)
                            # Hover over but don't click (just showing interest)
                            ActionChains(browser).move_to_element(button).perform()
                            logger.info("Hovering over reaction button")
                            time.sleep(random.uniform(1.0, 2.5))
                            
                            # Sometimes click on a reaction
                            if random.random() < 0.5:  # 50% chance to click a reaction
                                emotions = ["like", "love", "care", "haha", "wow", "sad", "angry"]
                                selected_emotion = random.choice(emotions)
                                logger.info(f"Considering reaction: {selected_emotion}")
                                
                                try:
                                    # Different XPaths for different emotions
                                    emotion_xpath_map = {
                                        "like": "//div[@role='button' and @aria-label='Like']",
                                        "love": "//div[@role='button' and @aria-label='Love']",
                                        "care": "//div[@role='button' and @aria-label='Care']",
                                        "haha": "//div[@role='button' and @aria-label='Haha']",
                                        "wow": "//div[@role='button' and @aria-label='Wow']",
                                        "sad": "//div[@role='button' and @aria-label='Sad']",
                                        "angry": "//div[@role='button' and @aria-label='Angry']"
                                    }
                                    
                                    # Wait for reaction panel to appear
                                    try:
                                        # Use a more reliable XPath for the reaction panel
                                        reaction_panel = WebDriverWait(browser, 5).until(
                                            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'reactions-panel') or contains(@style, 'opacity') or @role='dialog']"))
                                        )
                                        logger.info("Reaction panel appeared")
                                        time.sleep(random.uniform(0.5, 1.0))  # Short pause after panel appears
                                        
                                        # Try to find the specific emotion using multiple possible selectors
                                        try:
                                            # Try different approaches to find the emotion element
                                            emotion_xpaths = [
                                                emotion_xpath_map[selected_emotion],  # Original xpath
                                                f"//div[@aria-label='{selected_emotion.capitalize()}']",  # Alternative format
                                                f"//div[contains(@aria-label, '{selected_emotion}')]",  # Partial match
                                                f"//div[@data-reaction-type='{selected_emotion}']"  # Data attribute
                                            ]
                                            
                                            # Try each xpath until one works
                                            emotion_element = None
                                            for xpath in emotion_xpaths:
                                                try:
                                                    emotion_element = WebDriverWait(browser, 1).until(
                                                        EC.presence_of_element_located((By.XPATH, xpath))
                                                    )
                                                    if emotion_element:
                                                        break
                                                except:
                                                    continue
                                            
                                            if emotion_element:
                                                # Move to the emotion and click it
                                                ActionChains(browser).move_to_element(emotion_element).perform()
                                                logger.info(f"Hovering over {selected_emotion} reaction")
                                                
                                                # Variable wait time before clicking
                                                time.sleep(random.uniform(0.5, 1.5))
                                                
                                                # Click the emotion element
                                                emotion_element.click()
                                                logger.info(f"Clicked on {selected_emotion} reaction")
                                                
                                                # Wait after clicking
                                                time.sleep(random.uniform(2.0, 4.0))
                                            else:
                                                logger.debug(f"Could not find {selected_emotion} reaction with any selector")
                                            
                                            # Move away from the reaction panel without clicking
                                            ActionChains(browser).move_by_offset(200, 200).perform()
                                            logger.info("Moving away from reaction panel")
                                        except Exception as e:
                                            logger.debug(f"Could not find or interact with emotion element: {e}")
                                            # Move away to close the reaction panel
                                            ActionChains(browser).move_by_offset(200, 200).perform()
                                    except Exception as e:
                                        logger.debug(f"Reaction panel did not appear or could not be interacted with: {e}")
                                        # Try to move mouse away anyway to ensure we don't get stuck
                                        ActionChains(browser).move_by_offset(200, 200).perform()
                                except Exception as e:
                                    logger.debug(f"Failed to interact with reactions: {e}")
                    except Exception as e:
                        logger.debug(f"Failed to simulate reaction: {e}")

            # Occasionally click on videos that look interesting
            if random.random() < 0.15:  # 15% chance
                try:
                    videos = browser.find_elements(By.XPATH, "//div[contains(@class, 'watch')]//a[contains(@href, '/watch/')]")
                    if videos:
                        video = random.choice(videos)
                        # Scroll to make video visible
                        browser.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", video)
                        time.sleep(random.uniform(1.0, 2.0))
                        video.click()
                        logger.info("Clicked on a video to watch")
                        # Watch for a variable amount of time
                        watch_time = random.uniform(15.0, 45.0)
                        logger.info(f"Watching video for {watch_time:.1f} seconds")
                        time.sleep(watch_time)
                        browser.back()
                        time.sleep(random.uniform(2.0, 4.0))
                except Exception as e:
                    logger.debug(f"Failed to interact with video: {e}")
        
        # Navigate to Facebook homepage with natural browsing pattern
        logger.info("Navigating to Facebook homepage...")
        browser.get(FB_DEFAULT_URL)
        
        # Scroll on homepage with more natural reading patterns
        homepage_duration = random.randint(160, 230)  # 1.5-2.5 minutes
        logger.info(f"Browsing homepage for {homepage_duration} seconds...")
        start_time = time.time()
        
        while time.time() - start_time < homepage_duration:
            # Implement variable scrolling speeds and distances
            scroll_speed = random.choice(["slow", "medium", "fast"])
            
            if scroll_speed == "slow":
                # Slow careful reading
                scroll_amount = random.randint(100, 300)
                browser.execute_script(f"window.scrollBy(0, {scroll_amount});")
                time.sleep(random.uniform(4.0, 8.0))  # Longer time reading
            elif scroll_speed == "medium":
                # Normal browsing
                scroll_amount = random.randint(300, 600)
                browser.execute_script(f"window.scrollBy(0, {scroll_amount});")
                time.sleep(random.uniform(2.5, 5.0))
            else:  # fast
                # Scanning quickly
                scroll_amount = random.randint(600, 900)
                browser.execute_script(f"window.scrollBy(0, {scroll_amount});")
                time.sleep(random.uniform(1.0, 2.5))
                
            # SHARE A POST
            if random.random() < 0.4:  # 15% chance to share a post
                try:
                    # Find share buttons on posts
                    share_buttons = browser.find_elements(By.XPATH, 
                        "//div[@aria-label='Share' or contains(@aria-label, 'share') or contains(@aria-label, 'Share')]")
                    
                    if share_buttons:
                        # Choose a random share button
                        share_button = random.choice(share_buttons)
                        
                        # Scroll to make share button visible
                        browser.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", share_button)
                        time.sleep(random.uniform(1.0, 2.0))
                        
                        # Click the share button
                        share_button.click()
                        logger.info("Clicked on share button")
                        time.sleep(random.uniform(2.0, 3.0))
                        
                        # Look for "Share now" option in the share menu
                        try:
                            share_now_buttons = browser.find_elements(By.XPATH, 
                                "//div[contains(text(), 'Share now') or contains(@aria-label, 'Share now')]")
                            
                            if share_now_buttons:
                                share_now_button = share_now_buttons[0]
                                share_now_button.click()
                                logger.info("Shared a post")
                                time.sleep(random.uniform(3.0, 5.0))
                            else:
                                # If "Share now" not found, try to close the share dialog
                                close_buttons = browser.find_elements(By.XPATH, "//div[@aria-label='Close' or contains(@aria-label, 'close')]")
                                if close_buttons:
                                    close_buttons[0].click()
                                    logger.info("Closed share dialog")
                                    time.sleep(random.uniform(1.0, 2.0))
                        except Exception as e:
                            logger.debug(f"Failed to complete share action: {e}")
                            # Try to press Escape key to close any open dialogs
                            ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                            time.sleep(1.0)
                except Exception as e:
                    logger.debug(f"Failed to share post: {e}")
                    # Try to press Escape key to close any open dialogs
                    try:
                        ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                        time.sleep(1.0)
                    except:
                        pass
            
            # Simulate interest in specific content
            if random.random() < 0.25:  # 25% chance to show interest
                try:
                    # Find interactive elements like posts, images, or comments
                    interactive_elements = browser.find_elements(By.XPATH, 
                        "//div[contains(@class, 'feed')]/div | //div[contains(@class, 'post')] | //div[contains(@class, 'story')]")
                    
                    if interactive_elements:
                        element = random.choice(interactive_elements)
                        # Scroll element into view with natural movement
                        browser.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
                        time.sleep(random.uniform(1.0, 2.0))
                        
                        # Hover over the element to show interest
                        ActionChains(browser).move_to_element(element).perform()
                        logger.info("Showing interest in a post")
                        
                        # Longer pause to simulate reading
                        reading_time = random.uniform(8.0, 20.0)
                        logger.info(f"Reading content for {reading_time:.1f} seconds")
                        time.sleep(reading_time)
                        
                        # Sometimes expand comments or click on images
                        if random.random() < 0.3:
                            try:
                                comment_buttons = element.find_elements(By.XPATH, ".//span[contains(text(), 'comment') or contains(text(), 'Comment')]")
                                if comment_buttons:
                                    comment_buttons[0].click()
                                    logger.info("Expanded comments section")
                                    time.sleep(random.uniform(5.0, 12.0))
                            except Exception:
                                pass
                except Exception as e:
                    logger.debug(f"Failed to interact with content: {e}")

            # Occasionally search for topics related to games (more targeted)
            if random.random() < 0.4:
                try:
                    search_box = browser.find_element(By.XPATH, "//input[@placeholder='Search Facebook']")
                    
                    search_queries = [
                        "mobile game tips", "new game releases", "game strategies", "popular mobile games", 
                        "game recommendations", "gaming community", "best mobile games 2023", 
                        "free mobile games", "mobile game cheats", "mobile game updates", 
                        "upcoming game releases", "mobile game events", "mobile game giveaways",
                        "mobile game tournaments", "mobile game reviews", "mobile game guides",
                        "trending mobile games", "mobile game hacks", "mobile game mods",
                        "mobile game communities", "mobile game news", "mobile game forums"
                    ]
                    
                    # Extend search_queries with group_search_names
                    search_queries.extend(group_search_names)

                    search_query = random.choice(search_queries)
                    
                    # Type like a human with variable speed
                    search_box.click()
                    search_box.clear()
                    for char in search_query:
                        search_box.send_keys(char)
                        time.sleep(random.uniform(0.05, 0.25))  # Variable typing speed
                    
                    time.sleep(random.uniform(0.5, 1.5))  # Pause before hitting enter
                    search_box.send_keys(Keys.ENTER)
                    logger.info(f"Searching for game-related topic: {search_query}")
                    
                    # Browse search results
                    time.sleep(random.uniform(5.0, 12.0))
                    
                    # Scroll through results with variable speed
                    for _ in range(random.randint(2, 5)):
                        browser.execute_script(f"window.scrollBy(0, {random.randint(300, 700)});")
                        time.sleep(random.uniform(2.0, 5.0))
                    
                    # Return to homepage
                    browser.get(FB_DEFAULT_URL)
                    time.sleep(random.uniform(2.0, 4.0))
                except Exception as e:
                    logger.debug(f"Search simulation failed: {e}")
        
        logger.info("Human behavior simulation completed")
        
    except Exception as e:
        logger.error(f"Error during human behavior simulation: {e}")


def simulate_scrolling_behavior_when_init_facebook(browser):
    """
    Simulates natural human scrolling behavior in the browser
    
    Args:
        browser (webdriver.Chrome): The browser instance used for Selenium automation
        
    Returns:
        float: The final pause time in seconds
    """
    try:
        # Use more natural scrolling patterns with variable speeds and distances
        scroll_duration = random.randint(180, 240)
        start_time = time.time()
        
        while time.time() - start_time < scroll_duration:
            # Natural scrolling with acceleration and deceleration
            scroll_pattern = random.choice(["smooth", "quick", "pause_heavy"])
            
            if scroll_pattern == "smooth":
                # Smooth scrolling with gradual acceleration
                for i in range(3, 8):
                    scroll_amount = i * 100  # Gradually increasing scroll amount
                    browser.execute_script(f"window.scrollBy(0, {scroll_amount});")
                    time.sleep(random.uniform(0.3, 0.7))
            elif scroll_pattern == "quick":
                # Quick scroll followed by pause (like finding something interesting)
                scroll_amount = random.randint(500, 1200)
                browser.execute_script(f"window.scrollBy(0, {scroll_amount});")
            else:  # pause_heavy
                # Small scroll with longer pause (like reading content)
                scroll_amount = random.randint(200, 400)
                browser.execute_script(f"window.scrollBy(0, {scroll_amount});")
            
            # Variable pauses between scrolling actions
            if random.random() < 0.7:  # 70% chance for normal pause
                time.sleep(random.uniform(2.0, 5.5))
            else:  # 30% chance for longer engagement
                engagement_time = random.uniform(9.0, 17.0)
                logger.info(f"Engaging with content for {engagement_time:.1f} seconds...")
                time.sleep(engagement_time)
                
                # Simulate reactions during longer engagement (like, comment hover)
                if random.random() < 0.4:  # 40% chance to interact
                    try:
                        reaction_buttons = browser.find_elements(By.XPATH, "//div[@aria-label='Like' or @aria-label='React' or contains(@aria-label, 'reaction')]")
                        if reaction_buttons:
                            button = random.choice(reaction_buttons)
                            # Hover over but don't click (just showing interest)
                            ActionChains(browser).move_to_element(button).perform()
                            logger.info("Hovering over reaction button")
                            time.sleep(random.uniform(1.0, 2.5))
                    except Exception as e:
                        logger.debug(f"Failed to simulate reaction: {e}")
                        
            # SHARE A POST
            if random.random() < 0.1:
                try:
                    logger.info("Attempting to share a post...")
                    # Find share buttons using multiple possible selectors
                    share_buttons = browser.find_elements(By.XPATH, 
                        "//div[@aria-label='Share' or contains(@aria-label, 'share') or contains(@role, 'button')][.//span[text()='Share' or contains(text(), 'Share')]]")
                    
                    if share_buttons:
                        share_button = random.choice(share_buttons)
                        # Scroll to make the share button visible
                        browser.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", share_button)
                        time.sleep(random.uniform(0.8, 1.5))
                        
                        # Click the share button
                        share_button.click()
                        logger.info("Clicked share button")
                        time.sleep(random.uniform(2.0, 3.5))
                        
                        # Handle the share dialog
                        try:
                            # First try to add some text to the share
                            try:
                                # Look for text input field in the share dialog
                                text_input = WebDriverWait(browser, 5).until(
                                    EC.presence_of_element_located((By.XPATH, "//div[@role='dialog']//div[@contenteditable='true' or @role='textbox']"))
                                )
                                
                                share_text = random.choice(SHARE_COMMENT_IN_POST)
                                
                                # Type the text with human-like timing
                                for char in share_text:
                                    text_input.send_keys(char)
                                    time.sleep(random.uniform(0.05, 0.15))  # Realistic typing speed
                                
                                logger.info(f"Added text to share: '{share_text}'")
                                time.sleep(random.uniform(1.0, 2.0))
                            except Exception as text_error:
                                logger.info(f"Could not add text to share: {str(text_error)}")
                            
                            # Look for "Share now" or similar option
                            share_options = WebDriverWait(browser, 5).until(
                                EC.presence_of_element_located((By.XPATH, "//div[@role='dialog']//div[@aria-label='Share now' and @role='button'] | //div[@role='dialog']//div[text()='Share now' or contains(text(), 'Share now') or text()='Post' or contains(text(), 'Share')]"))
                            )
                            
                            share_options.click()
                            logger.info("Shared post with text")
                            
                            # Wait until share action is completed
                            time.sleep(random.uniform(5.0, 8.0))
                            
                            # Look for confirmation elements that indicate sharing is complete
                            try:
                                WebDriverWait(browser, 10).until_not(
                                    EC.presence_of_element_located((By.XPATH, "//div[@role='dialog']"))
                                )
                                logger.info("Share dialog closed, sharing completed")
                            except Exception as wait_error:
                                logger.info(f"Waiting for share completion: {str(wait_error)}")
                                time.sleep(random.uniform(3.0, 5.0))  # Additional wait time
                        except Exception as e:
                            logger.info(f"Could not complete share action: {str(e)}")
                            # Try to close the share dialog
                            try:
                                close_buttons = browser.find_elements(By.XPATH, "//div[@aria-label='Close' or @role='button'][.//i]")
                                if close_buttons:
                                    close_buttons[0].click()
                                    logger.info("Closed share dialog")
                                    time.sleep(random.uniform(1.0, 2.0))
                                else:
                                    # Try to press Escape key to close any open dialogs
                                    ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                                    time.sleep(1.0)
                            except Exception as close_error:
                                logger.info(f"Could not close share dialog: {str(close_error)}")
                                # Try to press Escape key as a last resort
                                try:
                                    ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                                    time.sleep(1.0)
                                except:
                                    pass
                    else:
                        logger.info("No share buttons found")
                except Exception as share_error:
                    logger.info(f"Error while attempting to share post: {str(share_error)}")
                        
            # Decide whether to hover over reactions
            if random.random() < 0.5:
                emotions = ["like", "love", "care", "haha", "wow", "sad", "angry"]
                selected_emotion = random.choice(emotions)
                logger.info(f"Considering reaction: {selected_emotion}")
                
                try:
                    # Different XPaths for different emotions
                    emotion_xpath_map = {
                        "like": "//div[@role='button' and @aria-label='Like']",
                        "love": "//div[@role='button' and @aria-label='Love']",
                        "care": "//div[@role='button' and @aria-label='Care']",
                        "haha": "//div[@role='button' and @aria-label='Haha']",
                        "wow": "//div[@role='button' and @aria-label='Wow']",
                        "sad": "//div[@role='button' and @aria-label='Sad']",
                        "angry": "//div[@role='button' and @aria-label='Angry']"
                    }
                    
                    # Find Like buttons
                    like_buttons = browser.find_elements(By.XPATH, "//div[@aria-label='Like' or @aria-label='React' or contains(@aria-label, 'reaction')]")
                    if like_buttons:
                        # Select a random Like button
                        like_button = random.choice(like_buttons)
                        
                        # First hover over the Like button
                        ActionChains(browser).move_to_element(like_button).perform()
                        logger.info("Hovering over Like button")
                        time.sleep(random.uniform(1.0, 2.0))
                        
                        # Wait for reaction panel to appear
                        try:
                            logger.info("Reaction panel appeared")
                            time.sleep(random.uniform(0.5, 1.0))  # Short pause after panel appears
                            
                            # Try to find the specific emotion using multiple possible selectors
                            try:
                                # Try different approaches to find the emotion element
                                emotion_xpaths = [
                                    emotion_xpath_map[selected_emotion],  # Original xpath
                                    f"//div[@aria-label='{selected_emotion.capitalize()}']",  # Alternative format
                                    f"//div[contains(@aria-label, '{selected_emotion}')]",  # Partial match
                                    f"//div[@data-reaction-type='{selected_emotion}']"  # Data attribute
                                ]
                                
                                # Try each xpath until one works
                                emotion_element = None
                                for xpath in emotion_xpaths:
                                    try:
                                        emotion_element = WebDriverWait(browser, 1).until(
                                            EC.presence_of_element_located((By.XPATH, xpath))
                                        )
                                        if emotion_element:
                                            break
                                    except:
                                        continue
                                
                                if emotion_element:
                                    # Move to the emotion and click it
                                    ActionChains(browser).move_to_element(emotion_element).perform()
                                    logger.info(f"Hovering over {selected_emotion} reaction")
                                    
                                    # Variable wait time before clicking
                                    time.sleep(random.uniform(0.5, 1.5))
                                    
                                    # Click the emotion element
                                    emotion_element.click()
                                    logger.info(f"Clicked on {selected_emotion} reaction")
                                    
                                    # Wait after clicking to ensure the reaction is registered
                                    time.sleep(random.uniform(2.0, 4.0))
                                    
                                    # Verify the reaction was registered before continuing
                                    try:
                                        # Look for confirmation that reaction was applied
                                        WebDriverWait(browser, 3).until(
                                            EC.presence_of_element_located((By.XPATH, f"//div[contains(@aria-label, '{selected_emotion}') and contains(@aria-label, 'ed')]"))
                                        )
                                        logger.info(f"Confirmed {selected_emotion} reaction was registered")
                                    except Exception as e:
                                        logger.debug(f"Could not confirm reaction was registered: {e}")
                                        # Additional wait to ensure reaction processing
                                        time.sleep(random.uniform(1.0, 2.0))
                                    
                                    # Continue only after ensuring reaction was processed
                                    continue
                                else:
                                    logger.debug(f"Could not find {selected_emotion} reaction with any selector")
                                
                                # Move away from the reaction panel without clicking
                                ActionChains(browser).move_by_offset(200, 200).perform()
                                logger.info("Moving away from reaction panel")
                            except Exception as e:
                                logger.debug(f"Could not find or interact with emotion element: {e}")
                                # Move away to close the reaction panel
                                ActionChains(browser).move_by_offset(200, 200).perform()
                        except Exception as e:
                            logger.debug(f"Reaction panel did not appear or could not be interacted with: {e}")
                            # Try to move mouse away anyway to ensure we don't get stuck
                            ActionChains(browser).move_by_offset(200, 200).perform()
                except Exception as e:
                    logger.debug(f"Failed to interact with reactions: {e}")
        
        # Occasionally navigate to a different section before returning to main task
        if random.random() < 0.3:  # 30% chance
            try:
                sections = ["watch", "marketplace", "groups"]
                section = random.choice(sections)
                logger.info(f"Briefly visiting {section} section...")
                browser.get(f"{FB_DEFAULT_URL}/{section}")
                time.sleep(random.uniform(5.0, 10.0))
                browser.get(FB_DEFAULT_URL)  # Return to homepage
            except Exception as e:
                logger.debug(f"Failed to visit section: {e}")
        
        # Final pause before starting the actual scraping
        final_pause = random.uniform(5, 8)
        logger.info(f"Finished human-like browsing behavior, pausing for {final_pause:.1f} seconds before scraping...")
        return final_pause
    except Exception as e:
        logger.error(f"Error during scrolling behavior simulation: {e}")
        return random.uniform(3, 5)  # Fallback pause time


def run_fb_scraper_multiple_fanpages(game_urls, environment, use_cookies=True):
    """
    Run Facebook scraper for multiple fanpages using a single browser session
    
    Args:
        game_urls (list): List of game URLs to scrape
        use_cookies (bool): Whether to use saved cookies for login
        
    Returns:
        bool: True if scraping completed successfully, False otherwise
    """
    try:
        # Choose a random account and login
        username, password = random.choice(FB_ACCOUNT_LIST)
        cookies_path = os.path.join(os.getcwd(), "facebook_cookies", f"{username}_cookies.pkl")
        browser = login_facebook(username, password, use_cookies=use_cookies, cookies_path=cookies_path)

        current_url = browser.current_url
        if current_url.startswith(f"{FB_DEFAULT_URL}/two_step_verification/authentication"):
            if not handle_captcha_if_present(browser, username, password):
                print("CAPTCHA handling failed, exiting.")
                return False  # Exit if CAPTCHA handling fails

        sleep_time = random.randint(3, 8)
        logger.info(f":::::: Sleeping for {sleep_time} seconds after scraping all games...")
        # sleep(sleep_time)
            
        # Add human-like behavior before starting to scrape
        logger.info("Simulating human-like browsing behavior before scraping...")
        
        # Simulate scrolling behavior and get final pause time
        final_pause = simulate_scrolling_behavior_when_init_facebook(browser)
        sleep(final_pause)
        
        list_game_fanpages = get_all_game_fanpages(environment)


        # Process each game URL with the same browser session
        for index, game_url in enumerate(game_urls):
            try:
                print(f"\n----- Starting to scrape: {game_url} -----")
                
                # Extract game name from URL
                game_name = game_url.rstrip("/").split("/")[-1]
                
                # Navigate to game page
                browser.get(f"{FB_DEFAULT_URL}/{game_url}")
                sleep(random.randint(7, 13) if index < len(game_urls) - 1 else 0)  # Wait for page load
                
                all_posts = set()
                last_height = browser.execute_script("return document.body.scrollHeight")

                # Scroll and collect posts
                for attempt in range(50):
                    print(f"\n[Scrolling Attempt {attempt + 1}]")
                    current_posts = get_posts_by_attribute(browser, game_name)
                    all_posts.update(current_posts)
                    
                    if len(all_posts) >= LIMIT_POST_PER_DAY:
                        print("Limit of posts reached.")
                        break

                    # Check if no posts found after 3 attempts
                    if attempt >= 3 and len(all_posts) == 0:
                        print("No posts found after 3 attempts, exiting.")
                        break
                    
                    # Scroll down to load more posts
                    scroll_down(browser)
                    new_height = browser.execute_script("return document.body.scrollHeight")

                    if new_height == last_height:
                        print("Reached the end of the page, stopping scroll.")
                        break

                    last_height = new_height
                    
                    if attempt == 49:
                        print("Too many scroll attempts, exiting.")


                # Save post IDs
                post_id_file_path = os.path.join(os.getcwd(), FOLDER_PATH_POST_ID_CRAWLER.strip("/\\"))
                if not os.path.exists(post_id_file_path):
                    os.makedirs(post_id_file_path)
                    
                post_id_file_name = f"facebook_{game_name}_post_ids.txt"
                post_id_full_path = os.path.join(post_id_file_path, post_id_file_name)
                
                with open(post_id_full_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(sorted(all_posts)))

                # Crawl post data
                crawlPostData(browser, readData(post_id_full_path), game_name, environment, list_game_fanpages)
                
                print(f"----- Done {len(all_posts)} posts: Game {game_name} -----")
                
                # Add random delay after processing all games
                if index < len(game_urls) - 1:  # Only sleep if not the last game
                    sleep_time = random.randint(70, 100)
                    logger.info(f":::::: Sleeping for {sleep_time} seconds after scraping all games...")
                    sleep(sleep_time)
                    simulate_human_behavior_when_scraping_game(browser, environment)
                    sleep(sleep_time)
                
            except Exception as e:
                print(f"Error processing {game_url}: {e}")
                continue  # Proceed to next game if error occurs in current game

        return True  # Successfully completed scraping all games

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