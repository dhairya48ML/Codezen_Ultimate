# # backend/pr_manager.py
# import os
# import subprocess
# import shutil
# import requests
# from pathlib import Path
# from datetime import datetime
# import uuid

# REPOS_DIR = Path(__file__).resolve().parent.parent / "repos"  # ./repos

# def _run(cmd, cwd=None, env=None):
#     """Run shell command, return (exit_code, stdout, stderr). Raises on error if needed."""
#     res = subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
#     return res.returncode, res.stdout.strip(), res.stderr.strip()

# def ensure_repos_dir():
#     REPOS_DIR.mkdir(parents=True, exist_ok=True)

# def clone_or_fetch(repo_clone_url, repo_owner, repo_name, install_token):
#     """
#     Clone repo into REPOS_DIR/{owner}_{name} if missing, otherwise fetch latest.
#     repo_clone_url: normal https clone url (e.g. https://github.com/owner/repo.git)
#     install_token: installation token (string) used to push
#     Returns local_path (Path)
#     """
#     ensure_repos_dir()
#     local_name = f"{repo_owner}_{repo_name}"
#     local_path = REPOS_DIR / local_name

#     # embed token for fetch/push operations when needed
#     token_clone_url = _embed_token_in_url(repo_clone_url, install_token)

#     if not local_path.exists():
#         # clone shallow so it's fast
#         code, out, err = _run(["git", "clone", "--depth", "1", token_clone_url, str(local_path)])
#         if code != 0:
#             raise RuntimeError(f"git clone failed: {err}\n{out}")
#         return local_path

#     # existing repo: ensure remotes set, fetch
#     # update origin url to token-embedded one for push
#     # but keep original remote intact for reading (we will fetch)
#     _run(["git", "remote", "set-url", "origin", token_clone_url], cwd=str(local_path))
#     code, out, err = _run(["git", "fetch", "--all"], cwd=str(local_path))
#     if code != 0:
#         raise RuntimeError(f"git fetch failed: {err}\n{out}")
#     return local_path

# # def _embed_token_in_url(clone_url, token):
# #     """
# #     Convert https://github.com/owner/repo.git -> https://x-access-token:{token}@github.com/owner/repo.git
# #     """
# #     if clone_url.startswith("https://"):
# #         return clone_url.replace("https://", f"https://x-access-token:{token}@")
# #     return clone_url

# def _embed_token_in_url(clone_url, token):
#     """
#     Use the GitHub-recommended format: https://TOKEN@github.com/owner/repo.git
#     Works on Windows, Mac, Linux.
#     """
#     if clone_url.startswith("https://"):
#         return clone_url.replace("https://", f"https://{token}@")
#     return clone_url


# def create_branch_and_commit(local_path: Path, files: list, branch_name: str, commit_message: str,
#                              author_name="CodeZen Agent", author_email="bot@codezen.ai"):
#     """
#     files: list of dicts: {"file_name": "path/inside/repo.py", "content": "..." }
#     """
#     # make sure we are on a fresh branch off default branch
#     code, default_branch, _ = _run(["git", "rev-parse", "--abbrev-ref", "origin/HEAD"], cwd=str(local_path))
#     if default_branch and default_branch.startswith("origin/"):
#         base = default_branch.replace("origin/", "")
#     else:
#         base = "main"

#     # ensure up to date
#     _run(["git", "checkout", base], cwd=str(local_path))
#     _run(["git", "reset", "--hard", f"origin/{base}"], cwd=str(local_path))

#     # create unique branch
#     short = uuid.uuid4().hex[:6]
#     final_branch = f"{branch_name}-{short}"

#     code, out, err = _run(["git", "checkout", "-b", final_branch], cwd=str(local_path))
#     if code != 0:
#         raise RuntimeError(f"git checkout failed: {err}\n{out}")

#     # -------- Write only changed files --------
#     changed = False
#     changed_files = []

#     for f in files:
#         target = local_path / f["file_name"]
#         target.parent.mkdir(parents=True, exist_ok=True)

#         old_content = ""
#         if target.exists():
#             with open(target, "r", encoding="utf-8") as fh:
#                 old_content = fh.read()

#         # Skip identical
#         if old_content.strip() == f["content"].strip():
#             print(f"⚠️ No actual changes in {f['file_name']} → skipping")
#             continue

#         # Write updated file
#         with open(target, "w", encoding="utf-8") as fh:
#             fh.write(f["content"])

#         changed = True
#         changed_files.append(f["file_name"])

#     # -------- No file changed? Stop --------
#     if not changed:
#         raise RuntimeError("No changes produced by LLM. Nothing to commit.")

#     # -------- Stage only changed files --------
#     for fname in changed_files:
#         _run(["git", "add", fname], cwd=str(local_path))

#     # -------- Commit --------
#     env = os.environ.copy()
#     env["GIT_AUTHOR_NAME"] = author_name
#     env["GIT_AUTHOR_EMAIL"] = author_email
#     env["GIT_COMMITTER_NAME"] = author_name
#     env["GIT_COMMITTER_EMAIL"] = author_email

#     code, out, err = _run(["git", "commit", "-m", commit_message], cwd=str(local_path), env=env)
#     if code != 0:
#         # nothing to commit? return branch anyway
#         if "nothing to commit" in err.lower():
#             return final_branch
#         raise RuntimeError(f"git commit failed: {err}\n{out}")

#     return final_branch


# def push_branch(local_path: Path, branch: str):
#     code, out, err = _run(["git", "push", "-u", "origin", branch], cwd=str(local_path))
#     if code != 0:
#         raise RuntimeError(f"git push failed: {err}\n{out}")
#     return True

# def create_pull_request(repo_owner, repo_name, head_branch, base_branch, title, body, install_token):
#     """
#     Use the installation token to create a PR via GitHub API.
#     Returns pr_url.
#     """
#     api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls"
#     headers = {
#         "Authorization": f"token {install_token}",
#         "Accept": "application/vnd.github+json"
#     }
#     payload = {
#         "title": title,
#         "head": head_branch,
#         "base": base_branch,
#         "body": body
#     }
#     r = requests.post(api_url, json=payload, headers=headers)
#     if r.status_code not in (200, 201):
#         raise RuntimeError(f"Create PR failed: {r.status_code} {r.text}")
#     return r.json().get("html_url")

# def create_pr_for_repo(repo_clone_url, repo_owner, repo_name, files_changes, install_token, branch_base_name=None):
#     """
#     Orchestrates: clone/fetch, create branch, commit, push, create PR.
#     files_changes: list of {file_name, content}
#     branch_base_name: str like "codezen/ai-fix-auth.py" (we'll sanitize)
#     Returns dict with pr_url and branch name.
#     """
#     ensure_repos_dir()
#     local = clone_or_fetch(repo_clone_url, repo_owner, repo_name, install_token)

#     # sanitize branch_base_name
#     if not branch_base_name:
#         branch_base_name = "codezen/ai-fix"
#     # make file-based name shorter and safe
#     # remove slashes, replace with dash
#     branch_base_name = branch_base_name.replace("/", "-").replace(" ", "-")

#     # build commit message
#     commit_message = f"AI Refactor: automated changes by CodeZen Agent ({datetime.utcnow().isoformat()}Z)"

#     # determine base branch
#     # try to read origin/HEAD mapping
#     _, origin_head, _ = _run(["git", "symbolic-ref", "refs/remotes/origin/HEAD"], cwd=str(local))
#     base_branch = "main"
#     if origin_head:
#         base_branch = os.path.basename(origin_head)

#     branch = create_branch_and_commit(local, files_changes, branch_base_name, commit_message)
#     push_branch(local, branch)

#     pr_title = "AI Refactor: Improvements suggested by CodeZen Agent"
#     pr_body = "Automated refactor proposed by CodeZen Agent. Please review the changes."

#     pr_url = create_pull_request(repo_owner, repo_name, branch, base_branch, pr_title, # backend/pr_manager.py

import os
import subprocess
import requests
from pathlib import Path
from datetime import datetime
import uuid

# ---------------------------------------------------------
# FIX: Store repos OUTSIDE backend folder (prevents reload)
# ---------------------------------------------------------
REPOS_DIR = Path(__file__).resolve().parent.parent.parent / "repos"


def _run(cmd, cwd=None, env=None):
    """Run shell command, return (code, stdout, stderr)."""
    res = subprocess.run(
        cmd, cwd=cwd, env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    return res.returncode, res.stdout.strip(), res.stderr.strip()


def ensure_repos_dir():
    REPOS_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# FIX: Correct GitHub token embed format
# ---------------------------------------------------------
def _embed_token_in_url(clone_url, token):
    """
    Correct GitHub App authentication format:
    https://x-access-token:TOKEN@github.com/owner/repo.git
    """
    clone_url = clone_url.rstrip("/")  # remove trailing slash

    if clone_url.startswith("https://"):
        return clone_url.replace(
            "https://",
            f"https://x-access-token:{token}@"
        )
    return clone_url


def clone_or_fetch(repo_clone_url, repo_owner, repo_name, install_token):
    ensure_repos_dir()
    local_path = REPOS_DIR / f"{repo_owner}_{repo_name}"

    token_clone_url = _embed_token_in_url(repo_clone_url, install_token)

    print("\n🔗 CLONE URL =", repo_clone_url)
    print("🔐 TOKEN CLONE URL =", token_clone_url[:80], "...")

    if not local_path.exists():
        print("📥 Cloning fresh repo...")
        code, out, err = _run(["git", "clone", "--depth", "1", token_clone_url, str(local_path)])
        if code != 0:
            print("❌ Clone Error:", err, out)
            raise RuntimeError(f"git clone failed: {err}\n{out}")
        return local_path

    print("🔃 Repo exists — fetching updates...")
    _run(["git", "remote", "set-url", "origin", token_clone_url], cwd=str(local_path))

    code, out, err = _run(["git", "fetch", "--all"], cwd=str(local_path))
    if code != 0:
        print("❌ Fetch Error:", err, out)
        raise RuntimeError(f"git fetch failed: {err}\n{out}")

    return local_path


def create_branch_and_commit(local_path, files, branch_base, commit_message,
                             author_name="CodeZen Agent", author_email="bot@codezen.ai"):

    # Detect main or master
    code, default_branch, _ = _run(
        ["git", "rev-parse", "--abbrev-ref", "origin/HEAD"], cwd=str(local_path)
    )

    base_branch = default_branch.replace("origin/", "") if default_branch.startswith("origin/") else "main"

    # Checkout base
    _run(["git", "checkout", base_branch], cwd=str(local_path))
    _run(["git", "reset", "--hard", f"origin/{base_branch}"], cwd=str(local_path))

    # Create unique branch
    final_branch = f"{branch_base}-{uuid.uuid4().hex[:6]}"
    code, out, err = _run(["git", "checkout", "-b", final_branch], cwd=str(local_path))
    if code != 0:
        raise RuntimeError(f"git checkout failed: {err}\n{out}")

    # Apply edits
    changed_files = []
    for f in files:
        target = local_path / f["file_name"]
        target.parent.mkdir(parents=True, exist_ok=True)

        old = target.read_text(encoding="utf-8", errors="ignore") if target.exists() else ""

        if old.strip() == f["content"].strip():
            print(f"⚠️ No change in {f['file_name']} — skipping")
            continue

        target.write_text(f["content"], encoding="utf-8")
        changed_files.append(f["file_name"])

    if not changed_files:
        raise RuntimeError("No changes produced by LLM")

    # Stage changed files
    for fname in changed_files:
        _run(["git", "add", fname], cwd=str(local_path))

    # Commit
    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"] = author_name
    env["GIT_AUTHOR_EMAIL"] = author_email
    env["GIT_COMMITTER_NAME"] = author_name
    env["GIT_COMMITTER_EMAIL"] = author_email

    code, out, err = _run(["git", "commit", "-m", commit_message], cwd=str(local_path), env=env)
    if code != 0:
        raise RuntimeError(f"git commit failed: {err}\n{out}")

    # IMPORTANT FIX: return ONLY the branch name
    return final_branch


def push_branch(local_path: Path, branch: str):
    print("\n🚀 Attempting git push...")
    print("📡 REMOTE URLS:")
    _run(["git", "remote", "-v"], cwd=str(local_path))

    code, out, err = _run(["git", "push", "-u", "origin", branch], cwd=str(local_path))

    print("📤 PUSH STDOUT:", out)
    print("📤 PUSH STDERR:", err)

    if code != 0:
        raise RuntimeError(
            f"git push failed:\nSTDOUT: {out}\nSTDERR: {err}"
        )

    print("✅ Push successful!")
    return True


def create_pull_request(repo_owner, repo_name, branch, base_branch, title, body, token):
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls"

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json"
    }

    payload = {
        "title": title,
        "head": branch,
        "base": base_branch,
        "body": body
    }

    r = requests.post(url, json=payload, headers=headers)
    if r.status_code not in (200, 201):
        raise RuntimeError(f"Create PR failed: {r.status_code} {r.text}")

    return r.json().get("html_url")


def create_pr_for_repo(repo_clone_url, repo_owner, repo_name, files_changes, install_token, branch_base_name=None):
    print("\n🧩 Starting PR Creation Flow...")
    print("🔑 INSTALL TOKEN PREFIX:", install_token[:10], "...")

    local = clone_or_fetch(repo_clone_url, repo_owner, repo_name, install_token)

    if not branch_base_name:
        branch_base_name = "codezen-ai-fix"

    branch_base_name = branch_base_name.replace("/", "-")

    commit_message = f"AI Refactor - CodeZen Agent ({datetime.utcnow().isoformat()}Z)"

    _, origin_head, _ = _run(
        ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
        cwd=str(local)
    )
    base_branch = os.path.basename(origin_head) if origin_head else "main"

    print("🪴 Base branch =", base_branch)

    branch = create_branch_and_commit(local, files_changes, branch_base_name, commit_message)
    print("🌿 Created branch =", branch)

    push_branch(local, branch)

    pr_url = create_pull_request(
        repo_owner, repo_name, branch, base_branch,
        "AI Refactor: CodeZen Agent",
        "Automated improvements by CodeZen Agent.",
        install_token
    )

    print("🔗 PR URL =", pr_url)
    return {"pr_url": pr_url, "branch": branch}
#     return {"pr_url": pr_url, "branch": branch}

