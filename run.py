import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

from dotenv import load_dotenv

# Try multiple .env locations; ignore silently if unreadable
for _env in (PROJECT_ROOT / ".env", PROJECT_ROOT / "references" / ".env"):
    try:
        if _env.exists():
            load_dotenv(_env)
            break
    except (PermissionError, OSError):
        pass

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=8080, load_dotenv=False)
