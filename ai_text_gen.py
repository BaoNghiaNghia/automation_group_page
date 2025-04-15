from backend.service.text_generate_gemini import rewrite_paragraph_gemini
from backend.service.text_generate_deepseek import rewrite_paragraph_deepseek
from backend.service.migrate_db import insert_paragraph_to_db
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    try:
        insert_paragraph_to_db()
        
        # # Step 1: Rewrite paragraph with DeepSeek
        # logger.info("Starting Step 1: Rewriting paragraphs with DeepSeek")
        # result = rewrite_paragraph_deepseek()
        # # Add a delay between Step 1 and Step 2
        # import time
        # logger.info("Adding a 4-second delay between steps...")
        # time.sleep(4)
        # # Wait for step 1 to complete before proceeding
        # if result:
        #     logger.info("Step 1 completed successfully.")
            
        #     try:
        #         # Step 2: Insert paragraph to database
        #         logger.info("Starting Step 2: Inserting paragraphs to database")
        #         insert_paragraph_to_db()
        #         logger.info("Step 2 completed: Paragraphs inserted to database.")
        #     except Exception as e:
        #         logger.error(f"Error in Step 2: {str(e)}")
        #         print(f"Step 2 failed: {str(e)}")
        # else:
        #     print("Step 1 failed. Cannot proceed to step 2.")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(f"Process failed with error: {str(e)}")
