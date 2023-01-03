import csv
import logging
import os
import subprocess

import git

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

# Open the CSV file
config_path = os.path.join(os.path.dirname(__file__), 'config.csv')
with open('config.csv', 'r') as f:
    # Read the contents of the file into a list of dictionaries,
    # where each dictionary represents a row in the CSV file
    rows = [{k: v for k, v in row.items()} for row in csv.DictReader(f, skipinitialspace=True)]

# Iterate over the rows in the list
for row in rows:
    # Extract the necessary information for each bot
    path_to_folder = os.path.expanduser(row['path_to_folder'])
    bot_name = row['bot_name']
    branch_to_use = row['branch_to_use']

    # Check if the branch matches config first
    # Open the repository
    repo = git.Repo(path_to_folder)
    # fetch the latest changes from the remote repository
    remote = repo.remote('origin')
    remote.fetch()
    # Check if the current branch name matches the given name
    if repo.active_branch.name != branch_to_use:
        # warning
        logger.warning(f'The current branch name ({repo.active_branch.name}) '
                       f'does not match the name specified in config ({branch_to_use})')
        if not repo.index.diff(repo.head.commit):
            # no staged files, switch branch
            repo.heads[branch_to_use].checkout()
            logger.info(f"Switched from branch {repo.active_branch.name} to {branch_to_use}")
    if not repo.index.diff(repo.head.commit):
        # no diff staged - pull
        remote.pull()

    # Launch the tmux session first
    #   Run the tmux command to list the sessions
    output = subprocess.run(['tmux', 'list-sessions'], stdout=subprocess.PIPE).stdout.decode('utf-8')
    # Check if the desired session is in the list
    if bot_name not in output:
        subprocess.run(['tmux', 'new-session', '-s', bot_name])

    path_to_executable = os.path.expanduser(row['path_to_executable'])
    path_to_logs = os.path.expanduser(row['path_to_logs'])
    parameters = row['parameters']
    command = f'python {path_to_executable} {parameters} >> {path_to_logs} ENTER'
    # Launch the command in the corresponding tmux session
    subprocess.run(['tmux', 'send-keys', '-t', bot_name, f'python'])
