const Product = require('../models/Product');

class ProductController {
  async getAllProducts(req, res) {
    try {
      const products = await Product.findAll();
      res.json(products);
    } catch (err) {
      console.error(err);
      res.status(500).json({ message: 'Error fetching products' });
    }
  }

  async getProductById(req, res) {
    try {
      const product = await Product.findById(req.params.id);
      res.json(product);
    } catch (err) {
      console.error(err);
      res.status(404).json({ message: 'Product not found' });
    }
  }
}

module.exports = ProductController;