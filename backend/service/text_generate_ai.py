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

            # Check if folder already has 10 clone files
            clone_files = [f for f in os.listdir(folder_path) if f.startswith('clone_') and f.endswith('.txt')]
            if len(clone_files) >= 10:
                print(f"Skipping {folder} - already has 10 clone files")
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
            # Print the rewritten text for debugging
            print("Generated text:")
            print(rewritten_text)
            print("-" * 80)
            # Split text into paragraphs
            paragraphs = []
            current_para = []
            
            for line in rewritten_text.split('\n'):
                line = line.strip()
                if not line:
                    continue
                    
                if line[0].isdigit() and '. ' in line:
                    if current_para:
                        paragraphs.append('\n'.join(current_para))
                    current_para = [line[line.find('.')+2:].strip()]  # Add 2 to skip both dot and space
                else:
                    current_para.append(line)
                    
            if current_para:
                paragraphs.append('\n'.join(current_para))

            # Ensure we have exactly 10 paragraphs
            if len(paragraphs) < 10:
                print(f"Warning: Only generated {len(paragraphs)} paragraphs for {folder}")
                # Generate remaining paragraphs by repeating the prompt
                while len(paragraphs) < 10:
                    response = client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=prompt
                    )
                    new_text = response.text.strip()
                    new_paras = []
                    current_para = []
                    
                    for line in new_text.split('\n'):
                        line = line.strip()
                        if not line:
                            continue
                            
                        if line[0].isdigit() and '. ' in line:
                            if current_para:
                                new_paras.append('\n'.join(current_para))
                            current_para = [line[line.find('.')+2:].strip()]
                        else:
                            current_para.append(line)
                            
                    if current_para:
                        new_paras.append('\n'.join(current_para))
                        
                    paragraphs.extend(new_paras[:10-len(paragraphs)])
                    sleep(2)

            # Save exactly 10 paragraphs
            for i in range(10):
                clone_file = os.path.join(folder_path, f'clone_{i+1}.txt')
                with open(clone_file, 'w', encoding='utf-8') as f:
                    f.write(paragraphs[i].strip())

            sleep(4)
            
        return rewritten_text
        
    except Exception as e:
        print(f"Error in rewrite_paragraph: {str(e)}")
        return None