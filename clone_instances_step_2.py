import os
import requests

API_URL = "https://boostgamemobile.com/service/ldplayer_devices/all?pc_runner=pc_2"
CONFIG_DIR = r"D:\LDPlayer\LDPlayer9\vms\config"

def fetch_device_mapping():
    response = requests.get(API_URL)
    data = response.json()
    items = data["devices"]["items"]

    # Bắt đầu từ leidian1.config
    mapping = {}
    for index, item in enumerate(items):
        config_filename = f"leidian{index + 1}.config"
        mapping[config_filename] = item["device_name"]

    return mapping

def update_config_file(config_path, player_name):
    if not os.path.exists(config_path):
        print(f"[!] Không tìm thấy: {config_path}")
        return

    lines = []
    updated = False
    with open(config_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip().startswith("statusSettings.playerName="):
                lines.append(f"statusSettings.playerName={player_name}\n")
                updated = True
            else:
                lines.append(line)

    if not updated:
        lines.append(f"statusSettings.playerName={player_name}\n")

    with open(config_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(f"[✓] {os.path.basename(config_path)} -> playerName = {player_name}")

def main():
    mapping = fetch_device_mapping()
    for config_filename, player_name in mapping.items():
        config_path = os.path.join(CONFIG_DIR, config_filename)
        update_config_file(config_path, player_name)

if __name__ == "__main__":
    main()
