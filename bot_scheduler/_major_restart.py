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
with open(config_path, 'r') as f:
    # Read the contents of the file into a list of dictionaries,
    # where each dictionary represents a row in the CSV file
    rows = [{k: v for k, v in row.items()} for row in csv.DictReader(f, skipinitialspace=True)]

# Iterate over the rows in the list
for row in rows:
    bot_name = row['bot_name']

    is_active = row['is_active'] == "True"
    if not is_active:
        logger.info(f"{bot_name} is disabled, skipping..")
        continue

    logger.info(f"Processing {bot_name}")

    # Extract the necessary information for each bot

    # Pull Git updates
    # Check if the branch matches config first
    path_to_folder = os.path.expanduser(row['path_to_folder'])
    branch_to_use = row['branch_to_use']
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
            logger.info(f"No staged files, switching from branch {repo.active_branch.name} to {branch_to_use}")
            # no staged files, switch branch
            repo.heads[branch_to_use].checkout()
        else:
            logger.warning("Local changes detected, keeping branch the same")
    if not repo.index.diff(repo.head.commit):
        # no diff staged - pull
        res = remote.pull()
        logger.info(f"Pulling updates. res: {res}")
    else:
        logger.warning("Local changes detected, skipping merge to avoid conflicts.")

    # Launch the tmux session first
    #   Run the tmux command to list the sessions
    output = subprocess.run(['tmux', 'list-sessions'], stdout=subprocess.PIPE).stdout.decode('utf-8')
    # Check if the desired session is in the list
    if bot_name not in output:
        logger.info(f"Restarting tmux session for {bot_name}")
        subprocess.run(['tmux', 'new-session', '-d', '-s', bot_name])

    path_to_executable = os.path.expanduser(row['path_to_executable'])
    path_to_logs = os.path.expanduser(row['path_to_logs'])
    parameters = row['parameters']
    command = f'python {path_to_executable} {parameters} >> {path_to_logs}'
    # Launch the command in the corresponding tmux session
    logger.info(f"Sending tmux command to start {bot_name}. Command: {command}")
    subprocess.run(['tmux', 'send-keys', '-t', bot_name, command])
    subprocess.run(["tmux", "send-keys", "-t", bot_name, "Enter"])
