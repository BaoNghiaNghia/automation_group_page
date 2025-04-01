from fblogin import run_fb_scraper_posts  # Import your main function from the script
from constants import GAME_NAME_URL
from celery import shared_task


@shared_task(name="tasks.run_main_task_minutes")  # Match the name in celery_config.py
def run_main_task_minutes():
    # Uncomment to call the actual function
    run_fb_scraper_posts(GAME_NAME_URL)
    # print(f"----- run_main_task {game_name}")
