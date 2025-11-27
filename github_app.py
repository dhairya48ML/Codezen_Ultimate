# import os, time, base64, jwt, requests
# from pathlib import Path
# from typing import Dict, Any
# from dotenv import load_dotenv
# from . import codezen_store as store

# import os

# GITHUB_APP_ID = os.environ.get("GITHUB_APP_ID")
# GITHUB_PRIVATE_KEY_PATH = os.environ.get("GITHUB_PRIVATE_KEY_PATH")


# GITHUB_APP_SLUG = "codezenultimate"
# print("Loaded GitHub App:", GITHUB_APP_SLUG)


# def _create_jwt() -> str:
#     """Create JWT for GitHub App."""
#     now = int(time.time())
#     private_key = Path(GITHUB_PRIVATE_KEY_PATH).read_text()
#     payload = {"iat": now - 60, "exp": now + (9 * 60), "iss": GITHUB_APP_ID}
#     return jwt.encode(payload, private_key, algorithm="RS256")

# def exchange_installation_token(installation_id: int) -> Dict[str, Any]:
#     """Exchange app JWT for an installation token."""
#     jwt_token = _create_jwt()
#     url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
#     headers = {"Authorization": f"Bearer {jwt_token}", "Accept": "application/vnd.github+json"}
#     r = requests.post(url, headers=headers)
#     r.raise_for_status()
#     return r.json()

# def create_branch_and_pr(owner, repo, base_branch, new_branch, files, token) -> Dict[str, Any]:
#     """Create branch, commit files, and open PR."""
#     headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
#     base_ref = f"https://api.github.com/repos/{owner}/{repo}/git/ref/heads/{base_branch}"
#     ref_resp = requests.get(base_ref, headers=headers)
#     base_sha = ref_resp.json()["object"]["sha"]

#     # create branch
#     branch_ref = f"refs/heads/{new_branch}"
#     requests.post(f"https://api.github.com/repos/{owner}/{repo}/git/refs",
#                   headers=headers, json={"ref": branch_ref, "sha": base_sha})

#     # commit files
#     for f in files:
#         encoded = base64.b64encode(f["content"].encode()).decode()
#         put = requests.put(f"https://api.github.com/repos/{owner}/{repo}/contents/{f['file_name']}",
#                            headers=headers,
#                            json={"message": f"AI Refactor: {f['file_name']}",
#                                  "content": encoded,
#                                  "branch": new_branch})
#         if put.status_code not in [200, 201]:
#             print(f"⚠️ Commit failed for {f['file_name']}: {put.text}")

#     # create PR
#     pr_payload = {"title": "AI Refactor - CodeZen Agent",
#                   "head": new_branch, "base": base_branch,
#                   "body": "Automated refactor by CodeZen AI Agent."}
#     pr = requests.post(f"https://api.github.com/repos/{owner}/{repo}/pulls",
#                        headers=headers, json=pr_payload)
#     if pr.status_code in [200, 201]:
#         pr_data = pr.json()
#         store.update_pr_status(f"{owner}/{repo}",
#                                {"last_pr": pr_data["html_url"],
#                                 "status": "created",
#                                 "merged": False})
#         return pr_data
#     else:
#         raise Exception(f"Failed to create PR: {pr.text}")

# # backend/github_app.py
# import os, time, base64, jwt, requests
# from pathlib import Path
# from typing import Dict, Any
# from . import codezen_store as store

# # ❌ REMOVE load_dotenv() – main.py already loads it
# # load_dotenv()

# # ✅ Correct: read from environment AFTER main.py loads .env
# GITHUB_APP_ID = os.environ.get("GITHUB_APP_ID")
# GITHUB_PRIVATE_KEY_PATH = os.environ.get("GITHUB_PRIVATE_KEY_PATH")
# GITHUB_APP_SLUG = "codezenultimate"

# print("DEBUG GITHUB_APP_ID =", GITHUB_APP_ID)
# print("DEBUG PRIVATE KEY PATH =", GITHUB_PRIVATE_KEY_PATH)

# def _create_jwt() -> str:
#     now = int(time.time())
#     private_key = Path(GITHUB_PRIVATE_KEY_PATH).read_text()
#     payload = {"iat": now - 60, "exp": now + (9 * 60), "iss": GITHUB_APP_ID}
#     return jwt.encode(payload, private_key, algorithm="RS256")

# def exchange_installation_token(installation_id: int) -> Dict[str, Any]:
#     jwt_token = _create_jwt()
#     url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
#     headers = {"Authorization": f"Bearer {jwt_token}", "Accept": "application/vnd.github+json"}
#     r = requests.post(url, headers=headers)
#     r.raise_for_status()
#     return r.json()

# backend/github_app.py
import os, time, base64, jwt, requests
from pathlib import Path
from typing import Dict, Any
from . import codezen_store as store

# ------------------------------
# Load env values (already loaded in main.py)
# ------------------------------
GITHUB_APP_ID = os.environ.get("GITHUB_APP_ID")
GITHUB_PRIVATE_KEY_PATH = os.environ.get("GITHUB_PRIVATE_KEY_PATH")
GITHUB_APP_SLUG = "codezenultimate"

# Convert to absolute path (IMPORTANT FIX)
if GITHUB_PRIVATE_KEY_PATH:
    GITHUB_PRIVATE_KEY_PATH = (
        Path(__file__).resolve().parent.parent / GITHUB_PRIVATE_KEY_PATH
        if not os.path.isabs(GITHUB_PRIVATE_KEY_PATH)
        else Path(GITHUB_PRIVATE_KEY_PATH)
    )

print("DEBUG GITHUB_APP_ID =", GITHUB_APP_ID)
print("DEBUG PRIVATE KEY PATH =", GITHUB_PRIVATE_KEY_PATH)


def _create_jwt() -> str:
    """Create signed JWT for GitHub App authentication."""
    now = int(time.time())

    if not GITHUB_PRIVATE_KEY_PATH or not GITHUB_PRIVATE_KEY_PATH.exists():
        raise RuntimeError(f"❌ PRIVATE KEY NOT FOUND at {GITHUB_PRIVATE_KEY_PATH}")

    private_key = GITHUB_PRIVATE_KEY_PATH.read_text()

    payload = {
        "iat": now - 60,
        "exp": now + (9 * 60),
        "iss": GITHUB_APP_ID,
    }

    return jwt.encode(payload, private_key, algorithm="RS256")


def exchange_installation_token(installation_id: int) -> Dict[str, Any]:
    """Exchange JWT for installation access token."""
    jwt_token = _create_jwt()

    url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github+json",
    }

    r = requests.post(url, headers=headers)
    r.raise_for_status()
    return r.json()

