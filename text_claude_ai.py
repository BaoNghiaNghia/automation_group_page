from google import genai
from backend.constants import GEMINI_API_KEY

# Initialize the Gemini client
client = genai.Client(api_key=GEMINI_API_KEY)

def rewrite_paragraph(paragraph):
    # Send the prompt to the Gemini API for text generation
    response = client.models.generate_content(
        model="gemini-2.0-flash",  # The Gemini 2.0 model used for text generation
        contents=f"Viết lại đoạn văn sau theo cách khác: \n{paragraph}"
    )

    # Return the rewritten text from the response
    rewritten_paragraph = response.text.strip()
    return rewritten_paragraph

# Example usage
original_paragraph = "Công nghệ AI đã có sự phát triển vượt bậc trong những năm gần đây. Nó đang được áp dụng trong nhiều lĩnh vực như chăm sóc sức khỏe, tài chính và giáo dục."

rewritten_paragraph = rewrite_paragraph(original_paragraph)
print("Đoạn văn gốc: \n", original_paragraph)
print("\nĐoạn văn đã viết lại: \n", rewritten_paragraph)
