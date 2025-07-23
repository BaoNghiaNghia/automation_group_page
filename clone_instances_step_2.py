import os
import json
import requests

API_URL = "https://boostgamemobile.com/service/ldplayer_devices/all"
CONFIG_DIR = r"D:\LDPlayer\LDPlayer9\vms\config"
START_INDEX = 338
END_INDEX = 635

# Cấu hình tối ưu hóa mặc định nếu chưa có
EXTRA_CONFIGS = {
    "basicSettings.rootMode": True,
    "statusSettings.closeOption": 1,
    "basicSettings.heightFrameRate": False,
    "basicSettings.adbDebug": 1,
    "advancedSettings.resolution": {
        "width": 720,
        "height": 1280
    },
    "advancedSettings.resolutionDpi": 320,
    "advancedSettings.cpuCount": 2,
    "advancedSettings.memorySize": 4096,
}

def fetch_device_mapping():
    try:
        response = requests.get(API_URL, params={
            "pc_runner": "pc_1",
            "status": "active"
        }, timeout=10)
        response.raise_for_status()
        data = response.json()

        items = data.get("devices", {}).get("items", [])
        if not items:
            print("[!] Không có thiết bị nào được trả về từ API.")
            return {}

        # Gán từ leidian338.config đến leidian635.config
        if len(items) > (END_INDEX - START_INDEX + 1):
            print(f"[!] Số lượng thiết bị trả về ({len(items)}) vượt quá phạm vi cho phép.")
            items = items[:END_INDEX - START_INDEX + 1]

        mapping = {}
        for i, item in enumerate(items):
            index = START_INDEX + i
            file_name = f"leidian{index}.config"
            player_name = item.get("device_name")
            if player_name:
                mapping[file_name] = player_name

        return mapping

    except Exception as e:
        print(f"[!] Lỗi khi gọi API: {e}")
        return {}


def parse_key_value_file(path):
    config = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key, value = key.strip(), value.strip()
            try:
                config[key] = json.loads(value)
            except:
                config[key] = value
    return config

def update_config_file(config_path, player_name):
    if not os.path.exists(config_path):
        print(f"[!] Không tìm thấy: {config_path}")
        return False

    try:
        config_dict = parse_key_value_file(config_path)
    except Exception as e:
        print(f"[!] Không thể đọc file {config_path}: {e}")
        return False

    if "statusSettings" not in config_dict or not isinstance(config_dict["statusSettings"], dict):
        config_dict["statusSettings"] = {}

    base_name = os.path.basename(config_path)
    default_player_name = base_name.replace(".config", "")
    final_player_name = player_name if player_name else default_player_name
    config_dict["statusSettings"]["playerName"] = final_player_name

    if player_name:
        print(f"[MAP] {base_name} → {player_name}")

    for key, value in EXTRA_CONFIGS.items():
        if key not in config_dict:
            config_dict[key] = value

    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_dict, f, ensure_ascii=False, indent=4)
        print(f"[✓] {base_name} đã chuyển sang JSON -> playerName = {final_player_name}")
        return True
    except Exception as e:
        print(f"[!] Lỗi khi ghi file {config_path}: {e}")
        return False

def main():
    mapping = fetch_device_mapping()
    print("[DEBUG] Device mapping:", mapping)
    updated_count = 0

    for i in range(START_INDEX, END_INDEX + 1):
        file_name = f"leidian{i}.config"
        full_path = os.path.join(CONFIG_DIR, file_name)
        player_name = mapping.get(file_name)
        if update_config_file(full_path, player_name):
            updated_count += 1

    print(f"\n✅ Đã cập nhật {updated_count} file từ leidian{START_INDEX}.config đến leidian{END_INDEX}.config")

if __name__ == "__main__":
    main()
