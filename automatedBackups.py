import os
import shutil
from datetime import datetime
import zipfile
import filecmp
import csv
import json
from pathlib import Path
import threading
import sys
import time

# Read config file
with open('config.json', 'r') as config_file:
    config_data = json.load(config_file)

backups_created = 0
folders_checked = 0
# Get the current date and time to use in the backup folder name
backup_timestamp = datetime.now().strftime("%d %B %Y %H%M%S")

# Global variable to indicate whether the loading animation should continue
loading_animation_running = True

def list_files_without_hidden(folder_path):
    # Get all files in the current folder, excluding hidden files
    return [f for f in os.listdir(folder_path) if not f.startswith('.')]

def add_files_from_folder_to_zip(zip_file_path, source_folder):
    # Create a ZipFile object in write mode
    with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Get a list of files in the source folder
        source_files = [f for f in list_files_without_hidden(source_folder) if os.path.isfile(os.path.join(source_folder, f))]

        # Add each file in the source folder to the zip file
        for filename in source_files:
            file_path = os.path.join(source_folder, filename)
            # The arcname parameter allows you to specify the path within the zip file
            zipf.write(file_path, os.path.relpath(file_path, source_folder))
            
def get_all_file_paths_in_folder(folder_path):
    # Get all files in the current folder
    files_path_array = set()
    folder_files_list = list_files_without_hidden(folder_path)

    # Remove temp_backup from paths if it exists
    clean_folder_files_list = [folder for folder in folder_files_list if "temp_backup" not in folder]

    # Get all the folders
    for file in clean_folder_files_list:
        file_absolute_path = os.path.join(folder_path, file)
        if os.path.isfile(file_absolute_path) and not file.startswith('.'):
            files_path_array.add(file)
    
    return files_path_array

def are_dir_trees_equal(dir1, dir2):
    output = True
    # Get dir1 file paths
    dir1_file_paths = get_all_file_paths_in_folder(dir1)
    # Get dir2 file paths
    dir2_file_paths = get_all_file_paths_in_folder(dir2)
    
    file_difference_dir1 = list(dir1_file_paths - dir2_file_paths)
    file_difference_dir2 = list(dir2_file_paths - dir1_file_paths)
    
    # Get file differences -- TESTING
    # print(f'file_difference: {file_difference_dir1}')
    # print(f'file_difference: {file_difference_dir2}')

    # Check if contents are the same if there are no differences in files between the folders
    if not file_difference_dir1 and not file_difference_dir2:
        # Check if the contents are the same
        for file_dir1, file_dir2 in zip(dir1_file_paths, dir2_file_paths):
            file_comparison = filecmp.cmp(f'{dir1}/{file_dir1}', f'{dir2}/{file_dir2}', shallow=True)

            if not file_comparison:
                output = False
                break
    else:
        output = False
    return output

# Function to compare files in the source directory with the latest backup for a specific source
def is_backup_needed(source_path, backup_directory):
    output = True
    files_backup = [os.path.join(backup_directory, file) for file in list_files_without_hidden(backup_directory) if os.path.isfile(os.path.join(backup_directory, file))]
    files_source = [os.path.join(source_path, file) for file in list_files_without_hidden(source_path) if os.path.isfile(os.path.join(source_path, file))]
    extracted_backup_path = f'{backup_directory}/temp_backup'
    
    if files_backup:
        # Get the latest backup 
        latest_backup_file = max(files_backup, key=os.path.getmtime)

        # Extract the latest backup
        with zipfile.ZipFile(latest_backup_file, 'r') as zip_ref:
            # Extract all the contents to the specified folder
            zip_ref.extractall(extracted_backup_path)
            
        output = not are_dir_trees_equal(source_path, extracted_backup_path)
    
    if not files_source:
        output = False

    # Remove temp_backup directory if it exists
    if os.path.exists(extracted_backup_path):
        shutil.rmtree(extracted_backup_path)

    return output

# Create the same folder structure for the backup as the source directory has
def create_source_folder_structure(source_dir):
    original_source_dir = Path(source_dir)
    source_folder_name = original_source_dir.name
    backup_folder_name = source_folder_name
    backup_folder_path = Path(config_data['backup_directory']) / backup_folder_name

    # Create main directory if it doesn't exist
    if not backup_folder_path.is_dir():
        backup_folder_path.mkdir(parents=True)

    def _create_existing_subfolders_for_path(source_dir):
        for source_directory in list_files_without_hidden(source_dir):
            # Create folder if it's not a file
            full_source_directory_path = Path(source_dir) / source_directory
            if not full_source_directory_path.is_file():
                # Get the extra layers in path
                layers_path = full_source_directory_path.relative_to(original_source_dir)
                # Build path and create the folder if it doesn't exist
                create_directory = backup_folder_path / layers_path
                if not create_directory.is_dir():
                    create_directory.mkdir(parents=True)

                # Go a level deeper to check for any existing subfolders
                _create_existing_subfolders_for_path(full_source_directory_path)

    _create_existing_subfolders_for_path(original_source_dir)

    return True

# Create backups for files inside each of the folders
def create_backup_for_folders(source_dir):
    source_folder_name = os.path.basename(source_dir)
    backup_folder_name = source_folder_name
    backup_folder_path = os.path.join(config_data['backup_directory'], backup_folder_name)
    def _create_backup_for_current_folder(current_folder):
        global backups_created
        global folders_checked
        # Get the extra layers in path
        layers_path = current_folder
        layers_path = layers_path.replace(source_dir, '')
        
        # # Build path and create backup
        backup_subfolder = f'{backup_folder_path}{layers_path}'
        source_folder_name = current_folder.split('\\')[-1]

        # # Check if a backup is needed for the current folder
        needed_backup = is_backup_needed(current_folder, backup_subfolder)

        # Create backup if changes were made
        if needed_backup:
            # Get zip file name and path
            zip_file_name = f'Backup {source_folder_name} {backup_timestamp}.zip'
            zip_file_path = rf'{backup_subfolder}\{zip_file_name}' # Using raw string literal to escape \
            
            # Create a zipfile backup for the files in the folder only
            backups_created += 1
            folders_checked += 1
            # print(f'Creating backup for file in: {current_folder}. Zip location: {zip_file_path}')
            add_files_from_folder_to_zip(zip_file_path, current_folder)
        else: 
            folders_checked += 1
            # print(f'No backup needed for {source_folder_name}')
    
    # Create backup for main source_dir
    _create_backup_for_current_folder(source_dir)

    # Cycle through all subfolders of source_dir and create backups
    def cycle_through_subfolders(folder_path):
        for source_subfolder in list_files_without_hidden(folder_path):
            full_source_subfolder_path = os.path.join(folder_path,source_subfolder)
            if not os.path.isfile(full_source_subfolder_path):
                _create_backup_for_current_folder(full_source_subfolder_path)

                # Go one level deeper
                cycle_through_subfolders(full_source_subfolder_path)

    cycle_through_subfolders(source_dir)

def mark_extra_folders_in_backup(source_dir):
    # Create log if it doesn't exist
    if not os.path.isfile(config_data['history_log']):
        with open(config_data['history_log'], mode='w', newline='') as file:
            pass
     
    source_folder_name = os.path.basename(source_dir)
    backup_folder_path = os.path.join(config_data['backup_directory'], source_folder_name)

    # Get the last record from the log by providing the path to the folder
    def _get_last_record_from_log(record_to_find):
        folder_exists_in_csv = False
        last_record = None
        # Check first if the file is already flagged
        with open(config_data['history_log'], mode='r') as file:
            csv_reader = csv.reader(file)
            
            # Iterate through each row in the CSV
            for row in csv_reader:
                # Get the last record in the CSV
                if row and row[0] == record_to_find:
                    folder_exists_in_csv = True
                    last_record = row
        
        return folder_exists_in_csv, last_record
    
    # Compare current backup directory with current source directory
    def _traverse__backup_subfolders_and_log_extra_folders(backup_dir):
        for current_backup_dir in list_files_without_hidden(backup_dir):
            full_backup_path = f'{backup_dir}/{current_backup_dir}'
            if not os.path.isfile(full_backup_path):
                # Try to get the same directory in the source folder
                same_source_directory_path = full_backup_path
                same_source_directory_path = same_source_directory_path.replace(backup_folder_path, source_dir)
                
                # If path doesn't exist, log it
                if not os.path.exists(same_source_directory_path):
                    folder_exists_in_csv = False
                    last_record = None
                    # Check first if the file is already flagged
                    folder_exists_in_csv, last_record = _get_last_record_from_log(full_backup_path)
                    data = [full_backup_path, backup_timestamp, '0']
                    # If the folder path doesn't exist in the CSV append the data
                    if not folder_exists_in_csv or last_record[2] == '1':
                            # Open the CSV file in append mode ('a')
                            with open(config_data['history_log'], mode='a', newline='') as file:
                                csv_writer = csv.writer(file)

                                # Write the data to the CSV file
                                csv_writer.writerow(data)
                else:
                    # Check if it was flagged before and add that it's back online
                    folder_exists_in_csv = False
                    last_record = None

                    # Get the last record
                    folder_exists_in_csv, last_record = _get_last_record_from_log(full_backup_path)

                    # If last record is flagged as missing, add that it's back online
                    if folder_exists_in_csv and last_record[2] == '0':
                        data = [full_backup_path, backup_timestamp, '1']
                        # Open the CSV file in append mode ('a')
                        with open(config_data['history_log'], mode='a', newline='') as file:
                            csv_writer = csv.writer(file)

                            # Write the data to the CSV file
                            csv_writer.writerow(data)

                # Traverse to a deeper level                
                _traverse__backup_subfolders_and_log_extra_folders(full_backup_path)
                
    _traverse__backup_subfolders_and_log_extra_folders(backup_folder_path)
    return True

def format_time(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours)} hours {int(minutes)} minutes {int(seconds)} seconds"

def loading_animation():
    num_dots = 0
    while loading_animation_running:
        sys.stdout.write("\rSearching and creating backups" + "." * num_dots + "   ")
        sys.stdout.flush()
        time.sleep(0.5)
        num_dots = (num_dots + 1) % 4

def print_directories_info():
    print("\nCreating backups for the following directories: \n")

    # Display directories being backed up from config_data
    for index, item in enumerate(config_data['source_directories']):
        print(f"{index + 1}. {item}") 
    print('\n')

def are_config_directories_valid():
    # Cycle through all the source directories
    for source_dir in config_data['source_directories']:
        if not os.path.exists(source_dir):
            print(f"ERROR: Source directory doesn't exist: {source_dir}")
            return False
    
    # Validate the other backup directories
    backup_directories = [config_data['backup_directory'],
                          config_data['recover_directory']
                          ]

    for backup_dir in backup_directories:
        if not os.path.exists(backup_dir):
            print(f"ERROR: Backup directory doesn't exist: {backup_dir}")
            return False

    return True

def main():
    global loading_animation_running
    script_timer = datetime.now()

    print_directories_info()

    if are_config_directories_valid():
        # Start the loading animation in a separate thread
        loading_thread = threading.Thread(target=loading_animation)
        loading_thread.start()

        # Cycle through all the source directories
        for source_dir in config_data['source_directories']:
            create_source_folder_structure(source_dir)
            mark_extra_folders_in_backup(source_dir)
            create_backup_for_folders(source_dir)

        # Stop the loading animation
        loading_animation_running = False
        loading_thread.join()

        elapsed_time = (datetime.now() - script_timer).total_seconds()
        formatted_time = format_time(elapsed_time)
        print(f'\n\nTotal running time: {formatted_time}\n\nBackups created: {backups_created}\nFolders checked: {folders_checked}\n')

main()