from constants import GAME_NAME_URL
from celery import shared_task
import subprocess

@shared_task(name="tasks.run_main_task_minutes")  # Match the name in celery_config.py
def run_main_task_minutes():
    try:
        # Run the script using subprocess to mimic `python fblogin.py`
        result = subprocess.run(
            ["python", "main.py"],  # Command to run the script
            check=True,                 # Raise an error if the command fails
            stdout=subprocess.PIPE,    # Capture the standard output
            stderr=subprocess.PIPE     # Capture the standard error
        )
        print(f"Command output: {result.stdout.decode()}")
        print(f"Command error (if any): {result.stderr.decode()}")

    except subprocess.CalledProcessError as e:
        print(f"Error running the Facebook scraper for game {GAME_NAME_URL}: {e}")
        print(f"Output: {e.stdout.decode()}")
        print(f"Error: {e.stderr.decode()}")
    except Exception as e:
        print(f"Unexpected error: {e}")
