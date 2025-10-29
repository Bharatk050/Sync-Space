@echo off

:: Install dependencies
pip install -r requirements.txt

:: Create database schema
mysql -u %DB_USERNAME% -p%DB_PASSWORD% < schema.sql

:: Start the application
python app.py