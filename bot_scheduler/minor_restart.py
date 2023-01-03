"""Check if any of the bots crashed (didn't touch the touch file) and restart if they did"""
import csv
import datetime
import os
import subprocess

# Open the CSV file
config_path = os.path.join(os.path.dirname(__file__), 'config.csv')
with open('config.csv', 'r') as f:
    # Read the contents of the file into a list of dictionaries,
    # where each dictionary represents a row in the CSV file
    rows = [{k: v for k, v in row.items()} for row in csv.DictReader(f, skipinitialspace=True)]

# Iterate over the rows in the list
for row in rows:
    is_active = row['is_active'] == "True"
    if not is_active:
        continue
    # Extract the necessary information for each bot
    path_to_folder = os.path.expanduser(row['path_to_folder'])
    path_to_executable = os.path.expanduser(row['path_to_executable'])
    path_to_logs = os.path.expanduser(row['path_to_logs'])
    bot_name = row['bot_name']
    branch_to_use = row['branch_to_use']  # todo: add, use
    parameters = row['parameters']

    # Get the modification time of the file
    path_to_heartbeat_file = os.path.expanduser(row['path_to_touch_file'])
    if os.path.exists(path_to_heartbeat_file):
        modification_time = os.path.getmtime(path_to_heartbeat_file)
        modification_time = datetime.datetime.fromtimestamp(modification_time)
        time_difference = datetime.datetime.now() - modification_time

        # Check if the time difference is greater than 5 minutes
        if time_difference < datetime.timedelta(minutes=5):
            # process is alive
            continue

    # Launch the tmux session first
    #   Run the tmux command to list the sessions
    output = subprocess.run(['tmux', 'list-sessions'], stdout=subprocess.PIPE).stdout.decode('utf-8')
    # Check if the desired session is in the list
    if bot_name not in output:
        subprocess.run(['tmux', 'new-session', '-d', '-s', bot_name])

    # Run the command in tmux
    command = f'python {path_to_executable} {parameters} >> {path_to_logs}'
    # Launch the command in the corresponding tmux session
    subprocess.run(['tmux', 'send-keys', '-t', bot_name, command])
    subprocess.run(["tmux", "send-keys", "-t", bot_name, "Enter"])
