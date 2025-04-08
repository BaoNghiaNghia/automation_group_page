import os
import random
from time import sleep
from openai import OpenAI
from backend.constants import DEEPSEEK_API_KEY, FOLDER_PATH_DATA_CRAWLER, DEEPSEEK_MODEL

# Initialize the DeepSeek client
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

NUMBER_OF_CLONE_PARAGRAPH = 10

def rewrite_paragraph_deepseek():
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

            # Read original content
            with open(content_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()

            # Generate rewritten paragraphs using DeepSeek API
            paragraphs_count = 0
            while paragraphs_count < NUMBER_OF_CLONE_PARAGRAPH:
                # Generate prompt for 2 versions at a time
                current_start = paragraphs_count + 1
                current_end = min(current_start + 1, NUMBER_OF_CLONE_PARAGRAPH)
                
                prompt = f"""Viết lại nội dung sau thành {current_end - current_start + 1} phiên bản theo nhiều cách khác nhau, vẫn giữ nguyên nội dung chủ đề. Hãy đánh số từ {current_start}-{current_end} trước mỗi phiên bản. Ví dụ:
                    {current_start}. [phiên bản {current_start}]
                    {current_end}. [phiên bản {current_end}]

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
                text = response.choices[0].message.content.strip()
                
                print(text)

                # Extract and save paragraphs
                for line in text.split('\n'):
                    line = line.strip()
                    if line and line[0].isdigit() and '. ' in line:
                        para_text = line[line.find('.')+2:].strip()
                        if para_text and paragraphs_count < NUMBER_OF_CLONE_PARAGRAPH:
                            paragraphs_count += 1
                            # Save paragraph immediately
                            clone_file = os.path.join(folder_path, f'clone_{paragraphs_count}.txt')
                            with open(clone_file, 'w', encoding='utf-8') as f:
                                f.write(para_text)

                if paragraphs_count < NUMBER_OF_CLONE_PARAGRAPH:
                    sleep(1)

            # Show progress
            progress = (idx / total_folders) * 100
            print(f"AI content folder: {folder} ({progress:.1f}% complete)")

            sleep(random.randint(5, 10))

    except Exception as e:
        print(f"Error in rewrite_paragraph_deepseek: {str(e)}")
        return False