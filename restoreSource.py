import datetime
import json
from datetime import datetime, timedelta
import sys
from pathlib import Path
import os
import csv
import zipfile
import filecmp
import shutil
import threading
import time

backups_combined = 0

# Get the current date and time to use in the backup folder name
backup_timestamp = datetime.now().strftime("%d %B %Y %H%M%S")

# Read config file
with open('config.json', 'r') as config_file:
    config_data = json.load(config_file)

def prompt_user_for_data():
    # Show welcome message
    welcome = """
    ░░░░░░  ░░░░░░░ ░░░░░░░ ░░░░░░░░  ░░░░░░  ░░░░░░  ░░░░░░░     ░░░░░░   ░░░░░   ░░░░░░ ░░   ░░ ░░    ░░ ░░░░░░  
    ▒▒   ▒▒ ▒▒      ▒▒         ▒▒    ▒▒    ▒▒ ▒▒   ▒▒ ▒▒          ▒▒   ▒▒ ▒▒   ▒▒ ▒▒      ▒▒  ▒▒  ▒▒    ▒▒ ▒▒   ▒▒ 
    ▒▒▒▒▒▒  ▒▒▒▒▒   ▒▒▒▒▒▒▒    ▒▒    ▒▒    ▒▒ ▒▒▒▒▒▒  ▒▒▒▒▒       ▒▒▒▒▒▒  ▒▒▒▒▒▒▒ ▒▒      ▒▒▒▒▒   ▒▒    ▒▒ ▒▒▒▒▒▒  
    ▓▓   ▓▓ ▓▓           ▓▓    ▓▓    ▓▓    ▓▓ ▓▓   ▓▓ ▓▓          ▓▓   ▓▓ ▓▓   ▓▓ ▓▓      ▓▓  ▓▓  ▓▓    ▓▓ ▓▓      
    ██   ██ ███████ ███████    ██     ██████  ██   ██ ███████     ██████  ██   ██  ██████ ██   ██  ██████  ██      
    """

    # Add all the files to the prompt string
    welcome += '\nPlease select which file do you wish to restore.\n\n'
    for i, path in enumerate(config_data['source_directories'], start=1):
        welcome += f'{i}. {path}\n'
    print(welcome)

    valid_file_input = False
    user_index = None
    while not valid_file_input:
        recover_file_prompt = input('\nEnter the index of the path to restore: ')
        try:
            if 1 <= int(recover_file_prompt) < len(config_data['source_directories']) + 1:
                valid_file_input = True
                user_index = int(recover_file_prompt) - 1
            else:
                print('Index is out of range.')
        except ValueError:
            print('Invalid input. Please enter an integer.')

    folder_to_restore = config_data['source_directories'][user_index]

    # Create a list to store the previous dates
    date_message = '\nPlease select an index from the dates below or enter another date for the backup you wish to restore.\n\n'
    current_date = datetime.now()
    dates = []
    # Loop to generate the previous 10 dates
    for i in range(1, 11):
        previous_date = current_date - timedelta(days=i)
        formatted_date = previous_date.strftime("%d %B %Y")
        if i == 10:
            spacing = ' '
        else:
            spacing = '  '
        dates.append(formatted_date)
        date_message += f"{i}.{spacing}{formatted_date}\n"
    
    print(date_message)

    valid_date_input = False
    userDate = None
    while not valid_date_input:
        date_to_restore_input = input('\nEnter the index or input a date in the format DD.MM.YYYY: ')

        try:
            date_to_restore_input_as_int = int(date_to_restore_input)
            if 1 <= date_to_restore_input_as_int <= 10:
                valid_date_input = True
                userDate = dates[date_to_restore_input_as_int - 1]
            else:
                print('Invalid input. Please enter an integer between 1 and 10.')
        except ValueError:
            try:
                # Try to parse the input as a date
                date_obj = datetime.strptime(date_to_restore_input, '%d.%m.%Y')
                valid_date_input = True
                userDate = date_obj.strftime('%d %B %Y')
            except ValueError:
                print('Invalid input. Please enter an integer between 1 and 10 or a date in the format DD.MM.YYYY.')


    # Get final confirmation
    confirmation_message = f'\nAre you sure you wish to restore:\n\nFolder:\t\t{folder_to_restore}\nRestore date:\t{userDate}\n\nPlease answer (y/n): '
    
    valid_confirmation = False
    while not valid_confirmation:
        confirmation_input = input(confirmation_message)

        try:
            if confirmation_input.lower() == 'y':
                valid_confirmation = True
            elif confirmation_input.lower() == 'n':
                valid_confirmation = True
                print('Stopping script.')
                sys.exit()                
            else:
                print('Wrong input.\n')
        except ValueError:
            print('Wrong input.\n')

    return folder_to_restore, userDate

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

def list_files_without_hidden(folder_path):
    # Get all files in the current folder, excluding hidden files
    return [f for f in os.listdir(folder_path) if not f.startswith('.')]

def list_only_files_without_hidden(folder_path):
    # Get only files in the current folder, excluding hidden files
    return [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f)) and not f.startswith('.')]

def restore_time_capsule(source_dir, date):
    source_folder_name = os.path.basename(source_dir)
    backup_folder_name = source_folder_name
    backup_folder_path = os.path.join(config_data['backup_directory'], backup_folder_name)

    def _restore_date_matching_backup_path(directory ,date):
        restore = False
        path = None
        formatted_date = datetime.strptime(date, "%d %B %Y").date()
        files_in_path = list_only_files_without_hidden(directory)

        # Cycle through backup files in the current folder
        for file in files_in_path:
            full_file_path = os.path.join(directory, file)
            creation_time = os.path.getctime(full_file_path)
            creation_date = datetime.fromtimestamp(creation_time).date()

            # If file creation date matches given date
            if formatted_date < creation_date or formatted_date == creation_date:
                restore = True
                path = full_file_path
                break
        
        return restore, path


    def _check_if_path_is_active_for_date(path, date):
        path_should_be_restored = False
        path_to_restore = None

        with open(config_data['history_log'], mode='r') as file:
            csv_reader = csv.reader(file)
            rows = list(csv_reader)
            
            # Reverse the list of rows to start from the bottom
            rows.reverse()

            # Restore path if there are no records in the log
            if not rows:
                path_should_be_restored, path_to_restore = _restore_date_matching_backup_path(path, date)
            else:
                # Iterate through each row in the reversed list
                for row in rows:
                    # Get the last record in the CSV
                    if row and row[0] == path:
                        date_arr = row[1].split(' ')[0:3]
                        row_date = ' '.join(date_arr)
                    
                        if row[2] == '1':
                            files_in_path = list_only_files_without_hidden(path)
                            
                            # Cycle through backup files in the current folder
                            for file in files_in_path:
                                full_file_path = os.path.join(path, file)
                                # print(f'full_file_path: {full_file_path}')
                                creation_time = os.path.getctime(full_file_path)
                                creation_date = datetime.fromtimestamp(creation_time)
                                formatted_date = creation_date.strftime('%d %B %Y')
                                formatted_row_date = datetime.strptime(row_date, "%d %B %Y")

                                # If csv record date and file date match, restore
                                if formatted_row_date < formatted_date or formatted_row_date == formatted_date:
                                    path_should_be_restored = True
                                    path_to_restore = full_file_path
                                    break

                        # Exit early if found the record
                        if path_should_be_restored:
                            break
                
                # Get latest backup if nothing was found in the loop
                if not path_should_be_restored:
                    path_should_be_restored, path_to_restore = _restore_date_matching_backup_path(path, date)
        
        return path_should_be_restored, path_to_restore
        
    # Traverse to all subfolders and restore backups
    def _restore_backup_for_current_folder(current_folder, date):
        global backups_combined

        # Check if current folder needs to be restored
        restore_file, path_to_restore = _check_if_path_is_active_for_date(current_folder, date)

        # Restore files for current folder
        if restore_file:
            recover_full_path = current_folder.replace(config_data['backup_directory'], config_data['recover_directory'])

            # Check if the target directory exists; if not, create it
            if not os.path.exists(recover_full_path):
                os.makedirs(recover_full_path)
            try:
                # Open the zip file
                with zipfile.ZipFile(path_to_restore, 'r') as zip_ref:
                    # Extract all the contents of the zip file to the target directory
                    zip_ref.extractall(recover_full_path)
                
                # Increment backups_combined
                backups_combined += 1

            except zipfile.BadZipFile:
                print(f'The file {path_to_restore} is not a valid zip archive.')
            except FileNotFoundError:
                print(f'The file {path_to_restore} does not exist.')
            except Exception as e:
                print(f'An error occurred: {str(e)}')
        
        # Traverse to lower folder levels
        for subfolder in list_files_without_hidden(current_folder):
            full_backup_path = os.path.join(current_folder,subfolder)
            if not os.path.isfile(full_backup_path):

                _restore_backup_for_current_folder(full_backup_path, date)

    _restore_backup_for_current_folder(backup_folder_path, date)

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

def delete_folder_content(directory):
    try:
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            if os.path.isfile(item_path):
                os.unlink(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
    except FileNotFoundError:
        print(f'The folder {directory} does not exist.')
    except Exception as e:
        print(f'An error occurred: {str(e)}')

def loading_animation():
    num_dots = 0
    while loading_animation_running:
        sys.stdout.write("\rSearching and creating backups" + "." * num_dots + "   ")
        sys.stdout.flush()
        time.sleep(0.5)
        num_dots = (num_dots + 1) % 4

def format_time(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours)} hours {int(minutes)} minutes {int(seconds)} seconds"

# Global variable to indicate whether the loading animation should continue
loading_animation_running = True

def main():
    global loading_animation_running
    script_timer = datetime.now()

    # Clean the recovery folder
    delete_folder_content(config_data['recover_directory'])

    restore_path, date = prompt_user_for_data()
    
    # Start the loading animation in a separate thread
    loading_thread = threading.Thread(target=loading_animation)
    loading_thread.start()

    restore_time_capsule(restore_path, date)

    # Stop the loading animation
    loading_animation_running = False
    loading_thread.join()

    # Get total computing time
    elapsed_time = (datetime.now() - script_timer).total_seconds()
    formatted_time = format_time(elapsed_time)

    # Print detailed message
    print(f'\n\nTotal running time: {formatted_time}\n\nCombined archives: {backups_combined}\n')
    print(f'\nPlease find your recoved file in the folder: {config_data["recover_directory"]}.\nThe folder should be moved to another location, as the scripts cleans the Recovery folder to avoid conflicts.\n')

main()