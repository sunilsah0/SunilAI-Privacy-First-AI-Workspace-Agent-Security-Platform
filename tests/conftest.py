import os

# Most tests create many users from one address, so rate limiting is off by default in tests.
# The rate-limit tests switch it on for themselves. This must run before the app is imported.
os.environ.setdefault("RATE_LIMIT_ENABLED", "0")
