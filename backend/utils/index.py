import os
import re, subprocess
import psutil
import sys
import random
import requests
from cryptography.fernet import Fernet
from backend.constants import (
    logger,
    ENV_CONFIG
)


# Generate a key (do this once and save it securely)
key = Fernet.generate_key()

# Create Fernet object
cipher_suite = Fernet(Fernet.generate_key())

def encrypt_string(plain_text: str) -> bytes:
    return cipher_suite.encrypt(plain_text.encode())

def decrypt_string(encrypted_text: bytes) -> str:
    return cipher_suite.decrypt(encrypted_text).decode()


def get_game_fanpages_unique(environment):
    """Fetch active game fanpage URLs from service and extract game names."""
    try:
        response = requests.get(f'{ENV_CONFIG[environment]["SERVICE_URL"]}/game_fanpages?page=1&limit=300', timeout=30)
        response.raise_for_status()
        data = response.json()

        active_games = list(set(game['fanpage'].split('/')[-1] for game in data['data']['items'] if game.get('status') == 'active'))
        
        # If there are active games, randomly shuffle them before returning
        if active_games:
            random.shuffle(active_games)

        return active_games
    except requests.exceptions.RequestException as e:
        print(f"Error fetching game fanpages")
        return []
    
def get_game_fanpages_unique_for_scan(environment):
    """Fetch active game fanpage URLs from service and extract game names."""
    try:
        response = requests.get(f'{ENV_CONFIG[environment]["SERVICE_URL"]}/game_fanpages/available-scan', timeout=30)
        response.raise_for_status()
        data = response.json()
        
        return data['items']
    except requests.exceptions.RequestException as e:
        print(f"Error fetching game fanpages")
        return []
    
def get_all_game_fanpages(environment, query):
    """Fetch game fanpage URLs from service and extract game names."""
    try:
        response = requests.get(
            f'{ENV_CONFIG[environment]["SERVICE_URL"]}/game_fanpages',
            params=query,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        return data['data']['items']

    except requests.exceptions.RequestException as e:
        print(f"Error fetching game fanpages")
        return []

def should_scrape_game(game_url, base_path):
    """Check if game should be scraped based on existing folders."""
    try:
        game_folders = [f for f in os.listdir(base_path) if f.startswith(f"{game_url}_")]
        return len(game_folders) == 0
    except OSError as e:
        print(f"Error checking game folders")
        return False


def filter_existing_posts(all_post_id_scanned, game_fanpage_id, environment):
    """
    Filter out posts that already exist in the database.
    
    Args:
        all_post_id_scanned (set): Set of post IDs to check
        game_fanpage_id (str): Name of the game fanpage
        environment (str): Current environment configuration
        
    Returns:
        set: Filtered set of post IDs that don't exist in database
    """
    if not all_post_id_scanned:
        return set()

    try:
        response = requests.post(
            f'{ENV_CONFIG[environment]["SERVICE_URL"]}/daily_posts_content/check_exist_post_id',
            headers={'Content-Type': 'application/json'},
            json={
                "post_id": list(all_post_id_scanned),
                "game_fanpage_id": game_fanpage_id
            },
            timeout=30
        )
        response.raise_for_status()
        return set(response.json().get('data', []))
            
    except requests.exceptions.RequestException as e:
        return all_post_id_scanned
    except Exception as e:
        return all_post_id_scanned
    
def get_chrome_version_main():
    ver = None

    # 1. Thử đọc từ Registry trên Windows
    if sys.platform.startswith("win"):
        try:
            import winreg
            # HKEY_CURRENT_USER cho Chrome user installs
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
            full_ver, _ = winreg.QueryValueEx(key, "version")
            ver = full_ver.split(".")[0]
            winreg.CloseKey(key)
            return ver
        except Exception:
            pass

        # cũng có thể thử dưới HKLM nếu cài cho tất cả user
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Google\Chrome\BLBeacon")
            full_ver, _ = winreg.QueryValueEx(key, "version")
            ver = full_ver.split(".")[0]
            winreg.CloseKey(key)
            return ver
        except Exception:
            pass

    # 2. Fallback: thử một loạt tên lệnh trên Linux / Mac
    for cmd in ("google-chrome", "chrome", "chromium-browser", "chromium", "Google Chrome"):
        try:
            out = subprocess.check_output([cmd, "--version"], stderr=subprocess.DEVNULL).decode()
            m = re.search(r"(\d+)\.", out)
            if m:
                return m.group(1)
        except Exception:
            continue

    return None


def close_remote_debug_port(remote_debug_port):
    try:
        for proc in psutil.process_iter(attrs=['pid', 'name']):
            # Check if the process is a Chrome browser instance
            if proc.info['name'] == 'chrome.exe':  # Modify for other browsers if necessary
                try:
                    # Only access connections if they are available
                    connections = proc.connections(kind='inet')
                    for conn in connections:
                        if conn.laddr.port == remote_debug_port:
                            proc.kill()  # Kill the process using the remote debug port
                            logger.info(f"Successfully killed the process using port {remote_debug_port}.")
                            break
                except psutil.NoSuchProcess:
                    logger.error("Process has already terminated.")
                    continue
                except psutil.AccessDenied:
                    logger.warning("Access denied to process connections.")
                    continue
    except Exception as e:
        logger.error(f"Error closing remote debug port: {str(e)}")