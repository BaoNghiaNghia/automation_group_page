from backend.service.text_generate_gemini import rewrite_paragraph_gemini
from backend.service.text_generate_deepseek import rewrite_paragraph_deepseek
from backend.service.migrate_db import insert_paragraph_to_db

if __name__ == "__main__":
    # Step 1: Rewrite paragraph with DeepSeek
    # result = rewrite_paragraph_deepseek()

    # Step 2: Insert paragraph to database
    insert_paragraph_to_db()

    # Step 3: Rewrite paragraph with I
