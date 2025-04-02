import requests
import base64
from selenium.webdriver.common.by import By
from constants import API_KEY_CAPTCHA, DOMAIN_CAPTCHA

def image_to_base64(image_url):
    """Convert an image URL to base64."""
    response = requests.get(image_url)
    return base64.b64encode(response.content).decode('utf-8')


def get_captcha_image(browser):
    """Retrieve CAPTCHA image if present on Facebook login page."""
    img_tags = browser.find_elements(By.TAG_NAME, "img")
    for img in img_tags:
        src = img.get_attribute("src")
        if src and "captcha" in src:
            return img
    return None

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