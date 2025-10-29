const mysql = require('mysql2/promise');

const db = mysql.createConnection({
  host: 'localhost',
  user: 'root',
  password: 'password',
  database: 'shoe_store_hub'
});

module.exports = db;