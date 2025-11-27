# from fastapi import FastAPI, Request, HTTPException, Body
# from fastapi.middleware.cors import CORSMiddleware
# from dotenv import load_dotenv
# import os, requests, json, time
# from typing import List, Optional
# from backend import github_app, llm_client, codezen_store as store
# from backend import llm_client
# from fastapi import APIRouter, Request
# from .pr_manager import create_pr_for_repo
# from urllib.parse import urlparse



# load_dotenv()
# app = FastAPI(title="CodeZen Ultimate Backend", version="1.0")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_methods=["*"],
#     allow_headers=["*"]
# )

# CODEZEN_PUBLIC_URL = os.getenv("CODEZEN_PUBLIC_URL")
# GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
# GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")

# @app.get("/")
# def home():
#     return {"message": "🚀 CodeZen Ultimate Backend Active"}

# # ---------- INIT ----------
# @app.post("/init")
# async def init_repo(data: dict = Body(...)):
#     repo_url = data.get("repo_url")
#     if not repo_url:
#         raise HTTPException(400, "Missing repo_url")

#     repo_owner = repo_url.rstrip("/").split("/")[-2]
#     repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
#     # install_link = f"https://github.com/apps/codezen-agent/installations/new"
#     install_link = f"https://github.com/apps/{github_app.GITHUB_APP_SLUG}/installations/new"
#     print(f"🔗 Generated installation link for {repo_owner}/{repo_name}")
#     return {"install_link": install_link, "repo": f"{repo_owner}/{repo_name}"}

# # ---------- GITHUB WEBHOOK ----------
# @app.post("/github/webhook")
# async def github_webhook(request: Request):
#     payload = await request.json()
#     event = request.headers.get("X-GitHub-Event")
#     action = payload.get("action")

#     print(f"📥 Webhook received: {event} action: {action}")

#     # Helper: generate token after installation
#     def generate_token_and_store(full_name: str, installation_id: int):
#         try:
#             token_data = github_app.exchange_installation_token(installation_id)
#             store.update_token(full_name, token_data["token"], token_data["expires_at"])
#             print(f"🔑 Token generated for {full_name}. Expires at {inst['expires_at']}")
#         except Exception as e:
#             print(f"❌ Failed to generate token for {full_name}: {e}")

#     # ========== INSTALLATION CREATED ==========
#     if event == "installation" and action == "created":
#         installation_id = payload["installation"]["id"]
#         repos = payload.get("repositories", [])

#         for r in repos:
#             full_name = r["full_name"]

#             # Save installation
#             store.save_installation(full_name, installation_id)
#             print(f"✅ Installation created: {full_name} → {installation_id}")

#             # Generate installation token
#             generate_token_and_store(full_name, installation_id)

#         return {"message": "installation created stored"}

#     # ========== INSTALLATION PERMISSIONS ACCEPTED ==========
#     if event == "installation" and action == "new_permissions_accepted":
#         installation_id = payload["installation"]["id"]
#         repos = payload.get("repositories", [])

#         for r in repos:
#             full_name = r["full_name"]

#             store.save_installation(full_name, installation_id)
#             print(f"🎯 Permissions accepted: {full_name} → {installation_id}")

#             generate_token_and_store(full_name, installation_id)

#         return {"message": "installation permissions accepted stored"}

#     # ========== REPO ADDED TO EXISTING INSTALLATION ==========
#     if event == "installation_repositories" and action == "added":
#         installation_id = payload["installation"]["id"]
#         repos = payload.get("repositories_added", [])

#         for r in repos:
#             full_name = r["full_name"]

#             store.save_installation(full_name, installation_id)
#             print(f"➕ Repo added to installation: {full_name} → {installation_id}")

#             generate_token_and_store(full_name, installation_id)

#         return {"message": "repositories added stored"}

#     # ========== REPO REMOVED FROM INSTALLATION ==========
#     if event == "installation_repositories" and action == "removed":
#         repos = payload.get("repositories_removed", [])
#         for r in repos:
#             full_name = r["full_name"]
#             print(f"➖ Repo removed from installation: {full_name}")
#         return {"message": "repositories removed"}

#     # ========== PULL REQUEST MERGED ==========
#     if event == "pull_request" and action == "closed":
#         if payload["pull_request"]["merged"]:
#             repo = payload["repository"]["full_name"]
#             store.update_pr_status(repo, {"merged": True})
#             print(f"🔔 PR merged for {repo}")

#     return {"message": "ok"}


# @app.post("/oauth/callback")
# async def oauth_callback(payload: dict):
#     installation_id = payload.get("installation_id")
#     repo = payload.get("repository")
#     if not installation_id or not repo:
#         raise HTTPException(400, "Missing installation_id or repo")

#     # 1. Save installation ID
#     store.save_installation(repo, installation_id)

#     # 2. Generate installation token
#     token_data = github_app.exchange_installation_token(installation_id)

#     # 3. Save token into store
#     inst = store.get_installation(repo)
#     inst["token"] = token_data["token"]
#     inst["expires_at"] = token_data["expires_at"]

#     print(f"✅ Installation stored for {repo}")
#     return {"ok": True, "repo": repo}


# # ---------- ANALYZE ----------
# @app.post("/analyze")
# async def analyze(data: dict = Body(...)):
#     repo_url = data.get("repo_url")
#     files = data.get("files", [])
#     if not files:
#         raise HTTPException(400, "No files provided")

#     print(f"🧩 Analyzing {len(files)} files from {repo_url}")
#     analysis = llm_client.analyze_files(files)
#     return {"analysis": analysis}


# # # ---------- STATUS ----------
# # @app.get("/status")
# # async def get_status(repo: str):
# #     status = store.get_pr_status(repo)
# #     return {"repo": repo, "status": status}

# @app.get("/status")
# async def status(repo: str):
#     data = store.get_installation(repo)
#     if not data:
#         return {"repo": repo, "status": {"status": "unknown"}}
#     return {"repo": repo, "status": data}

# @app.post("/apply-fixes")
# async def apply_fixes(payload: dict):
#     try:
#         repo_url = payload["repo_url"]
#         approved = payload["approved"]   # list of {file_name, comment}

#         # fetch installation token
#         owner = repo_url.rstrip("/").split("/")[-2]
#         name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
#         repo_full = f"{owner}/{name}"
#         inst = store.get_installation(repo_full)

#         if not inst:
#             return {"ok": False, "error": "No installation found for this repo"}

#         token = inst["token"]

#         # ---------- LLM APPLY FIXES ----------
#         updated = llm_client.apply_refactors(approved)
#         files_out = updated.get("updated_files", [])

#         if not files_out:
#             return {"ok": False, "error": "LLM returned no updates"}

#         # ---------- CREATE PR ----------
#         result = create_pr_for_repo(
#             repo_url,
#             owner,
#             name,
#             files_out,
#             token,
#             branch_base_name="codezen/ai-fix"
#         )

#         return {
#             "ok": True,
#             "pr_url": result["pr_url"],
#             "branch": result["branch"]
#         }

#     except Exception as e:
#         return {"ok": False, "error": str(e)}


# @app.get("/get-token")
# async def get_token(repo: str):
#     """
#     Return a fresh GitHub Installation Access Token for the given repo (owner/repo).
#     """
#     inst = store.get_installation(repo)

#     if not inst:
#         raise HTTPException(status_code=404, detail="No installation found for this repo")

#     installation_id = inst.get("installation_id")
#     if not installation_id:
#         raise HTTPException(status_code=400, detail="Installation ID missing")

#     # Call GitHub to generate a token
#     token_data = github_app.exchange_installation_token(installation_id)

#     # Save token in store
#     inst["token"] = token_data["token"]
#     inst["expires_at"] = token_data["expires_at"]

#     return token_data

# def generate_token_and_store(full_name: str, installation_id: int):
#     try:
#         token_data = github_app.exchange_installation_token(installation_id)

#         # Save token persistently
#         store.update_token(
#             full_name,
#             token_data["token"],
#             token_data["expires_at"]
#         )

#         print(
#             f"🔑 Token generated for {full_name}. Expires at {token_data['expires_at']}"
#         )

#     except Exception as e:
#         print(f"❌ Failed to generate token for {full_name}: {e}")

# # backend/main.py
# from dotenv import load_dotenv
# load_dotenv()

# from fastapi import FastAPI, Request, HTTPException, Body
# from fastapi.middleware.cors import CORSMiddleware
# from dotenv import load_dotenv
# import os, requests, json, time
# from typing import List, Optional
# from backend import github_app, llm_client, codezen_store as store
# from fastapi import APIRouter
# from .pr_manager import create_pr_for_repo
# from urllib.parse import urlparse

# from pathlib import Path



# env_path = Path(__file__).resolve().parent / ".env"
# load_dotenv(dotenv_path=env_path)

# print("DEBUG: LOADED ENV FROM =", env_path)

# app = FastAPI(title="CodeZen Ultimate Backend", version="1.0")

# print("DEBUG: PRIVATE KEY PATH =", os.getenv("GITHUB_PRIVATE_KEY_PATH"))

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_methods=["*"],
#     allow_headers=["*"]
# )

# CODEZEN_PUBLIC_URL = os.getenv("CODEZEN_PUBLIC_URL")
# GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
# GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")


# @app.get("/")
# def home():
#     return {"message": "🚀 CodeZen Ultimate Backend Active"}


# # ---------- INIT ----------
# @app.post("/init")
# async def init_repo(data: dict = Body(...)):
#     repo_url = data.get("repo_url")
#     if not repo_url:
#         raise HTTPException(400, "Missing repo_url")

#     repo_owner = repo_url.rstrip("/").split("/")[-2]
#     repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
#     install_link = f"https://github.com/apps/{github_app.GITHUB_APP_SLUG}/installations/new"
#     print(f"🔗 Generated installation link for {repo_owner}/{repo_name}")
#     return {"install_link": install_link, "repo": f"{repo_owner}/{repo_name}"}


# # ---------- TOKEN GENERATION HELPER (module-level) ----------
# def generate_token_and_store(full_name: str, installation_id: int):
#     """
#     Exchange installation id for an installation access token and persist it.
#     Uses store.update_token(repo_full, token, expires_at).
#     """
#     try:
#         token_data = github_app.exchange_installation_token(installation_id)
#         # Persist token using store helper
#         store.update_token(full_name, token_data["token"], token_data.get("expires_at"))
#         print(f"🔑 Token generated for {full_name}. Expires at {token_data.get('expires_at')}")
#         return True
#     except Exception as e:
#         print(f"❌ Failed to generate token for {full_name}: {e}")
#         return False


# # ---------- GITHUB WEBHOOK ----------
# @app.post("/github/webhook")
# async def github_webhook(request: Request):
#     payload = await request.json()
#     event = request.headers.get("X-GitHub-Event")
#     action = payload.get("action")

#     print(f"📥 Webhook received: {event} action: {action}")

#     # ========== INSTALLATION CREATED ==========
#     if event == "installation" and action == "created":
#         installation_id = payload["installation"]["id"]
#         repos = payload.get("repositories", [])

#         for r in repos:
#             full_name = r["full_name"]
#             # Save installation id persistently
#             store.save_installation(full_name, installation_id)
#             print(f"✅ Installation created: {full_name} → {installation_id}")

#             # Generate and persist token
#             generate_token_and_store(full_name, installation_id)

#         return {"message": "installation created stored"}

#     # ========== INSTALLATION PERMISSIONS ACCEPTED ==========
#     if event == "installation" and action == "new_permissions_accepted":
#         installation_id = payload["installation"]["id"]
#         repos = payload.get("repositories", [])
#         for r in repos:
#             full_name = r["full_name"]
#             store.save_installation(full_name, installation_id)
#             print(f"🎯 Permissions accepted: {full_name} → {installation_id}")
#             generate_token_and_store(full_name, installation_id)
#         return {"message": "installation permissions accepted stored"}

#     # ========== REPO ADDED TO EXISTING INSTALLATION ==========
#     if event == "installation_repositories" and action == "added":
#         installation_id = payload["installation"]["id"]
#         repos = payload.get("repositories_added", [])
#         for r in repos:
#             full_name = r["full_name"]
#             store.save_installation(full_name, installation_id)
#             print(f"➕ Repo added to installation: {full_name} → {installation_id}")
#             generate_token_and_store(full_name, installation_id)
#         return {"message": "repositories added stored"}

#     # ========== REPO REMOVED FROM INSTALLATION ==========
#     if event == "installation_repositories" and action == "removed":
#         repos = payload.get("repositories_removed", [])
#         for r in repos:
#             full_name = r["full_name"]
#             # remove from INSTALLATIONS if you want — currently we just log
#             print(f"➖ Repo removed from installation: {full_name}")
#         return {"message": "repositories removed"}

#     # ========== PULL REQUEST MERGED ==========
#     if event == "pull_request" and action == "closed":
#         if payload["pull_request"]["merged"]:
#             repo = payload["repository"]["full_name"]
#             store.update_pr_status(repo, {"merged": True})
#             print(f"🔔 PR merged for {repo}")

#     return {"message": "ok"}


# # ---------- OAUTH CALLBACK (optional) ----------
# @app.post("/oauth/callback")
# async def oauth_callback(payload: dict):
#     installation_id = payload.get("installation_id")
#     repo = payload.get("repository")
#     if not installation_id or not repo:
#         raise HTTPException(400, "Missing installation_id or repo")

#     # 1. Save installation ID (persistently)
#     store.save_installation(repo, installation_id)

#     # 2. Generate installation token
#     token_data = github_app.exchange_installation_token(installation_id)

#     # 3. Save token into store (use update_token helper)
#     store.update_token(repo, token_data["token"], token_data.get("expires_at"))

#     print(f"✅ Installation stored for {repo}")
#     return {"ok": True, "repo": repo}


# # ---------- ANALYZE ----------
# @app.post("/analyze")
# async def analyze(data: dict = Body(...)):
#     repo_url = data.get("repo_url")
#     files = data.get("files", [])
#     if not files:
#         raise HTTPException(400, "No files provided")

#     print(f"🧩 Analyzing {len(files)} files from {repo_url}")
#     analysis = llm_client.analyze_files(files)
#     return {"analysis": analysis}


# # ---------- STATUS ----------
# @app.get("/status")
# async def status(repo: str):
#     data = store.get_installation(repo)
#     if not data:
#         return {"repo": repo, "status": {"status": "unknown"}}
#     return {"repo": repo, "status": data}


# # ---------- APPLY FIXES ----------
# @app.post("/apply-fixes")
# async def apply_fixes(payload: dict):
#     try:
#         repo_url = payload["repo_url"]
#         approved = payload["approved"]   # list of {file_name, comment}

#         # parse owner/name
#         owner = repo_url.rstrip("/").split("/")[-2]
#         name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
#         repo_full = f"{owner}/{name}"
#         inst = store.get_installation(repo_full)

#         if not inst:
#             return {"ok": False, "error": "No installation found for this repo"}

#         token = inst.get("token")
#         if not token:
#             # attempt to generate a fresh token if missing
#             installation_id = inst.get("installation_id")
#             if not installation_id:
#                 return {"ok": False, "error": "Installation ID missing"}
#             ok = generate_token_and_store(repo_full, installation_id)
#             if not ok:
#                 return {"ok": False, "error": "Failed to generate installation token"}
#             inst = store.get_installation(repo_full)
#             token = inst.get("token")

#         # ---------- LLM APPLY FIXES ----------
#         updated = llm_client.apply_refactors(approved)
#         files_out = updated.get("updated_files", [])

#         if not files_out:
#             return {"ok": False, "error": "LLM returned no updates"}

#         # ---------- CREATE PR ----------
#         result = create_pr_for_repo(
#             repo_url,
#             owner,
#             name,
#             files_out,
#             token,
#             branch_base_name="codezen/ai-fix"
#         )

#         return {
#             "ok": True,
#             "pr_url": result["pr_url"],
#             "branch": result["branch"]
#         }

#     except Exception as e:
#         return {"ok": False, "error": str(e)}


# # ---------- GET TOKEN (manual refresh) ----------
# @app.get("/get-token")
# async def get_token(repo: str):
#     """
#     Return a fresh GitHub Installation Access Token for the given repo (owner/repo).
#     """
#     inst = store.get_installation(repo)

#     if not inst:
#         raise HTTPException(status_code=404, detail="No installation found for this repo")

#     installation_id = inst.get("installation_id")
#     if not installation_id:
#         raise HTTPException(status_code=400, detail="Installation ID missing")

#     # Call GitHub to generate a token
#     token_data = github_app.exchange_installation_token(installation_id)

#     # Save token in store
#     store.update_token(repo, token_data["token"], token_data.get("expires_at"))

#     return token_data

# backend/main.py

# ------------------------------------------------------
# 1) LOAD .env BEFORE importing github_app or anything else
# ------------------------------------------------------
from dotenv import load_dotenv
import os
from pathlib import Path

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

print("DEBUG: LOADED ENV FROM =", env_path)
print("DEBUG: PRIVATE KEY PATH =", os.getenv("GITHUB_PRIVATE_KEY_PATH"))
print("DEBUG: GITHUB_APP_ID =", os.getenv("GITHUB_APP_ID"))

# ------------------------------------------------------
# 2) NOW safe to import all backend modules
# ------------------------------------------------------
from fastapi import FastAPI, Request, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
import requests, json, time
from typing import List, Optional

from backend import github_app, llm_client, codezen_store as store
from .pr_manager import create_pr_for_repo
from urllib.parse import urlparse

# ------------------------------------------------------
# FASTAPI APP INIT
# ------------------------------------------------------
app = FastAPI(title="CodeZen Ultimate Backend", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

CODEZEN_PUBLIC_URL = os.getenv("CODEZEN_PUBLIC_URL")
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")


@app.get("/")
def home():
    return {"message": "🚀 CodeZen Ultimate Backend Active"}


def generate_token_and_store(full_name: str, installation_id: int):
    try:
        token_data = github_app.exchange_installation_token(installation_id)
        store.update_token(full_name, token_data["token"], token_data.get("expires_at"))
        print(f"🔑 Token generated for {full_name}. Expires at {token_data.get('expires_at')}")
        return True
    except Exception as e:
        print(f"❌ Failed to generate token for {full_name}: {e}")
        return False


# # ------------------------------------------------------
# # INIT REPO
# # ------------------------------------------------------
# @app.post("/init")
# async def init_repo(data: dict = Body(...)):
#     repo_url = data.get("repo_url")
#     if not repo_url:
#         raise HTTPException(400, "Missing repo_url")

#     repo_owner = repo_url.rstrip("/").split("/")[-2]
#     repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")

#     install_link = f"https://github.com/apps/{github_app.GITHUB_APP_SLUG}/installations/new"

#     print(f"🔗 Generated installation link for {repo_owner}/{repo_name}")

#     return {"install_link": install_link, "repo": f"{repo_owner}/{repo_name}"}
# @app.post("/init")
# async def init_repo(data: dict = Body(...)):
#     repo_url = data.get("repo_url")
#     if not repo_url:
#         raise HTTPException(400, "Missing repo_url")

#     repo_owner = repo_url.rstrip("/").split("/")[-2]
#     repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")

#     # ---- Force installation into YOUR GitHub account ----
#     INSTALL_TARGET_ID = "201926241"  # <-- Your GitHub numerical ID

#     install_link = (
#         f"https://github.com/apps/{github_app.GITHUB_APP_SLUG}"
#         f"/installations/new/permissions?target_id={INSTALL_TARGET_ID}"
#     )

#     print(f"🔗 Generated installation link for {repo_owner}/{repo_name}")

#     return {"install_link": install_link, "repo": f"{repo_owner}/{repo_name}"}

@app.post("/init")
async def init_repo(data: dict = Body(...)):
    repo_url = data.get("repo_url")
    if not repo_url:
        raise HTTPException(400, "Missing repo_url")

    # extract owner + repo name
    repo_owner = repo_url.rstrip("/").split("/")[-2]
    repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")

    # Installation link (NO target_id)
    install_link = f"https://github.com/apps/{github_app.GITHUB_APP_SLUG}/installations/new"

    print(f"🔗 Generated installation link for {repo_owner}/{repo_name}")

    return {
        "install_link": install_link,
        "repo": f"{repo_owner}/{repo_name}"
    }


# ------------------------------------------------------
# WEBHOOKS
# ------------------------------------------------------
@app.post("/github/webhook")
async def github_webhook(request: Request):
    payload = await request.json()
    event = request.headers.get("X-GitHub-Event")
    action = payload.get("action")

    print(f"📥 Webhook received: {event} action: {action}")

    # INSTALLATION CREATED
    if event == "installation" and action == "created":
        installation_id = payload["installation"]["id"]
        repos = payload.get("repositories", [])

        for r in repos:
            full_name = r["full_name"]
            store.save_installation(full_name, installation_id)
            print(f"✅ Installation created: {full_name} → {installation_id}")
            generate_token_and_store(full_name, installation_id)

        return {"message": "installation created stored"}

    # PERMISSION ACCEPTED
    if event == "installation" and action == "new_permissions_accepted":
        installation_id = payload["installation"]["id"]
        repos = payload.get("repositories", [])

        for r in repos:
            full_name = r["full_name"]
            store.save_installation(full_name, installation_id)
            print(f"🎯 Permissions accepted: {full_name} → {installation_id}")
            generate_token_and_store(full_name, installation_id)

        return {"message": "permissions updated"}

    # REPOSITORY ADDED
    if event == "installation_repositories" and action == "added":
        installation_id = payload["installation"]["id"]
        repos = payload.get("repositories_added", [])

        for r in repos:
            full_name = r["full_name"]
            store.save_installation(full_name, installation_id)
            print(f"➕ Repo added: {full_name} → {installation_id}")
            generate_token_and_store(full_name, installation_id)

        return {"message": "repository added"}

    return {"message": "ok"}


# ------------------------------------------------------
# ANALYZE
# ------------------------------------------------------
@app.post("/analyze")
async def analyze(data: dict = Body(...)):
    files = data.get("files", [])
    if not files:
        raise HTTPException(400, "No files provided")

    print(f"🧩 Analyzing {len(files)} files")
    analysis = llm_client.analyze_files(files)
    return {"analysis": analysis}


# ------------------------------------------------------
# STATUS
# ------------------------------------------------------
@app.get("/status")
async def status(repo: str):
    data = store.get_installation(repo)
    if not data:
        return {"repo": repo, "status": {"status": "unknown"}}

    return {"repo": repo, "status": data}


# # ------------------------------------------------------
# # APPLY FIXES → CREATE PR
# # ------------------------------------------------------
# @app.post("/apply-fixes")
# async def apply_fixes(payload: dict):
#     try:
#         repo_url = payload["repo_url"]
#         approved = payload["approved"]

#         owner = repo_url.rstrip("/").split("/")[-2]
#         name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
#         repo_full = f"{owner}/{name}"

#         inst = store.get_installation(repo_full)
#         if not inst:
#             return {"ok": False, "error": "No installation found"}

#         token = inst.get("token")

#         # Token missing? regenerate
#         if not token:
#             installation_id = inst.get("installation_id")
#             if not installation_id:
#                 return {"ok": False, "error": "Installation ID missing"}

#             if not generate_token_and_store(repo_full, installation_id):
#                 return {"ok": False, "error": "Failed to generate installation token"}

#             inst = store.get_installation(repo_full)
#             token = inst.get("token")

#         # LLM refactor
#         updated = llm_client.apply_refactors(approved)
#         files_out = updated.get("updated_files", [])

#         if not files_out:
#             return {"ok": False, "error": "LLM returned no updates"}

#         result = create_pr_for_repo(
#             repo_url,
#             owner,
#             name,
#             files_out,
#             token,
#             branch_base_name="codezen/ai-fix"
#         )

#         return {"ok": True, "pr_url": result["pr_url"], "branch": result["branch"]}

#     except Exception as e:
#         return {"ok": False, "error": str(e)}

@app.post("/apply-fixes")
async def apply_fixes(payload: dict):
    try:
        repo_url = payload["repo_url"]
        approved = payload["approved"]  # list of files

        owner = repo_url.rstrip("/").split("/")[-2]
        name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
        repo_full = f"{owner}/{name}"

        inst = store.get_installation(repo_full)
        if not inst:
            return {"ok": False, "error": "No installation found"}

        token = inst.get("token")

        # If token missing → regenerate
        if not token:
            installation_id = inst.get("installation_id")
            if not installation_id:
                return {"ok": False, "error": "Installation ID missing"}

            if not generate_token_and_store(repo_full, installation_id):
                return {"ok": False, "error": "Failed to generate installation token"}

            inst = store.get_installation(repo_full)
            token = inst.get("token")

        # ---- Build changes for LLM ----
        llm_changes = []
        use_original_only = False

        for f in approved:
            if f.get("use_original"):
                # Developer pressed N → skip LLM
                use_original_only = True

            llm_changes.append({
                "file_name": f["file_name"],
                "old_content": f["old_content"],
                "refactors": f.get("refactors", [])
            })

        # ---- If developer pressed NO → push original code ----
        if use_original_only:
            final_files = [
                {"file_name": c["file_name"], "content": c["old_content"]}
                for c in llm_changes
            ]
        else:
            # ---- LLM refactor ----
            updated = llm_client.apply_refactors(llm_changes)
            final_files = updated.get("updated_files", [])

        if not final_files:
            return {"ok": False, "error": "No updates produced"}

        # ---- Create PR ----
        result = create_pr_for_repo(
            repo_url,
            owner,
            name,
            final_files,
            token,
            branch_base_name="codezen/ai-fix"
        )

        return {"ok": True, "pr_url": result["pr_url"], "branch": result["branch"]}

    except Exception as e:
        return {"ok": False, "error": str(e)}



# ------------------------------------------------------
# MANUAL TOKEN REFRESH
# ------------------------------------------------------
@app.get("/get-token")
async def get_token(repo: str):
    inst = store.get_installation(repo)

    if not inst:
        raise HTTPException(404, "No installation found")

    installation_id = inst.get("installation_id")
    if not installation_id:
        raise HTTPException(400, "Installation ID missing")

    token_data = github_app.exchange_installation_token(installation_id)
    store.update_token(repo, token_data["token"], token_data.get("expires_at"))

    return token_data
