# """
# Handles local LLM (Ollama) communication for analysis/refactor.
# Compatible with Ollama v0.12+ (uses /api/chat)
# """

# import os, requests, json, re
# from dotenv import load_dotenv
# load_dotenv()

# # Default Ollama endpoint
# OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

# MODEL = "llama3.2:3b"   # Best for your laptop


# def analyze_files(files):
#     """Send code to LLM and return structured analysis."""

#     prompt = (
#         "You are CodeZen AI. Analyze the following files.\n"
#         "Return STRICT JSON format ONLY. Structure:\n"
#         "[{\n"
#         '  "file": "filename",\n'
#         '  "issues": ["..."],\n'
#         '  "refactors": ["..."],\n'
#         '  "summary": "..." \n'
#         "}]\n\n"
#         f"FILES:\n{json.dumps(files)}"
#     )

#     payload = {
#         "model": MODEL,
#         "messages": [
#             {"role": "user", "content": prompt}
#         ]
#     }

#     r = requests.post(f"{OLLAMA_URL}/api/chat", json=payload)
#     r.raise_for_status()

#     data = r.json()
#     text = data["message"]["content"]
#     return _extract_json(text)


# def apply_refactors(approved):
#     """Request code changes based on approved suggestions."""

#     prompt = (
#         "Apply these refactor suggestions to the code.\n"
#         "Return JSON ONLY with the structure:\n"
#         "{ \"updated_files\": [ { \"file\": \"..\", \"content\": \"..\" } ] }\n\n"
#         f"Suggestions:\n{json.dumps(approved)}"
#     )

#     payload = {
#         "model": MODEL,
#         "messages": [
#             {"role": "user", "content": prompt}
#         ]
#     }

#     r = requests.post(f"{OLLAMA_URL}/api/chat", json=payload)
#     r.raise_for_status()

#     data = r.json()
#     text = data["message"]["content"]
#     return _extract_json(text)


# def _extract_json(text: str):
#     """Extract JSON even if LLM wraps it inside explanations."""

#     try:
#         return json.loads(text)
#     except Exception:
#         pass

#     # Try to extract array JSON
#     try:
#         match = re.search(r"\[.*\]", text, re.DOTALL)
#         if match:
#             return json.loads(match.group())
#     except:
#         pass

#     # Try to extract object JSON
#     try:
#         match = re.search(r"\{.*\}", text, re.DOTALL)
#         if match:
#             return json.loads(match.group())
#     except:
#         pass

#     return {
#         "error": "Invalid JSON from model",
#         "raw": text[:500]
#     }

# import os
# import json
# import requests
# import concurrent.futures

# OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
# # MODEL = "qwen2.5-coder:1.5b"
# # FALLBACK_MODEL = "llama3.2:1b"
# MODEL = "llama3.2:1b"
# FALLBACK_MODEL = "qwen2.5-coder:1.5b"

# def ask_ollama(prompt):
#     payload = {
#         "model": MODEL,
#         "prompt": prompt,
#         "stream": False
#     }

#     # Correct API for Ollama v0.1.43
#     r = requests.post(f"{OLLAMA_URL}/api/generate", json=payload)
#     r.raise_for_status()

#     return r.json().get("response", "")

# def analyze_single_file(file_obj):
#     content = file_obj["content"][:6000]  # limit for speed

#     prompt = (
#         "Strict JSON only.\n"
#         "Format: {\"file\":\"x\",\"issues\":[],\"refactors\":[],\"summary\":\"...\"}\n"
#         f"File name: {file_obj['file_name']}\n"
#         f"Code:\n{content}"
#     )

#     resp = ask_ollama(prompt)
#     print("\n\n----- RAW MODEL OUTPUT -----\n")
#     print(resp)
#     print("\n---------------------------\n\n")
#     return _extract_json(resp)


# def analyze_files(files):
#     results = []

#     # parallel analysis (4 threads)
#     with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
#         future_map = {executor.submit(analyze_single_file, f): f for f in files}

#         for future in concurrent.futures.as_completed(future_map):
#             results.append(future.result())

#     return results


# def apply_refactors(changes):
#     prompt = (
#         "Strict JSON. Format: {\"updated_files\": [...]}\n"
#         f"{json.dumps(changes)}"
#     )
#     resp = ask_ollama(prompt)
#     return _extract_json(resp)


# # def _extract_json(text):
# #     try:
# #         return json.loads(text)
# #     except:
# #         import re
# #         m = re.search(r"\{.*\}", text, re.DOTALL)
# #         if m:
# #             return json.loads(m.group())
# #         return {"error": "Invalid JSON", "raw": text[:200]}

# def _extract_json(text):
#     import re, json

#     # 1. Try direct JSON
#     try:
#         return json.loads(text)
#     except:
#         pass

#     # 2. Try to extract the first {...}
#     m = re.search(r"\{(?:[^{}]|(?:\{[^{}]*\}))*\}", text, re.DOTALL)
#     if m:
#         try:
#             return json.loads(m.group())
#         except:
#             pass

#     # 3. Try to extract the first [ ... ]
#     m = re.search(r"\[(?:[^\[\]]|(?:\[[^\[\]]*\]))*\]", text, re.DOTALL)
#     if m:
#         try:
#             return json.loads(m.group())
#         except:
#             pass

#     # 4. Last resort
#     return {
#         "error": "Invalid JSON",
#         "raw": text[:500]
#     }

# # ---- LM Studio LLM Client ----
# import os
# import json
# import requests
# import concurrent.futures
# import re

# LMSTUDIO_API = os.getenv("LMSTUDIO_API", "http://localhost:1234/v1")
# MODEL = os.getenv("LMSTUDIO_MODEL", "qwen2.5-coder-7b-instruct")


# def ask_llm(prompt: str) -> str:
#     url = f"{LMSTUDIO_API}/chat/completions"

#     payload = {
#         "model": MODEL,
#         "messages": [
#             {"role": "system", "content": "You are a code analysis AI. Output ONLY valid JSON."},
#             {"role": "user", "content": prompt},
#         ],
#         "temperature": 0.2,
#         "max_tokens": 2048,
#     }

#     r = requests.post(url, json=payload)
#     r.raise_for_status()

#     return r.json()["choices"][0]["message"]["content"]


# def analyze_single_file(file_obj):
#     content = file_obj["content"][:6000]

#     # prompt = (
#     #     "Return STRICT JSON ONLY.\n"
#     #     "Format: {\"file\":\"x\",\"issues\":[],\"refactors\":[],\"summary\":\"...\"}\n"
#     #     f"File name: {file_obj['file_name']}\n"
#     #     f"Code:\n{content}"
#     # )
    
#     prompt = """
#         Return STRICT JSON ONLY.
#         Output format:
#         {
#           "updated_files": [
#                 {
#                     "file_name": "string",
#                     "content": "string (FULL UPDATED FILE CONTENT)"
#                 }
#             ]
#         }

#     DO NOT change keys.
#     DO NOT include any extra text.
#     Your job: apply the provided refactor suggestions and return the updated files.
#     """

#     prompt += json.dumps(changes)


#     resp = ask_llm(prompt)
#     return extract_json(resp)


# def analyze_files(files):
#     results = []

#     with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
#         future_map = {executor.submit(analyze_single_file, f): f for f in files}

#         for future in concurrent.futures.as_completed(future_map):
#             results.append(future.result())

#     return results


# def apply_refactors(changes):
#     prompt = (
#         "Return STRICT JSON ONLY.\n"
#         "Format: {\"updated_files\": [...]}\n"
#         f"{json.dumps(changes)}"
#     )

#     resp = ask_llm(prompt)
#     return extract_json(resp)


# def extract_json(text: str):
#     """Extract JSON even if model adds extra text."""
#     try:
#         return json.loads(text)
#     except:
#         m = re.search(r"\{.*\}", text, re.DOTALL)
#         if m:
#             try:
#                 return json.loads(m.group())
#             except:
#                 pass

#     return {"error": "Invalid JSON", "raw": text[:200]}

# # ---- LM Studio LLM Client ----
# import os
# import json
# import requests
# import concurrent.futures
# import re

# LMSTUDIO_API = os.getenv("LMSTUDIO_API", "http://localhost:1234/v1")
# MODEL = os.getenv("LMSTUDIO_MODEL", "qwen2.5-coder-7b-instruct")


# def ask_llm(prompt: str) -> str:
#     url = f"{LMSTUDIO_API}/chat/completions"

#     payload = {
#         "model": MODEL,
#         "messages": [
#             {"role": "system", "content": "You are a code analysis AI. Output ONLY valid JSON."},
#             {"role": "user", "content": prompt},
#         ],
#         "temperature": 0.2,
#         "max_tokens": 2048,
#     }

#     r = requests.post(url, json=payload)
#     r.raise_for_status()
#     return r.json()["choices"][0]["message"]["content"]


# # -----------------------------
# # FILE ANALYSIS (NO CODE CHANGE)
# # -----------------------------
# def analyze_single_file(file_obj):
#     content = file_obj["content"][:600]

#     prompt = (
#         "Return STRICT JSON ONLY.\n"
#         "Format: {\n"
#         "  \"file\": \"filename.py\",\n"
#         "  \"issues\": [],\n"
#         "  \"refactors\": [],\n"
#         "  \"summary\": \"...\"\n"
#         "}\n\n"
#         f"File name: {file_obj['file_name']}\n"
#         f"Code:\n{content}"
#     )

#     resp = ask_llm(prompt)
#     return extract_json(resp)


# def analyze_files(files):
#     results = []
#     with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
#         future_map = {executor.submit(analyze_single_file, f): f for f in files}
#         for future in concurrent.futures.as_completed(future_map):
#             results.append(future.result())
#     return results


# # -----------------------------
# # APPLY REFACTORS (UPDATED)
# # -----------------------------
# def apply_refactors(changes):
#     """
#     changes = list of {file_name, comment}
#     LLM must return:
#     {
#       "updated_files": [
#         { "file_name": "...", "content": "FULL NEW CODE" }
#       ]
#     }
#     """
#     prompt = """
# Return STRICT JSON ONLY.
# Output format:
# {
#   "updated_files": [
#     {
#       "file_name": "string",
#       "content": "string (FULL UPDATED FILE CONTENT)"
#     }
#   ]
# }

# DO NOT change key names.
# DO NOT add explanations.
# Your job: Apply the given refactor suggestions and output ONLY the updated files.
# """

#     prompt += json.dumps(changes)

#     resp = ask_llm(prompt)
#     return extract_json(resp)


# # -----------------------------
# # JSON EXTRACTION
# # -----------------------------
# def extract_json(text: str):
#     """Extract JSON even if model adds extra text."""
#     try:
#         return json.loads(text)
#     except:
#         m = re.search(r"\{.*\}", text, re.DOTALL)
#         if m:
#             try:
#                 return json.loads(m.group())
#             except:
#                 pass

#     return {"error": "Invalid JSON", "raw": text[:200]}

# # ============================================================
# # Unified LLM Client for CodeZen
# # Supports: LM Studio (local), Gemini (cloud)
# # Switch using .env  ->  USE_GEMINI=true OR false
# # ============================================================

# import os
# import json
# import re
# import concurrent.futures
# import requests

# USE_GEMINI = os.getenv("USE_GEMINI", "false").lower() == "true"


# # ------------------------------------------------------------
# # Gemini Setup (Loaded only if enabled)
# # ------------------------------------------------------------
# if USE_GEMINI:
#     import google.generativeai as genai
#     GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
#     GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

#     if not GEMINI_API_KEY:
#         raise RuntimeError("❌ Gemini enabled but no GEMINI_API_KEY set in .env")

#     genai.configure(api_key=GEMINI_API_KEY)
#     gemini_model = genai.GenerativeModel(GEMINI_MODEL)


# # ------------------------------------------------------------
# # LM Studio Params
# # ------------------------------------------------------------
# LMSTUDIO_API = os.getenv("LMSTUDIO_API", "http://localhost:1234/v1")
# LMSTUDIO_MODEL = os.getenv("LMSTUDIO_MODEL", "qwen2.5-coder-7b-instruct")


# # ============================================================
# # LLM CALL: AUTO SWITCH between Gemini and LM Studio
# # ============================================================
# def ask_llm(prompt: str) -> str:
#     if USE_GEMINI:
#         # ------------- Gemini Mode -------------
#         out = gemini_model.generate_content(prompt)
#         return out.text.strip()
#     else:
#         # ------------- LM Studio Mode ----------
#         url = f"{LMSTUDIO_API}/chat/completions"
#         payload = {
#             "model": LMSTUDIO_MODEL,
#             "messages": [
#                 {
#                     "role": "system",
#                     "content": (
#                         "You are a strict JSON code analysis engine. "
#                         "Always output ONLY valid JSON. No markdown. No text outside JSON."
#                     )
#                 },
#                 {"role": "user", "content": prompt},
#             ],
#             "temperature": 0.1,
#             "max_tokens": 2048,
#         }

#         r = requests.post(url, json=payload)
#         r.raise_for_status()
#         return r.json()["choices"][0]["message"]["content"]


# # ============================================================
# # ANALYZE SINGLE FILE
# # ============================================================
# def analyze_single_file(file_obj):
#     content = file_obj["content"][:1200]

#     prompt = f"""
# Return STRICT VALID JSON ONLY.

# JSON format:
# {{
#   "file": "{file_obj['file_name']}",
#   "issues": ["problem1", "problem2"],
#   "refactors": ["suggestion1", "suggestion2"],
#   "summary": "short summary"
# }}

# Analyze the following code and fill these fields:

# Code:
# {content}
# """

#     resp = ask_llm(prompt)
#     return extract_json(resp)


# # ============================================================
# # ANALYZE MULTIPLE FILES
# # ============================================================
# def analyze_files(files):
#     results = []
#     with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
#         future_map = {executor.submit(analyze_single_file, f): f for f in files}
#         for future in concurrent.futures.as_completed(future_map):
#             results.append(future.result())
#     return results

# # ============================================================
# # APPLY LLM REFACTORS (UPGRADED VERSION – NEVER RETURNS EMPTY)
# # ============================================================
# def apply_refactors(changes):
#     """
#     changes = [
#         {
#             "file_name": "...",
#             "old_content": "FULL ORIGINAL CODE",
#             "refactors": ["fix unused imports", "rewrite function", ...]
#         }
#     ]
#     """

#     # ---- Force fallback if changes list is empty ----
#     if not changes:
#         return {
#             "updated_files": []
#         }

#     # ---- Build improved, strict, deterministic prompt ----
#     prompt = f"""
# You are an advanced code refactoring engine.
# Your job: rewrite FULL updated source code for each file listed below.

# IMPORTANT RULES:
# - Output STRICT VALID JSON ONLY (NO markdown, NO comments).
# - For each file, ALWAYS produce a complete updated file under "updated_files".
# - NEVER return an empty "updated_files" array.
# - If refactor suggestions are unclear, FIX obvious issues and rewrite clean, runnable code.
# - ALWAYS include 100% of the file content in rewritten form.
# - Do not skip files even if changes are small or unclear.
# - Do not add explanations. Only updated code.

# Final JSON format:
# {{
#   "updated_files": [
#     {{
#       "file_name": "string",
#       "content": "FULL UPDATED CODE WITHOUT MARKDOWN"
#     }}
#   ]
# }}

# Here are the files with their original code and the refactor instructions.
# Use them to rewrite full improved versions of each file:

# {json.dumps(changes, indent=2)}
# """

#     # ---- Call model ----
#     resp = ask_llm(prompt)
#     data = extract_json(resp)

#     # ---- HARD SAFETY CHECK ----
#     files_out = data.get("updated_files", [])

#     # If model still fails → fallback: return original unchanged files
#     if not files_out:
#         print("⚠️ LLM returned empty output. Falling back to original files.")

#         fallback_files = []
#         for c in changes:
#             fallback_files.append({
#                 "file_name": c["file_name"],
#                 "content": c["old_content"]
#             })

#         return {"updated_files": fallback_files}

#     return data


# # ============================================================
# # JSON extraction helper
# # ============================================================
# def extract_json(text: str):
#     """
#     Safely extract JSON even if the LLM adds stray text.
#     """
#     try:
#         return json.loads(text)
#     except:
#         pass

#     # Try regex fallback
#     m = re.search(r"\{.*\}", text, re.DOTALL)
#     if m:
#         try:
#             return json.loads(m.group())
#         except:
#             pass

#     return {"error": "Invalid JSON", "raw": text[:300]}


# ============================================================
# Unified LLM Client for CodeZen
# Supports: LM Studio (local), Gemini (cloud)
# Switch using .env  ->  USE_GEMINI=true OR false
# ============================================================

import os
import json
import re
import concurrent.futures
import requests

USE_GEMINI = os.getenv("USE_GEMINI", "false").lower() == "true"


# ------------------------------------------------------------
# Gemini Setup (Loaded only if enabled)
# ------------------------------------------------------------
if USE_GEMINI:
    import google.generativeai as genai
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash-latest")

    if not GEMINI_API_KEY:
        raise RuntimeError("❌ Gemini enabled but no GEMINI_API_KEY set in .env")

    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel(GEMINI_MODEL)


# ------------------------------------------------------------
# LM Studio Params
# ------------------------------------------------------------
LMSTUDIO_API = os.getenv("LMSTUDIO_API", "http://localhost:1234/v1")
LMSTUDIO_MODEL = os.getenv("LMSTUDIO_MODEL", "qwen2.5-coder-7b-instruct")


# ============================================================
# LLM CALL: AUTO SWITCH between Gemini and LM Studio
# ============================================================
def ask_llm(prompt: str) -> str:
    if USE_GEMINI:
        out = gemini_model.generate_content(prompt)
        return out.text.strip()

    url = f"{LMSTUDIO_API}/chat/completions"
    payload = {
        "model": LMSTUDIO_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a strict JSON code analysis engine. "
                    "Always output ONLY valid JSON. No markdown. No text outside JSON."
                )
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 4096,
    }

    r = requests.post(url, json=payload)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


# ============================================================
# SUPPORTED LANGUAGES (STRICT)
# ============================================================
def get_language_from_filename(file_name):
    """Only accept .py, .js, .ts, .java"""
    ext = file_name.split(".")[-1].lower()
    return {
        "py": "Python",
        "js": "JavaScript",
        "ts": "TypeScript",
        "java": "Java"
    }.get(ext)  # returns None if unsupported


# ============================================================
# LANGUAGE-SPECIFIC RULES
# ============================================================
LANGUAGE_RULES = {
    "Python": {
        "tooling": "super-pylint",
        "docstring_style": "PEP 257 docstrings",
        "standards": "PEP 8",
        "example_doc": "`Returns: int`",
        "example_comment": "# comment"
    },
    "JavaScript": {
        "tooling": "super-ESLint",
        "docstring_style": "JSDoc /** */",
        "standards": "Airbnb/Prettier",
        "example_doc": "@returns {string}",
        "example_comment": "// comment"
    },
    "TypeScript": {
        "tooling": "TS-ESLint",
        "docstring_style": "JSDoc/TSDoc",
        "standards": "Prettier + TS rules",
        "example_doc": "@returns {string}",
        "example_comment": "// comment"
    },
    "Java": {
        "tooling": "Checkstyle",
        "docstring_style": "Javadoc",
        "standards": "Java standard style",
        "example_doc": "@return String",
        "example_comment": "// comment"
    }
}


# ============================================================
# ANALYZE SINGLE FILE (SMART + SKIP UNSUPPORTED)
# ============================================================
def analyze_single_file(file_obj):
    file_name = file_obj["file_name"]

    # Skip if unsupported
    language = get_language_from_filename(file_name)
    if not language:
        print(f"⏩ Skipping unsupported file: {file_name}")
        return None

    rules = LANGUAGE_RULES[language]
    content = file_obj["content"][:8000]

    prompt = f"""
Return STRICT VALID JSON ONLY.

You are an expert {language} reviewer using {rules["tooling"]} style rules.

Analyze the following code with strict rules:
- Docstring/documentation issues
- Noise comments vs good comments
- Dead code removal
- Formatting issues ({rules["standards"]})
- Logic bugs, undefined variables, unreachable code
- Module import issues

JSON format:
{{
  "file": "{file_name}",
  "issues": [],
  "refactors": [],
  "summary": ""
}}

Code:
{content}
"""

    resp = ask_llm(prompt)
    return extract_json(resp)


# ============================================================
# ANALYZE MULTIPLE FILES
# ============================================================
def analyze_files(files):
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(analyze_single_file, f): f for f in files}

        for f in concurrent.futures.as_completed(futures):
            try:
                result = f.result()
                if result:
                    results.append(result)
            except Exception as e:
                fname = futures[f]["file_name"]
                print(f"❌ Error analyzing {fname}: {e}")
                results.append({
                    "file": fname,
                    "error": str(e),
                    "issues": [],
                    "refactors": [],
                    "summary": "Analysis failed"
                })

    return results


# ============================================================
# APPLY REFACTORS (SAFER + FULL FILE OUTPUT)
# ============================================================
def apply_refactors(changes):
    if not changes:
        return {"updated_files": []}

    prompt = f"""
Return STRICT VALID JSON ONLY.

You are a code refactoring engine.
Rewrite FULL UPDATED code for each file.
Rules:
- Output ONLY JSON
- Must return 100% full file content
- Must follow instructions strictly
- No markdown, no comments, no explanation

JSON format:
{{
  "updated_files": [
    {{
      "file_name": "string",
      "content": "FULL UPDATED CODE"
    }}
  ]
}}

Tasks:
{json.dumps(changes, indent=2)}
"""

    resp = ask_llm(prompt)
    data = extract_json(resp)

    # safety fallback
    if not data.get("updated_files"):
        print("⚠️ LLM returned empty output. Falling back to original files.")
        return {
            "updated_files": [
                {"file_name": c["file_name"], "content": c["old_content"]}
                for c in changes
            ]
        }

    return data


# ============================================================
# JSON extraction
# ============================================================
def extract_json(text: str):
    try:
        return json.loads(text)
    except:
        pass

    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except:
            pass

    return {"error": "Invalid JSON", "raw": text[:300]}

