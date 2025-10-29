# README_RUN

# Running the Application
To run the application, follow these steps:

1. Install the required dependencies by running `pip install -r requirements.txt`
2. Create the database schema by running `mysql -u <username> -p<password> < schema.sql`
3. Start the application by running `python app.py`

## Environment Variables
The following environment variables are required:
* `DB_USERNAME`: the username for the database
* `DB_PASSWORD`: the password for the database
* `DB_HOST`: the host for the database
* `DB_PORT`: the port for the database

## Config File
The `config.yaml` file contains the application configuration.
```yml
db:
  username: ${DB_USERNAME}
  password: ${DB_PASSWORD}
  host: ${DB_HOST}
  port: ${DB_PORT}
```
## Schema File
The `schema.sql` file contains the database schema.
```sql
CREATE TABLE users (
  id INT PRIMARY KEY,
  name VARCHAR(255),
  email VARCHAR(255)
);
```
## Requirements File
The `requirements.txt` file contains the required dependencies.
```
flask
mysql-connector-python
```
## Security Considerations
To ensure the security of the application, the following measures should be taken:

* Use a secure password for the database
* Use a secure connection to the database (e.g. SSL/TLS)
* Validate user input to prevent SQL injection attacks
* Use a web application firewall (WAF) to protect against common web attacks