const express = require('express');
const router = express.Router();
const stripe = require('stripe')('sk_test_1234567890');

// Create payment intent
router.post('/', async (req, res) => {
  try {
    const paymentIntent = await stripe.paymentIntents.create({
      amount: req.body.amount,
      currency: 'usd',
      payment_method_types: ['card']
    });
    res.json({ clientSecret: paymentIntent.client_secret });
  } catch (err) {
    console.error(err);
    res.status(500).json({ message: 'Error creating payment intent' });
  }
});

module.exports = router;