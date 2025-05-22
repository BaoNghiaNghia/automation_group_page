import logging
import argparse
from backend.constants import ENV_CONFIG, logger
from backend.service.update_ld_devices import update_ld_devices
from backend.service.scraper_post_fb import run_fb_scraper_multiple_fanpages
from backend.utils.index import get_all_game_fanpages


if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Run the text generation process")
    parser.add_argument("--environment", "-e", choices=["local", "production"], default="local",
                        help="Specify the environment: local or production")
    args = parser.parse_args()
    
    logger.info(f"Running in {args.environment} environment")
    
    try:
        run_post_fanpage_with_editor_role(all_game_fanpages, args.environment)
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(f"Process failed with error: {str(e)}")
