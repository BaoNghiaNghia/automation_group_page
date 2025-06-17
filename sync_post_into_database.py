import argparse
from backend.service.migrate_db import sync_post_into_database
from backend.constants import logger


if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Run the text generation process")
    parser.add_argument("--environment", "-e", choices=["local", "production"], default="local", help="Specify the environment: local or production")
    args = parser.parse_args()
    
    logger.info(f"Running in {args.environment} environment")
    
    try:
        sync_post_into_database(args.environment)

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(f"Process failed with error: {str(e)}")
