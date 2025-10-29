const Payment = require('../models/Payment');

class PaymentController {
  async createPaymentIntent(req, res) {
    try {
      const paymentIntent = await Payment.createPaymentIntent(req.body);
      res.json({ clientSecret: paymentIntent.client_secret });
    } catch (err) {
      console.error(err);
      res.status(500).json({ message: 'Error creating payment intent' });
    }
  }
}

module.exports = PaymentController;