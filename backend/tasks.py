import os
import shutil
from celery import shared_task
from backend.fblogin import run_fb_scraper_posts
from backend.constants import FOLDER_PATH_DATA_CRAWLER, FOLDER_PATH_POST_ID_CRAWLER, GAME_NAME_URL

@shared_task(name="backend.tasks.run_main_task_minutes")  # Match the name in celery_config.py
def run_main_task_minutes():
    try:
        print("----- :::: run_main_task_minutes :::: -----")
        run_fb_scraper_posts(GAME_NAME_URL)
    except Exception as e:
        print(f"Unexpected error: {e}")

@shared_task(name="backend.tasks.delete_data_folders")  # Match the name in celery_config.py
def delete_data_folders():
    try:
        print("----- delete_data_folders -----")

        # Delete data_crawler folder if it exists
        data_crawler_path = os.path.join(os.getcwd(), FOLDER_PATH_DATA_CRAWLER.strip('/'))
        if os.path.exists(data_crawler_path):
            shutil.rmtree(data_crawler_path)
            print(f"Deleted folder: {data_crawler_path}")

        # Delete posts_id_crawler folder if it exists  
        posts_id_path = os.path.join(os.getcwd(), FOLDER_PATH_POST_ID_CRAWLER.strip('/'))
        if os.path.exists(posts_id_path):
            shutil.rmtree(posts_id_path)
            print(f"Deleted folder: {posts_id_path}")
    except Exception as e:
        print(f"Error deleting folders: {e}")
