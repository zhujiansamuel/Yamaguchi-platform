"""
Email Parsing Workers for Data Acquisition.

This module contains workers for processing email-based order updates:
- Email Content Analysis: Parse emails and distribute to appropriate handlers
- Initial Order Confirmation Email: Process initial order confirmation emails
- Order Confirmation Notification Email: Process order confirmation notifications
- Send Notification Email: Process notification emails

All workers share Redis DB 10 and use the Purchasing model locking mechanism.
"""
