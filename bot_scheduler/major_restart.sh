# kill all python processes
echo "$(date -u) --Killing previous python jobs"
pkill python

# Wait for processes to finish
sleep 5

# run major_restart.py
echo "$(date -u) -- Re-launching. Running _major_restart.py"
python /home/jarvis-service-account/projects/bot_scheduler/bot_scheduler/_major_restart.py