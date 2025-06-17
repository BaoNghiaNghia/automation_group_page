import os
import random
from google import genai
from time import sleep
from backend.constants import GEMINI_API_KEY, FOLDER_PATH_DATA_CRAWLER, GEMINI_MODEL

# Initialize the Gemini client
client = genai.Client(api_key=GEMINI_API_KEY)

NUMBER_OF_CLONE_PARAGRAPH = 10

def rewrite_paragraph_gemini():
    try:
        # Check if data crawler folder exists
        data_crawler_path = os.path.join(os.getcwd(), FOLDER_PATH_DATA_CRAWLER.strip("/\\"))
        print(f"Data crawler path: {data_crawler_path}")
        if not os.path.exists(data_crawler_path):
            raise Exception("Data crawler folder does not exist")
        
        # Process each folder in data crawler directory
        total_folders = len([f for f in os.listdir(data_crawler_path) if os.path.isdir(os.path.join(data_crawler_path, f))])
        for idx, folder in enumerate(os.listdir(data_crawler_path), 1):
            folder_path = os.path.join(data_crawler_path, folder)
            content_file = os.path.join(folder_path, "content.txt")
            
            # Skip if not a directory or content.txt doesn't exist
            if not os.path.isdir(folder_path) or not os.path.exists(content_file):
                continue

            clone_files = [f for f in os.listdir(folder_path) if f.startswith('clone_') and f.endswith('.txt')]
            if len(clone_files) >= NUMBER_OF_CLONE_PARAGRAPH:
                print(f"Skipping {folder} - already has {NUMBER_OF_CLONE_PARAGRAPH} clone files")
                continue

            # Read original content``
            with open(content_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()

            # Generate rewritten paragraphs using Gemini API
            prompt = f"""Viết lại đoạn văn sau thành {NUMBER_OF_CLONE_PARAGRAPH} đoạn theo nhiều cách khác nhau, vẫn giữ nguyên nội dung chủ đề và không chia nhỏ. Hãy đánh số từ 1-{NUMBER_OF_CLONE_PARAGRAPH} cho mỗi đoạn. Ví dụ:
                1. [đoạn văn 1]
                2. [đoạn văn 2]
                3. [đoạn văn 3]
                ...
                {NUMBER_OF_CLONE_PARAGRAPH}. [đoạn văn {NUMBER_OF_CLONE_PARAGRAPH}]

                Đoạn văn gốc:
                {content}
                """

            paragraphs = []
            while len(paragraphs) < NUMBER_OF_CLONE_PARAGRAPH:
                # Generate content
                response = client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=prompt
                )
                text = response.text.strip()

                # Extract paragraphs
                for line in text.split('\n'):
                    line = line.strip()
                    if line and line[0].isdigit() and '. ' in line:
                        para_text = line[line.find('.')+2:].strip()
                        if para_text and len(paragraphs) < NUMBER_OF_CLONE_PARAGRAPH:
                            paragraphs.append(para_text)

                if len(paragraphs) < NUMBER_OF_CLONE_PARAGRAPH:
                    sleep(1)

            # Save paragraphs
            for i, para in enumerate(paragraphs, 1):
                clone_file = os.path.join(folder_path, f'clone_{i}.txt')
                with open(clone_file, 'w', encoding='utf-8') as f:
                    f.write(para)

            # Show progress
            progress = (idx / total_folders) * 100
            print(f"AI content folder: {folder} ({progress:.1f}% complete)")

            sleep(random.randint(5, 10))

    except Exception as e:
        print(f"Error in rewrite_paragraph_gemini: {str(e)}")
        return False