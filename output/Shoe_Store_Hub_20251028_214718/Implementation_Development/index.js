const express = require('express');
const app = express();
const port = 3000;

// Import routes
const productRoutes = require('./routes/products');
const paymentRoutes = require('./routes/payments');

// Use routes
app.use('/products', productRoutes);
app.use('/payments', paymentRoutes);

// Start server
app.listen(port, () => {
  console.log(`Server started on port ${port}`);
});