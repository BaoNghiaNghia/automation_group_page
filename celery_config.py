from celery import Celery
from celery.schedules import crontab

# Create the Celery app instance and configure it to use Redis as the broker
app = Celery('tasks', broker='redis://redis:6379/0')

# Celery Beat schedule to run the task every hour
app.conf.beat_schedule = {
    'run-main-every-hour': {
        'task': 'run_main_task.run_main_task',  # Use the full path to the task function
        'schedule': crontab(minute=0, hour='*'),  # Run every hour
    },
}

# Optional: You can add more configurations like timezone if necessary
app.conf.timezone = 'UTC'
