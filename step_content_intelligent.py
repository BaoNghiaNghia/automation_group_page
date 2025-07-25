import argparse
from backend.constants import ENV_CONFIG, logger
from backend.service.scraper.scraper_post_group import run_scraper_multiple_groups
from backend.service.scraper.scraper_post_twitter import run_scraper_multiple_twitter
from backend.service.scraper.scraper_post_fanpage import run_fb_scraper_multiple_fanpages
from backend.utils.index import get_all_game_fanpages


if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Run the text generation process")
    parser.add_argument("--environment", "-e", choices=["local", "production"], default="production", help="Specify the environment: local or production")
    args = parser.parse_args()

    logger.info(f"Running in {args.environment} environment")

    try:
        # Get game URLs to scrape
        if not (all_game_fanpages := get_all_game_fanpages(args.environment, {
            "page": 1,
            "limit": 300,
            "priority": 2        # 2 is highest priority
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
        # logger.info(f"x_refs_total: {x_refs_total}")

        run_fb_scraper_multiple_fanpages(page_refs_total, args.environment)
        # run_scraper_multiple_groups(group_refs_total, args.environment)
        # run_scraper_multiple_twitter(x_refs_total, args.environment)

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(f"Process failed with error: {str(e)}")
