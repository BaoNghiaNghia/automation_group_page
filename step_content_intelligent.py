import argparse
from backend.constants import ENV_CONFIG, logger
from backend.service.scraper.scraper_post_fanpage import run_fb_scraper_multiple_fanpages
from backend.service.scraper.scraper_post_group import run_scraper_multiple_groups
from backend.service.scraper.scraper_post_twitter import run_scraper_multiple_twitter
from backend.utils.index import get_all_game_fanpages


if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Run the text generation process")
    parser.add_argument("--environment", "-e", choices=["local", "production"], default="production",
                        help="Specify the environment: local or production")
    args = parser.parse_args()
    
    logger.info(f"Running in {args.environment} environment")
    
    try:
        # Get game URLs to scrape
        if not (all_game_fanpages := get_all_game_fanpages(args.environment, {
            "page": 1,
            "limit": 300,
            "priority": 1        # 0 (normal) and 1 (priority)
        })):
            logger.error("No game URLs found")
            exit(1)
        logger.info(f"Found {len(all_game_fanpages)} game fanpages to scrape")
        
        group_refs_total, page_refs_total, x_refs_total = [], [], []
        for idx, game in enumerate(all_game_fanpages, 1):
            logger.info(f"  ID: {game.get('name_of_game', 'N/A')}")
            note = game.get('note')
            if note is None:
                logger.warning(f"  Note is None for game: {game.get('name_of_game', 'N/A')}")
                note = ''
            logger.info(f"  Note: {note}")

            for line in note.split('\n'):
                if line.startswith("Group_Ref_"):
                    group_refs_total.append(line[len("Group_Ref_"):])
                elif line.startswith("Page_Ref_"):
                    page_refs_total.append(line[len("Page_Ref_"):])
                elif line.startswith("X_Ref_"):
                    x_refs_total.append(line[len("X_Ref_"):])

        logger.info(f"group_refs_total: {group_refs_total}")
        logger.info(f"page_refs_total: {page_refs_total}")
        logger.info(f"x_refs_total: {x_refs_total}")

        run_fb_scraper_multiple_fanpages(all_game_fanpages, args.environment)
        
        run_scraper_multiple_groups(all_game_fanpages, args.environment)
        
        run_scraper_multiple_twitter(all_game_fanpages, args.environment)

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(f"Process failed with error: {str(e)}")
