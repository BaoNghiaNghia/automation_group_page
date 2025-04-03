from constants import GAME_NAME_URL
from celery import shared_task
from fblogin import run_fb_scraper_posts

@shared_task(name="tasks.run_main_task_minutes")  # Match the name in celery_config.py
def run_main_task_minutes():
    try:
        print("----- run_main_task_minutes -----")
        # run_fb_scraper_posts(GAME_NAME_URL)
    except Exception as e:
        print(f"Unexpected error: {e}")
