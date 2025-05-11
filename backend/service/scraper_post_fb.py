import os
import json
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

from backend.utils.captcha_solver import solve_captcha, get_captcha_result, readDataFromFile, writeFileTxtPost
from backend.service.simulation_behaviour import simulate_human_behavior_when_scraping_game, simulate_scrolling_behavior_when_init_facebook
from backend.utils.index import get_all_game_fanpages
from backend.constants import (
    FB_ACCOUNT_LIST, 
    FB_DEFAULT_URL, 
    FOLDER_PATH_DATA_CRAWLER, 
    LIMIT_POST_PER_DAY, 
    FOLDER_PATH_POST_ID_CRAWLER, 
    ENV_CONFIG, 
    SPAM_KEYWORDS_IN_POST,
    LIST_COMPETIOR_GROUP_LINK,
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
    """_summary_

    Args:
        browser (_type_): _description_
        game_name (_type_): _description_

    Returns:
        _type_: _description_
    """
    
    posts = []
    try:
        # Use the more specific XPath pattern to find post links
        post_links = browser.find_elements(By.XPATH, "//div[3]/div[@role='article']/div/div/div/div/div/div/div/div/div/div/div/div[13]/div/div/div[2]/div/div[2]/div/div[2]/span/div/span[1]/span/a")
        
        for link in post_links:
            href = link.get_attribute('href')
            post_id = extract_post_id_from_url(href)
            if post_id and post_id not in posts:
                posts.append(post_id)
                print(f"Post ID found: {post_id}")
                
        # If no posts found with the specific XPath, fall back to the URL-based approach
        if not posts:
            base_url = f"{FB_DEFAULT_URL}/{game_name}/posts"
            fallback_links = browser.find_elements(By.XPATH, f"//a[starts-with(@href, '{base_url}')]")
            
            for link in fallback_links:
                href = link.get_attribute('href')
                post_id = extract_post_id_from_url(href)
                if post_id and post_id not in posts:
                    posts.append(post_id)
                    print(f"Post ID found (fallback): {post_id}")
    except Exception as e:
        print(f"Error retrieving posts: {e}")
    return posts

def scroll_down(browser):
    """Scroll down the page to load more posts."""
    browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    sleep(random.randint(5, 9))  # Wait for content to load


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
                while current_bottom_diff > 5 and scroll_rounds < 100:
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
                                    
                                    if response.status_code == 200:
                                        print(f"Successfully sent batch {i//batch_size + 1}/{total_batches} ({len(batch)} profiles)")
                                        successful_batches += 1
                                    else:
                                        print(f"API request failed: status {response.status_code}, response: {response.text}")
                                        
                                    # Add a 500ms delay between API requests
                                    sleep(0.5)
                                except requests.exceptions.RequestException as req_err:
                                    print(f"Request error sending batch {i//batch_size + 1}: {req_err}")
                                    
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
        
    
def run_fb_scraper_single_fanpage_posts(game_name, use_cookies=True):
    """Run the Facebook scraper for a single fanpage."""
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
            crawlPostData(browser, readDataFromFile(post_id_full_path), game_name)

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
        


def scan_spam_in_group(browser, environment):
    """_summary_

    Args:
        browser (_type_): _description_
        environment (_type_): _description_
    """



def crawl_member_in_group_competition(browser, environment):
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
            sleep(random.randint(3, 6))
            
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
            sleep(sleep_time)
        
        # Second loop: Send data to API for all collected groups
        for group_link in LIST_COMPETIOR_GROUP_LINK:
            group_name = urlparse(group_link).path.split('/')[2]
            file_path = os.path.join(save_dir, f"{group_name}_members.txt")
            
            if os.path.exists(file_path):
                logger.info(f"Sending data to API for group: {group_name}")
                send_member_data_to_api(file_path, group_name, environment)
                
                sleep_time = random.randint(2, 5)
                logger.info(f"Sleeping for {sleep_time} seconds before processing next API request...")
                sleep(sleep_time)

    except Exception as e:
        logger.error(f"Error while crawling members from competitor groups: {e}")

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
        sleep(random.randint(2, 4))
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
            logger.error(f"Error finding member links: {e}")
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
            
            if response.status_code == 200:
                logger.info(f"Successfully sent batch {i//batch_size + 1}/{total_batches} ({len(batch)} profiles)")
                successful_batches += 1
            else:
                logger.error(f"API request failed: status {response.status_code}, response: {response.text}")
                
            # Add a 500ms delay between API requests
            sleep(0.5)
        except requests.exceptions.RequestException as req_err:
            logger.error(f"Request error sending batch {i//batch_size + 1}: {req_err}")
    
    # Only delete file if at least one batch was successful
    if successful_batches > 0 and os.path.exists(file_path):
        os.remove(file_path)
        logger.info(f"Successfully deleted file: {file_path}")
    elif successful_batches == 0:
        logger.warning(f"No batches were successfully sent, keeping file: {file_path}")


def process_game_url(browser, game_url, index, game_urls, environment, list_game_fanpages):
    """
    Process a single game URL for Facebook scraping
    
    Args:
        browser: Selenium browser instance
        game_url (str): URL of the game fanpage to scrape
        index (int): Current index in the game_urls list
        game_urls (list): List of all game URLs being processed
        environment: Environment configuration
        list_game_fanpages: List of all game fanpages
    """
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
        crawlPostData(browser, readDataFromFile(post_id_full_path), game_name, environment, list_game_fanpages)

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

        return True  # Successfully completed scraping all games


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
        
        # ----------------------- Scan Spam in Group ----------------------- #
        scan_spam_in_group(browser, environment)
        
        # ----------------------- Crawler member in group competition ----------------------- #
        crawl_member_in_group_competition(browser, environment)
        
        # ----------------------- Scraper fanpages ----------------------- #
        list_game_fanpages = get_all_game_fanpages(environment)

        # Process each game URL with the same browser session
        for index, game_url in enumerate(game_urls):
            process_game_url(browser, game_url, index, game_urls, environment, list_game_fanpages)
        
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

