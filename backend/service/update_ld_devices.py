import os
import json
import time
import requests
import datetime
from backend.constants import ENV_CONFIG

# Main function to execute the process
def update_ld_devices(config_folder, environment):
    # Function to fetch device names from API
    service_url = ENV_CONFIG[environment]['SERVICE_URL']
    def fetch_device_names_from_api():
        try:
            # Construct the API URL
            api_url = f"{service_url}/ldplayer_devices" if service_url.endswith('/service') else f"{service_url}/service/ldplayer_devices"
            
            # Make the API request
            response = requests.get(api_url)
            
            # Check if the request was successful
            if response.status_code == 200:
                data = response.json()
                
                # Extract device names from the response
                if 'devices' in data and 'items' in data['devices']:
                    device_names = [item['device_name'] for item in data['devices']['items']]
                    return device_names
                else:
                    print("Error: Unexpected response format")
                    return []
            else:
                print(f"Error: API request failed with status code {response.status_code}")
                return []
        except Exception as e:
            print(f"Error fetching device names from API: {str(e)}")
            return []

    # Function to read and extract value of the given key from JSON config files
    def extract_player_names(config_folder, key):
        player_names = []  # List to store player names
        
        # Loop through all files in the directory
        for filename in os.listdir(config_folder):
            # Check if the file ends with '.config'
            if filename.endswith(".config"):
                file_path = os.path.join(config_folder, filename)
                
                try:
                    # Open and read the JSON file
                    with open(file_path, 'r', encoding='utf-8') as file:
                        data = json.load(file)
                        
                        # If the key exists, append its value to the list
                        if key in data:
                            player_names.append(data[key].strip())
                except (json.JSONDecodeError, FileNotFoundError) as e:
                    # Handle errors silently (ignore the file if there's an issue reading it)
                    pass
        
        return player_names

    # Define the key to search for
    key_to_search = "statusSettings.playerName"

    # Extract player names from all .config files in the specified folder
    local_player_names = extract_player_names(config_folder, key_to_search)
    print(f"Tổng cộng: {len(local_player_names)} thiết bị")
    # Print the result as an array of strings
    print(local_player_names)

    # Fetch device names from the API
    database_device_names = fetch_device_names_from_api()
    print(f"Tổng cộng: {len(database_device_names)} thiết bị")
    # Print the result as an array of strings
    print(database_device_names)

    # Find devices that are not in the database
    missing_devices = [device for device in local_player_names if device not in database_device_names]
    print(f"Số lượng thiết bị không có trong cơ sở dữ liệu: {len(missing_devices)}")
    print(missing_devices)

    # Create new devices in the database for missing devices
    def create_new_device(device_name):
        try:
            url = f"{service_url}/ldplayer_devices/create"

            headers = {
                "Content-Type": "application/json"
            }
            
            # Generate a device ID based on the device name
            device_id = f"LD-{device_name}"
            
            # Prepare the payload with default values
            payload = {
                "device_name": device_name,
                "device_id": device_id,
                "device_model": "Samsung Galaxy S10",
                "android_version": "12",
                "serial_number": f"SN{device_name}",
                "udid": f"UD{device_name}",
                "imei": f"IM{device_name}",
                "last_run": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                "pc_runner": "Máy chạy Group 1",
                "count_today": 0,
                "status": "active"
            }

            # Make the API request
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code in (200, 201):
                print(f"Successfully created device: {device_name}")
                # Calculate and show progress percentage
                current_index = missing_devices.index(device_name) + 1
                percentage = (current_index / len(missing_devices)) * 100
                print(f"Progress: {percentage:.1f}% ({current_index}/{len(missing_devices)})")
                return True
            else:
                print(f"Failed to create device {device_name}. Status code: {response.status_code}")
                return False
        except Exception as e:
            print(f"Error creating device {device_name}: {str(e)}")
            return False
    
    # Process all missing devices
    if missing_devices:
        print("Creating missing devices in the database...")
        success_count = 0
        
        for device_name in missing_devices:
            if create_new_device(device_name):
                success_count += 1
            # Add a small delay between requests to avoid overwhelming the API
            time.sleep(0.5)
        
        print(f"Created {success_count} out of {len(missing_devices)} missing devices")
    else:
        print("No missing devices to create")