import json
import os
import random
import string
from pathlib import Path

# Cấu hình đường dẫn và phạm vi index
TEMPLATE_PATH = r"D:\LDPlayer\LDPlayer9\vms\config\leidian0.config"
OUTPUT_DIR = r"D:\LDPlayer\LDPlayer9\vms\config"
START_INDEX = 338
END_INDEX = 635

def random_imei():
    return "01" + ''.join(random.choices(string.digits, k=13))

def random_imsi():
    return "4600" + ''.join(random.choices(string.digits, k=11))

def random_sim_serial():
    return "898600" + ''.join(random.choices(string.digits, k=14))

def random_android_id():
    return ''.join(random.choices('0123456789abcdef', k=16))

def random_mac():
    return "00DB" + ''.join(random.choices('0123456789ABCDEF', k=8))

def load_template():
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(index, config):
    file_name = f"leidian{index}.config"
    path = Path(OUTPUT_DIR) / file_name
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)
    print(f"✓ Đã tạo file cấu hình: {file_name}")

def generate():
    template = load_template()
    total = END_INDEX - START_INDEX + 1
    for i in range(START_INDEX, END_INDEX + 1):
        config = template.copy()

        # Random hóa thông tin thiết bị
        config["propertySettings.phoneIMEI"] = random_imei()
        config["propertySettings.phoneIMSI"] = random_imsi()
        config["propertySettings.phoneSimSerial"] = random_sim_serial()
        config["propertySettings.phoneAndroidId"] = random_android_id()
        config["propertySettings.macAddress"] = random_mac()

        # Cập nhật tên player
        if "statusSettings" not in config:
            config["statusSettings"] = {}
        config["statusSettings"]["playerName"] = f"leidian{i}"

        # Cấu hình tối ưu hóa
        config["basicSettings.rootMode"] = True
        config["statusSettings"]["closeOption"] = 1
        config["basicSettings.heightFrameRate"] = False
        config["basicSettings.adbDebug"] = 1
        config["advancedSettings.resolution"] = {
            "width": 720,
            "height": 1280
        }
        config["advancedSettings.resolutionDpi"] = 320
        config["advancedSettings.cpuCount"] = 2
        config["advancedSettings.memorySize"] = 4096

        save_config(i, config)

    print(f"\n✅ Đã hoàn tất tạo {total} file cấu hình từ leidian{START_INDEX} đến leidian{END_INDEX}.")

if __name__ == "__main__":
    generate()
