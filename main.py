import requests
import os
from pathlib import Path
from backend.fblogin import run_fb_scraper_posts
from backend.constants import SERVICE_URL, FOLDER_PATH_DATA_CRAWLER

def get_game_fanpages():
    """Fetch game fanpage URLs from service and extract game names."""
    try:
        response = requests.get(f'{SERVICE_URL}/game_fanpages')
        response.raise_for_status()
        return [game['fanpage'].split('/')[-1] for game in response.json()]
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

if __name__ == "__main__":
    game_urls = get_game_fanpages()
    if not game_urls:
        print("No game URLs found. Exiting.")
        exit(1)
        
    print("Found game URLs:", game_urls)
    
    # Create base crawler path
    base_path = Path(FOLDER_PATH_DATA_CRAWLER.strip("/\\"))
    base_path = Path.cwd() / base_path
    
    for game_url in game_urls:
        data_crawler_path = base_path / game_url
        print(f"Processing path: {data_crawler_path}")

        if not should_scrape_game(game_url, base_path):
            print(f":::: ---- Skipping {game_url} - folder already exists ---- ::::")
            continue
            
        print(f"Scraping posts for {game_url}")
        run_fb_scraper_posts(game_url)
        
        break
