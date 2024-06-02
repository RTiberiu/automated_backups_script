# Automated backups script  

## What it does
The script crawls through the entire folder structure of a directory and creates archives for the files in each folder. It creates the same folder structure in the desired backup directory and that's where the archives will be placed.  
The script creates an archive for a folder's files only if any of the files were changed (modified or newly created) since the last backup was made.

## How to use it  
1. Configure the `config.json` file:  
   a. Add to the property `source_directories` all the main directories you wish to have backed up. As mentioned above, the script will crawl through the entire directory, so only the parent directory needs to be added.  
   b. Add to the property `backup_directory`, `recover_directory`, and `history_log` the disered backup location, where all the archives and backups will be stored.  
   c. Change the property `max_backups` to the desired amount of backups to be stored for each folder's files. A higher number provides a greater history but at an increased memory cost.  
2. Using the `automatedBackups.py`:  
3. Using the `restoreSource.py`:  
