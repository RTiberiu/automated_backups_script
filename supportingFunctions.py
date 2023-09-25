import os
import shutil
from datetime import datetime
import zipfile
import filecmp

def consolidate_backups(backup_folder):
    # Get all the backup files
    backup_files = os.listdir(backup_folder)

    # Create consolidating file
    consolidate_folder = f'{backup_folder}/consolidating'
    os.makedirs(consolidate_folder, exist_ok=True)

    for file in backup_files:
        # Extract file
        file_folder_path = f'{backup_folder}/{os.path.splitext(file)[0]}'
        print(f'file_folder_path: {file_folder_path}')
        with zipfile.ZipFile(f'{backup_folder}/{file}', 'r') as zip_ref:
            os.makedirs(file_folder_path, exist_ok=True)
            zip_ref.extractall(file_folder_path)
        
        # TODO Go through each extracted folder, and check it against the "consolidating" folder     
        
        shutil.rmtree(file_folder_path)

    # TODO Zip the consolidated folder
    # TODO Decide if to remove all the previous backups
    
    shutil.rmtree(consolidate_folder)
    
    return True

def remove_unnecessary_backups(backup_directory):
    directories = os.listdir(backup_directory)
    
    for directory in directories:
        backup_folder = f'{backup_directory}/{directory}'
        backup_paths =  os.listdir(backup_folder)
        number_of_backups = len(backup_paths)
        
        if number_of_backups > max_backups:
            print(f'Consolidating backups for: {directory}')
            consolidate_backups(backup_folder)

    return True

def add_folder_to_zip(zip_filename, source_folder):
    # Create a ZipFile object in write mode
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Walk through the source folder and its subdirectories
        for foldername, subfolders, filenames in os.walk(source_folder):
            # Add each file in the current folder to the zip file
            for filename in filenames:
                file_path = os.path.join(foldername, filename)
                # The arcname parameter allows you to specify the path within the zip file
                zipf.write(file_path, os.path.relpath(file_path, source_folder))
            
            # Add empty folders to the zip file
            for subfolder in subfolders:
                folder_path = os.path.join(foldername, subfolder)
                # Use arcname to ensure empty folders are included
                zipf.write(folder_path, os.path.relpath(folder_path, source_folder))



# # Cycle through all the source directories
# for source_dir in source_directories:
#     source_folder_name = os.path.basename(source_dir)
#     backup_folder_name = f"{source_folder_name} (Backups)"

#     # Create the backup folder if it doesn't exist
#     backup_folder_path = os.path.join(backup_directory, backup_folder_name)
#     os.makedirs(backup_folder_path, exist_ok=True)
    
#     # Check if the source differs from the latest backup
#     create_backup = is_backup_needed(source_dir, backup_folder_path)

#     if create_backup:
#         backup_file_name = f"Backup {source_folder_name} {backup_timestamp}.zip"
#         backup_file_path = f"{backup_folder_path}/{backup_file_name}"
#         add_folder_to_zip(backup_file_path, source_dir)
#         print(f'A backup was created for: {source_dir}')
#     else:
#         print(f'No backup needed for: {source_dir}.')

#     remove_unnecessary_backups(backup_directory)