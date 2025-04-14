import os
import json

# Main function to execute the process
def main():
    config_folder = r"C:\LDPlayer\LDPlayer9\vms\config"

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
    player_names = extract_player_names(config_folder, key_to_search)

    # Print the result as an array of strings
    print(player_names)

# Call the main function to execute
if __name__ == "__main__":
    main()
