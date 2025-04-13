from backend.service.text_generate_gemini import rewrite_paragraph_gemini
from backend.service.text_generate_deepseek import rewrite_paragraph_deepseek
from backend.service.migrate_db import insert_paragraph_to_db

if __name__ == "__main__":
    # rewrite_paragraph_gemini()
    # result = rewrite_paragraph_deepseek()
    # if result is not False:
    insert_paragraph_to_db()
