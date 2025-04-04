import requests
import os
from backend.fblogin import run_fb_scraper_posts
from backend.constants import SERVICE_URL, FOLDER_PATH_DATA_CRAWLER

def get_game_fanpages():
    response = requests.get(f'{SERVICE_URL}/game_fanpages')
    data = response.json()
    
    # Extract fanpage URLs and get the text after the last /
    game_urls = []
    for game in data:
        fanpage = game['fanpage']
        game_name = fanpage.split('/')[-1]
        game_urls.append(game_name)
    
    return game_urls

if __name__ == "__main__":
    game_urls = get_game_fanpages()
    print(game_urls)
    for game_url in game_urls:
        data_crawler_path = os.path.join(os.getcwd(), FOLDER_PATH_DATA_CRAWLER.strip("/\\"), game_url)
        print(data_crawler_path)
        # Check if any folder starts with game_url
        game_url_folders = [f for f in os.listdir(os.path.dirname(data_crawler_path)) if f.startswith(game_url + "_")]
        if game_url_folders:
            print(f":::: ---- Skipping {game_url} - folder already exists ---- ::::")
            continue
        print(f"Scraping posts for {game_url}")
        run_fb_scraper_posts(game_url)

