"""
ml_models — PhishAware v2 LSTM email generation package.

Public API:
    generate_campaign_emails(campaign, num_phishing, num_legitimate)
"""

from ml_models.email_generator import generate_campaign_emails

__all__ = ['generate_campaign_emails']
