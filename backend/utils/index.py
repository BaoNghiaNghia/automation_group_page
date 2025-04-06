import requests
import os
from backend.constants import SERVICE_URL

def get_game_fanpages():
    """Fetch game fanpage URLs from service and extract game names."""
    try:
        response = requests.get(f'{SERVICE_URL}/game_fanpages')
        response.raise_for_status()
        data = response.json()
        return [game['fanpage'].split('/')[-1] for game in data['items']]
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
