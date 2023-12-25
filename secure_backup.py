import datetime
import os
import shutil
from config import backup_dir, Ulysses_backup_dir

def secure_backup():

    current_date = datetime.date.today()
    formatted_date = current_date.strftime("%Y%m%d")
    last_backup = os.path.join(Ulysses_backup_dir, "Latest Backup.ulbackup")
    
    if os.path.exists(last_backup):
        last_backup_target = os.path.join(backup_dir, f"ulysses-{formatted_date}.ulbackup")
        shutil.copytree(last_backup, last_backup_target, dirs_exist_ok=True)
        print(f"Backup done {last_backup_target}")
    else:
        print("No Ulysses backup found!")

secure_backup()