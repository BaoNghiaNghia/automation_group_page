import random
from time import sleep
from fblogin import main  # Import your main function from the script

# Import the Celery app instance from celery_config
from celery_config import app

# Define the Celery task that will invoke the main function
@app.task
def run_main_task(game_name):
    main(game_name)
