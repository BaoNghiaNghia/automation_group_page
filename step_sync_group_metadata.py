import argparse
from backend.constants import ENV_CONFIG, logger
from backend.service.sync_metadata_group import run_sync_metadata_group


if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Run the text generation process")
    parser.add_argument("--environment", "-e", choices=["local", "production"], default="local",
                        help="Specify the environment: local or production")
    args = parser.parse_args()
    
    logger.info(f"Running in {args.environment} environment")
    
    try:
        run_sync_metadata_group(args.environment)
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(f"Process failed with error: {str(e)}")
