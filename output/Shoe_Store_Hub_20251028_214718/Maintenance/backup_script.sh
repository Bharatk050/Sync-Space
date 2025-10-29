#!/bin/bash

# Set backup directory
BACKUP_DIR=/var/backups/shoe_store_hub

# Set database credentials
DB_USER=root
DB_PASSWORD=password
DB_NAME=shoe_store_hub

# Set backup schedule
CRON_SCHEDULE="0 2 * * *"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
mysqldump -u $DB_USER -p$DB_PASSWORD $DB_NAME > $BACKUP_DIR/$(date +\%Y-\%m-\%d-\%H-\%M-\%S).sql

# Backup configuration files
cp -r /etc/shoe_store_hub $BACKUP_DIR/

# Backup user data
cp -r /var/www/shoe_store_hub/user_data $BACKUP_DIR/