import argparse
import time
import sys
from backend.service.migrate_db import sync_post_into_database
from backend.constants import logger

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Run the post sync process in loop")
    parser.add_argument("--environment", "-e", choices=["local", "production"], default="production",
                        help="Specify the environment: local or production")
    args = parser.parse_args()
    
    logger.info(f"Running in {args.environment} environment")
    
    try:
        for i in range(100):
            logger.info(f"===== Run {i+1}/100 =====")
            sync_post_into_database(args.environment)
            logger.info("Sync completed successfully.")

            if i < 99:  # Không sleep sau lần cuối
                logger.info("Waiting 10 seconds before next run...")
                time.sleep(10)

        logger.info("✅ All 100 sync cycles completed successfully.")

    except Exception as e:
        logger.error(f"Unexpected error during run: {str(e)}", exc_info=True)
        print(f"Process failed with error: {str(e)}")
        sys.exit(1)
