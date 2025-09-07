/* eslint-env node */
const express = require('express');
const nodemailer = require('nodemailer');
const sgMail = require('@sendgrid/mail');
const AWS = require('aws-sdk');
const winston = require('winston');

const router = express.Router();

// Setup logger
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [new winston.transports.Console()],
});

// Initialize email providers
if (process.env.SENDGRID_API_KEY) {
  sgMail.setApiKey(process.env.SENDGRID_API_KEY);
}

let sesClient;
if (process.env.AWS_ACCESS_KEY_ID && process.env.AWS_SECRET_ACCESS_KEY) {
  AWS.config.update({
    region: process.env.AWS_REGION || 'us-east-1',
    accessKeyId: process.env.AWS_ACCESS_KEY_ID,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
  });
  sesClient = new AWS.SES();
}

// SMTP transporter
let smtpTransporter;
if (process.env.SMTP_HOST) {
  smtpTransporter = nodemailer.createTransporter({
    host: process.env.SMTP_HOST,
    port: process.env.SMTP_PORT || 587,
    secure: process.env.SMTP_PORT === '465',
    auth: {
      user: process.env.SMTP_USER,
      pass: process.env.SMTP_PASS,
    },
  });
}

// Send email endpoint
router.post('/send', async (req, res) => {
  try {
    const { to, subject, text, html, provider = 'auto' } = req.body;

    if (!to || !subject || (!text && !html)) {
      return res.status(400).json({
        error: 'Missing required fields: to, subject, and text/html',
      });
    }

    const emailData = {
      to,
      subject,
      text,
      html,
      from: process.env.FROM_EMAIL || 'noreply@aivo.ai',
    };

    let result;
    switch (provider) {
      case 'sendgrid':
        result = await sendViaSendGrid(emailData);
        break;
      case 'ses':
        result = await sendViaSES(emailData);
        break;
      case 'smtp':
        result = await sendViaSMTP(emailData);
        break;
      default:
        result = await sendEmailAuto(emailData);
    }

    logger.info('Email sent successfully', {
      to,
      subject,
      provider: result.provider,
    });
    res.status(200).json({
      success: true,
      message: 'Email sent successfully',
      provider: result.provider,
      messageId: result.messageId,
    });
  } catch (error) {
    logger.error('Email sending failed', { error: error.message });
    res.status(500).json({
      error: 'Failed to send email',
      message: error.message,
    });
  }
});

// Auto-select email provider
async function sendEmailAuto(emailData) {
  if (process.env.SENDGRID_API_KEY) {
    return await sendViaSendGrid(emailData);
  } else if (sesClient) {
    return await sendViaSES(emailData);
  } else if (smtpTransporter) {
    return await sendViaSMTP(emailData);
  } else {
    throw new Error('No email provider configured');
  }
}

// SendGrid implementation
async function sendViaSendGrid(emailData) {
  const msg = {
    to: emailData.to,
    from: emailData.from,
    subject: emailData.subject,
    text: emailData.text,
    html: emailData.html,
  };

  const result = await sgMail.send(msg);
  return {
    provider: 'sendgrid',
    messageId: result[0].headers['x-message-id'],
  };
}

// AWS SES implementation
async function sendViaSES(emailData) {
  const params = {
    Source: emailData.from,
    Destination: {
      ToAddresses: Array.isArray(emailData.to) ? emailData.to : [emailData.to],
    },
    Message: {
      Subject: { Data: emailData.subject },
      Body: {},
    },
  };

  if (emailData.text) {
    params.Message.Body.Text = { Data: emailData.text };
  }
  if (emailData.html) {
    params.Message.Body.Html = { Data: emailData.html };
  }

  const result = await sesClient.sendEmail(params).promise();
  return {
    provider: 'ses',
    messageId: result.MessageId,
  };
}

// SMTP implementation
async function sendViaSMTP(emailData) {
  const mailOptions = {
    from: emailData.from,
    to: emailData.to,
    subject: emailData.subject,
    text: emailData.text,
    html: emailData.html,
  };

  const result = await smtpTransporter.sendMail(mailOptions);
  return {
    provider: 'smtp',
    messageId: result.messageId,
  };
}

module.exports = router;
