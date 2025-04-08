import os
import re
import random
from time import sleep
import logging
from openai import OpenAI
from backend.constants import DEEPSEEK_API_KEY, FOLDER_PATH_DATA_CRAWLER, DEEPSEEK_MODEL
from backend.utils.index import get_all_game_fanpages

# Initialize the DeepSeek client
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

NUMBER_OF_CLONE_PARAGRAPH = 10

def rewrite_paragraph_deepseek():
    try:
        game_fanpages = get_all_game_fanpages()
        if not game_fanpages:
            logger.error("No game URLs found from get_game_fanpages")
            raise Exception("No game URLs found from get_game_fanpages")
        
        hashtag_by_game = {item['fanpage'].split('/')[-1]: item['hashtag'] for item in game_fanpages}
        
        # Check if data crawler folder exists
        data_crawler_path = os.path.join(os.getcwd(), FOLDER_PATH_DATA_CRAWLER.strip("/\\"))
        if not os.path.exists(data_crawler_path):
            logger.error("Data crawler folder does not exist")
            raise Exception("Data crawler folder does not exist")
        
        # Process each folder in data crawler directory
        total_folders = len([f for f in os.listdir(data_crawler_path) if os.path.isdir(os.path.join(data_crawler_path, f))])

        for idx, folder in enumerate(os.listdir(data_crawler_path), 1):
            folder_path = os.path.join(data_crawler_path, folder)
            content_file = os.path.join(folder_path, "content.txt")
            
            # Skip if not a directory or content.txt doesn't exist
            if not os.path.isdir(folder_path) or not os.path.exists(content_file):
                logger.warning(f"Skipping {folder} - not a valid directory or content.txt does not exist")
                continue

            clone_files = [f for f in os.listdir(folder_path) if f.startswith('clone_') and f.endswith('.txt')]
            if len(clone_files) >= NUMBER_OF_CLONE_PARAGRAPH:
                logger.info(f"Skipping {folder} - already has {NUMBER_OF_CLONE_PARAGRAPH} clone files")
                continue

            # Read original content
            with open(content_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    logger.warning(f"Warning: {content_file} is empty.")
                    continue

            # Generate rewritten paragraphs using DeepSeek API
            prompt = f"""Viết lại nội dung sau thành {NUMBER_OF_CLONE_PARAGRAPH} phiên bản Tiếng Việt theo nhiều cách khác nhau, giới hạn lại 10 dòng. Hãy đánh số từ 1-{NUMBER_OF_CLONE_PARAGRAPH} trước mỗi phiên bản. Ví dụ:
                1. [phiên bản 1]
                ...
                {NUMBER_OF_CLONE_PARAGRAPH}. [phiên bản {NUMBER_OF_CLONE_PARAGRAPH}]

                Đoạn văn gốc:
                ```
                {content}
                ```
            """

            # Generate content using DeepSeek
            response = client.chat.completions.create(
                model=DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": prompt}
                ]
            )
            textResponse = response.choices[0].message.content.strip()
            
            # Regular expression to match the text between the numbers and remove the numbers
            pattern = r'(\d+\..*?)(?=\n\d+\.|\Z)'

            # Find all matches and remove the number at the start of each match
            matches = re.findall(pattern, textResponse, re.DOTALL)

            # Output the groups
            for clone_idx, match in enumerate(matches, 1):
                cleaned_text = re.sub(r'^\d+\.\s*', '', match.strip())
                game_name = folder.split('_')[0]  # Extract game name from folder
                hashtag = hashtag_by_game.get(game_name, "")  # Get hashtag by game name
                if hashtag:
                    cleaned_text += f"\n{hashtag}"
                clone_file = os.path.join(folder_path, f'clone_{clone_idx}.txt')
                with open(clone_file, 'w', encoding='utf-8') as f:
                    f.write(cleaned_text)

            # Show progress
            progress = (idx / total_folders) * 100
            logger.info(f"AI content: {folder} ({progress:.1f}%)")

            sleep(random.randint(8, 15))

    except Exception as e:
        logger.error(f"Error in rewrite_paragraph_deepseek: {str(e)}")
        return False