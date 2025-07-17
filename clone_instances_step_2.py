import os
import json
import requests

API_URL = "https://boostgamemobile.com/service/ldplayer_devices/all?pc_runner=pc_2"
CONFIG_DIR = r"D:\LDPlayer\LDPlayer9\vms\config"

# Các cấu hình bổ sung cần thêm (dưới dạng key-value chuỗi)
EXTRA_CONFIGS = {
    "basicSettings.rootMode": "true",
    "statusSettings.closeOption": "1",
    "basicSettings.heightFrameRate": "false",
    "basicSettings.adbDebug": "1",
    "advancedSettings.resolution": json.dumps({"width": 720, "height": 1280}),
    "advancedSettings.resolutionDpi": "320",
    "advancedSettings.cpuCount": "2",
    "advancedSettings.memorySize": "4096",
}

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

    config_dict = {}

    # Đọc file hiện có
    with open(config_path, "r", encoding="utf-8") as f:
        for line in f:
            if "=" in line:
                key, value = line.strip().split("=", 1)
                config_dict[key] = value

    # Cập nhật hoặc thêm playerName
    config_dict["statusSettings.playerName"] = player_name

    # Thêm các config còn thiếu
    for key, value in EXTRA_CONFIGS.items():
        if key not in config_dict:
            config_dict[key] = value

    # Ghi đè lại toàn bộ file
    with open(config_path, "w", encoding="utf-8") as f:
        for key, value in config_dict.items():
            f.write(f"{key}={value}\n")

    print(f"[✓] {os.path.basename(config_path)} -> playerName = {player_name}")

def main():
    mapping = fetch_device_mapping()
    for config_filename, player_name in mapping.items():
        config_path = os.path.join(CONFIG_DIR, config_filename)
        update_config_file(config_path, player_name)

if __name__ == "__main__":
    main()
