const express = require('express');
const router = express.Router();
const mysql = require('mysql2/promise');

// Database connection
const db = mysql.createConnection({
  host: 'localhost',
  user: 'root',
  password: 'password',
  database: 'shoe_store_hub'
});

// Get all products
router.get('/', async (req, res) => {
  try {
    const [products] = await db.execute('SELECT * FROM products');
    res.json(products);
  } catch (err) {
    console.error(err);
    res.status(500).json({ message: 'Error fetching products' });
  }
});

// Get product by ID
router.get('/:id', async (req, res) => {
  try {
    const [product] = await db.execute('SELECT * FROM products WHERE id = ?', [req.params.id]);
    res.json(product);
  } catch (err) {
    console.error(err);
    res.status(404).json({ message: 'Product not found' });
  }
});

module.exports = router;