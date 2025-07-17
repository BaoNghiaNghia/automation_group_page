import os
import time
import psutil
import socket
import random
import shutil
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    NoAlertPresentException,
    UnexpectedAlertPresentException,
    ElementNotInteractableException,
)
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from backend.utils.index import (
    get_chrome_version_main
)
from backend.constants import (
    logger,
    BASE_PROFILE_DIR
)


def close_all_alerts(browser):
    """Đóng tất cả alert popup nếu có."""
    if browser is None:
        return
        
    try:
        for _ in range(5):  # lặp nhiều lần đề phòng nhiều alert
            alert = browser.switch_to.alert
            alert.dismiss()  # Hoặc alert.accept() tùy tình huống
            time.sleep(0.5)
    except NoAlertPresentException:
        pass
    except UnexpectedAlertPresentException:
        pass


def close_html_popups(browser):
    """Đóng các popup dạng modal HTML nếu có."""
    try:
        # Ví dụ: popup có class 'popup' và nút đóng có class 'close-btn'
        popups = browser.find_elements(By.CLASS_NAME, "popup")
        for popup in popups:
            try:
                close_btn = popup.find_element(By.CLASS_NAME, "close-btn")
                close_btn.click()
                time.sleep(0.5)
            except ElementNotInteractableException:
                pass
    except Exception:
        pass


def clear_chrome_cache_folder(user_data_dir):
    """
    Xóa thư mục cache 'Cache_Data' nằm trong đường dẫn:
    <user_data_dir>/Profile_<tên_profile>/Cache/Cache_Data
    """
    # Lấy tên thư mục profile, giả sử có dạng 'Profile_<email>'
    profile_folder_name = None
    # Duyệt các thư mục con trong user_data_dir để tìm folder bắt đầu bằng 'Profile_'
    try:
        for entry in os.listdir(user_data_dir):
            if entry.startswith('Profile_') and os.path.isdir(os.path.join(user_data_dir, entry)):
                profile_folder_name = entry
                break
    except Exception as e:
        logger.warning(f"Failed to list directories in {user_data_dir}")
        return

    if not profile_folder_name:
        logger.info(f"No profile folder found in {user_data_dir}")
        return

    cache_data_path = os.path.join(user_data_dir, profile_folder_name, 'Cache', 'Cache_Data')

    if os.path.exists(cache_data_path) and os.path.isdir(cache_data_path):
        try:
            shutil.rmtree(cache_data_path)
        except Exception as e:
            logger.warning(f"Failed to clear cache folder {cache_data_path}")
    else:
        logger.info(f"Cache folder not found or not a directory: {cache_data_path}")


def is_logged_in(browser):
    """Check if the user is logged in to Google."""
    try:
        # Look for elements that indicate a successful login
        # This could be a profile icon or email address
        WebDriverWait(browser, 5).until(
            EC.presence_of_element_located((By.XPATH, "//a[contains(@href, 'SignOutOptions')]"))
        )
        logger.info("Login verification successful - user is logged in")
        return True
    except:
        logger.warning("Login verification failed - user is not logged in")
        return False


def wait_for_redirect(browser, expected_url):
    """Wait for the page to redirect to the expected URL."""
    try:
        WebDriverWait(browser, 2).until(
            EC.url_contains(expected_url)
        )
        print(f"Page has been redirected to: {browser.current_url}")
    except Exception as e:
        print(f"Error: Page did not redirect to {expected_url}. Current URL: {browser.current_url}")




def clear_uc_driver_cache():
    cache_dir = os.path.expandvars(r'%APPDATA%\undetected_chromedriver')
    if os.path.exists(cache_dir):
        try:
            shutil.rmtree(cache_dir)
        except Exception as e:
            logger.warning(f"Failed to delete cache folder {cache_dir}")
    else:
        logger.info(f"No undetected-chromedriver cache folder found at {cache_dir}")


def is_port_used_by_chrome(port):
    try:
        for proc in psutil.process_iter(['name', 'cmdline']):
            try:
                if proc.info['name'] and 'chrome' in proc.info['name'].lower():
                    cmdline = proc.info.get('cmdline', [])
                    for arg in cmdline:
                        if f'--remote-debugging-port={port}' in arg:
                            return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception as e:
        logger.warning(f"Exception occurred while checking if port {port} is used by Chrome")
    return False

def find_free_debug_port(start_port=9222, end_port=9224):
    """
    Find a random available debug port in the range that is not in use by any process
    except if the port is already used by another Chrome browser, in which case ignore it.
    """
    try:
        ports = list(range(start_port, end_port + 1))
        random.shuffle(ports)
        for port in ports:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(0.5)
                    if sock.connect_ex(('127.0.0.1', port)) != 0:
                        # Port is not in use at all
                        return port
                    else:
                        # Port is in use, check if it's used by Chrome
                        if is_port_used_by_chrome(port):
                            # Ignore this port, as it's used by another Chrome browser
                            continue
                        # Port is in use, but not by Chrome, so skip it
            except Exception as e:
                logger.warning(f"Exception occurred while checking port {port}")
                continue
        raise RuntimeError(f"⚠️ Không tìm được remote_debug_port trống trong khoảng {start_port}–{end_port}!")
    except Exception as e:
        logger.error(f"Error in find_free_debug_port")
        raise


def kill_chrome_using_profile(user_data_dir, port_range=(9222, 9224)):
    """
    Diệt Chrome đang dùng user_data_dir hoặc bất kỳ remote_debug_port trong khoảng.
    """
    start_port, end_port = port_range
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] and 'chrome' in proc.info['name'].lower():
                cmdline = proc.info.get('cmdline', [])
                uses_profile = any(f'--user-data-dir={user_data_dir}' in arg for arg in cmdline)
                uses_port = any(f'--remote-debugging-port={port}' in arg for arg in cmdline for port in range(start_port, end_port + 1))

                if uses_profile or uses_port:
                    # Log the specific port being killed
                    for port in range(start_port, end_port + 1):
                        if f'--remote-debugging-port={port}' in cmdline:
                            logger.info(f"🛑 Terminating Chrome PID={proc.pid} using profile/port {port}")
                            break
                    proc.terminate()
                    proc.wait(timeout=5)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
            continue


def kill_chrome_using_profile(user_data_dir, port_range=(9222, 9224)):
    """Terminate Chrome processes using the specified user data dir or remote debug port."""
    start_port, end_port = port_range
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] and 'chrome' in proc.info['name'].lower():
                cmdline = proc.info.get('cmdline', [])
                uses_port = any(f'--remote-debugging-port={port}' in arg for port in range(start_port, end_port + 1) for arg in cmdline)
                if uses_port:
                    logger.info(f"🛑 Terminating Chrome PID={proc.pid} using port {start_port}")
                    proc.terminate()
                    proc.wait(timeout=5)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
            continue


def get_chrome_options(user_data_dir, profile_dir, remote_debug_port, proxy):
    """Configure Chrome options for undetected_chromedriver."""
    try:
        options = uc.ChromeOptions()
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
        options.add_argument("--disable-blink-features=AutomationControlled")

        # Remote debugging setup
        options.add_argument(f"--remote-debugging-port={remote_debug_port}")
        options.add_argument(f"--user-data-dir={user_data_dir}")
        options.add_argument(f"--profile-directory={profile_dir}")

        # Add proxy if provided
        if proxy:
            options.add_argument(f'--proxy-server={proxy}')
            logger.info(f"Proxy {proxy} is being used")

        prefs = {
            "profile.default_content_setting_values.notifications": 1,
            "profile.default_content_setting_values.media_stream_camera": 1,
            "profile.default_content_setting_values.media_stream_mic": 1,
            "profile.default_content_setting_values.geolocation": 1,
            "profile.managed_default_content_settings.javascript": 1,
            "profile.default_content_settings.cookies": 1
        }
        options.add_experimental_option("prefs", prefs)

        return options
    except Exception as e:
        logger.error(f"Error configuring Chrome options")
        return None



def init_chrome_undetected_chromedriver(account, position_type="topleft", driver_path=None, proxy=None):
    """Initialize Chrome browser with undetected_chromedriver and unique remote debug port."""
    try:
        logger.info(f"------------------------- Start profile {account['username']} -------------------------")

        user_data_dir = os.path.join(BASE_PROFILE_DIR, f"chrome_profile_{account['username']}")
        profile_dir = f"Profile_{account['username']}"

        os.makedirs(BASE_PROFILE_DIR, exist_ok=True)
        os.makedirs(user_data_dir, exist_ok=True)

        remote_debug_port = find_free_debug_port(9222, 9229)

        options = get_chrome_options(user_data_dir, profile_dir, remote_debug_port, proxy)
        
        ver = get_chrome_version_main()
        
        if driver_path:
            browser = uc.Chrome(options=options, driver_executable_path=driver_path, version_main=int(ver))
        else:
            browser = uc.Chrome(options=options, version_main=int(ver))

        # Manually find the PID of the browser process
        browser_pid = None
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            if 'chrome' in proc.info['name'].lower():
                cmdline = proc.info.get('cmdline', [])
                if f'--remote-debugging-port={remote_debug_port}' in cmdline:
                    browser_pid = proc.info['pid']
                    break

        if browser_pid:
            logger.info(f"Chrome process PID: {browser_pid}")
        else:
            logger.warning("Could not find Chrome process PID.")

        # Capture the Chrome process command line to get the used port
        process = psutil.Process(browser_pid)  # Get process details using psutil

        # Find the remote debugging port in the command line
        cmdline = process.cmdline()
        debug_port = None
        for arg in cmdline:
            if '--remote-debugging-port=' in arg:
                debug_port = arg.split('=')[1]
                break

        if debug_port:
            logger.info(f"------------------------- Chrome is using remote debug port: {debug_port} -------------------------")
        else:
            logger.warning("Could not find remote debug port in the command line.")

        # Set window size and position based on position_type
        screen_width = browser.execute_script("return window.screen.width")
        screen_height = browser.execute_script("return window.screen.height")

        window_width = int(screen_width * 0.5)
        window_height = int(screen_height * 0.75)

        if position_type == "topleft":
            pos_x, pos_y = 0, 0
        elif position_type == "topright":
            pos_x, pos_y = screen_width - window_width, 0
        elif position_type == "bottomright":
            pos_x, pos_y = screen_width - window_width, (screen_height - window_height)*4/5
        elif position_type == "bottomleft":
            pos_x, pos_y = 0, screen_height - window_height
        else:
            pos_x, pos_y = 0, 0  # fallback

        browser.set_window_position(pos_x, pos_y)
        browser.set_window_size(window_width, window_height)

        return browser, remote_debug_port

    except Exception as e:
        logger.error(f"❌ Failed to initialize Chrome with undetected-chromedriver")
        raise
    
    
def authentication_google_account(account, position_type="topright", proxy=None):
    """Login to Google using account details and save cookies for future use."""
    browser = None
    try:
        browser, remote_debug_port = init_chrome_undetected_chromedriver(account, position_type, proxy)
        
        browser.get("https://accounts.google.com/ServiceLogin")
        
        time.sleep(random.randint(1, 2))
        
        # Username input
        WebDriverWait(browser, 2).until(
            EC.presence_of_element_located((By.ID, "identifierId"))
        )

        # Input email and press Enter
        if email_input := browser.find_element(By.ID, "identifierId"):
            email_input.send_keys(account["username"])
            email_input.send_keys(Keys.RETURN)

        time.sleep(random.randint(2, 5))

        # Password input
        WebDriverWait(browser, 2).until(
            EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div[1]/div[2]/c-wiz/div/div[2]/div/div/div/form/span/section[2]/div/div/div[1]/div[1]/div/div/div/div/div[1]/div/div[1]/input"))
        )

        # Input password and press Enter
        password_input = WebDriverWait(browser, 2).until(
            EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div[1]/div[2]/c-wiz/div/div[2]/div/div/div/form/span/section[2]/div/div/div[1]/div[1]/div/div/div/div/div[1]/div/div[1]/input"))
        )
        if password_input:
            password_input.send_keys(account["password"])
            password_input.send_keys(Keys.RETURN)

        time.sleep(random.randint(2, 4))
        
        # Find and click the element
        if element_option_recovery_email := browser.find_element(By.XPATH, "/html/body/div[1]/div[1]/div[2]/c-wiz/div/div[2]/div/div/div/form/span/section[2]/div/div/section/div/div/div/ul/li[3]/div"):
            element_option_recovery_email.click()
            logger.info("Successfully clicked the specified element")
        
            time.sleep(random.randint(2, 3))
            
            # RECOVERY EMAIL INPUT
            recovery_email_locator = (By.XPATH, "//input[@type='email' and contains(@aria-label, 'recovery')]")
            WebDriverWait(browser, 20).until(
                EC.presence_of_element_located(recovery_email_locator)
            )

            if recovery_email_input := browser.find_element(*recovery_email_locator):
                recovery_email_input.clear()  # Clear any existing text
                recovery_email_input.send_keys(account['recovery_email'])
                recovery_email_input.send_keys(Keys.RETURN)

                logger.info(f"Successfully entered recovery email: {account['recovery_email']}")

        time.sleep(random.randint(2, 3))
        
        # Button Lưu
        try:
            button_1 = WebDriverWait(browser, 2).until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/c-wiz[2]/div/div/div/div/div[2]/button[2]"))
            )
            button_1.click()
            logger.info("Successfully clicked the specified button")
        except Exception as e:
            logger.warning(f"Failed to click button_1")
            
        time.sleep(random.randint(2, 3))

        # Find and click "Not Now" button
        try:
            not_now_button = WebDriverWait(browser, 2).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Not Now')]"))
            )
            not_now_button.click()
            logger.info("Successfully clicked the 'Not Now' button")
        except Exception as e:
            logger.warning(f"Failed to click 'Not Now' button")
            
        time.sleep(random.randint(2, 3))

        # Button Lưu
        try:
            button_1 = WebDriverWait(browser, 2).until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/c-wiz[2]/div/div/div/div/div[2]/button[2]"))
            )
            button_1.click()
            logger.info("Successfully clicked the specified button")
        except Exception as e:
            logger.warning(f"Failed to click button_1")
            
        time.sleep(random.randint(2, 3))

        # Final button click "Bỏ qua"
        try:
            button_2 = WebDriverWait(browser, 2).until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/c-wiz[3]/div/div/div/div/div/div[2]/button[1]/span"))
            )
            button_2.click()
            logger.info("Successfully clicked the specified button")
        except Exception as e:
            logger.warning(f"Failed to click button_2")
            
        time.sleep(random.randint(2, 3))
            
        # Final button click "Bỏ qua"
        try:
            button_2 = WebDriverWait(browser, 2).until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/c-wiz[3]/div/div/div/div/div/div[2]/button[1]/span"))
            )
            button_2.click()
            logger.info("Successfully clicked the specified button")
        except Exception as e:
            logger.warning(f"Failed to click button_2")

        time.sleep(random.randint(2, 3))

        # Check if logged in by verifying the profile element
        if is_logged_in(browser):
            logger.info(f"Successfully logged into Google account: {account['username']}")
        else:
            logger.warning(f"Failed to log into Google account: {account['username']}")

    except Exception as e:
        logger.error(f"---------- Login failed for {account['username']}")
    
    return browser, remote_debug_port