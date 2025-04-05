import os
from google import genai
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
        
        # Get all text from content.txt files in data crawler subfolders
        all_content = []
        for folder in os.listdir(data_crawler_path):
            folder_path = os.path.join(data_crawler_path, folder)
            if os.path.isdir(folder_path):
                content_file = os.path.join(folder_path, "content.txt") 
                if os.path.exists(content_file):
                    with open(content_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        all_content.append(content)
                        
            break
        
        # Combine all content into single paragraph
        if all_content:
            paragraph = " ".join(all_content)
            
        # return paragraph

        # Send the prompt to the Gemini API for text generation
        response = client.models.generate_content(
            model="gemini-2.0-flash",  # The Gemini 2.0 model used for text generation
            contents=f"""Viết lại đoạn văn sau thành 10 đoạn theo nhiều cách khác nhau. Hãy đánh số từ 1-10 cho mỗi đoạn. Ví dụ:
                1. [đoạn văn 1]
                2. [đoạn văn 2]
                3. [đoạn văn 3]
                ...
                10. [đoạn văn 10]

                Đoạn văn gốc:
                {paragraph}
                """
        )

        # Return the rewritten text from the response
        rewritten_paragraph = response.text.strip()
        
        # Split the response into paragraphs
        paragraphs = rewritten_paragraph.split('\n')
        
        # Extract and save each numbered paragraph
        current_content = ""
        current_number = None
        
        # Get the folder path of content.txt
        folder_path = os.path.join(data_crawler_path, folder)
        
        for line in paragraphs:
            line = line.strip()
            # Check if line starts with a number
            if line and line[0].isdigit() and '. ' in line:
                # Save previous content if exists
                if current_number is not None and current_content:
                    clone_file = os.path.join(folder_path, f'clone_{current_number}.txt')
                    with open(clone_file, 'w', encoding='utf-8') as f:
                        f.write(current_content.strip())
                
                # Start new content
                current_number = line[0]
                current_content = line[line.find('.')+1:].strip()
            elif line:
                current_content += '\n' + line
        
        # Save the last paragraph
        if current_number is not None and current_content:
            clone_file = os.path.join(folder_path, f'clone_{current_number}.txt')
            with open(clone_file, 'w', encoding='utf-8') as f:
                f.write(current_content.strip())
        return rewritten_paragraph
        
    except Exception as e:
        print(f"Error in rewrite_paragraph: {str(e)}")
        return None
