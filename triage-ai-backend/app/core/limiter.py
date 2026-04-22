from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200/day", "50/hour"],
)

ASSESS_LIMIT   = "30/hour"
AUTH_LIMIT     = "10/minute"
UPLOAD_LIMIT   = "20/hour"
QUESTIONS_LIMIT = "120/hour"
ANALYTICS_LIMIT = "60/hour"
