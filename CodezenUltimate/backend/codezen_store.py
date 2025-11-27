import json
import os
from typing import Dict, Any

STORE_FILE = ""

# In-memory store (loaded on startup)
INSTALLATIONS: Dict[str, Dict[str, Any]] = {}
PR_STATUS: Dict[str, Dict[str, Any]] = {}

# ---------- INTERNAL HELPERS ----------

def _load_store():
    """Load installation info from JSON file into memory."""
    global INSTALLATIONS
    if os.path.exists(STORE_FILE):
        try:
            with open(STORE_FILE, "r") as f:
                INSTALLATIONS = json.load(f)
                print(f"📁 Loaded installations.json with {len(INSTALLATIONS)} repos.")
        except Exception as e:
            print(f"⚠️ Failed to load installations.json: {e}")
            INSTALLATIONS = {}
    else:
        INSTALLATIONS = {}

def _save_store():
    """Flush installation store to JSON file."""
    try:
        with open(STORE_FILE, "w") as f:
            json.dump(INSTALLATIONS, f, indent=2)
        print("💾 installations.json updated.")
    except Exception as e:
        print(f"❌ Failed to write installations.json: {e}")

# Call on import to load file
_load_store()


# ---------- PUBLIC STORE FUNCTIONS ----------

def save_installation(repo_full: str, installation_id: int):
    INSTALLATIONS[repo_full] = {
        "installation_id": installation_id,
        "status": "installed"
    }
    _save_store()


def get_installation(repo_full: str):
    return INSTALLATIONS.get(repo_full)


def update_token(repo_full: str, token: str, expires_at: str):
    if repo_full not in INSTALLATIONS:
        return
    INSTALLATIONS[repo_full]["token"] = token
    INSTALLATIONS[repo_full]["expires_at"] = expires_at
    _save_store()


def update_pr_status(repo_full: str, data: Dict[str, Any]):
    PR_STATUS[repo_full] = data
    # PR status not stored persistently (optional)
