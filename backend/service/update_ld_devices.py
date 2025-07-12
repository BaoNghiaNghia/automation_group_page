import os
import json
import time
import requests
import datetime
from backend.constants import ENV_CONFIG, logger


def extract_player_names(config_folder):
    """Extract player names from LDPlayer config files"""
    player_names = []
    key_to_search = "statusSettings.playerName"
    
    try:
        # Loop through all files in the directory
        for filename in os.listdir(config_folder):
            if not filename.endswith(".config"):
                continue
                
            file_path = os.path.join(config_folder, filename)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    
                    if key_to_search in data:
                        device_name = data[key_to_search].strip()
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
    
    logger.info(f"Start updated config files ldplayer instance")
    updated_count = 0
    try:
        for filename in os.listdir(config_folder):
            if not filename.endswith(".config"):
                continue

            file_path = os.path.join(config_folder, filename)

            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)

                data["basicSettings.adbDebug"] = 1
                data["basicSettings.rootMode"] = True
                data["basicSettings.standaloneSysVmdk"] = False
                data["advancedSettings.cpuCount"] = 4
                data["advancedSettings.memorySize"] = 4096
                data["advancedSettings.resolution"] = {
                    "width": 720,
                    "height": 1280
                }
                data["advancedSettings.resolutionDpi"] = 240

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


def create_new_device_batch(device_names, batch_size=10, pcrunner="pc_1", environment="production"):
    """Create new devices in the database in batches"""
    try:
        service_url = ENV_CONFIG[environment]['SERVICE_URL']
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
    
    
def fetch_device_names_from_api(environment):
    """Fetch device names from the API and return as a list"""
    try:
        # Construct the API URL
        service_url = ENV_CONFIG[environment]['SERVICE_URL']
        api_url = f"{service_url}/ldplayer_devices/all"

        # Make the API request
        response = requests.get(api_url, timeout=30)
        if response.status_code in [200, 201]:
            data = response.json()
            
            if 'devices' in data and 'items' in data['devices']:
                return data['devices']['items']
            else:
                logger.error("Unexpected response format from API")
                return []
        else:
            logger.error(f"API request failed with status code {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Error fetching device names from API: {str(e)}")
        return []


def mark_missing_devices_as_banned(database_device, local_player_names, environment):
    """
    Với mỗi thiết bị trong database, nếu không có trong danh sách local thì cập nhật status = 'facebook_banned'
    Gửi toàn bộ thông tin thiết bị lên, chỉ thay đổi trường status.
    """
    banned_count = 0
    local_set = set(local_player_names)

    for device in database_device:
        device_name = device.get('device_name')
        if not device_name:
            continue

        # Nếu device không tồn tại trên local -> update status
        if device_name not in local_set:
            try:
                # Chuẩn bị payload cập nhật
                updated_payload = device.copy()
                updated_payload["status"] = "facebook_banned"

                service_url = ENV_CONFIG[environment]['SERVICE_URL']
                url = f"{service_url}/ldplayer_devices/update/{device_name}"
                headers = {"Content-Type": "application/json"}

                response = requests.put(url, headers=headers, json=updated_payload, timeout=10)
                if response.status_code in [200, 201]:
                    logger.info(f"⚠️ Thiết bị '{device_name}' bị đánh dấu là facebook_banned")
                    banned_count += 1
                else:
                    logger.warning(f"❌ Không cập nhật được {device_name}, mã lỗi: {response.status_code}")
            except Exception as e:
                logger.error(f"‼️ Lỗi khi cập nhật thiết bị {device_name}: {str(e)}")

    return banned_count





def update_ld_devices(config_folder, environment, pcrunner):
    """
    Đồng bộ thiết bị LDPlayer giữa local và database:
    - Cập nhật file config
    - Tạo thiết bị mới nếu thiếu trong DB
    - Đánh dấu thiết bị mất trên local là 'facebook_banned'
    """
    logger.info("🔄 Bắt đầu đồng bộ thiết bị LDPlayer...")

    # Bước 1: Cập nhật file cấu hình
    update_config_file(config_folder)

    # Bước 2: Đọc danh sách thiết bị local
    local_player_names = extract_player_names(config_folder)
    logger.info(f"📱 Tìm thấy {len(local_player_names)} thiết bị local")

    # Bước 3: Đọc danh sách thiết bị từ DB
    database_device = fetch_device_names_from_api(environment)
    database_device_names = [item['device_name'] for item in database_device]
    logger.info(f"🗄️  Tìm thấy {len(database_device_names)} thiết bị trong database")

    # Bước 4: Tìm thiết bị cần tạo mới
    missing_devices = list(set(local_player_names) - set(database_device_names))
    logger.info(f"🆕 Có {len(missing_devices)} thiết bị cần thêm vào database")

    print(f"Tổng cộng local: {len(local_player_names)} | DB: {len(database_device_names)} | Thiết bị mới: {len(missing_devices)}")

    if missing_devices:
        print("🚀 Đang thêm thiết bị mới vào database...")
        success_count = 0
        batch_size = 20
        for i in range(0, len(missing_devices), batch_size):
            batch = missing_devices[i:i + batch_size]
            success_count += create_new_device_batch(batch, batch_size, pcrunner, environment)
            progress = min(i + batch_size, len(missing_devices)) / len(missing_devices) * 100
            print(f"Progress: {progress:.1f}% ({i + batch_size}/{len(missing_devices)})")
            time.sleep(1)
        print(f"✅ Đã thêm {success_count}/{len(missing_devices)} thiết bị vào database")
    else:
        print("✅ Không có thiết bị mới cần thêm")

    # Bước 5: Cập nhật trạng thái 'facebook_banned' cho thiết bị không còn trong local
    banned_count = mark_missing_devices_as_banned(database_device, local_player_names, environment)
    print(f"📛 Đã cập nhật {banned_count} thiết bị thành 'facebook_banned' vì không còn xuất hiện trên local")