from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from time import sleep

# 1. Khai báo biến browser
service = Service(executable_path="./chromedriver.exe")
browser = webdriver.Chrome(service=service)

# 2. Mở thử một trang web
browser.get("http://facebook.com")

# 2a. Điền thông tin vào ô user và pass
txtUser = browser.find_element(By.ID, "email")
txtUser.send_keys("0399988593")  # <-- Điền username thật của bạn vào đây

txtPass = browser.find_element(By.ID, "pass")
txtPass.send_keys("p6+p7N&r%M$#B5b")

# 2b. Submit form
txtPass.send_keys(Keys.ENTER)

# 3. Dừng chương trình 5 giây
sleep(30)

# 4. Đóng trình duyệt
# browser.close()
