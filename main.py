from pathlib import Path
from backend.fblogin import run_fb_scraper_posts
from backend.constants import FOLDER_PATH_DATA_CRAWLER
from backend.utils.index import get_game_fanpages, should_scrape_game

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
