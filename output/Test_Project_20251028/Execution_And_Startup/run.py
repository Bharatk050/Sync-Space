# Generated on: 2025-10-28 22:16:56

import os
import sys

# Install dependencies
os.system('pip install -r requirements.txt')

# Create database schema
os.system(f'mysql -u {os.environ["DB_USERNAME"]} -p{os.environ["DB_PASSWORD"]} < schema.sql')

# Start the application
os.system('python app.py')