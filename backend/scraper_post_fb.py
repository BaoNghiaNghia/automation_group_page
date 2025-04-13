import random
import requests
import os
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
from backend.constants import FB_ACCOUNT_LIST, FB_DEFAULT_URL, FOLDER_PATH_DATA_CRAWLER, LIMIT_POST_PER_DAY, FOLDER_PATH_POST_ID_CRAWLER
import logging


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def init_browser(is_ubuntu=False):
    """Initialize Chrome browser with required options."""
    chrome_options = Options()
    
    # Common options
    prefs = {
        "profile.default_content_setting_values.notifications": 1
    }
    chrome_options.add_experimental_option("prefs", prefs)

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
    return browser

def login_facebook(username, password, is_ubuntu=False):
    """Login to Facebook using Selenium."""
    browser = init_browser(is_ubuntu)
    browser.get(FB_DEFAULT_URL)
    
    # Wait for login elements and enter credentials
    WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.ID, "email")))
    browser.find_element(By.ID, "email").send_keys(username)
    browser.find_element(By.ID, "pass").send_keys(password)
    browser.find_element(By.ID, "pass").send_keys(Keys.ENTER)
    
    # Wait for Facebook to respond after login
    WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.TAG_NAME, "img")))
    return browser

def login_facebook_ubuntu(username, password):
    """Convenience function for Ubuntu login."""
    return login_facebook(username, password, is_ubuntu=True)


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
def download_file(image_url, file_number, post_id, folder_path="/data_crawl/", game_name=""):
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
                # print(f"Skipping small image (dimensions: {width}x{height}) from URL: {image_url}")
                return
            
            # Update the image name with the correct file extension
            image_name = f"{file_number}.png"
            
            # Save the image
            with open(os.path.join(post_path, image_name), 'wb') as handler:
                handler.write(response.content)
            
            print(f"Image saved as {image_name} in {post_path} (dimensions: {width}x{height})")
        else:
            print(f"Failed to fetch image, Status code: {response.status_code}")
            
    except Exception as e:
        print(f"Error downloading image from {image_url}: {e}")


def crawlPostData(driver, postIds, game_name):
    empty_post_count = 0  # Counter for empty posts
    written_post_count = 0  # Counter for posts written to file

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
                    print(f"Post ID: {postId} - Content: {postContent[:50]}{'...' if len(postContent) > 50 else ''}")

                stt = 0
                for img in dataPost["images"]:
                    stt += 1
                    download_file(img, str(stt), postId, FOLDER_PATH_DATA_CRAWLER, game_name)

            sleep(random.randint(8, 12))
        except Exception as e:
            print(f"Error in crawlPostData: {e}")

    # Print total counts after processing
    print(f"\nTotal empty posts skipped: {empty_post_count}")
    print(f"Total posts written to file: {written_post_count}")



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
    
    
def run_fb_scraper_single_fanpage_posts(game_name):
    try:
        # Choose a random account and login
        username, password = random.choice(FB_ACCOUNT_LIST)
        browser = login_facebook(username, password)
        # browser = login_facebook_ubuntu(username, password)

        sleep(random.randint(2, 5))

        # Handle CAPTCHA if present
        if handle_captcha_if_present(browser, username, password):
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

                # Scroll down to load more posts
                scroll_down(browser)
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


def run_fb_scraper_multiple_fanpages(game_urls):
    """
    Run Facebook scraper for multiple fanpages using a single browser session
    
    Returns:
        bool: True if scraping completed successfully, False otherwise
    """
    try:
        # Choose a random account and login
        username, password = random.choice(FB_ACCOUNT_LIST)
        browser = login_facebook(username, password)
        
        current_url = browser.current_url
        if current_url.startswith("https://www.facebook.com/two_step_verification/authentication"):
            if not handle_captcha_if_present(browser, username, password):
                print("CAPTCHA handling failed, exiting.")
                return False  # Exit if CAPTCHA handling fails

        sleep_time = random.randint(3, 8)
        logger.info(f":::::: Sleeping for {sleep_time} seconds after scraping all games...")
        sleep(sleep_time)
            
        # Add human-like behavior before starting to scrape
        print("Simulating human-like browsing behavior before scraping...")
        
        # Perform some initial scrolls to mimic a person browsing
        initial_scroll_count = random.randint(3, 7)  # Random number of initial scrolls
        
        for i in range(initial_scroll_count):
            # Scroll down with varying speeds
            scroll_height = random.randint(300, 800)  # Random scroll distance
            browser.execute_script(f"window.scrollBy(0, {scroll_height});")
            
            # Add a random delay between scrolls (1-3 seconds)
            delay = random.uniform(4, 10)
            print(f"Initial scroll {i+1}/{initial_scroll_count}, waiting {delay:.2f} seconds...")
            sleep(delay)
            
            # Sometimes move mouse to random positions (simulating human behavior)
            if random.random() > 0.7:  # 30% chance to move mouse
                try:
                    # Find a random element to hover over
                    elements = browser.find_elements(By.TAG_NAME, "div")
                    if elements:
                        random_element = random.choice(elements[:20])  # Choose from first 20 elements
                        ActionChains(browser).move_to_element(random_element).perform()
                        print("Moving mouse to random element...")
                except Exception as e:
                    print(f"Mouse movement failed: {e}")
        
        # Pause briefly before starting the actual scraping
        final_pause = random.uniform(4, 6)
        print(f"Finished initial browsing behavior, pausing for {final_pause:.2f} seconds before scraping...")
        sleep(final_pause)

        # Process each game URL with the same browser session
        for index, game_url in enumerate(game_urls):
            try:
                print(f"\n----- Starting to scrape: {game_url} -----")
                
                # Extract game name from URL
                game_name = game_url.rstrip("/").split("/")[-1]
                
                # Navigate to game page
                browser.get(f"{FB_DEFAULT_URL}/{game_url}")
                sleep(random.randint(5, 9) if index < len(game_urls) - 1 else 0)  # Wait for page load
                
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
                crawlPostData(browser, readData(post_id_full_path), game_name)
                
                print(f"----- Done {len(all_posts)} posts: Game {game_name} -----")
                
                # Add random delay after processing all games
                if index < len(game_urls) - 1:  # Only sleep if not the last game
                    sleep_time = random.randint(120, 400)
                    logger.info(f":::::: Sleeping for {sleep_time} seconds after scraping all games...")
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