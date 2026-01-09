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

LIMIT_SCROLL_FRIEND_REACTION_POST = 5

API_KEY_CAPTCHA = 'point_3d0bd505d511c336b6279f4815057b9a'
FB_DEFAULT_URL = "https://www.facebook.com"
TWITTER_DEFAULT_URL = "https://x.com"


BASE_PROFILE_DIR = os.path.join(os.getcwd(), "Profile_Google")

GMAIL_TWITTER = [
    { 
        "username":"baonghia.ios@gmail.com",
        "password": "BaoNghia123@@"
    }
]

SCRAPER_FB_ACCOUNT_LIST = [
    ("0399988593", "p6+p7N&r%M$#B5b"),
]

SCRAPER_TWITTER_ACCOUNT_LIST = [
    ("baonghia.ios@gmail.com", "BaoNghia123@@"),
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
CONFIG_LDPLAYER_FOLDER = ENV_CONFIG[ENVIRONMENT]["CONFIG_LDPLAYER_FOLDER"]

DOMAIN_CAPTCHA = "https://captcha69.com"
FOLDER_PATH_DATA_CRAWLER = "/data_crawler/"
FOLDER_PATH_POST_ID_CRAWLER = "/data_posts_id/"
LIMIT_POST_PER_DAY = 50

# SHA1
EDITOR_ACCOUNT_FACEBOOK = [
    ("86ec2edd1535f3a1ccf3f745faba54ee95e6588a", "bb0f68fff346acf117208efbbac2f8c9c4d65baa")
]


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

SPAM_KEYWORDS_IN_POST = [
    "Ngân Hàng",
    "NHUỘM",
    "Mẫu Cắt Tạo Kiểu",
    "kiểu tóc",
    "DÁNG UỐN SÓNG LƯỜI",
    "tóc",
    "Hoàn cảnh",
    "tội quá",
    "Xin hãy giúp đỡ",
    "A DI ĐÀ PHẬT",
    "hạng ráng",
    "Số Tài Khoản",
    "CTK",
    "Nội dung",
    "giúp đỡ em",
    "Chủ tk",
    "ngân hàng",
    "giết",
    "đánh",
    "súng",
    "dao",
    "tấn công",
    "bạo loạn",
    "bom",
    "chém",
    "đâm",
    "nổ súng",
    "tội phạm",
    "bắt cóc",
    "chiến tranh",
    "bạo hành",
    "đánh bom",
    "tra tấn",
    "súng trường",
    "sát hại",
    "khủng bố",
    "hành hung",
    "vũ khí",
    "hủy diệt",
    "đánh lộn",
    "ẩu đả",
    "bầu cử",
    "chế độ",
    "tôn giáo",
    "tà đạo",
    "chính quyền",
    "biểu tình",
    "cách mạng",
    "lật đổ",
    "xung đột",
    "chính trị",
    "bạo động",
    "tư tưởng cực đoan",
    "chính sách",
    "chủ nghĩa",
    "đảng phái",
    "lật đổ chính quyền",
    "phản động",
    "luận điệu xuyên tạc",
    "nội chiến",
    "phe đối lập",
    "lô đề",
    "đánh bài",
    "cá độ",
    "đa cấp",
    "nổ hũ",
    "slot game",
    "tài chính 0 đồng",
    "cam kết lợi nhuận",
    "lừa đảo online",
    "kiếm tiền nhanh",
    "đầu tư siêu lợi nhuận",
    "chứng khoán lừa đảo",
    "tín dụng đen",
    "cho vay nặng lãi",
    "vay tiền nhanh",
    "tín dụng ảo",
    "app vay tiền",
    "cá cược thể thao",
    "sex",
    "làm tình",
    "khiêu dâm",
    "gái gọi",
    "sugar baby",
    "sugar daddy",
    "mại dâm",
    "thủ dâm",
    "xxx",
    "video nóng",
    "phim sex",
    "chat sex",
    "sexting",
    "ảnh nóng",
    "khỏa thân",
    "webcam 18+",
    "nội dung khiêu dâm",
    "quan hệ tình dục",
    "đồ chơi tình dục",
    "massage 18+",
    "phim người lớn",
    "clip nóng",
    "bạo dâm",
    "đồng tính nam nữ 18+",
    "thuốc trị bệnh",
    "giảm cân nhanh",
    "trằng da cấp tốc",
    "phá thai an toàn",
    "đặc trị",
    "thần dược",
    "khỏi 100%",
    "thuốc đông y",
    "tăng cường sinh lý",
    "thuốc cường dương",
    "kích thích tố",
    "giảm cân siêu tốc",
    "thuốc bổ sung nội tiết tố",
    "thuốc làm to vòng 1",
    "thuốc chống ung thư không rõ nguồn gốc",
    "thuốc tăng cân",
    "thuốc mọc tóc",
    "thuốc kích dục",
    "hàng fake",
    "livestream lậu",
    "xem phim miễn phí",
    "phần mềm crack",
    "tải nhạc chùa",
    "vi phạm bản quyền",
    "mod game",
    "tài khoản netflix lậu",
    "share tài khoản spotify",
    "bán acc game lậu",
    "chia sẻ phim không bản quyền",
    "phần mềm bẻ khóa",
    "bán tool hack",
    "bán key lậu",
    "website tải lậu",
    "crack phần mềm",
    "phim lậu",
    "game lậu",
    "tự tử",
    "tự sát",
    "nhảy cầu",
    "nhảy lầu",
    "cắt cổ tay",
    "tự hại",
    "hành vi nguy hiểm",
    "bóp cổ",
    "uống thuốc độc",
    "tìm cách tự tử",
    "đau khổ cùng cực",
    "tuyệt vọng",
    "muốn chết",
    "không muốn sống",
    "chết đi",
    "giải thoát bằng cái chết",
    "phân biệt chủng tộc",
    "kỳ thị",
    "bài xích",
    "ghét bỏ",
    "tẩy chay",
    "xúc phạm",
    "xúc phạm giới tính",
    "phân biệt vùng miền",
    "kỳ thị tôn giáo",
    "nhạo báng",
    "thù địch",
    "ngôn từ kích động",
    "xúc phạm danh dự",
    "nói xấu dân tộc",
    "kỳ thị người khuyết tật",
    "kiếm tiền online",
    "làm giàu nhanh",
    "thu nhập thụ động",
    "làm việc tại nhà",
    "công việc online",
    "affiliate marketing",
    "dropshipping",
    "cam kết lợi nhuận",
    "đầu tư tài chính không rủi ro",
    "công việc lương cao không cần kinh nghiệm",
    "đăng ký miễn phí",
    "nhận ngay tiền thưởng",
    "tài khoản quảng cáo",
    "unlock tài khoản facebook"
]