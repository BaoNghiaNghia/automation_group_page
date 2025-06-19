import os
import base64
import requests
from selenium.webdriver.common.by import By
from backend.constants import API_KEY_CAPTCHA, DOMAIN_CAPTCHA

def image_to_base64(image_url):
    """Convert an image URL to base64."""
    response = requests.get(image_url, timeout=30)
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
    response = requests.post(f'{DOMAIN_CAPTCHA}/in.php', data=payload, timeout=30)
    response_text = response.text

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
    response = requests.post(f'{DOMAIN_CAPTCHA}/res.php', data=payload, timeout=30)
    response_text = response.text

    # Check if the response is valid and contains the expected result
    if response_text.startswith('OK|'):
        return response_text.split('|')[1]
    else:
        print(f"Error fetching CAPTCHA result: {response_text}")
        return None

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
        print(f"Error writing to file {file_path}")


# Read Post IDs from file (assumed function)
def readDataFromFile(fileName):
    with open(fileName, 'r', encoding="utf-8") as f:
        return [line.strip() for line in f.readlines()]
    