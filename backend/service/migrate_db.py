import os
import logging
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def insert_paragraph_to_db():
    
    try:
        # Define the data crawler path
        data_crawler_path = os.path.join(os.getcwd(), "data_crawler")
        
        # Check if the data crawler directory exists
        if not os.path.exists(data_crawler_path):
            logger.error("Data crawler folder does not exist")
            raise Exception("Data crawler folder does not exist")
        
        output_file = 'all_post_today.json'
        
        batch_size = 1000  # Process in batches of 1000 items
        batch_data = []
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('[\n')
            
            first_item = True
            for folder in os.listdir(data_crawler_path):
                folder_path = os.path.join(data_crawler_path, folder)
                
                if not os.path.isdir(folder_path):
                    continue

                try:
                    game_name, post_id = folder.split('_', 1)
                except ValueError:
                    logger.warning(f"Skipping {folder} - invalid folder name format")
                    continue
                
                image_path = folder_path
                txt_files = [f for f in os.listdir(folder_path) if f.endswith('.txt')]
                
                for txt_file in txt_files:
                    file_path = os.path.join(folder_path, txt_file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f_txt:
                            content = f_txt.read().strip()
                            if content:
                                file_name = os.path.splitext(txt_file)[0]
                                batch_data.append({
                                    'game_name': game_name,
                                    'post_id': post_id,
                                    'file_name': file_name,
                                    'content': content,
                                    'image_path': image_path
                                })
                                
                                # When batch is full, write and reset batch
                                if len(batch_data) >= batch_size:
                                    if first_item:
                                        first_item = False
                                    else:
                                        f.write(',\n')
                                    json.dump(batch_data, f, ensure_ascii=False, indent=4)
                                    batch_data.clear()
                    except Exception as e:
                        logger.error(f"Error reading {file_path}: {str(e)}")
            
            # Write any remaining data in the final batch
            if batch_data:
                if first_item:
                    first_item = False
                else:
                    f.write(',\n')
                json.dump(batch_data, f, ensure_ascii=False, indent=4)
                
            f.write('\n]')
        
        logger.info(f"Data saved to {output_file}")
        return "Processing complete"

    except Exception as e:
        logger.error(f"Error in insert_paragraph_to_db: {str(e)}")
        return []
