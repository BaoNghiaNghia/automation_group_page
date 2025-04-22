from backend.service.text_generate_gemini import rewrite_paragraph_gemini
from backend.service.text_generate_deepseek import rewrite_paragraph_deepseek
from backend.service.migrate_db import sync_device_from_computer
import logging
import argparse

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
        sync_device_from_computer(args.environment, args.pcrunner)

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(f"Process failed with error: {str(e)}")
