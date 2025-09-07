/* eslint-env node */
/**
 * Health check routes for the email service
 * @module routes/health
 */

const express = require('express');
const router = express.Router();

// Health check endpoint
router.get('/', (req, res) => {
  res.status(200).json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    service: 'email-service',
    version: '1.0.0',
    uptime: process.uptime(),
  });
});

// Detailed health check
router.get('/detailed', (req, res) => {
  const healthInfo = {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    service: 'email-service',
    version: '1.0.0',
    uptime: process.uptime(),
    memory: process.memoryUsage(),
    environment: process.env.NODE_ENV || 'development',
    providers: {
      sendgrid: process.env.SENDGRID_API_KEY ? 'configured' : 'not configured',
      ses: process.env.AWS_ACCESS_KEY_ID ? 'configured' : 'not configured',
      smtp: process.env.SMTP_HOST ? 'configured' : 'not configured',
    },
  };

  res.status(200).json(healthInfo);
});

module.exports = router;
