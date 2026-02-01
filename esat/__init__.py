"""
ESAT - Email Security Assessment Tool
A modular tool for email security testing and blue team training.
"""

__version__ = "1.0.0"
__author__ = "ESAT Team"
__license__ = "MIT"

# Import main classes from modules
from .template_manager import TemplateManager
from .smtp_manager import SMTPManager, SMTPAuthType, SMTPEncryption
from .report_generator import ReportGenerator
from .rate_limiter import RateLimiterManager, TokenBucket, AdaptiveRateLimiter, TimeWindowLimiter
from .scheduler import CampaignScheduler, SchedulerCLI, ScheduleStatus

__all__ = [
    'TemplateManager',
    'SMTPManager',
    'SMTPAuthType',
    'SMTPEncryption',
    'ReportGenerator',
    'RateLimiterManager',
    'TokenBucket',
    'AdaptiveRateLimiter',
    'TimeWindowLimiter',
    'CampaignScheduler',
    'SchedulerCLI',
    'ScheduleStatus'
]
