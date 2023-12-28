import os

#Where to backup on the Mac - desktop by default
backup_dir = '~/Desktop/Ubackup/'

#Ulysses backup files
Ulysses_backup_dir = '~/Library/Group Containers/X5AZV975AG.com.soulmen.shared/Ulysses/Backups/'

#Ulysses files non icloud
Ulysses_dir = '~/Library/Mobile Documents/X5AZV975AG~com~soulmen~ulysses3/Documents'

#Witth a . hide ulysses original datas, otherwise empty 
uHide = "."

backup_dir = os.path.expanduser(backup_dir)
Ulysses_backup_dir = os.path.expanduser(Ulysses_backup_dir)
Ulysses_dir = os.path.expanduser(Ulysses_dir)