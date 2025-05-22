import os
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed

SRC_ROOT = r"D:\LDPlayer\LDPlayer9\vms"
BACKUP_ROOT = r"Z:\Backup_LDPlayer_Fb_Acc"

def backup_instance(instance_folder_name):
    src_path = os.path.join(SRC_ROOT, instance_folder_name)
    dst_path = os.path.join(BACKUP_ROOT, instance_folder_name)
    
    try:
        if os.path.exists(dst_path):
            shutil.rmtree(dst_path)  # Remove old backup folder to overwrite

        shutil.copytree(src_path, dst_path)
        return (instance_folder_name, "Success")
    except Exception as e:
        return (instance_folder_name, f"Failed: {e}")

def main():
    if not os.path.exists(SRC_ROOT):
        print(f"Source root not found: {SRC_ROOT}")
        return

    os.makedirs(BACKUP_ROOT, exist_ok=True)

    instances = [f for f in os.listdir(SRC_ROOT) if os.path.isdir(os.path.join(SRC_ROOT, f))]

    print(f"Found {len(instances)} instances to back up.")

    max_workers = 2  # Limit concurrency to 2
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(backup_instance, inst) for inst in instances]

        for future in as_completed(futures):
            inst_name, status = future.result()
            print(f"[{inst_name}] Backup status: {status}")

if __name__ == "__main__":
    main()
