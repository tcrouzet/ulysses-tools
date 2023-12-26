import datetime
import os
import shutil
import subprocess
import zipfile
from config import backup_dir, Ulysses_backup_dir

def secure_backup():

    current_date = datetime.date.today()
    formatted_date = current_date.strftime("%Y%m%d")
    last_backup = os.path.join(Ulysses_backup_dir, "Latest Backup.ulbackup")
    
    if os.path.exists(last_backup):
        last_backup_target = os.path.join(backup_dir, f"ulysses-{formatted_date}.ulbackup")
        shutil.copytree(last_backup, last_backup_target, dirs_exist_ok=True)
        #print(f"Backup done {last_backup_target}")

        # Zip the copied folder
        zip_target = f"{last_backup_target}.zip"
        with zipfile.ZipFile(zip_target, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(last_backup_target):
                for file in files:
                    zipf.write(os.path.join(root, file), 
                               os.path.relpath(os.path.join(root, file),
                               os.path.join(last_backup_target, '..')))
        #print(f"Zip done {zip_target}")
        
        # Remove the original folder after zipping if needed
        #shutil.rmtree(last_backup_target)

        print(f"Backup done and zipped: {zip_target}")

    else:
        print("No Ulysses backup found!")

def secure_backup_shell():

    current_date = datetime.date.today()
    formatted_date = current_date.strftime("%Y%m%d")
    last_backup = os.path.join(Ulysses_backup_dir, "Latest Backup.ulbackup")
    
    if os.path.exists(last_backup):
        last_backup_target = os.path.join(backup_dir, f"ulysses-{formatted_date}.ulbackup")
        zip_target = f"{last_backup_target}.zip"

        # Copier le dossier
        subprocess.run(["cp", "-r", last_backup, last_backup_target], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Zipper le dossier
        subprocess.run(["zip", "-r", zip_target, last_backup_target], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Supprimer le dossier copié
        subprocess.run(["rm", "-rf", last_backup_target])

        print(f"Backup done and zipped: {zip_target}")
    else:
        print("No Ulysses backup found!")

os.system('clear')
secure_backup()