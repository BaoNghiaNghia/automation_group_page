import os
import json
import time
import random
import shutil
import pickle

import requests
from requests.exceptions import RequestException

from PIL import Image
from io import BytesIO
import undetected_chromedriver as uc
from urllib.parse import urlparse


from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from backend.utils.captcha_solver import (
    solve_captcha,
    get_captcha_result,
    readDataFromFile,
    writeFileTxtPost
)
from backend.utils.index import (
    filter_existing_posts,
    get_chrome_version_main,
    close_remote_debug_port
)
from backend.constants import (
    logger,
    SCRAPER_TWITTER_ACCOUNT_LIST, 
    FB_DEFAULT_URL, 
    FOLDER_PATH_DATA_CRAWLER, 
    LIMIT_POST_PER_DAY, 
    FOLDER_PATH_POST_ID_CRAWLER, 
    ENV_CONFIG,
    LIST_COMPETIOR_GROUP_LINK,
    LIMIT_SCROLL_FRIEND_REACTION_POST,
    GMAIL_TWITTER,
    TWITTER_DEFAULT_URL
)

from backend.service.scraper.init_undetected_chromedriver import (
    authentication_google_account
)


def clear_uc_driver_cache():
    cache_dir = os.path.expandvars(r'%APPDATA%\undetected_chromedriver')
    if os.path.exists(cache_dir):
        try:
            shutil.rmtree(cache_dir)
            logger.info(f"Deleted undetected-chromedriver cache folder: {cache_dir}")
        except Exception as e:
            logger.warning(f"Failed to delete cache folder {cache_dir}")
    else:
        logger.info(f"No undetected-chromedriver cache folder found at {cache_dir}")


def init_chrome_undetected_chromedriver():
    """Initialize Chrome browser with undetected-chromedriver options."""
    try:
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

        ver = get_chrome_version_main()
        browser = uc.Chrome(version_main=int(ver), options=options)

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
    except Exception as e:
        logger.error(f"Error initializing undetected-chromedriver: {e}")
        return None


def login_twitter(username, password):
    """Login to Facebook using undetected-chromedriver with option to use saved cookies."""
    try:
        browser = init_chrome_undetected_chromedriver()
        return browser
    except Exception as e:
        logger.error(f"Error during Facebook login for {username}")
        return None


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
        logger.error(f"Error saving cookies")


def extract_facebook_post_or_video_id(url):
    """
    Extract the post or video ID from a Facebook URL and detect its type.

    Returns:
        (id, type): 
            id (str or None): The extracted ID, or None if not found.
            type (str): 'post', 'video', or None.
    """
    try:
        # Handle WebElement objects by getting their href attribute
        if hasattr(url, 'get_attribute'):
            url = url.get_attribute('href')
        
        # Ensure url is a string
        if not isinstance(url, str):
            logger.error(f"Invalid URL type: {type(url)}")
            return None, None
            
        parsed_url = urlparse(url)
        path = parsed_url.path
        logger.debug(f"Parsing Facebook URL path: {path}")
        # Detect video link
        if "/videos/" in path:
            parts = path.split("/videos/")
            if len(parts) > 1:
                id_part = parts[1].split("/")[0].split("?")[0]
                if id_part.isdigit():
                    return id_part, "video"
        # Detect reel link by /reels/
        if "/reels/" in path:
            parts = path.split("/reels/")
            if len(parts) > 1:
                id_part = parts[1].split("?")[0].split("/")[0]
                if id_part.isdigit():
                    return id_part, "reel"
        # Detect post link by /posts/
        if "/posts/" in path:
            return path.split("/posts/")[1].split("?")[0], "post"
        # Detect post link by /permalink/
        if "/permalink/" in path:
            post_id = path.split("/permalink/")[1].split("?")[0]
            if post_id.isdigit():
                return post_id, "post"
        # Detect post link by story_fbid param
        if "story_fbid=" in url:
            post_id = url.split("story_fbid=")[1].split("&")[0]
            if post_id.isdigit():
                return post_id, "post"
    except Exception as e:
        logger.error(f"Failed to extract post or video ID from {url}: {str(e)}")
    return None, None


def extract_facebook_video_id(url):
    """
    Extract the video ID from a Facebook video URL.
    Example: https://www.facebook.com/ChaosZeroNightmareEN/videos/1149253179828050
    Returns: '1149253179828050'
    """
    try:
        path = urlparse(url).path
        # Look for '/videos/<id>' in the path
        if "/videos/" in path:
            parts = path.split("/videos/")
            if len(parts) > 1:
                # The part after '/videos/' may contain the ID and possibly a trailing slash
                id_part = parts[1].split("/")[0]
                # Remove any query parameters if present
                id_part = id_part.split("?")[0]
                if id_part.isdigit():
                    return id_part
    except Exception as e:
        print(f"Failed to extract video ID from {url}")
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
        print(f"Error locating or clicking the 'Continue' button")
        
        
def wait_for_redirect(browser, expected_url):
    """Wait for the page to redirect to the expected URL."""
    try:
        # Wait for URL to contain the expected part
        browser.get(expected_url)
        print(f"Page has been redirected to: {browser.current_url}")
    except Exception as e:
        print(f"Error: Page did not redirect to {expected_url}. Current URL: {browser.current_url}")
        print(f"Error details")

def wait_for_page_load(browser):
    """Wait for the page to load after submitting the CAPTCHA."""
    # Print the current URL after clicking the 'Continue' button
    print(f"Current URL before redirect: {browser.current_url}")
    WebDriverWait(browser, 30).until(
        EC.url_changes(browser.current_url)  # Wait until the URL changes
    )
    print(f"Page has been redirected to: {browser.current_url}")


def get_list_post_ID_by_attribute(browser, game_name):
    """_summary_

    Args:
        browser (_type_): _description_
        game_name (_type_): _description_

    Returns:
        _type_: _description_
    """
    
    all_ids_found = []
    try:
        # Find post links by looking for anchor elements with specific attributes
        post_links = browser.find_elements(By.XPATH, "//a[starts-with(@attributionsrc, '/privacy_sandbox') and @role='link']")
        for link in post_links:
            href = link.get_attribute('href')
            found_id, type_id = extract_facebook_post_or_video_id(link)
            if found_id and f"{found_id}|{type_id}" not in all_ids_found:
                all_ids_found.append(f"{found_id}|{type_id}")
                print(f"{type_id} ID: {found_id}")
                
        # If no posts found with the specific XPath, fall back to the URL-based approach
        if not all_ids_found:
            base_url = f"{FB_DEFAULT_URL}/{game_name}/posts"
            fallback_links = browser.find_elements(By.XPATH, f"//a[starts-with(@href, '{base_url}')]")
            
            for link in fallback_links:
                href = link.get_attribute('href')
                found_id, type_id = extract_facebook_post_or_video_id(link)
                if found_id and f"{found_id}|{type_id}" not in all_ids_found:
                    all_ids_found.append(f"{found_id}|{type_id}")
                    print(f"{type_id} ID: {found_id}")
                    logger.info(f"Processing fallback link: {href}")
    except Exception as e:
        print(f"Error retrieving posts")

    return all_ids_found


def scroll_down(browser):
    """Scroll down the page to load more posts."""
    browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(random.randint(5, 9))  # Wait for content to load


def clonePostContent(driver, postId):
    """Clone the post content and images from the post ID."""
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

        # Try case 1 first
        image_links = driver.find_elements(By.XPATH, "/html/body/div[1]/div/div[1]/div/div[5]/div/div/div[2]/div/div/div/div/div/div/div/div[2]/div[2]/div/div/div/div/div/div/div/div/div/div/div/div/div[13]/div/div/div[3]/div[2]/div//a//img")
        
        # If case 1 doesn't find any images, try case 2
        if not image_links:
            image_links = driver.find_elements(By.XPATH, "/html/body/div[1]/div/div[1]/div/div[5]/div/div/div[2]/div/div/div/div/div/div/div/div[2]/div[2]/div/div/div/div/div/div/div/div/div/div/div/div/div[13]/div/div/div[3]/div/div[1]/div/div/div/div[1]/a/div[1]/div[1]/div/img")

        for img in image_links:
            linkImage = img.get_attribute('src')
            if linkImage:
                linksArr.append(linkImage)

        postData = {"post_id": postId, "content": content, "images": linksArr}

        return postData
    except Exception as e:
        print(f"Error in clonePostContent")
        return False

# Function to download image and save with the correct extension
def download_image_file(image_url, file_number, post_id, folder_path="/data_crawl/", game_name=""):
    """Download image file and save with the correct extension."""
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
            response = requests.get(image_url, stream=True, timeout=30)
            if response.status_code in [200, 201]:
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
        response = requests.get(image_url, stream=True, timeout=30)
        if response.status_code in [200, 201]:
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
        print(f"Error downloading image from {image_url}")


def crawlDetailPostData(driver, postIds, game_name, environment, list_game_fanpages):
    """Crawl post data from the post IDs."""
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
                    
                # TODO: Stop get friend reaction post
                # handle_friend_reaction(driver, game_fanpage_id, environment)

            time.sleep(random.randint(12, 14))
        except Exception as e:
            print(f"Error in crawlDetailPostData")


def handle_friend_reaction(driver, game_fanpage_id, environment):
    # Click on the specified element (like button or reaction)
    try:
        # Wait for a random time before clicking to simulate human behavior
        time.sleep(random.uniform(1.5, 3.0))
        
        # Find and click the specified element
        like_button = driver.find_element(By.XPATH, 
            "/html/body/div[1]/div/div[1]/div/div[5]/div/div/div[2]/div/div/div/div/div/div/div/div[2]/div[2]/div/div/div/div/div/div/div/div/div/div/div/div/div[13]/div/div/div[4]/div/div/div[1]/div/div[1]/div/div[1]/div/span/div/span[2]")
        
        
        # Scroll element into view
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", like_button)
        
        # Wait a moment after scrolling
        time.sleep(random.uniform(0.8, 1.5))
        
        # Click the element
        like_button.click()
        print(f"Clicked on reaction element for post ID: {id}")
        
        # Wait for about 7 seconds after clicking like button
        sleep_time = random.uniform(6.5, 9.5)
        print(f"Waiting for {sleep_time:.2f} seconds after clicking like button...")
        time.sleep(sleep_time)
        
        # Call the function to handle reaction panel
        handle_get_friend_reaction_post_panel(driver, game_fanpage_id, environment)

        
        # Wait a moment after clicking
        time.sleep(random.uniform(1.0, 2.0))
    except Exception as e:
        print(f"Could not click on reaction element")

# Function to handle reaction panel scrolling and profile extraction
def handle_get_friend_reaction_post_panel(driver, game_fanpage_id, environment):
    """Handle the reaction panel scrolling and profile extraction."""
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
                print(f"Could not find reaction panel with {option_name}")

        # Only proceed if we found a reaction panel
        if reaction_panel:
            # Add a random sleep to ensure the panel is fully loaded
            time.sleep(random.uniform(1.0, 2.0))

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
                while current_bottom_diff > 5 and scroll_rounds < LIMIT_SCROLL_FRIEND_REACTION_POST:
                    action = ActionChains(driver)
                    action.click_and_hold(drag_element)
                    time.sleep(random.uniform(1, 3))  # Hold for a moment
                    
                    # Adjust scroll distance based on difference
                    scroll_distance = min(100, current_bottom_diff)
                    action.move_by_offset(0, scroll_distance)
                    action.release()
                    action.perform()
                    
                    time.sleep(random.uniform(1, 3))
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
                time.sleep(random.uniform(0.3, 0.7))
                
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
                        
                    # Save profile IDs to API in batches
                    if unique_profile_ids:
                        try:                                 
                            # Process in batches
                            profile_list = list(unique_profile_ids)
                            batch_size = 20
                            
                            # Process in batches with error handling
                            successful_batches = 0
                            total_batches = (len(profile_list) - 1) // batch_size + 1
                            
                            for i in range(0, len(profile_list), batch_size):
                                batch = profile_list[i:i+batch_size]
                                payload = []
                                
                                for profile_id in batch:
                                    # Handle both numeric IDs and username formats
                                    profile_link = ""
                                    if profile_id.isdigit():
                                        profile_link = f"www.facebook.com/profile.phop?id={profile_id}"
                                    else:
                                        profile_link = f"www.facebook.com/{profile_id}"

                                    payload.append({
                                        "profile_id": profile_id,
                                        "game_fanpages_id": game_fanpage_id,
                                        "profile_link": profile_link
                                    })

                                headers = {'Content-Type': 'application/json'}
                                api_url = f'{ENV_CONFIG[environment]["SERVICE_URL"]}/friend_list_group_game/insert-batch'
                                
                                try:
                                    response = requests.post(api_url, headers=headers, data=json.dumps(payload), timeout=30)
                                    
                                    if response.status_code in [200, 201]:
                                        print(f"Successfully sent batch {i//batch_size + 1}/{total_batches} ({len(batch)} profiles)")
                                        successful_batches += 1
                                    else:
                                        print(f"API request failed: status {response.status_code}, response: {response.text}")
                                        
                                    # Add a 500ms delay between API requests
                                    time.sleep(0.5)
                                except requests.exceptions.RequestException as req_err:
                                    print(f"Request error sending batch {i//batch_size + 1}: {req_err}")
                                    
                        except Exception as api_error:
                            print(f"Error sending profile IDs to API: {str(api_error)}")
                else:
                    print("No reaction links found in the panel")
            except Exception as e:
                print(f"Error extracting reaction links")

            print("Completed scrolling through the reaction panel")
        else:
            print("No reaction panel found with any XPATH option, skipping panel interaction")

    except Exception as e:
        print(f"Could not scroll through reaction panel")
        
    
def run_fb_scraper_single_fanpage_posts(game_name, use_cookies=True):
    """Run the Facebook scraper for a single fanpage."""
    try:
        # Choose a random account and login
        username, password = random.choice(SCRAPER_TWITTER_ACCOUNT_LIST)
        cookies_path = os.path.join(os.getcwd(), "facebook_cookies", f"{username}_cookies.pkl")
        browser = login_twitter(username, password, use_cookies=use_cookies, cookies_path=cookies_path)

        time.sleep(random.randint(2, 5))

        # Handle CAPTCHA if present
        if handle_captcha_if_present(browser, username, password):
            # Save cookies again after CAPTCHA handling
            if is_logged_in(browser):
                save_cookies(browser, username, cookies_path)
                
            # Wait for redirect to the game page
            wait_for_redirect(browser, f"{FB_DEFAULT_URL}/{game_name}")

            all_post_id_scanned = set()
            last_height = browser.execute_script("return document.body.scrollHeight")

            # Scroll and collect posts, with a maximum number of attempts
            for attempt in range(50):
                print(f"\n[Scrolling Attempt {attempt + 1}]")
                current_posts = get_list_post_ID_by_attribute(browser, game_name)
                
                all_post_id_scanned.update(current_posts)
                

                if len(all_post_id_scanned) >= LIMIT_POST_PER_DAY:
                    print("Limit of posts reached.")
                    break

                # Check if no posts found after 3 attempts
                if attempt >= 3 and len(all_post_id_scanned) == 0:
                    print("No posts found after 3 attempts, exiting.")
                    time.sleep(random.randint(10, 15))
                    browser.quit()
                    return

                # Scroll down smoothly to load more posts
                scheight = 1.0
                while scheight < 10.0:
                    browser.execute_script("window.scrollTo(0, document.body.scrollHeight/%s);" % scheight)
                    scheight += 0.01
                    time.sleep(0.01)  # Small pause between scroll increments
                
                # Add a small pause after smooth scrolling
                time.sleep(random.uniform(1.0, 2.0))
                
                new_height = browser.execute_script("return document.body.scrollHeight")

                # If no new content is loaded, stop scrolling
                if new_height == last_height:
                    print("Reached the end of the page, stopping scroll.")
                    break

                last_height = new_height

                if attempt == 49:
                    print("Too many scroll attempts, exiting.")

            # Output the number of posts collected
            print(f"\nTotal unique posts collected: {len(all_post_id_scanned)}")

            # Save the post IDs to a file
            post_id_file_path = os.path.join(os.getcwd(), FOLDER_PATH_POST_ID_CRAWLER.strip("/\\"))
            if not os.path.exists(post_id_file_path):
                os.makedirs(post_id_file_path)

            post_id_file_name = f"facebook_{game_name}_post_ids.txt"
            post_id_full_path = os.path.join(post_id_file_path, post_id_file_name)

            with open(post_id_full_path, "w", encoding="utf-8") as f:
                f.write("\n".join(sorted(all_post_id_scanned)))

            # Crawl and download post data
            crawlDetailPostData(browser, readDataFromFile(post_id_full_path), game_name)

            print(f"----- Done {all_post_id_scanned} posts: Game {game_name} -----")

        else:
            print("No CAPTCHA image found or failed to handle CAPTCHA.")

    except Exception as e:
        print(f"Error in main")

    finally:
        # Ensure the browser is closed properly
        try:
            browser.quit()
            print("Browser closed successfully.")
        except Exception as e:
            print(f"Error closing browser")
    
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
            time.sleep(random.randint(5, 9))

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
        print(f"Error while handling CAPTCHA")
        


def scan_spam_in_group(browser, environment):
    """_summary_

    Args:
        browser (_type_): _description_
        environment (_type_): _description_
    """



# def crawl_member_in_group_competition(browser, environment):
    """
    Crawl member information from competitor groups
    
    Args:
        browser: Selenium WebDriver instance
        environment: Environment configuration
    """
    try:
        logger.info("Starting to crawl members from competitor groups...")
        
        # Create directory for competitor group members if it doesn't exist
        save_dir = os.path.join(os.getcwd(), "competitor_group_members")
        os.makedirs(save_dir, exist_ok=True)
        
        # Get list of already processed groups
        processed_groups = set()
        if os.path.exists(save_dir):
            for filename in os.listdir(save_dir):
                if filename.endswith("_members.txt"):
                    processed_groups.add(filename.replace("_members.txt", ""))

        # First loop: Collect member links for all groups
        for group_link in LIST_COMPETIOR_GROUP_LINK:
            # Extract group name from URL
            group_name = urlparse(group_link).path.split('/')[2]
            
            # Skip if this group has already been processed
            if group_name in processed_groups:
                logger.info(f"Skipping group {group_name} as it has already been processed")
                continue
                
            logger.info(f"Processing group: {group_link}")
            
            # Navigate to the group members page
            browser.get(group_link)
            time.sleep(random.randint(3, 6))
            
            # Wait for the page to load
            WebDriverWait(browser, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Collect member links
            member_links = collect_member_links(browser)
            
            # Save member links to file
            file_path = os.path.join(save_dir, f"{group_name}_members.txt")
            with open(file_path, "w") as f:
                for link in member_links:
                    f.write(f"{link}\n")
            
            logger.info(f"Saved {len(member_links)} member links for group {group_name}")
            
            # Random sleep between processing groups
            sleep_time = random.randint(5, 10)
            logger.info(f"Sleeping for {sleep_time} seconds before processing next group...")
            time.sleep(sleep_time)
        
        # Second loop: Send data to API for all collected groups
        for group_link in LIST_COMPETIOR_GROUP_LINK:
            group_name = urlparse(group_link).path.split('/')[2]
            file_path = os.path.join(save_dir, f"{group_name}_members.txt")
            
            if os.path.exists(file_path):
                logger.info(f"Sending data to API for group: {group_name}")
                send_member_data_to_api(file_path, group_name, environment)
                
                sleep_time = random.randint(2, 5)
                logger.info(f"Sleeping for {sleep_time} seconds before processing next API request...")
                time.sleep(sleep_time)

    except Exception as e:
        logger.error(f"Error while crawling members from competitor groups")

def collect_member_links(browser):
    """
    Collect member links by scrolling through the members page
    
    Args:
        browser: Selenium WebDriver instance
        
    Returns:
        set: Set of member links
    """
    member_links = set()  # Using set for faster duplicate checking
    target_member_count = 4000
    max_scroll_attempts = 100
    scroll_count = 0
    
    # XPath pattern for finding member links
    xpath_pattern = "//a[contains(@href, '/user/') or contains(@href, '/profile.php')]"
    
    # Scroll until we find enough members or reach max scroll attempts
    while len(member_links) < target_member_count and scroll_count < max_scroll_attempts:
        # Scroll down to load more members
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.randint(2, 4))
        scroll_count += 1
        
        # Try to find member links
        try:
            elements = browser.find_elements(By.XPATH, xpath_pattern)
            
            if elements:
                for element in elements:
                    href = element.get_attribute('href')
                    if href:
                        if '/groups/' in href and '/user/' in href:
                            user_id = href.split('/user/')[1].strip('/')
                            href = f"www.facebook.com/{user_id}"
                        member_links.add(href)
        except Exception as e:
            logger.error(f"Error finding member links")
            continue

        # Log progress every 5 scroll attempts
        if scroll_count % 5 == 0:
            logger.info(f"Found {len(member_links)} member links so far (scroll attempt {scroll_count})")
        
        # Break if we've found enough members
        if len(member_links) >= target_member_count:
            logger.info(f"Reached target of {target_member_count} member links")
            break
    
    logger.info(f"Found {len(member_links)} member links total")
    return member_links


def send_member_data_to_api(file_path, group_name, environment):
    """
    Send member data to API in batches
    
    Args:
        file_path: Path to the file containing member links
        group_name: Name of the group
        environment: Environment configuration
    """
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return
        
    # Read all member links at once
    with open(file_path, 'r') as f:
        all_member_links = [line.strip() for line in f if line.strip()]
    
    if not all_member_links:
        logger.warning(f"No member links found in {file_path}")
        return
        
    batch_size = 20
    headers = {'Content-Type': 'application/json'}
    api_url = f'{ENV_CONFIG[environment]["SERVICE_URL"]}/friend_list_group_game/insert-batch'
    
    # Process in batches with error handling
    successful_batches = 0
    total_batches = (len(all_member_links) - 1) // batch_size + 1
    
    for i in range(0, len(all_member_links), batch_size):
        batch = all_member_links[i:i+batch_size]
        
        # Extract profile_id from the URL
        payload = []
        for link in batch:
            profile_id = None
            if '/profile.php?id=' in link:
                profile_id = link.split('/profile.php?id=')[1].split('&')[0]
            else:
                parts = link.strip('/').split('/')
                if parts and parts[-1].isdigit():
                    profile_id = parts[-1]
                else:
                    profile_id = parts[-1] 
            
            payload.append({
                "profile_id": profile_id,
                "game_fanpages_id": 1,
                "profile_link": link
            })
        
        try:
            response = requests.post(api_url, headers=headers, data=json.dumps(payload), timeout=30)
            
            if response.status_code in [200, 201]:
                logger.info(f"Successfully sent batch {i//batch_size + 1}/{total_batches} ({len(batch)} profiles)")
                successful_batches += 1
            else:
                logger.error(f"API request failed: status {response.status_code}, response: {response.text}")
                
            # Add a 500ms delay between API requests
            time.sleep(0.5)
        except requests.exceptions.RequestException as req_err:
            logger.error(f"Request error sending batch {i//batch_size + 1}: {req_err}")
    
    # Only delete file if at least one batch was successful
    if successful_batches > 0 and os.path.exists(file_path):
        os.remove(file_path)
        logger.info(f"Successfully deleted file: {file_path}")
    elif successful_batches == 0:
        logger.warning(f"No batches were successfully sent, keeping file: {file_path}")


def process_game_fanpage(browser, game_fanpages_object, index, x_refs_total, environment):
    """
    Process a single game URL for Facebook scraping
    
    Args:
        browser: Selenium browser instance
        game_url (str): URL of the game fanpage to scrape
        index (int): Current index in the x_refs_total list
        x_refs_total (list): List of all game URLs being processed
        environment: Environment configuration
    """
    try:
        game_url = game_fanpages_object['fanpage'].split('/')[-1]
        print(f"\n----- Starting to scrape: {game_url} -----")
        
        # Extract game name from URL
        game_name = game_url.rstrip("/").split("/")[-1]
        
        # Navigate to game page
        browser.get(f"{FB_DEFAULT_URL}/{game_url}")
        time.sleep(random.randint(5, 7) if index < len(x_refs_total) - 1 else 0)  # Wait for page load
        
        all_post_id_scanned = set()
        last_height = browser.execute_script("return document.body.scrollHeight")

        # Scroll and collect posts
        for attempt in range(50):
            print(f"\n[Scrolling Attempt {attempt + 1}]")
            current_posts = get_list_post_ID_by_attribute(browser, game_name)
            all_post_id_scanned.update(current_posts)
            
            if len(all_post_id_scanned) >= LIMIT_POST_PER_DAY:
                print("Limit of posts reached.")
                break

            # Check if no posts found after 3 attempts
            if attempt >= 3 and len(all_post_id_scanned) == 0:
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

        logger.info(f"Filtered post IDs for {game_name}: {len(all_post_id_scanned)} posts")
        # Save post IDs
        post_id_file_path = os.path.join(os.getcwd(), FOLDER_PATH_POST_ID_CRAWLER.strip("/\\"))
        if not os.path.exists(post_id_file_path):
            os.makedirs(post_id_file_path)
        
        post_id_file_name = f"facebook_{game_name}_post_ids.txt"
        post_id_full_path = os.path.join(post_id_file_path, post_id_file_name)

        all_post_id_scanned = filter_existing_posts(all_post_id_scanned, game_fanpages_object['id'], environment)
        
        with open(post_id_full_path, "w", encoding="utf-8") as f:
            f.write("\n".join(sorted(all_post_id_scanned)))


        # # Crawl post data
        # crawlDetailPostData(browser, readDataFromFile(post_id_full_path), game_name, environment, x_refs_total)

        # print(f"----- Done {len(all_post_id_scanned)} posts: Game {game_name} -----")

        # # Add random delay after processing all games
        # if index < len(x_refs_total) - 1:
        #     sleep_time = random.randint(70, 100)
        #     logger.info(f":::::: Sleeping for {sleep_time} seconds after scraping all games...")
        #     time.sleep(sleep_time)
        #     simulate_human_behavior_when_scraping_game(browser, environment)
        #     time.sleep(sleep_time)
        
    except Exception as e:
        print(f"Error processing {game_url}")

        return True  # Successfully completed scraping all games


def run_scraper_multiple_twitter(x_refs_total, environment, use_cookies=True):
    try:
        gmail_twitter = GMAIL_TWITTER[0]
        browser_running, remote_debug_port = authentication_google_account(gmail_twitter, position_type="topleft")

        # Ensure browser is running before proceeding
        if browser_running is None:
            logger.error("Browser instance is None")
            raise Exception("Browser instance is None")

        time.sleep(random.uniform(1, 2))
        browser_running.get(TWITTER_DEFAULT_URL)
        
        time.sleep(random.uniform(4, 6))
        
        # INSERT_YOUR_CODE
        for game_ref in x_refs_total:
            try:
                # INSERT_YOUR_CODE
                # logger.info(f"Processing Twitter game_ref: {game_ref}")
                browser_running.get(game_ref.get('ref'))
                time.sleep(random.uniform(4, 6))
                
                all_anchor_records = dict()  # key: href, value: record (can be dict or just href)
                max_scrolls = 50
                last_height = browser_running.execute_script("return document.body.scrollHeight")
                for scroll_count in range(max_scrolls):
                    anchor_elements = browser_running.find_elements(
                        By.XPATH,
                        '//a[@dir="ltr" and @role="link" and starts-with(@href, "/") and contains(@href, "/status/")]'
                    )
                    logger.info(f"Scroll {scroll_count+1}/{max_scrolls}: Found {len(anchor_elements)} <a> tags matching Twitter status pattern.")
                    for a in anchor_elements:
                        href = a.get_attribute("href")
                        if href and href not in all_anchor_records:
                            # You can expand this record as needed, e.g. with tweet id, text, etc.
                            record = {"href": href}
                            all_anchor_records[href] = record
                            logger.info(f"Found tweet link: {href}")
                    scroll_down(browser_running)
                    new_height = browser_running.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        logger.info(f"Reached the bottom of the page after {scroll_count+1} scrolls.")
                        break
                    last_height = new_height
                logger.info(f"Total unique tweet records found after {scroll_count+1} scrolls: {len(all_anchor_records)}")

                time.sleep(random.uniform(1, 2))
            except Exception as e:
                logger.error(f"Error processing Twitter game")
        
        time.sleep(random.uniform(100, 200))
        
    except (RequestException, WebDriverException) as e:
        logger.error(
            f"🚨 Connection/WebDriver error on account {gmail_twitter['username']}. "
            "Closing browser and moving to next account."
        )
    except Exception as e:
        logger.error(f"Unexpected error during Twitter processing")
    
    finally:
        if browser_running:
            browser_running.quit()

        # Close the remote debug port if it's still open
        if remote_debug_port:
            close_remote_debug_port(remote_debug_port)
