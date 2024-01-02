import os

#Where to backup on the Mac - desktop by default
backup_dir = '~/Desktop/Ubackup/'

#Ulysses backup files
Ulysses_backup_dir = '~/Library/Group Containers/X5AZV975AG.com.soulmen.shared/Ulysses/Backups/'

#Ulysses files non icloud
Ulysses_dir = '~/Library/Mobile Documents/X5AZV975AG~com~soulmen~ulysses3/Documents'

#Witth a . hide ulysses original datas and medias, otherwise empty 
uHide = ""

#Save or not Ulysses metadata (used for debug)
uOriginal = False

#No accent in file names
no_accent_in_file = False

backup_dir = os.path.expanduser(backup_dir)
Ulysses_backup_dir = os.path.expanduser(Ulysses_backup_dir)
Ulysses_dir = os.path.expanduser(Ulysses_dir)