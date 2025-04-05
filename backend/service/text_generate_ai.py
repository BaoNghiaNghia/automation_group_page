import os
from google import genai
from backend.constants import GEMINI_API_KEY, FOLDER_PATH_DATA_CRAWLER

# Initialize the Gemini client
client = genai.Client(api_key=GEMINI_API_KEY)

def rewrite_paragraph(paragraph):
    try:
        # Check if data crawler folder exists
        data_crawler_path = os.path.join(os.getcwd(), FOLDER_PATH_DATA_CRAWLER.strip("/\\"))
        print(f"Data crawler path: {data_crawler_path}")
        if not os.path.exists(data_crawler_path):
            raise Exception("Data crawler folder does not exist")

        # Send the prompt to the Gemini API for text generation
        response = client.models.generate_content(
            model="gemini-2.0-flash",  # The Gemini 2.0 model used for text generation
            contents=f"Viết lại đoạn văn sau thành 10 đoạn theo cách khác. Đoạn văn gốc: \n{paragraph}"
        )

        # Return the rewritten text from the response
        rewritten_paragraph = response.text.strip()
        return rewritten_paragraph
        
    except Exception as e:
        print(f"Error in rewrite_paragraph: {str(e)}")
        return None
