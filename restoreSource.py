import datetime
import json
from datetime import datetime, timedelta
import sys
from pathlib import Path
import os
import csv

backups_combined = 0

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

def list_files_without_hidden(folder_path):
    # Get all files in the current folder, excluding hidden files
    return [f for f in os.listdir(folder_path) if not f.startswith('.')]

def restore_time_capsule(source_dir, date):
    source_folder_name = os.path.basename(source_dir)
    backup_folder_name = source_folder_name
    backup_folder_path = os.path.join(config_data['backup_directory'], backup_folder_name)

    def _check_if_path_is_active_for_date(path, date):
        path_should_be_restored = False

        with open(config_data['history_log'], mode='r') as file:
            csv_reader = csv.reader(file)
            rows = list(csv_reader)
            
            # Reverse the list of rows to start from the bottom
            rows.reverse()
            
            # Iterate through each row in the reversed list
            for row in rows:
                # Get the last record in the CSV
                if row and row[0] == path:
                    date = row[1].split(' ')[0:2]
                    print(f'XX date: {date}')
                    # path_should_be_restored = True
                    # last_record = row

    # Traverse to all subfolders and restore backups
    def _restore_backup_for_current_folder(current_folder, date):
        global backups_combined

        for subfolder in list_files_without_hidden(current_folder):
            full_backup_path = os.path.join(current_folder,subfolder)
            if not os.path.isfile(full_backup_path):
                print(f'current_folder: {full_backup_path}')
                _check_if_path_is_active_for_date(current_folder, date)

                _restore_backup_for_current_folder(full_backup_path, date)



    _restore_backup_for_current_folder(backup_folder_path, date)

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
            zip_file_path = f'{backup_subfolder}\{zip_file_name}'
            
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

def main():
    # restore_path, date = prompt_user_for_data()

    restore_path, date = 'X:\\source2', '03 September 2023'
    print(f'restore_path: {restore_path}, date: {date}')
    restore_time_capsule(restore_path, date)
    
main()