import json
import os
import random
import string
from pathlib import Path

TEMPLATE_PATH = r"D:\LDPlayer\LDPlayer9\vms\config\leidian0.config"
OUTPUT_DIR = r"D:\LDPlayer\LDPlayer9\vms\config"
START_INDEX = 1
END_INDEX = 340

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
    print(f"✓ Generated: {file_name}")

def generate():
    template = load_template()
    for i in range(START_INDEX, END_INDEX + 1):
        config = template.copy()
        config["propertySettings.phoneIMEI"] = random_imei()
        config["propertySettings.phoneIMSI"] = random_imsi()
        config["propertySettings.phoneSimSerial"] = random_sim_serial()
        config["propertySettings.phoneAndroidId"] = random_android_id()
        config["propertySettings.macAddress"] = random_mac()
        config["statusSettings.playerName"] = f"leidian{i}"

        save_config(i, config)

if __name__ == "__main__":
    generate()
