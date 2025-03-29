import random
import requests
import base64
import uuid
import json
import os
from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait

def image_to_base64(image_url):
    """Convert an image URL to base64."""
    response = requests.get(image_url)
    image_data = response.content
    return base64.b64encode(image_data).decode('utf-8')

def solve_captcha(image_url):
    """Solve CAPTCHA by sending the base64 image to the CAPTCHA API."""
    # Convert the image to base64
    base64_image = image_to_base64(image_url)
    
    # Prepare the API payload
    api_url = 'https://captcha69.com/in.php'
    payload = {
        'key': 'point_3d0bd505d511c336b6279f4815057b9a',
        'type_captcha': 'Default v.1',
        'method': 'base64',
        'body': base64_image
    }

    # Send the image data to the CAPTCHA API
    response = requests.post(api_url, data=payload)
    return response.text

def get_captcha_result(captcha_id):
    """Fetch CAPTCHA result using the provided captcha_id."""
    # URL for fetching the CAPTCHA result
    api_url = 'https://captcha69.com/res.php'
    
    # Prepare the payload with the CAPTCHA ID
    payload = {
        'key': 'point_3d0bd505d511c336b6279f4815057b9a',
        'action': 'get',
        'id': captcha_id
    }
    
    # Send the request to the API to fetch the result
    response = requests.post(api_url, data=payload)
    
    # Return the response text (this will be either the result or an error message)
    return response.text

# OCR API function
def ocr_space_file(filename, overlay=False, api_key='K82610453088957', language='eng'):
    payload = {
        'isOverlayRequired': overlay,
        'apikey': api_key,
        'language': language,
    }
    with open(filename, 'rb') as f:
        r = requests.post(
            'https://api.ocr.space/parse/image',
            files={filename: f},
            data=payload,
        )
    return r.content.decode()

# Danh sách tài khoản Facebook (user, password)
accounts = [
    ("0399988593", "p6+p7N&r%M$#B5b"),
    # ("Dinh09102002@gmail.com", "Vutuan1985@")
]


# Chọn ngẫu nhiên một tài khoản
username, password = random.choice(accounts)

# Mở trình duyệt
service = Service(executable_path="./chromedriver.exe")
browser = webdriver.Chrome(service=service)
browser.get("https://facebook.com")
sleep(2)

# Đăng nhập
browser.find_element(By.ID, "email").send_keys(username)
browser.find_element(By.ID, "pass").send_keys(password)
browser.find_element(By.ID, "pass").send_keys(Keys.ENTER)

# Chờ Facebook phản hồi
sleep(5)

# Lấy tất cả thẻ <img>
img_tags = browser.find_elements(By.TAG_NAME, "img")

captcha_img = None
for img in img_tags:
    src = img.get_attribute("src")
    alt = img.get_attribute("alt")
    if src and "captcha" in src:
        captcha_img = img
        break
    
print(f"----- captcha image : {captcha_img.get_attribute("src")}")
id_ocr_resolver = solve_captcha(captcha_img.get_attribute("src"))
captcha_text = get_captcha_result(id_ocr_resolver.split('|')[1] )
print(f"----- captcha text : {captcha_text}")

# Nếu tìm thấy captcha image
if captcha_img:
    captcha_input = browser.find_element(By.TAG_NAME, "input")

    # Nhập captcha
    captcha_input.send_keys(captcha_text)
    captcha_input.send_keys(Keys.ENTER)
else:
    print("Không tìm thấy ảnh captcha")

# Đợi thêm để xem kết quả
sleep(100)
browser.quit()