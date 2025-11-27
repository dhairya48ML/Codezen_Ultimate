# import os
# import sys
# import json
# import requests
# import subprocess

# BACKEND_URL = os.getenv("CODEZEN_BACKEND")  # must be set by user

# def require_backend():
#     if not BACKEND_URL:
#         print("❌ CODEZEN_BACKEND not set.")
#         print("Set it using:")
#         print('  set CODEZEN_BACKEND="https://your-ngrok-url.ngrok-free.dev"')
#         sys.exit(1)

# def cmd_init():
#     require_backend()

#     # Get git remote URL
#     try:
#         repo_url = subprocess.check_output(
#             ["git", "remote", "get-url", "origin"],
#             stderr=subprocess.STDOUT
#         ).decode().strip()
#     except:
#         print("❌ No git remote found. Initialize your repo and add origin.")
#         return

#     print(f"📦 Repo detected: {repo_url}")

#     payload = {"repo_url": repo_url}
#     r = requests.post(f"{BACKEND_URL}/init", json=payload, verify=False)

#     print(r.json())

# def cmd_analyze():
#     require_backend()

#     # Collect all files
#     tracked = subprocess.check_output(
#         ["git", "ls-files"], stderr=subprocess.STDOUT
#     ).decode().splitlines()

#     files = []
#     for path in tracked:
#         if path.endswith((".py", ".js", ".ts", ".java")):
#             with open(path, "r", encoding="utf-8") as f:
#                 files.append({"file_name": path, "content": f.read()})

#     payload = {"repo_url": "local", "files": files}
#     r = requests.post(f"{BACKEND_URL}/analyze", json=payload, verify=False)

#     print(json.dumps(r.json(), indent=2))

# def cmd_status():
#     require_backend()

#     # Read repo name
#     repo_url = subprocess.check_output(
#         ["git", "remote", "get-url", "origin"]
#     ).decode().strip()

#     owner = repo_url.rstrip("/").split("/")[-2]
#     name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
#     repo_full = f"{owner}/{name}"

#     r = requests.get(
#         f"{BACKEND_URL}/status",
#         params={"repo": repo_full},
#         verify=False
#     )
#     print(json.dumps(r.json(), indent=2))

# def main():
#     if len(sys.argv) < 2:
#         print("Usage: codezen <init|analyze|status>")
#         return

#     cmd = sys.argv[1]

#     if cmd == "init":
#         cmd_init()
#     elif cmd == "analyze":
#         cmd_analyze()
#     elif cmd == "status":
#         cmd_status()
#     else:
#         print(f"❌ Unknown command: {cmd}")

# if __name__ == "__main__":
#     main()


# import os
# import sys
# import json
# import requests
# import subprocess
# import urllib3

# # Disable SSL warnings (ngrok uses custom certs)
# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# def get_backend_url():
#     """Always read fresh env variable value."""
#     url = os.getenv("CODEZEN_BACKEND")
#     if not url:
#         print("❌ CODEZEN_BACKEND not set.")
#         print("Set it using:")
#         print('  set CODEZEN_BACKEND="https://your-ngrok-url.ngrok-free.dev"')
#         sys.exit(1)

#     # Remove accidental quotes
#     return url.strip('"').strip("'")


# def run_git_command(cmd):
#     """Safe wrapper to execute git commands."""
#     try:
#         return subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode().strip()
#     except subprocess.CalledProcessError as e:
#         print("❌ Git error:", e.output.decode())
#         sys.exit(1)


# def cmd_init():
#     backend = get_backend_url()

#     # Detect repo
#     repo_url = run_git_command(["git", "remote", "get-url", "origin"])
#     print(f"\n📦 Repo detected: {repo_url}")

#     payload = {"repo_url": repo_url}
#     r = requests.post(f"{backend}/init", json=payload, verify=False)

#     try:
#         data = r.json()
#     except:
#         print("❌ Backend returned invalid response:")
#         print(r.text)
#         return

#     install_link = data.get("install_link")
#     repo_full = data.get("repo")

#     print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
#     print(f"🚀 CodeZen  repo:  {repo_full}")
#     print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

#     # Install link (as you requested)
#     print("🔗 Install the CodeZen GitHub App to continue:")
#     print(f"   {install_link}\n")

#     # Status command
#     print("👉 To check installation status:")
#     print("   codezen status\n")


# def cmd_analyze():
#     backend = get_backend_url()

#     tracked = run_git_command(["git", "ls-files"]).splitlines()

#     files = []
#     for path in tracked:
#         if path.endswith((".py", ".js", ".ts", ".java")):
#             try:
#                 with open(path, "r", encoding="utf-8") as f:
#                     files.append({"file_name": path, "content": f.read()})
#             except Exception as e:
#                 print(f"⚠ Skipping unreadable file {path}: {e}")

#     if not files:
#         print("❌ No supported code files found")
#         sys.exit(1)

#     payload = {"repo_url": "local", "files": files}
#     r = requests.post(f"{backend}/analyze", json=payload, verify=False)
#     output = r.json()["analysis"]

#     approved = []   # store accepted suggestions

#     # ---------- DISPLAY CLEAN ANALYSIS ----------
#     for file_result in output:
#         print(f"\n📄 {file_result['file']}")

#         if file_result.get("issues"):
#             print("⚠️ Issues:")
#             for issue in file_result["issues"]:
#                 print(f"  - {issue.get('description')}")

#         if file_result.get("refactors"):
#             print("💡 Suggestions:")
#             for s in file_result["refactors"]:
#                 print(f"  - {s.get('description')}")

#             choice = input("\nApply these suggestions? (y/n): ").strip().lower()
#             if choice == "y":
#                 approved.append({
#                     "file_name": file_result["file"],
#                     # "comment": ", ".join([s["description"] for s in file_result["refactors"]])
#                     "comment": ", ".join([
#                     s.get("description", s.get("issue", "Refactor applied"))
#                     for s in file_result.get("refactors", [])
#                     ])
#                 })

#     if not approved:
#         print("\n🚫 No changes approved.")
#         return

#     repo_url = run_git_command(["git", "remote", "get-url", "origin"])

#     print("\n🚀 Sending approved changes to backend...")

#     payload = {
#         "repo_url": repo_url,
#         "approved": approved
#     }

#     r = requests.post(f"{backend}/apply-fixes", json=payload, verify=False)
#     print("\nBackend response:")
#     print(r.json())


# def cmd_status():
#     backend = get_backend_url()

#     repo_url = run_git_command(["git", "remote", "get-url", "origin"])
#     owner = repo_url.rstrip("/").split("/")[-2]
#     name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
#     full = f"{owner}/{name}"

#     r = requests.get(f"{backend}/status", params={"repo": full}, verify=False)

#     try:
#         print(json.dumps(r.json(), indent=2))
#     except:
#         print("❌ Invalid JSON response:")
#         print(r.text)


# def main():
#     if len(sys.argv) < 2:
#         print("Usage: codezen <init|analyze|status>")
#         return

#     cmd = sys.argv[1]

#     if cmd == "init":
#         cmd_init()
#     elif cmd == "analyze":
#         cmd_analyze()
#     elif cmd == "status":
#         cmd_status()
#     else:
#         print(f"❌ Unknown command: {cmd}")


# if __name__ == "__main__":
#     main()

# import os
# import sys
# import json
# import requests
# import subprocess
# import urllib3
# from pathlib import Path

# # Disable SSL warnings
# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# CLI_VERSION = "0.2.0"


# # ---------------------------------------------------------
# # Load backend URL
# # ---------------------------------------------------------
# def get_backend_url():
#     """Read backend URL from env or config file."""
#     # 1) check environment variable
#     env_url = os.getenv("CODEZEN_BACKEND")
#     if env_url:
#         return env_url.strip().strip('"').strip("'")

#     # 2) fallback to local CLI config file
#     config_path = Path.home() / ".codezen_config.json"
#     if config_path.exists():
#         try:
#             data = json.load(open(config_path))
#             if "backend" in data:
#                 return data["backend"]
#         except:
#             pass

#     print("❌ Backend URL not set.")
#     print("Set it using:")
#     print("   codezen config --backend <URL>")
#     sys.exit(1)


# # ---------------------------------------------------------
# # Save backend config
# # ---------------------------------------------------------
# def save_backend_url(url: str):
#     cfg = {"backend": url.strip()}
#     config_path = Path.home() / ".codezen_config.json"
#     json.dump(cfg, open(config_path, "w"), indent=2)
#     print(f"✅ Backend saved: {url}")


# # ---------------------------------------------------------
# # Git wrapper
# # ---------------------------------------------------------
# def run_git_command(cmd):
#     try:
#         return subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode().strip()
#     except subprocess.CalledProcessError as e:
#         print("\n❌ Git error:")
#         print(e.output.decode())
#         sys.exit(1)


# # ---------------------------------------------------------
# # Command: init
# # ---------------------------------------------------------
# def cmd_init():
#     backend = get_backend_url()

#     # Detect repo
#     repo_url = run_git_command(["git", "remote", "get-url", "origin"])
#     print(f"\n📦 Repo detected: {repo_url}")

#     payload = {"repo_url": repo_url}
#     r = requests.post(f"{backend}/init", json=payload, verify=False)

#     try:
#         data = r.json()
#     except:
#         print("❌ Backend returned invalid response:")
#         print(r.text)
#         return

#     install_link = data.get("install_link")
#     repo_full = data.get("repo")

#     print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
#     print(f"🚀 CodeZen Repository: {repo_full}")
#     print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

#     print("🔗 Install the CodeZen GitHub App:")
#     print(f"   {install_link}\n")

#     print("👉 After installation, check status:")
#     print("   codezen status\n")


# def cmd_analyze():
#     backend = get_backend_url()

#     # get tracked files
#     tracked = run_git_command(["git", "ls-files"]).splitlines()

#     files = []
#     for path in tracked:
#         if path.endswith((".py", ".js", ".ts", ".java")):
#             try:
#                 with open(path, "r", encoding="utf-8") as f:
#                     files.append({"file_name": path, "content": f.read()})
#             except Exception as e:
#                 print(f"⚠️ Skipping unreadable file {path}: {e}")

#     if not files:
#         print("❌ No supported code files found")
#         sys.exit(1)

#     # send to backend
#     payload = {"repo_url": "local", "files": files}
#     r = requests.post(f"{backend}/analyze", json=payload, verify=False)
#     data = r.json()

#     analysis = data.get("analysis", [])
#     approved = []

#     for result in analysis:
#         file_name = result["file"]

#         print(f"\n📄 {file_name}")
#         print("────────────────────────────────────────")

#         if result.get("summary"):
#             print(f"📝 Summary: {result['summary']}")

#         if result.get("issues"):
#             print("\n⚠️ Issues:")
#             for i in result["issues"]:
#                 print(f"  • {i}")

#         if result.get("refactors"):
#             print("\n💡 Suggestions:")
#             for s in result["refactors"]:
#                 print(f"  • {s}")

#         # Ask developer
#         choice = input("\nApply these suggestions? (y/n): ").strip().lower()

#         # Load full original file
#         with open(file_name, "r", encoding="utf-8") as f:
#             original_code = f.read()

#         approved.append({
#             "file_name": file_name,
#             "old_content": original_code,                # CRITICAL
#             "refactors": result.get("refactors", []),    # may be empty
#             "use_original": (choice != "y")              # true if n
#         })

#     repo_url = run_git_command(["git", "remote", "get-url", "origin"])

#     print("\n🚀 Sending approved changes to backend...")
#     r = requests.post(f"{backend}/apply-fixes", json={
#         "repo_url": repo_url,
#         "approved": approved
#     }, verify=False)

#     print("\nBackend response:")
#     print(json.dumps(r.json(), indent=2))


# # # ---------------------------------------------------------
# # # Command: analyze
# # # ---------------------------------------------------------
# # def cmd_analyze():
# #     backend = get_backend_url()

# #     tracked = run_git_command(["git", "ls-files"]).splitlines()

# #     files = []
# #     for path in tracked:
# #         if path.endswith((".py", ".js", ".ts", ".java")):
# #             try:
# #                 with open(path, "r", encoding="utf-8") as f:
# #                     files.append({"file_name": path, "content": f.read()})
# #             except Exception as e:
# #                 print(f"⚠️ Skipping unreadable file {path}: {e}")

# #     if not files:
# #         print("❌ No supported code files found (.py, .js, .ts, .java)")
# #         sys.exit(1)

# #     payload = {"repo_url": "local", "files": files}
# #     r = requests.post(f"{backend}/analyze", json=payload, verify=False)
# #     data = r.json()

# #     output = data.get("analysis", [])
# #     approved = []

# #     # -------- Pretty Analysis -------
# #     for file_result in output:
# #         print(f"\n📄 {file_result['file']}")
# #         print("────────────────────────────────────────")

# #         if file_result.get("summary"):
# #             print(f"📝 Summary: {file_result['summary']}")

# #         if file_result.get("issues"):
# #             print("\n⚠️ Issues:")
# #             for issue in file_result["issues"]:
# #                 print(f"  • {issue}")

# #         if file_result.get("refactors"):
# #             print("\n💡 Suggestions:")
# #             for s in file_result["refactors"]:
# #                 print(f"  • {s}")

# #             choice = input("\nApply these suggestions? (y/n): ").strip().lower()
# #             if choice == "y":
# #                 approved.append({
# #                     "file_name": file_result["file"],
# #                     "comment": ", ".join(file_result.get("refactors", []))
# #                 })

# #     if not approved:
# #         print("\n🚫 No changes approved.")
# #         return

# #     repo_url = run_git_command(["git", "remote", "get-url", "origin"])
# #     print("\n🚀 Sending approved changes to backend...")

# #     payload = {
# #         "repo_url": repo_url,
# #         "approved": approved
# #     }

# #     r = requests.post(f"{backend}/apply-fixes", json=payload, verify=False)
# #     print("\nBackend response:")
# #     print(json.dumps(r.json(), indent=2))


# # ---------------------------------------------------------
# # Command: status
# # ---------------------------------------------------------
# def cmd_status():
#     backend = get_backend_url()

#     repo_url = run_git_command(["git", "remote", "get-url", "origin"])
#     owner = repo_url.rstrip("/").split("/")[-2]
#     name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
#     full_name = f"{owner}/{name}"

#     r = requests.get(f"{backend}/status", params={"repo": full_name}, verify=False)

#     try:
#         print(json.dumps(r.json(), indent=2))
#     except:
#         print("❌ Invalid JSON response:")
#         print(r.text)


# # ---------------------------------------------------------
# # Command: version
# # ---------------------------------------------------------
# def cmd_version():
#     print(f"CodeZen CLI version {CLI_VERSION}")


# # ---------------------------------------------------------
# # Help menu
# # ---------------------------------------------------------
# def cmd_help():
#     print("""
# CodeZen CLI - Developer Automation Tool

# Commands:
#   codezen init                 Initialize repo & generate install link
#   codezen analyze              Analyze code & apply fixes
#   codezen status               Check installation status
#   codezen config --backend URL Set backend URL
#   codezen version              Show CLI version
#   codezen help                 Show this help menu

# Examples:
#   codezen config --backend https://abc.ngrok-free.app
#   codezen init
#   codezen analyze
# """)

# # ---------------------------------------------------------
# # Main CLI entry
# # ---------------------------------------------------------
# def main():
#     if len(sys.argv) < 2:
#         cmd_help()
#         return

#     cmd = sys.argv[1]

#     if cmd == "init":
#         cmd_init()
#     elif cmd == "analyze":
#         cmd_analyze()
#     elif cmd == "status":
#         cmd_status()
#     elif cmd == "version":
#         cmd_version()
#     elif cmd == "help":
#         cmd_help()
#     elif cmd == "config":
#         if "--backend" in sys.argv:
#             idx = sys.argv.index("--backend") + 1
#             if idx >= len(sys.argv):
#                 print("❌ Missing backend URL")
#                 return
#             save_backend_url(sys.argv[idx])
#         else:
#             print("❌ Usage: codezen config --backend <URL>")
#     else:
#         print(f"❌ Unknown command: {cmd}")
#         cmd_help()


# if __name__ == "__main__":
#     main()


import os
import sys
import json
import requests
import subprocess
import urllib3
from pathlib import Path

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

CLI_VERSION = "0.2.2"

# ---------------------------------------------------------
# Load backend URL
# ---------------------------------------------------------
def get_backend_url():
    env_url = os.getenv("CODEZEN_BACKEND")
    if env_url:
        return env_url.strip().strip('"').strip("'")

    config_path = Path.home() / ".codezen_config.json"
    if config_path.exists():
        try:
            data = json.load(open(config_path))
            if "backend" in data:
                return data["backend"]
        except:
            pass

    print("❌ Backend URL not set.")
    print("Set it using:")
    print("   codezen config --backend <URL>")
    sys.exit(1)

# ---------------------------------------------------------
# Save backend config
# ---------------------------------------------------------
def save_backend_url(url: str):
    cfg = {"backend": url.strip()}
    config_path = Path.home() / ".codezen_config.json"
    json.dump(cfg, open(config_path, "w"), indent=2)
    print(f"✅ Backend saved: {url}")

# ---------------------------------------------------------
# Git wrapper
# ---------------------------------------------------------
def run_git_command(cmd):
    try:
        return subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode().strip()
    except subprocess.CalledProcessError as e:
        print("\n❌ Git error:")
        print(e.output.decode())
        sys.exit(1)

# ---------------------------------------------------------
# Command: init
# ---------------------------------------------------------
def cmd_init():
    backend = get_backend_url()
    repo_url = run_git_command(["git", "remote", "get-url", "origin"])
    print(f"\n📦 Repo detected: {repo_url}")

    r = requests.post(f"{backend}/init", json={"repo_url": repo_url}, verify=False)

    try:
        data = r.json()
    except:
        print("❌ Backend returned invalid response:")
        print(r.text)
        return

    install_link = data.get("install_link")
    repo_full = data.get("repo")

    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"🚀 CodeZen Repository: {repo_full}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

    print("🔗 Install the CodeZen GitHub App:")
    print(f"   {install_link}\n")

    print("👉 After installation, run:")
    print("   codezen status\n")


# ---------------------------------------------------------
# Command: analyze
# ---------------------------------------------------------
def cmd_analyze():
    backend = get_backend_url()

    # tracked = run_git_command(["git", "ls-files"]).splitlines()
    # files = []

    # for path in tracked:
    #     if path.endswith((".py", ".js", ".ts", ".java")):
    #         try:
    #             with open(path, "r", encoding="utf-8") as f:
    #                 files.append({"file_name": path, "content": f.read()})
    #         except Exception as e:
    #             print(f"⚠️ Skipping unreadable file {path}: {e}")
    
        # ---------------------------------------------------------
    # Scan entire project including new/modified/untracked files
    # ---------------------------------------------------------
    files = []
    allowed_ext = (".py", ".js", ".ts", ".java")

    for root, dirs, filenames in os.walk(".", topdown=True):
        # Ignore junk/system directories
        dirs[:] = [d for d in dirs if d not in (
            "venv", "env", ".git", "dist", "build", "node_modules", "__pycache__"
        )]

        for name in filenames:
            if name.endswith(allowed_ext):
                path = os.path.join(root, name)

                try:
                    with open(path, "r", encoding="utf-8") as f:
                        files.append({
                            "file_name": path.replace(".\\", ""),
                            "content": f.read()
                        })
                except Exception as e:
                    print(f"⚠️ Skipping unreadable file {path}: {e}")

    if not files:
        print("❌ No supported code files found")
        sys.exit(1)

    # SEND TO BACKEND
    r = requests.post(f"{backend}/analyze", json={"repo_url": "local", "files": files}, verify=False)

    try:
        data = r.json()
    except:
        print("❌ Backend returned non-JSON response:")
        print(r.text)
        return

    analysis = data.get("analysis", [])
    approved = []

    for result in analysis:
        file_name = result["file"]

        print(f"\n📄 {file_name}")
        print("────────────────────────────────────────")

        if result.get("summary"):
            print(f"📝 Summary: {result['summary']}")

        if result.get("issues"):
            print("\n⚠️ Issues:")
            for issue in result["issues"]:
                print(f"  • {issue}")

        if result.get("refactors"):
            print("\n💡 Suggestions:")
            for s in result["refactors"]:
                print(f"  • {s}")

        choice = input("\nApply these suggestions? (y/n): ").strip().lower()

        with open(file_name, "r", encoding="utf-8") as f:
            original_code = f.read()

        # FIX: NORMALIZE REFACTORS
        raw_refactors = result.get("refactors", [])
        normalized_refactors = []

        for ref in raw_refactors:
            if isinstance(ref, str):
                normalized_refactors.append(ref)
            elif isinstance(ref, dict):
                normalized_refactors.append(json.dumps(ref))
            else:
                normalized_refactors.append(str(ref))

        approved.append({
            "file_name": file_name,
            "old_content": original_code,
            "refactors": normalized_refactors,
            "use_original": (choice != "y")
        })

    repo_url = run_git_command(["git", "remote", "get-url", "origin"])

    print("\n🚀 Sending approved changes to backend...")
    r = requests.post(f"{backend}/apply-fixes", json={
        "repo_url": repo_url,
        "approved": approved
    }, verify=False)

    try:
        print(json.dumps(r.json(), indent=2))
    except:
        print("❌ Backend returned non-JSON response:")
        print(r.text)

# ---------------------------------------------------------
# Command: status
# ---------------------------------------------------------
def cmd_status():
    backend = get_backend_url()

    repo_url = run_git_command(["git", "remote", "get-url", "origin"])
    owner = repo_url.rstrip("/").split("/")[-2]
    name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
    full_name = f"{owner}/{name}"

    r = requests.get(f"{backend}/status", params={"repo": full_name}, verify=False)

    try:
        print(json.dumps(r.json(), indent=2))
    except:
        print("❌ Invalid JSON response:")
        print(r.text)

# ---------------------------------------------------------
# Command: version
# ---------------------------------------------------------
# def cmd_version():
#     print(f"Motivity-Labs-CodeZen version {CLI_VERSION}")

CLI_VERSION = "0.2.2"
CLI_BRAND = "MotivityLabs CodeZen Agent"

def cmd_version():
    print(f"{CLI_BRAND} - v{CLI_VERSION}")


# ---------------------------------------------------------
# Help
# ---------------------------------------------------------
def cmd_help():
    print("""
CodeZen CLI - Developer Automation Tool

Commands:
  codezen init                 Initialize repo
  codezen analyze              Analyze code & apply fixes
  codezen status               Check installation status
  codezen config --backend URL Set backend URL
  codezen version              Show CLI version
  codezen help                 Show this help menu
""")

# ---------------------------------------------------------
# Main
# ---------------------------------------------------------
def main():
    if len(sys.argv) < 2:
        cmd_help()
        return

    cmd = sys.argv[1]

    if cmd == "init":
        cmd_init()
    elif cmd == "analyze":
        cmd_analyze()
    elif cmd == "status":
        cmd_status()
    elif cmd == "version":
        cmd_version()
    elif cmd == "help":
        cmd_help()
    elif cmd == "config":
        if "--backend" in sys.argv:
            idx = sys.argv.index("--backend") + 1
            if idx >= len(sys.argv):
                print("❌ Missing backend URL")
                return
            save_backend_url(sys.argv[idx])
        else:
            print("❌ Usage: codezen config --backend <URL>")
    else:
        print(f"❌ Unknown command: {cmd}")
        cmd_help()

if __name__ == "__main__":
    main()
