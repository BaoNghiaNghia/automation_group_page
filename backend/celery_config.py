from celery import Celery
from celery.schedules import crontab

# Import the task module to register tasks with Celery
import tasks  # This ensures that Celery registers the tasks defined in task.py

# Create the Celery app instance and configure it to use Redis as the broker
celery_app = Celery(
    'backend', 
    broker='redis://redis:6379/0',
    backend='redis://redis:6379/0'
)  # Include tasks module explicitly

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"], 
    result_serializer="json",
    timezone="Asia/Ho_Chi_Minh",  # Set timezone to Vietnam
    enable_utc=False,  # Disable UTC to use the local timezone
)

# Celery Beat schedule to run the task every minute
celery_app.conf.beat_schedule = {
    'ru-_main-task-minutes': {
        'task': 'tasks.run_main_task_minutes',  # Use the full path to the task function
        'schedule': crontab(minute="*/3"),  # Run every minute
    },
}

celery_app.autodiscover_tasks(["backend"])
