import argparse
from backend.constants import ENV_CONFIG, logger
from backend.service.proxy_mapping import run_setting_proxy


if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Run the text generation process")
    parser.add_argument("--environment", "-e", choices=["local", "production"], default="production",
                        help="Specify the environment: local or production")
    parser.add_argument("--pcrunner", "-pc", type=str, default="pc_1",
                        help="Specify the computer name to sync from")
    args = parser.parse_args()
    
    logger.info(f"Running in {args.environment} environment")
    
    try:
        run_setting_proxy(ENV_CONFIG[args.environment]["CONFIG_LDPLAYER_FOLDER"], args.environment, args.pcrunner)

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(f"Process failed with error: {str(e)}")
