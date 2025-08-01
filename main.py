import time
import argparse
from pathlib import Path
from backend.utils.index import get_all_game_fanpages
from backend.service.migrate_db import sync_post_into_database
from backend.service.update_ld_devices import update_ld_devices
from backend.constants import FOLDER_PATH_DATA_CRAWLER, ENV_CONFIG, logger
from backend.service.scraper.scraper_post_fanpage import run_fb_scraper_multiple_fanpages


def run_step(step_num, step_name, func, *args, **kwargs):
    """Execute a step with proper logging and error handling"""
    logger.info(f"Starting Step {step_num}: {step_name}...")
    try:
        result = func(*args, **kwargs)
        logger.info(f"-------------------------- Step {step_num} completed successfully. --------------------------")
        return result
    except Exception as e:
        logger.error(f"Error in Step {step_num} ({step_name}): {str(e)}")
        print(f"Step {step_num} failed: {str(e)}")
        return None


if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Run the scraper in local or production mode")
    parser.add_argument("--environment", "-e", choices=["local", "production"], default="production",
                        help="Specify the environment: local or production")
    parser.add_argument("--pcrunner", "-pc", type=str, default="pc_2",
                        help="Specify the computer name to sync from")
    args = parser.parse_args()
    
    logger.info(f"Running in {args.environment} environment")


    try:
        # Create and normalize base path once
        base_path = Path.cwd() / FOLDER_PATH_DATA_CRAWLER.strip("/\\")
        base_path.mkdir(parents=True, exist_ok=True)

        # Get game URLs to scrape
        if not (all_game_fanpages := get_all_game_fanpages(args.environment, {
            "page": 1,
            "limit": 300,
            "priority": 1        # 0 (normal) and 1 (priority)
        })):
            logger.error("No game URLs found")
            exit(1)
        
        group_refs_total, page_refs_total, x_refs_total = [], [], []
        for idx, game in enumerate(all_game_fanpages, 1):
            note = game.get('note')
            if note is None:
                logger.warning(f"  Note is None for game: {game.get('name_of_game', 'N/A')}")
                note = ''

            for line in note.split('\n'):
                if line.startswith("Group_Ref_"):
                    # Get text after the first colon
                    ref_value = line.split(":", 1)[1].strip() if ":" in line else ""
                    group_refs_total.append({"ref": ref_value, **game})
                elif line.startswith("Page_Ref_"):
                    ref_value = line.split(":", 1)[1].strip() if ":" in line else ""
                    page_refs_total.append({"ref": ref_value, **game})
                elif line.startswith("X_Ref_"):
                    ref_value = line.split(":", 1)[1].strip() if ":" in line else ""
                    x_refs_total.append({"ref": ref_value, **game})


        # ------------------------ Step 0: Check LDPlayer devices ------------------------
        run_step(0, "Checking LDPlayer devices", update_ld_devices, ENV_CONFIG[args.environment]["CONFIG_LDPLAYER_FOLDER"], args.environment, args.pcrunner)
        time.sleep(4)  # Delay before proceeding to next step

        # ------------------------ Step 1: Scrape multiple fanpages ------------------------
        result = run_step(1, "Scraping multiple fanpages", run_fb_scraper_multiple_fanpages, all_game_fanpages, args.environment)
        time.sleep(5)  # Delay between steps

        if not result:
            logger.warning("Step 1 failed. Cannot proceed to step 2.")
            print("Step 1 failed. Cannot proceed to step 2.")
            exit(1)

        # # ------------------------ Step 2: Rewrite paragraphs with DeepSeek ------------------------
        # rewrite_result = run_step(2, "Rewriting paragraphs with DeepSeek", rewrite_paragraph_deepseek, args.environment)
        # time.sleep(5)  # Delay between steps

        # if not rewrite_result:
        #     logger.warning("Step 2 failed. Cannot proceed to step 3.")
        #     print("Step 2 failed. Cannot proceed to step 3.")
        #     exit(1)

        # ------------------------ Step 3: Insert paragraph to database ------------------------
        run_step(3, "Inserting paragraphs to database", sync_post_into_database, args.environment)
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        exit(1)


# TODO 1: Quét tất cả các group đối thủ, kiếm bài post có nhiều tương tác, ghi chép lại rồi scrape về. viết lại content. sau đó cho tool đăng
# TODO 2: Cho 1 form nhập lên các bài, upload hình ảnh.
# TODO 3: Tool chạy seeding tay, nhập url + số lượng like hoặc tim