import logging
import argparse
from backend.constants import ENV_CONFIG, logger
from backend.service.update_ld_devices import update_ld_devices
from backend.service.scraper_post_fb import run_fb_scraper_multiple_fanpages
from backend.utils.index import get_game_fanpages


if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Run the text generation process")
    parser.add_argument("--environment", "-e", choices=["local", "production"], default="local",
                        help="Specify the environment: local or production")
    parser.add_argument("--pcrunner", "-pc", type=str, default="pc_1",
                        help="Specify the computer name to sync from")
    args = parser.parse_args()
    
    logger.info(f"Running in {args.environment} environment")
    
    try:

        # Get game URLs to scrape
        if not (game_urls := get_game_fanpages(args.environment)):
            logger.error("No game URLs found")
            exit(1)

        run_fb_scraper_multiple_fanpages(game_urls, args.environment)
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(f"Process failed with error: {str(e)}")
