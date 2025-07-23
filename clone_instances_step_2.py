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

        return {
            f"leidian{index + 1}.config": item["device_name"]
            for index, item in enumerate(items)
            if "device_name" in item
        }

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

def update_config_file(config_path, player_name=None):
    if not os.path.exists(config_path):
        print(f"[!] Không tìm thấy: {config_path}")
        return False

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            first_char = f.read(1)
            f.seek(0)
            if first_char == "{":
                config_dict = json.load(f)
            else:
                config_dict = parse_key_value_file(config_path)
    except Exception as e:
        print(f"[!] Không thể đọc file {config_path}: {e}")
        return False

    # Nếu có player_name từ API thì cập nhật
    if player_name:
        if "statusSettings" not in config_dict:
            config_dict["statusSettings"] = {}
        config_dict["statusSettings"]["playerName"] = player_name

    # Thêm các cấu hình còn thiếu
    for key, value in EXTRA_CONFIGS.items():
        if key not in config_dict:
            config_dict[key] = value

    # Ghi lại dưới dạng JSON
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_dict, f, ensure_ascii=False, indent=4)
        print(f"[✓] Đã cập nhật: {os.path.basename(config_path)}")
        return True
    except Exception as e:
        print(f"[!] Lỗi ghi file {config_path}: {e}")
        return False

def main():
    mapping = fetch_device_mapping()
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
