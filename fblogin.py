import random
from urllib.parse import urlparse, parse_qs
import requests
import os
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
from constants import FB_ACCOUNT_LIST, FB_DEFAULT_URL, GAME_NAME_URL, API_KEY_CAPTCHA, DOMAIN_CAPTCHA, FOLDER_PATH_DATA_CRAWLER, LIMIT_POST_PER_DAY


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
    response = requests.post(f'{DOMAIN_CAPTCHA}/in.php', data=payload)
    response_text = response.text
    print(f"Captcha solve response: {response}")  # Debugging output

    # Ensure we got a valid captcha_id
    if response_text.startswith('OK|'):
        return response_text
    else:
        print(f"Error solving CAPTCHA: {response_text}")
        return None

def get_captcha_result(captcha_id):
    """Fetch CAPTCHA result using the provided captcha_id."""
    payload = {
        'key': API_KEY_CAPTCHA,
        'action': 'get',
        'id': captcha_id
    }
    response = requests.post(f'{DOMAIN_CAPTCHA}/res.php', data=payload)
    response_text = response.text

    # Check if the response is valid and contains the expected result
    if response_text.startswith('OK|'):
        return response_text.split('|')[1]
    else:
        print(f"Error fetching CAPTCHA result: {response_text}")
        return None


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
    sleep(5)  # Wait for content to load


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

        # print(postData)
        return postData
    except Exception as e:
        print(f"Error in clonePostContent: {e}")
        return False


# def clonePostContent(driver, postId):
#     try:
#         driver.get(f"{FB_DEFAULT_URL}/{str(postId)}")
        
#         # Find the parent image container using the full XPath
#         imageGrElement = driver.find_elements(By.XPATH, "/html/body/div[1]/div/div[1]/div/div[5]/div/div/div[2]/div/div/div/div/div/div/div/div[2]/div[2]/div/div/div/div/div/div/div/div/div/div/div/div/div[13]/div/div/div[3]/div[2]")
        
#         # Find the content element containing all the text
#         contentElement = driver.find_elements(By.XPATH, "/html/body/div[1]/div/div[1]/div/div[5]/div/div/div[2]/div/div/div/div/div/div/div/div[2]/div[2]/div/div/div/div/div/div/div/div/div/div/div/div/div[13]/div/div/div[3]/div[1]")
        
#         content = ""
#         # Get all text from contentElement
#         if len(contentElement):
#             content = " ".join([elem.text for elem in contentElement])  # Concatenate text from all elements
        
#         # Get all image links inside the parent image element
#         linksArr = []
#         if len(imageGrElement):
#             childsImage = imageGrElement[0].find_elements(By.TAG_NAME, "img")
#             for childImg in childsImage:
#                 linkImage = childImg.get_attribute('src')
#                 if linkImage:
#                     linksArr.append(linkImage)

#         postData = {"post_id": postId, "content": content, "images": linksArr}

#         print(postData)
#         return postData
#     except Exception as e:
#         print(f"Error in clonePostContent: {e}")
#         return False


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

        # Update the image name with the correct file extension
        image_name = f"{file_number}.png"

        # Get the image content from the URL and save it to the file
        img_data = requests.get(image_url).content

        # Save the image
        with open(os.path.join(post_path, image_name), 'wb') as handler:
            handler.write(img_data)

        print(f"Image saved as {image_name} in {post_path}")
    except Exception as e:
        print(f"Error downloading image from {image_url}: {e}")


def crawlPostData(driver, postIds, game_name):
    for id in postIds:
        try:
            dataPost = clonePostContent(driver, id)
            if dataPost:
                postId = str(dataPost['post_id'])
                postContent = str(dataPost['content'])
                writeFileTxtPost('content.txt', postContent, postId, FOLDER_PATH_DATA_CRAWLER, game_name)
                print(f"Post ID: {postId} - Content: {postContent}")
                stt = 0
                for img in dataPost["images"]:
                    stt += 1
                    download_file(img, str(stt), postId, FOLDER_PATH_DATA_CRAWLER, game_name)
                
            sleep(5)
        except Exception as e:
            print(f"Error in crawlPostData: {e}")

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


def run_fb_scraper_posts(game_name):
    try:
        # Choose a random account and login
        username, password = random.choice(FB_ACCOUNT_LIST)
        browser = login_facebook(username, password)

        # Handle CAPTCHA if present
        if captcha_img := get_captcha_image(browser):
            captcha_img_url = captcha_img.get_attribute("src")
            print(f"Found CAPTCHA image: {captcha_img_url}")

            # Solve CAPTCHA and submit
            captcha_id = solve_captcha(captcha_img_url).split('|')[1]
            captcha_text = get_captcha_result(captcha_id)
            print(f"Captcha Reponse: {captcha_text}")

            captcha_input = browser.find_element(By.TAG_NAME, "input")
            captcha_input.send_keys(captcha_text)
            submit_captcha(browser)
            sleep(5)

            # Re-login if needed
            try:
                login_form = WebDriverWait(browser, 10).until(
                    EC.presence_of_element_located((By.ID, "email"))
                )
                browser.find_element(By.ID, "email").send_keys(username)
                browser.find_element(By.ID, "pass").send_keys(password + Keys.ENTER)
            except Exception:
                print("Already logged in or no re-login needed.")

            # Wait for redirect and collect posts
            wait_for_redirect(browser, f"{FB_DEFAULT_URL}/{game_name}")

            all_posts = set()
            last_height = browser.execute_script("return document.body.scrollHeight")
            
            for attempt in range(50):
                print(f"\n[Scrolling Attempt {attempt + 1}]")
                current_posts = get_posts_by_attribute(browser, game_name)
                all_posts.update(current_posts)
                
                if len(all_posts) >= LIMIT_POST_PER_DAY:
                    break
                
                # Check if no posts found after 3 attempts
                if attempt >= 3 and len(all_posts) == 0:
                    print("No posts found after 4 attempts, exiting.")
                    sleep(10)
                    browser.quit()
                    return
                
                # Scroll down and check if we've reached the bottom
                scroll_down(browser)
                new_height = browser.execute_script("return document.body.scrollHeight")
                
                if new_height == last_height:
                    print("Reached end of page, stopping scroll.")
                    break
                    
                last_height = new_height
                
                if attempt == 49:
                    print("Too many scroll attempts, exiting.")

            print(f"\nTotal unique posts collected: {len(all_posts)}")

            # Save posts to file
            post_id_file_name = f"facebook_{game_name}_post_ids.txt"
            with open(post_id_file_name, "w", encoding="utf-8") as f:
                f.write("\n".join(sorted(all_posts)))
            print(f"Post IDs saved to {post_id_file_name}")

            # Process posts
            sleep(5)
            crawlPostData(browser, readData(post_id_file_name), game_name)
            
            sleep(2)
            print(f"----- Done {LIMIT_POST_PER_DAY} posts: Game {game_name} -----")
            
        else:
            print("No CAPTCHA image found.")
            
    except Exception as e:
        print(f"Error in main: {e}")
        
    finally:
        browser.quit()
