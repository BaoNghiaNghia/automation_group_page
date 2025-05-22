import os
import random
import requests
from cryptography.fernet import Fernet
from backend.constants import ENV_CONFIG


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
        response = requests.get(f'{ENV_CONFIG[environment]["SERVICE_URL"]}/game_fanpages')
        response.raise_for_status()
        data = response.json()
        
        # Get all active game fanpages
        # Extract unique game fanpage URLs by using a set to remove duplicates
        active_games = list(set(game['fanpage'].split('/')[-1] for game in data['items'] if game.get('status') == 'active'))
        
        # If there are active games, randomly shuffle them before returning
        if active_games:
            random.shuffle(active_games)
        
        return active_games
    except requests.exceptions.RequestException as e:
        print(f"Error fetching game fanpages: {e}")
        return []
    
def get_game_fanpages_unique_for_scan(environment):
    """Fetch active game fanpage URLs from service and extract game names."""
    try:
        response = requests.get(f'{ENV_CONFIG[environment]["SERVICE_URL"]}/game_fanpages/available-scan')
        response.raise_for_status()
        data = response.json()
        
        return data['items']
    except requests.exceptions.RequestException as e:
        print(f"Error fetching game fanpages: {e}")
        return []
    
def get_all_game_fanpages(environment):
    """Fetch game fanpage URLs from service and extract game names."""
    try:
        response = requests.get(f'{ENV_CONFIG[environment]["SERVICE_URL"]}/game_fanpages')
        response.raise_for_status()
        data = response.json()
        return data['items']

    except requests.exceptions.RequestException as e:
        print(f"Error fetching game fanpages: {e}")
        return []

def should_scrape_game(game_url, base_path):
    """Check if game should be scraped based on existing folders."""
    try:
        game_folders = [f for f in os.listdir(base_path) if f.startswith(f"{game_url}_")]
        return len(game_folders) == 0
    except OSError as e:
        print(f"Error checking game folders: {e}")
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