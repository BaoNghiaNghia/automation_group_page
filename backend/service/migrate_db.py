def insert_paragraph_to_db():
    import os
    import logging
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        # Define the data crawler path
        data_crawler_path = os.path.join(os.getcwd(), "data_crawler")
        
        # Check if the data crawler directory exists
        if not os.path.exists(data_crawler_path):
            logger.error("Data crawler folder does not exist")
            raise Exception("Data crawler folder does not exist")
        
        # Process each folder in data crawler directory
        all_data = []
        
        for folder in os.listdir(data_crawler_path):
            folder_path = os.path.join(data_crawler_path, folder)
            
            # Skip if not a directory
            if not os.path.isdir(folder_path):
                continue
                
            # Parse folder name to get game name and post_id
            try:
                game_name, post_id = folder.split('_', 1)
            except ValueError:
                logger.warning(f"Skipping {folder} - invalid folder name format")
                continue
            
            # Use folder path as image_path instead of specific image file
            image_path = folder_path
                
            txt_files = [f for f in os.listdir(folder_path) if f.endswith('.txt')]
            
            for txt_file in txt_files:
                file_path = os.path.join(folder_path, txt_file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content:
                            file_name = os.path.splitext(txt_file)[0]
                            all_data.append({
                                'game_name': game_name,
                                'post_id': post_id,
                                'file_name': file_name,
                                'content': content,
                                'image_path': image_path
                            })

                except Exception as e:
                    logger.error(f"Error reading {file_path}: {str(e)}")
        
        logger.info(f"Processed {len(all_data)} text files from {data_crawler_path}")
        
        import json
        output_file = 'response.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=4)
        
        logger.info(f"Data saved to {output_file}")
        return all_data

    except Exception as e:
        logger.error(f"Error in insert_paragraph_to_db: {str(e)}")
        return []
