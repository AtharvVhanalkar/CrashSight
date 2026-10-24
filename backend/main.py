import os
import sys
import json
import base64
import platform
import subprocess
from fastapi import FastAPI, Form, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import requests
from dotenv import load_dotenv
import re

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

app = FastAPI(title="CrashSight Autonomous Triage", version="3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

APP_REGISTRY = {
    "vlc": {
        "name": "VLC Media Player",
        "has_github": True,
        "github_owner": "videolan",
        "github_repo": "vlc",
        "website_support": "https://forum.videolan.org/viewforum.php?f=14",
        "context": "You are a C/C++ video multimedia systems engineer specializing in VLC. Focus on FFmpeg codecs, hardware acceleration (VA-API, DXVA2, VideoToolbox), audio de-sync, and demuxing."
    },
    "vscode": {
        "name": "Visual Studio Code",
        "has_github": True,
        "github_owner": "microsoft",
        "github_repo": "vscode",
        "website_support": "https://code.visualstudio.com/docs/supporting/troubleshoot",
        "context": "You are a TypeScript/Electron engineer specializing in VS Code. Focus on extension host processes, Language Server Protocol (LSP), V8 memory limits, and workspace config corruptions."
    },
    "obs": {
        "name": "OBS Studio",
        "has_github": True,
        "github_owner": "obsproject",
        "github_repo": "obs-studio",
        "website_support": "https://obsproject.com/forum/categories/troubleshooting-and-support.17/",
        "context": "You are a Graphics & Systems engineer specializing in OBS Studio. Focus on NVENC/AMF GPU encoder stalls, DirectX/OpenGL game capture hooks, audio sample rate mismatch, and dropped frames."
    },
    "discord": {
        "name": "Discord",
        "has_github": False,
        "github_owner": None,
        "github_repo": None,
        "website_support": "https://support.discord.com/hc/en-us/requests/new",
        "context": "You are a WebRTC & Electron engineer specializing in Discord client runtime. Focus on RTC voice socket drops, Krisp noise suppression audio pipeline errors, GPU hardware acceleration flags, and cache integrity."
    },
    "blinkit": {
        "name": "Blinkit",
        "has_github": False,
        "github_owner": None,
        "github_repo": None,
        "website_support": "https://blinkit.com/faq",
        "context": "You are a Mobile & Frontend Systems reliability engineer specializing in Quick-Commerce platforms (Blinkit). Focus on checkout session token invalidation, cart sync websocket disconnects, GPS location geofencing failures, and CDN image load timeouts."
    }
}

class LocationLookupRequest(BaseModel):
    app_key: str
    target_type: str

class ExecuteCommandRequest(BaseModel):
    command: str

class DispatchRequest(BaseModel):
    app_key: str
    target_type: str
    report_markdown: str

def run_local_gemma4(prompt: str, images_b64: list[str] = None) -> dict:
    payload = {
        "model": "gemma4",
        "prompt": prompt,
        "format": "json",
        "stream": False
    }
    if images_b64:
        payload["images"] = images_b64

    try:
        res = requests.post("http://127.0.0.1:11434/api/generate", json=payload, timeout=60)
        res.raise_for_status()
        raw_output = res.json().get("response", "{}")
        return json.loads(raw_output)
    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=503, 
            detail="Local Gemma 4 engine is not running on localhost:11434. Start it via 'ollama run gemma4' or select Cloud API."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemma 4 inference failed: {str(e)}")

@app.post("/api/locate-target")
async def locate_target(req: LocationLookupRequest):
    app_info = APP_REGISTRY.get(req.app_key.lower())
    if not app_info:
        raise HTTPException(status_code=404, detail="Unknown application")

    if req.target_type == "github":
        if not app_info["has_github"]:
            return {
                "available": False,
                "reason": f"{app_info['name']} is proprietary closed-source software and does not host an open GitHub issue repository.",
                "recommended": "website"
            }
        return {
            "available": True,
            "target": "https://github.com/AtharvVhanalkar/CrashSight",
            "destination_label": f"GitHub Issue Tracker ({app_info['name']})"
        }
    else:
        return {
            "available": True,
            "target": app_info["website_support"],
            "destination_label": f"{app_info['name']} Official Support Desk"
        }



@app.post("/api/execute-remediation")
async def execute_remediation(req: ExecuteCommandRequest):
    cmd = req.command.strip()
    
    # 1. Block sudo or root privileges
    if cmd.startswith("sudo ") or " sudo " in cmd:
        raise HTTPException(status_code=400, detail="Sudo/root execution is not permitted.")

    # 2. Block wiping root (/), entire home (~), or drive formatting
    dangerous_patterns = [
        r"rm\s+-[a-zA-Z]*rf\s+/\s*$",            # rm -rf /
        r"rm\s+-[a-zA-Z]*rf\s+/\*",              # rm -rf /*
        r"rm\s+-[a-zA-Z]*rf\s+(~|~/|\$HOME)\s*$", # rm -rf ~ or ~/
        r":\(\)\s*\{\s*:\|:&\s*\};:",           # Fork bomb
        r"mkfs",                                 # Format disk
        r"dd\s+if=",                             # Raw disk write
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, cmd):
            raise HTTPException(status_code=400, detail="Command contains unsafe operations targeting root or entire drive.")

    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=12)
        return {
            "status": "success" if res.returncode == 0 else "error",
            "returncode": res.returncode,
            "stdout": res.stdout.strip() or "Command completed with no standard output.",
            "stderr": res.stderr.strip()
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Execution timed out after 12 seconds.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution error: {str(e)}")

@app.post("/api/analyze")
async def analyze_crash(
    app_key: str = Form(...),
    description: str = Form(...),
    engine: str = Form("cloud"),
    files: list[UploadFile] = File(default=[])
):
    app_info = APP_REGISTRY.get(app_key.lower())
    if not app_info:
        raise HTTPException(status_code=400, detail="Invalid application key.")

    os_info = f"{platform.system()} {platform.release()} ({platform.machine()})"

    prompt = f"""
    {app_info['context']}

    CRASH INCIDENT CONTEXT:
    Target App: {app_info['name']}
    Host Environment: {os_info}
    User Crash Description: {description}

    DIAGNOSTIC INSTRUCTIONS:
    1. Assess whether this issue is user-repairable via a safe local terminal/powershell command (e.g. cache wipe, process reset, GPU flag toggle, config reset).
    2. If repairable, set is_user_repairable to true and provide an executable single-line command for {platform.system()}.
    3. If NOT repairable (e.g., hard upstream segmentation fault, upstream API failure, missing source implementation), set is_user_repairable to false and set safe_command to "NONE (Requires Upstream Patch)".
    4. Provide the exact root cause and generate a structured markdown bug report.

    Respond STRICTLY in valid JSON matching this schema:
    {{
      "is_user_repairable": true,
      "error_class": "string",
      "root_cause": "string",
      "safe_command": "string",
      "has_github": {str(app_info['has_github']).lower()},
      "markdown_bug_report": "string"
    }}
    """

    image_bytes = []
    if files:
        for f in files:
            if f.content_type.startswith("image/"):
                image_bytes.append((f.content_type, await f.read()))

    if engine.lower() == "gemma4":
        b64_images = [base64.b64encode(b).decode("utf-8") for _, b in image_bytes]
        return run_local_gemma4(prompt, b64_images)

    # Cloud Engine
    contents = [prompt]
    for mime, b in image_bytes:
        contents.append({"mime_type": mime, "data": b})

    model = genai.GenerativeModel("gemini-3.8-flash")
    try:
        response = model.generate_content(
            contents,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.2
            )
        )
        return json.loads(response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cloud Analysis failed: {str(e)}")

@app.post("/api/dispatch")
async def dispatch_issue(req: DispatchRequest):
    app_info = APP_REGISTRY.get(req.app_key.lower())
    if not app_info:
        raise HTTPException(status_code=400, detail="Invalid application key.")

    if req.target_type == "github":
        if not GITHUB_TOKEN:
            raise HTTPException(status_code=500, detail="GITHUB_TOKEN is missing in backend .env file.")
        
        target_owner = "AtharvVhanalkar"
        target_repo = "CrashSight"

        headers = {
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        payload = {
            "title": f"[{app_info['name']}] Autonomous Crash Triage Escalation",
            "body": req.report_markdown
        }
        res = requests.post(
            f"https://api.github.com/repos/{target_owner}/{target_repo}/issues",
            json=payload,
            headers=headers
        )
        if res.status_code == 201:
            return {"status": "success", "url": res.json().get("html_url")}
        raise HTTPException(status_code=res.status_code, detail=f"GitHub API Error: {res.text}")
    else:
        return {"status": "success", "url": app_info["website_support"]}