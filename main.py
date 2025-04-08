from pathlib import Path
import random
from time import sleep
from backend.fblogin import run_fb_scraper_single_fanpage_posts, run_fb_scraper_multiple_fanpages
from backend.constants import FOLDER_PATH_DATA_CRAWLER
from backend.utils.index import get_game_fanpages, should_scrape_game
import logging


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
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
        
        # Single Fanpage
        # for i, game_url in enumerate(game_urls):
        #     game_path = base_path / game_url
        #     logger.info(f"Processing: {game_path}")

        #     if not should_scrape_game(game_url, base_path):
        #         logger.info(f"Skipping {game_url} - folder exists")
        #         continue
                
        #     logger.info(f"Scraping posts for {game_url}")
        #     run_fb_scraper_single_fanpage_posts(game_url)
            
        #     # Add random delay between games, except for last game
        #     if i < len(game_urls) - 1:
        #         sleep_time = random.randint(120, 400)
        # logger.info(f":::::: Sleeping for {sleep_time} seconds after scraping all games...")
        # sleep(sleep_time)
        
        # Multiple Fanpages
        logger.info("Starting to scrape multiple fanpages...")
        run_fb_scraper_multiple_fanpages(game_urls)

        # Add random delay after processing all games
        sleep_time = random.randint(120, 400)
        logger.info(f":::::: Sleeping for {sleep_time} seconds after scraping all games...")
        sleep(sleep_time)

    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        exit(1)
