import time
import logging
from pathlib import Path
from backend.service.scraper_post_fb import run_fb_scraper_multiple_fanpages
from backend.constants import FOLDER_PATH_DATA_CRAWLER, CONFIG_LDPLAYER_FOLDER
from backend.utils.index import get_game_fanpages
from backend.service.migrate_db import insert_paragraph_to_db
from backend.service.text_generate_deepseek import rewrite_paragraph_deepseek
from backend.service.update_ld_devices import main as check_ld_devices


def run_step(step_num, step_name, func, *args, **kwargs):
    """Execute a step with proper logging and error handling"""
    logger.info(f"Starting Step {step_num}: {step_name}...")
    try:
        result = func(*args, **kwargs)
        logger.info(f"Step {step_num} completed successfully.")
        return result
    except Exception as e:
        logger.error(f"Error in Step {step_num} ({step_name}): {str(e)}")
        print(f"Step {step_num} failed: {str(e)}")
        return None


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

        # ------------------------ Step 0: Check LDPlayer devices ------------------------
        run_step(0, "Checking LDPlayer devices", check_ld_devices, CONFIG_LDPLAYER_FOLDER)
        time.sleep(4)  # Delay before proceeding to next step
        
        # ------------------------ Step 1: Scrape multiple fanpages ------------------------
        result = run_step(1, "Scraping multiple fanpages", run_fb_scraper_multiple_fanpages, game_urls)
        time.sleep(5)  # Delay between steps
        
        if not result:
            logger.warning("Step 1 failed. Cannot proceed to step 2.")
            print("Step 1 failed. Cannot proceed to step 2.")
            exit(1)
            
        # ------------------------ Step 2: Rewrite paragraphs with DeepSeek ------------------------
        rewrite_result = run_step(2, "Rewriting paragraphs with DeepSeek", rewrite_paragraph_deepseek)
        time.sleep(5)  # Delay between steps
        
        if not rewrite_result:
            logger.warning("Step 2 failed. Cannot proceed to step 3.")
            print("Step 2 failed. Cannot proceed to step 3.")
            exit(1)
            
        # ------------------------ Step 3: Insert paragraph to database ------------------------
        run_step(3, "Inserting paragraphs to database", insert_paragraph_to_db)

    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        exit(1)
