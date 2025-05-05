import os
import time
import json
import base64
import requests
from backend.utils.index import get_all_game_fanpages
from backend.constants import SERVICE_URL, ENV_CONFIG, logger

def sync_post_into_database(environment):
    
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

            # Create a dictionary mapping game fanpage URLs to their IDs
            # Handle potential duplicates by keeping the last occurrence of each key
            game_fanpages_id = {}
            for item in game_fanpages:
                game_key = item['fanpage'].split('/')[-1]

                if game_key in game_fanpages_id:
                    # If the key already exists, convert to array if it's not already
                    if isinstance(game_fanpages_id[game_key], list):
                        game_fanpages_id[game_key].append(item['id'])
                    else:
                        # Convert single value to array with both values
                        game_fanpages_id[game_key] = [game_fanpages_id[game_key], item['id']]
                else:
                    # First occurrence of this game_key
                    game_fanpages_id[game_key] = item['id']

            logger.info(f"Data saved to {game_fanpages_id}")

            # Skip processing if game_fanpages_id is empty
            if not game_fanpages_id:
                logger.warning("No game_fanpages_id found, skipping folder processing")
                batch_data = []
            else:
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
                    image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                    
                    
                    # Process image files and upload them to the API
                    # Counter to track number of images uploaded
                    image_upload_count = 0
                    
                    for image_file in image_files:
                        try:
                            image_file_path = os.path.join(folder_path, image_file)
                            
                            # Prepare the API endpoint for image upload
                            upload_url = f'{ENV_CONFIG[environment]["SERVICE_URL"]}/daily_posts_content/upload-image'
                            
                            # Open the image file and prepare it for upload
                            with open(image_file_path, 'rb') as img_file:
                                # Create a multipart form with the image file
                                files = {'file': (image_file, img_file, 'multipart/form-data')}
                                
                                # Send the request to upload the image
                                response = requests.post(upload_url, files=files)
                                
                                # Check if the upload was successful
                                if response.status_code == 200:
                                    logger.info(f"Successfully uploaded image: {image_file}")
                                else:
                                    logger.error(f"Failed to upload image {image_file}. Status code: {response.status_code}")
                            
                            # Increment the counter after each upload
                            image_upload_count += 1
                            
                            # Add a delay of 1 second after every 10 image uploads
                            if image_upload_count % 10 == 0:
                                time.sleep(2)

                        except Exception as e:
                            logger.error(f"Error uploading image {image_file}: {str(e)}")
                    
                    # Process text files and create data entries
                    for txt_file in txt_files:
                        file_path = os.path.join(folder_path, txt_file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f_txt:
                                content = f_txt.read().strip()
                                if content:
                                    file_name = os.path.splitext(txt_file)[0]
                                    # Get game_fanpages_id with proper type conversion
                                    game_id = game_fanpages_id.get(game_name)
                                    
                                    # Handle case when game_id is null
                                    if game_id is None:
                                        continue
                                    # Handle case when game_id is an array
                                    elif isinstance(game_id, list):
                                        # Create an entry for each game_id in the array
                                        for single_game_id in game_id:
                                            batch_data.append({
                                                'fanpage': game_name,
                                                'game_fanpages_id': single_game_id,
                                                'post_id': post_id,
                                                'clone_version': file_name,
                                                'content': content,
                                                'img_path': image_path,
                                                'image_blob': None
                                            })
                                    else:
                                        # Handle single game_id as before
                                        batch_data.append({
                                            'fanpage': game_name,
                                            'game_fanpages_id': game_id,
                                            'post_id': post_id,
                                            'clone_version': file_name,
                                            'content': content,
                                            'img_path': image_path,
                                            'image_blob': None
                                        })

                        except Exception as e:
                            logger.error(f"Error reading {file_path}: {str(e)}")

            # Write any remaining data in the final batch
            if batch_data:
                json.dump(batch_data, f, ensure_ascii=False, indent=4)

        time.sleep(5)
        
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
        logger.error(f"Error in sync_post_into_database: {str(e)}")
        return []
