import os
import time
import json
import logging
import requests
from backend.utils.index import get_all_game_fanpages
from backend.constants import SERVICE_URL, ENV_CONFIG

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



def sync_post_into_databse(environment):
    
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
            game_fanpages = get_all_game_fanpages(environment)
            if not game_fanpages:
                logger.error("No game URLs found from get_game_fanpages")
                raise Exception("No game URLs found from get_game_fanpages")

            game_fanpages_id = {item['fanpage'].split('/')[-1]: item['id'] for item in game_fanpages}

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
                                    'fanpage': game_name,
                                    'game_fanpages_id': game_fanpages_id.get(game_name, None),
                                    'post_id': post_id,
                                    'clone_version': file_name,
                                    'content': content,
                                    'img_path': image_path
                                })

                    except Exception as e:
                        logger.error(f"Error reading {file_path}: {str(e)}")

            # Write any remaining data in the final batch
            if batch_data:
                json.dump(batch_data, f, ensure_ascii=False, indent=4)

        logger.info(f"Data saved to {output_file}")

        # Add a 5-second delay to prevent overwhelming the system
        time.sleep(5)
        logger.info("Added 5-second delay before completing the process")

        # Now read the output file and send data in batches to the API
        logger.info("Starting to send data to API in batches")
        
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Process data in batches of 10
            batch_size = 10
            total_records = len(data)
            total_batches = (total_records + batch_size - 1) // batch_size  # Ceiling division
            
            api_url = f'{ENV_CONFIG[environment]["SERVICE_URL"]}/daily_posts_content/insert-batch'
            headers = {'Content-Type': 'application/json'}
            
            for i in range(0, total_records, batch_size):
                batch = data[i:i+batch_size]
                batch_num = i // batch_size + 1

                logger.info(f"Sending batch {batch_num}/{total_batches} ({len(batch)} records)")
                
                try:
                    response = requests.post(api_url, headers=headers, data=json.dumps(batch))
                    
                    if response.status_code in [200, 201]:
                        logger.info(f"Batch {batch_num} successfully sent. Response: {response.text}")
                    else:
                        logger.error(f"Failed to send batch {batch_num}. Status code: {response.status_code}, Response: {response.text}")
                
                except Exception as e:
                    logger.error(f"Error sending batch {batch_num}: {str(e)}")
                
                # Add a small delay between batches to prevent overwhelming the API
                logger.info(f"Adding 5 second delay between batches")
                time.sleep(5)
            
            logger.info(f"Completed sending all {total_batches} batches to API")
        
        except Exception as e:
            logger.error(f"Error processing output file for API: {str(e)}")
        return "Processing complete"

    except Exception as e:
        logger.error(f"Error in sync_post_into_databse: {str(e)}")
        return []
