import pyautogui
import requests
import time

# ======= CONFIG ========
API_URL = "https://localhost:8080/service/proxy/all"
LDPLAYER_PATH_TEMPLATE = r"C:\Program Files\LDPlayer\LDPlayer9\ldplayer{}.exe"
WAIT = 1  # Thời gian chờ giữa các thao tác
VERIFY_SSL = False  # Bỏ nếu API localhost có chứng chỉ tự ký
# =======================

# Gọi API lấy danh sách proxy
def fetch_proxies():
    response = requests.get(API_URL, verify=VERIFY_SSL)
    response.raise_for_status()
    return response.json()

# Tạo proxy trong ProxyCap
def add_proxy(proxy, index):
    pyautogui.hotkey('alt', 'p')  # Vào menu Proxies
    time.sleep(WAIT)
    pyautogui.press('tab', presses=3)
    pyautogui.press('tab', presses=2)
    pyautogui.press('enter')  # Nhấn Add
    time.sleep(WAIT)

    pyautogui.write(f'Proxy_{index}')
    pyautogui.press('tab')
    if proxy["type"].lower() == "socks5":
        pyautogui.press('down', presses=2)
    elif proxy["type"].lower() == "https":
        pyautogui.press('down')
    pyautogui.press('tab')
    pyautogui.write(proxy["ip"])
    pyautogui.press('tab')
    pyautogui.write(str(proxy["port"]))
    pyautogui.press('tab')
    pyautogui.write(proxy.get("username", ""))
    pyautogui.press('tab')
    pyautogui.write(proxy.get("password", ""))
    pyautogui.press('enter')  # OK
    time.sleep(WAIT)

# Tạo rule cho LDPlayer instance tương ứng
def add_rule(index):
    pyautogui.hotkey('alt', 'r')  # Vào menu Rules
    time.sleep(WAIT)
    pyautogui.press('tab', presses=3)
    pyautogui.press('tab', presses=2)
    pyautogui.press('enter')  # Add
    time.sleep(WAIT)

    pyautogui.write(f'LDPlayer{index}')
    pyautogui.press('tab', presses=2)  # Đến Program
    path = LDPLAYER_PATH_TEMPLATE.format(index)
    pyautogui.write(path.replace("\\", "\\\\"))
    pyautogui.press('tab', presses=3)
    pyautogui.press('down', presses=index)  # Chọn proxy đúng index
    pyautogui.press('tab', presses=3)
    pyautogui.press('enter')  # OK
    time.sleep(WAIT)

# Mở ProxyCap trước khi chạy
def wait_for_user_start():
    pyautogui.alert("⚠️ Hãy mở ProxyCap và giữ giao diện hiện lên. Sau đó nhấn OK để bắt đầu.")

# Main
def run_setting_proxy():
    wait_for_user_start()
    proxies = fetch_proxies()

    for i, proxy in enumerate(proxies[:250]):  # Chỉ lấy 250 proxy đầu
        index = i + 1
        print(f"🔧 Đang xử lý proxy {index}: {proxy['ip']}:{proxy['port']}")
        add_proxy(proxy, index)
        add_rule(index)

    pyautogui.alert("✅ Đã hoàn tất gán proxy cho 250 instance LDPlayer.")