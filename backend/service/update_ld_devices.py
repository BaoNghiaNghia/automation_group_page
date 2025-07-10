import os
import json
import time
import requests
import datetime
from backend.constants import ENV_CONFIG, logger

def update_ld_devices(config_folder, environment, pcrunner):
    """
    Main function to synchronize LDPlayer devices between local config files and database.
    
    Args:
        config_folder (str): Path to the folder containing LDPlayer config files
        environment (str): Environment to use (local or production)
        pcrunner (str): Name of the computer running the sync
    """
    service_url = ENV_CONFIG[environment]['SERVICE_URL']
    
    def fetch_device_names_from_api():
        """Fetch device names from the API and return as a list"""
        try:
            # Construct the API URL
            api_url = f"{service_url}/ldplayer_devices/all"

            # Make the API request
            response = requests.get(api_url, timeout=30)
            if response.status_code in [200, 201]:
                data = response.json()
                
                if 'devices' in data and 'items' in data['devices']:
                    return [item['device_name'] for item in data['devices']['items']]
                else:
                    logger.error("Unexpected response format from API")
                    return []
            else:
                logger.error(f"API request failed with status code {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error fetching device names from API: {str(e)}")
            return []

    def extract_player_names(config_folder, key):
        """Extract player names from LDPlayer config files"""
        player_names = []
        
        try:
            # Loop through all files in the directory
            for filename in os.listdir(config_folder):
                if not filename.endswith(".config"):
                    continue
                    
                file_path = os.path.join(config_folder, filename)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        data = json.load(file)
                        
                        if key in data:
                            device_name = data[key].strip()
                            # Only add non-empty device names and ignore those with "(banned)"
                            if device_name and "(banned)" not in device_name:
                                player_names.append(device_name)
                except (json.JSONDecodeError, FileNotFoundError, UnicodeDecodeError) as e:
                    # Skip problematic files
                    logger.debug(f"Skipping file {filename}: {str(e)}")
                    continue
        except Exception as e:
            logger.error(f"Error reading config directory: {str(e)}")
            
        return player_names
        
    def update_config_file(config_folder):
        """
        Update a specific key in a device's .config file
        
        Args:
            config_folder (str): Path to the folder containing LDPlayer config files
        
        Returns:
            bool: True if update was successful, False otherwise
        """
        updated_count = 0
        try:
            # Loop through all files in the directory with .config extension
            for filename in os.listdir(config_folder):
                if not filename.endswith(".config"):
                    continue

                file_path = os.path.join(config_folder, filename)

                try:
                    # Read the current config
                    with open(file_path, 'r', encoding='utf-8') as file:
                        data = json.load(file)

                    # Update essential settings for automation
                    # Convert from default values to automation-ready values
                    data["basicSettings.adbDebug"] = 1  # Enable ADB debugging (0 -> 1)
                    data["basicSettings.rootMode"] = True  # Enable root mode (false -> true)
                    data["basicSettings.standaloneSysVmdk"] = False  # Enable standalone system (false -> true)
                    # Update resolution and DPI settings for better automation compatibility
                    data["advancedSettings.resolution"] = {
                        "width": 720,
                        "height": 1280
                    }
                    data["advancedSettings.resolutionDpi"] = 320

                    # Write the updated config back to the file
                    with open(file_path, 'w', encoding='utf-8') as file:
                        json.dump(data, file, indent=2)

                    updated_count += 1
                        
                except (json.JSONDecodeError, FileNotFoundError, UnicodeDecodeError) as e:
                    logger.debug(f"Skipping file {filename} during update: {str(e)}")
                    continue
                
            # Check if Shared_images_ldplayer folder exists in parent directory, if not create it
            parent_dir = os.path.join(os.path.dirname(os.getcwd()), "adb_fb_post", "ADB", "bin", "Debug")
            shared_images_folder = os.path.join(parent_dir, "Shared_images_ldplayer")
            if not os.path.exists(shared_images_folder):
                try:
                    os.makedirs(shared_images_folder)
                    logger.info(f"Created Shared_images_ldplayer folder at {shared_images_folder}")
                except Exception as e:
                    logger.error(f"Failed to create Shared_images_ldplayer folder: {str(e)}")
            
            # For each config file, create a player-specific folder and update the config
            for filename in os.listdir(config_folder):
                if not filename.endswith(".config"):
                    continue

                file_path = os.path.join(config_folder, filename)
                
                try:
                    # Read the config to get the player name
                    with open(file_path, 'r', encoding='utf-8') as file:
                        data = json.load(file)
                    
                    # Get player name from config
                    if "statusSettings.playerName" in data:
                        player_name = data["statusSettings.playerName"].strip()
                        if player_name and "(banned)" not in player_name:
                            # Create player-specific folder inside Shared_images_ldplayer
                            player_folder = os.path.join(shared_images_folder, player_name)
                            if not os.path.exists(player_folder):
                                try:
                                    os.makedirs(player_folder)
                                    logger.debug(f"Created folder for player {player_name}")
                                except Exception as e:
                                    logger.error(f"Failed to create folder for player {player_name}: {str(e)}")
                                    continue
                            
                            # Update the sharedPictures setting in the config using forward slashes
                            player_folder_formatted = player_folder.replace("\\", "/")
                            data["statusSettings.sharedPictures"] = player_folder_formatted
                            
                            # Write the updated config back to the file
                            with open(file_path, 'w', encoding='utf-8') as file:
                                json.dump(data, file, indent=2)
                            
                            logger.debug(f"Updated sharedPictures path for {player_name}")
                except (json.JSONDecodeError, FileNotFoundError, UnicodeDecodeError) as e:
                    logger.debug(f"Skipping file {filename} during shared pictures update: {str(e)}")
                    continue
            
            logger.info(f"Successfully updated {updated_count} config files")
            return True
        except Exception as e:
            logger.error(f"Error updating config files: {str(e)}")
            return False

    def create_new_device_batch(device_names, batch_size=10):
        """Create new devices in the database in batches"""
        try:
            url = f"{service_url}/ldplayer_devices/insert-batch"
            headers = {"Content-Type": "application/json"}
            
            # Prepare the payload with default values for each device
            payload = []
            current_time = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            
            for device_name in device_names:
                device_data = {
                    "device_name": device_name,
                    "device_id": f"LD-{device_name}",
                    "device_model": "Samsung Galaxy S10",
                    "android_version": "12",
                    "serial_number": f"SN{device_name}",
                    "udid": f"UD{device_name}",
                    "imei": f"IM{device_name}",
                    "last_run": current_time,
                    "pc_runner": pcrunner,
                    "count_today": 0,
                    "status": "active"
                }
                payload.append(device_data)
            
            # Make the API request
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code in (200, 201):
                logger.info(f"Successfully created {len(device_names)} devices in batch")
                return len(device_names)
            else:
                logger.error(f"Failed to create devices batch. Status code: {response.status_code}")
                return 0
        except Exception as e:
            logger.error(f"Error creating devices batch: {str(e)}")
            return 0

    # Main execution flow
    key_to_search = "statusSettings.playerName"
    
    update_config_file(config_folder)
    

    # Extract player names from all .config files in the specified folder
    local_player_names = extract_player_names(config_folder, key_to_search)
    
    logger.info(f"Found {len(local_player_names)} local devices")

    # Fetch device names from the API
    database_device_names = fetch_device_names_from_api()
    logger.info(f"Found {len(database_device_names)} devices in database")

    # Find devices that are not in the database
    missing_devices = [device for device in local_player_names if device not in database_device_names]
    logger.info(f"Found {len(missing_devices)} devices missing from database")
    
    # Merged print statements
    print(f"Tổng cộng: {len(local_player_names)} thiết bị trên máy {pcrunner}\n"
        f"Tổng cộng: {len(database_device_names)} thiết bị trong Database\n"
        f"Số lượng thiết bị bổ sung: {len(missing_devices)}")

    # Process all missing devices in batches
    if missing_devices:
        print("Tạo thiết bị mới trong Database...")
        success_count = 0
        total_devices = len(missing_devices)
        batch_size = 20
        
        for i in range(0, total_devices, batch_size):
            batch = missing_devices[i:i+batch_size]
            if batch:
                success_count += create_new_device_batch(batch, batch_size)
                
                # Calculate and show progress percentage
                processed = min(i + batch_size, total_devices)
                percentage = (processed / total_devices) * 100
                print(f"Progress: {percentage:.1f}% ({processed}/{total_devices})")
                
                # Add a small delay between batches to avoid overwhelming the API
                time.sleep(1)
        
        logger.info(f"Created {success_count} out of {total_devices} missing devices")
        print(f"Created {success_count} out of {total_devices} missing devices")
    else:
        logger.info("No missing devices to create")
        print("No missing devices to create")
