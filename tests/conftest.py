import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("QDRANT_URL", "http://localhost:6333")
os.environ.setdefault("ADMIN_USERNAME", "admin")
os.environ.setdefault("ADMIN_PASSWORD", "test-password")
os.environ.setdefault("JWT_SECRET", "test-secret")
