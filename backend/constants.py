import os
import logging
from dotenv import load_dotenv
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file in the main route folder
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

API_KEY_CAPTCHA = 'point_3d0bd505d511c336b6279f4815057b9a'
FB_DEFAULT_URL = "https://www.facebook.com"
FB_ACCOUNT_LIST = [
    ("0399988593", "p6+p7N&r%M$#B5b"),
    # ("Cdy006947@gmail.com", "Haha123@"),
    
    # ("0928649691", "vutuan1985@"),
    # ("0921747844", "vutuan1985@"),
    # ("0928618253", "vutuan1985@"),
]
# Environment-specific configurations
ENV_CONFIG = {
    "local": {
        "SERVICE_URL": "http://127.0.0.1:8080/service",
        "CONFIG_LDPLAYER_FOLDER": r"C:\LDPlayer\LDPlayer9\vms\config"
    },
    "production": {
        "SERVICE_URL": "https://boostgamemobile.com/service",
        "CONFIG_LDPLAYER_FOLDER": r"D:\LDPlayer\LDPlayer9\vms\config"
    }
}

# Get environment from env var or default to local
ENVIRONMENT = os.getenv("ENVIRONMENT", "local")

# Set the appropriate configuration based on environment
SERVICE_URL = os.getenv("SERVICE_URL", ENV_CONFIG[ENVIRONMENT]["SERVICE_URL"])
CONFIG_LDPLAYER_FOLDER = ENV_CONFIG[ENVIRONMENT]["CONFIG_LDPLAYER_FOLDER"]

DOMAIN_CAPTCHA = "https://captcha69.com"
FOLDER_PATH_DATA_CRAWLER = "/data_crawler/"
FOLDER_PATH_POST_ID_CRAWLER = "/data_posts_id/"
LIMIT_POST_PER_DAY = 20




GEMINI_API_KEY = "AIzaSyCZCzQFbJIoKf4TPaazA7VvmlfiLuQvhSM"
GEMINI_MODEL = "gemini-2.0-flash"

DEEPSEEK_API_KEY = "sk-e71d03c8c9a44344b3c39ef6db11526c"
DEEPSEEK_MODEL = "deepseek-chat"

# Generate a random human-like comment
SHARE_COMMENT_IN_POST = [
    # English comments
    "Interesting!",
    "Check this out!",
    "Thought you might like this",
    "Worth sharing",
    "What do you think about this?",
    "This is cool",
    "Saw this and thought of you",
    "Hmm, interesting perspective",
    "Have you seen this?",
    "This caught my attention",
    # Vietnamese comments
    "Thú vị quá!",
    "Xem cái này đi!",
    "Nghĩ bạn sẽ thích cái này",
    "Đáng để chia sẻ",
    "Bạn nghĩ gì về cái này?",
    "Cái này hay nè",
    "Thấy cái này và nghĩ đến bạn",
    "Hmm, góc nhìn thú vị",
    "Bạn đã xem cái này chưa?",
    "Cái này thu hút sự chú ý của mình",
    "Đáng xem đấy!",
    "Chia sẻ với mọi người",
    "Hay quá, không thể bỏ qua",
    "Cùng xem nhé!",
    "Bài viết hay, chia sẻ lại",
    "Rất đáng để suy ngẫm",
    "Cảm thấy thú vị về điều này",
    "Mọi người nghĩ sao?",
    "Đọc xong thấy hay nên share",
    "Chia sẻ cho ai cần"
]

LIST_COMPETIOR_GROUP_LINK = [
    "https://www.facebook.com/groups/lastwarsurvivalvn/members",
    "https://www.facebook.com/groups/370081218909245/members",
    "https://www.facebook.com/groups/lucdiathanhoa/members",
    "https://www.facebook.com/groups/vikingrisevietnam/members"
]