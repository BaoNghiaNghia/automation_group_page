from pathlib import Path
from backend.fblogin import run_fb_scraper_posts
from backend.constants import FOLDER_PATH_DATA_CRAWLER
from backend.utils.index import get_game_fanpages, should_scrape_game
import logging

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    try:
        # Create and normalize base path once
        base_path = Path.cwd() / FOLDER_PATH_DATA_CRAWLER.strip("/\\")
        base_path.mkdir(parents=True, exist_ok=True)

        # Get game URLs to scrape
        if not (game_urls := get_game_fanpages()):
            logger.error("No game URLs found")
            exit(1)
            
        logger.info(f"Found {len(game_urls)} game URLs: {game_urls}")
        
        # Process each game URL
        for game_url in game_urls:
            game_path = base_path / game_url
            logger.info(f"Processing: {game_path}")

            if not should_scrape_game(game_url, base_path):
                logger.info(f"Skipping {game_url} - folder exists")
                continue
                
            logger.info(f"Scraping posts for {game_url}")
            run_fb_scraper_posts(game_url)
            
            break  # Only process first game URL

    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        exit(1)
