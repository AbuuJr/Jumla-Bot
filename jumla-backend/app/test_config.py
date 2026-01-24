# app/test_config.py
import sys
from pathlib import Path
# --- Project root & python path (so imports work) ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from app.config import settings

print("DB URL:", settings.DATABASE_URL)
print("ENV:", settings.ENVIRONMENT)
