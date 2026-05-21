"""
Test configuration - loads .env first, then fills in stub values for any
variables still missing so that unit tests (which use TestModel) can run
without a real .env file.
"""
from dotenv import load_dotenv
load_dotenv()  # load real .env values first so they take precedence

import os
os.environ.setdefault("GEMINI_API_KEY", "test-gemini-key-placeholder")
os.environ.setdefault("USER_API_KEY", "test-user-key")
os.environ.setdefault("DEFAULT_GOOGLE_MODEL", "gemini-2.5-flash-lite")
