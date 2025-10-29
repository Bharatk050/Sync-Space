# Generated on: 2025-10-28 21:57:19

import schedule
import time
import os
import tarfile

def backup():
    # Create a tarball of the current directory
    with tarfile.open('backup.tar.gz', 'w:gz') as tar:
        tar.add('.')

# Schedule the backup to run daily at 2am
schedule.every().day.at("02:00").do(backup)

while True:
    schedule.run_pending()
    time.sleep(1)