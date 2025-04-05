import os
from google import genai
from time import sleep
from backend.constants import GEMINI_API_KEY, FOLDER_PATH_DATA_CRAWLER

# Initialize the Gemini client
client = genai.Client(api_key=GEMINI_API_KEY)

def rewrite_paragraph():
    try:
        # Check if data crawler folder exists
        data_crawler_path = os.path.join(os.getcwd(), FOLDER_PATH_DATA_CRAWLER.strip("/\\"))
        print(f"Data crawler path: {data_crawler_path}")
        if not os.path.exists(data_crawler_path):
            raise Exception("Data crawler folder does not exist")
        
        # Process each folder in data crawler directory
        for folder in os.listdir(data_crawler_path):
            folder_path = os.path.join(data_crawler_path, folder)
            content_file = os.path.join(folder_path, "content.txt")
            
            # Skip if not a directory or content.txt doesn't exist
            if not os.path.isdir(folder_path) or not os.path.exists(content_file):
                continue

            # Read original content
            with open(content_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Generate rewritten paragraphs using Gemini API
            prompt = f"""Viết lại đoạn văn sau thành 10 đoạn theo nhiều cách khác nhau, vẫn giữ nguyên nội dung chủ đề và không chia nhỏ. Hãy đánh số từ 1-10 cho mỗi đoạn. Ví dụ:
                1. [đoạn văn 1]
                2. [đoạn văn 2]
                3. [đoạn văn 3]
                ...
                10. [đoạn văn 10]

                Đoạn văn gốc:
                {content}
                """
            
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            rewritten_text = response.text.strip()

            # Process and save rewritten paragraphs
            current_content = []
            current_number = None

            for line in rewritten_text.split('\n'):
                line = line.strip()
                if not line:
                    continue
                    
                # Check for new numbered paragraph
                if line[0].isdigit() and '. ' in line:
                    # Save previous paragraph if exists
                    if current_number and current_content:
                        clone_file = os.path.join(folder_path, f'clone_{current_number}.txt')
                        with open(clone_file, 'w', encoding='utf-8') as f:
                            f.write('\n'.join(current_content).strip())
                    
                    # Start new paragraph
                    current_number = line[0]
                    current_content = [line[line.find('.')+1:].strip()]
                else:
                    current_content.append(line)

            # Save final paragraph
            if current_number and current_content:
                clone_file = os.path.join(folder_path, f'clone_{current_number}.txt')
                with open(clone_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(current_content).strip())

            sleep(3)
            
        return rewritten_text
        
    except Exception as e:
        print(f"Error in rewrite_paragraph: {str(e)}")
        return None