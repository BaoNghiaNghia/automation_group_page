import time
from pathlib import Path
from time import sleep
from backend.scraper_post_fb import run_fb_scraper_multiple_fanpages
from backend.constants import FOLDER_PATH_DATA_CRAWLER
from backend.utils.index import get_game_fanpages
from backend.service.migrate_db import insert_paragraph_to_db
from backend.service.text_generate_deepseek import rewrite_paragraph_deepseek
from backend.service.update_ld_devices import main as check_ld_devices
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


        # Step 0: Check LDPlayer devices
        logger.info("Starting Step 0: Checking LDPlayer devices...")
        try:
            check_ld_devices(r"C:\LDPlayer\LDPlayer9\vms\config")
            logger.info("Step 0 completed: LDPlayer devices checked successfully.")
        except Exception as e:
            logger.error(f"Error in Step 0 (checking LDPlayer devices): {str(e)}")
            print(f"Step 0 failed: {str(e)}")
        
        # Add a delay before proceeding to Step 1
        logger.info("Adding a 4-second delay between steps...")
        time.sleep(4)
        
        # Step 1: Scrape multiple fanpages
        logger.info("Starting Step 1: Scraping multiple fanpages...")
        result = run_fb_scraper_multiple_fanpages(game_urls)
        
        # Add a delay between Step 1 and Step 2
        logger.info("Adding a 4-second delay between steps...")
        time.sleep(5)
        
        # Wait for step 1 to complete before proceeding
        if result:
            logger.info("Step 1 completed successfully.")
            
            try:
                # Step 2: Rewrite paragraphs with DeepSeek
                logger.info("Starting Step 2: Rewriting paragraphs with DeepSeek")
                rewrite_result = rewrite_paragraph_deepseek()
                
                # Add a delay between Step 2 and Step 3
                logger.info("Adding a 4-second delay between steps...")
                time.sleep(5)
                
                if rewrite_result:
                    logger.info("Step 2 completed successfully.")
                    
                    try:
                        # Step 3: Insert paragraph to database
                        logger.info("Starting Step 3: Inserting paragraphs to database")
                        insert_paragraph_to_db()
                        logger.info("Step 3 completed: Paragraphs inserted to database.")
                    except Exception as e:
                        logger.error(f"Error in Step 3: {str(e)}")
                        print(f"Step 3 failed: {str(e)}")
                else:
                    logger.warning("Step 2 failed. Cannot proceed to step 3.")
                    print("Step 2 failed. Cannot proceed to step 3.")
            except Exception as e:
                logger.error(f"Error in Step 2: {str(e)}")
                print(f"Step 2 failed: {str(e)}")
        else:
            logger.warning("Step 1 failed. Cannot proceed to step 2.")
            print("Step 1 failed. Cannot proceed to step 2.")

    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        exit(1)
