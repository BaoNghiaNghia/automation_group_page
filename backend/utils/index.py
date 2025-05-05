import os
import random
import requests
from backend.constants import ENV_CONFIG

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
