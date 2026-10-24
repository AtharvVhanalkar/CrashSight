import os
import re
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

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

app = FastAPI(title="CrashSight Autonomous Triage", version="4.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- VERIFIED HISTORICAL INCIDENT REPOSITORY (Few-Shot Grounding) ---
HISTORICAL_INCIDENTS = [
    {
        "app": "vscode",
        "symptom": "Language server process crash / ResourceUnavailable / Named Pipe broken",
        "visual_signature": "Red notification modal 'ResourceUnavailable' or 'Language Service disconnected'",
        "error_class": "IPC_NAMED_PIPE_DISCONNECT",
        "root_cause": "The TypeScript/LSP background language server terminated unexpectedly. The host process received ResourceUnavailable because the named pipe IPC endpoint vanished.",
        "safe_command": "pkill -f 'tsserver|vscode' 2>/dev/null || true; rm -rf ~/Library/Application\\ Support/Code/User/workspaceStorage/* 2>/dev/null || true",
        "is_user_repairable": True
    },
    {
        "app": "discord",
        "symptom": "RTC Connecting / ICE_CONNECTION_FAILED / voice socket drop",
        "visual_signature": "Orange or Red 'RTC Connecting' banner in voice channel footer",
        "error_class": "WEBRTC_ICE_HANDSHAKE_STALL",
        "root_cause": "Corrupted WebRTC ICE candidate cache and stale Electron GPU render state preventing socket handshake.",
        "safe_command": "pkill -f Discord 2>/dev/null || true; rm -rf ~/Library/Application\\ Support/discord/Cache ~/Library/Application\\ Support/discord/GPUCache 2>/dev/null || true",
        "is_user_repairable": True
    },
    {
        "app": "vlc",
        "symptom": "Hardware acceleration deadlock / black screen audio only",
        "visual_signature": "Black viewport during playback or stuttering frame demuxer",
        "error_class": "GPU_DECODE_SURFACE_LOCK",
        "root_cause": "Hardware-accelerated decoding pipeline deadlock in VideoToolbox/VA-API rendering layer.",
        "safe_command": "rm -f ~/.config/vlc/vlcrc ~/Library/Preferences/org.videolan.vlc/vlcrc 2>/dev/null || true",
        "is_user_repairable": True
    },
    {
        "app": "obs",
        "symptom": "Encoder stall / NVENC overload / Preview freeze",
        "visual_signature": "Status bar 'Encoding overloaded' or frozen OpenGL/Metal canvas",
        "error_class": "ENCODER_BUFFER_STARVATION",
        "root_cause": "Graphics capture hook encountered an unhandled texture lock, deadlocking compositing frames.",
        "safe_command": "pkill -f obs 2>/dev/null || true; rm -rf ~/.config/obs-studio/plugin_config 2>/dev/null || true",
        "is_user_repairable": True
    },
    {
        "app": "blinkit",
        "symptom": "Hydration deadlock / Session token loop / Blank webview",
        "visual_signature": "White blank screen on startup or stuck cart spinner",
        "error_class": "INDEXEDDB_SESSION_DEADLOCK",
        "root_cause": "IndexedDB deserialization failure during startup bootstrap.",
        "safe_command": "rm -rf ~/Library/Caches/Blinkit ~/Library/Application\\ Support/Blinkit/Cache 2>/dev/null || true",
        "is_user_repairable": True
    }
]

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
        "context": "You are a TypeScript/Electron engineer specializing in VS Code. Focus on extension host processes, Language Server Protocol (LSP), V8 memory limits, named pipes, and workspace storage corruptions."
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

class ExecuteCommandRequest(BaseModel):
    command: str

class LocationLookupRequest(BaseModel):
    app_key: str
    target_type: str

class DispatchRequest(BaseModel):
    app_key: str
    target_type: str
    report_markdown: str

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
    
    # 1. Guardrails: Block privilege escalation and catastrophic disk commands
    if cmd.startswith("sudo ") or " sudo " in cmd:
        raise HTTPException(status_code=400, detail="Sudo/root execution is not permitted.")

    dangerous_patterns = [
        r"rm\s+-[a-zA-Z]*rf\s+/\s*$",
        r"rm\s+-[a-zA-Z]*rf\s+/\*",
        r"rm\s+-[a-zA-Z]*rf\s+(~|~/|\$HOME)\s*$",
        r":\(\)\s*\{\s*:\|:&\s*\};:",
        r"mkfs",
        r"dd\s+if=",
    ]
    for pattern in dangerous_patterns:
        if re.search(pattern, cmd):
            raise HTTPException(status_code=400, detail="Command contains unsafe operations.")

    try:
        # Run command with safe shell environment
        res = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=12
        )
        
        # If exit code was 1 solely due to 'no process found', treat as clean state
        stderr_msg = res.stderr.strip()
        if res.returncode != 0 and "No matching processes" in stderr_msg:
            return {
                "status": "success",
                "returncode": 0,
                "stdout": "Target process is not running. Stale state cleared successfully.",
                "stderr": ""
            }

        return {
            "status": "success" if res.returncode == 0 else "error",
            "returncode": res.returncode,
            "stdout": res.stdout.strip() or "Remediation command completed successfully.",
            "stderr": stderr_msg
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

    # Match past incident cases for this app to ground the model
    matching_cases = [c for c in HISTORICAL_INCIDENTS if c["app"] == app_key.lower()]
    historical_context_str = json.dumps(matching_cases, indent=2)

    prompt = f"""
    {app_info['context']}

    VERIFIED HISTORICAL RESOLUTION CASES (FEW-SHOT GROUNDING):
    {historical_context_str}

    NEW INCIDENT INTAKE:
    Target App: {app_info['name']}
    Host Platform: {platform.system()} {platform.release()} ({platform.machine()})
    User Description: {description}

    INSTRUCTIONS:
    1. Inspect the user description and any visual screenshots/logs provided.
    2. Check if this incident resembles any of the verified historical resolution cases above.
    3. Determine if the issue is repairable on the user's machine (cache corruption, process deadlock, stale IPC named pipe, GPU flag conflict).
    4. Provide an idempotent, safe terminal command. Always append `2>/dev/null || true` to kill/removal commands so they never throw 'No matching processes found'.
    5. Generate a structured technical bug report ready for developers.

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

    image_contents = []
    if files:
        for f in files:
            if f.content_type.startswith("image/"):
                image_contents.append({"mime_type": f.content_type, "data": await f.read()})

    if engine.lower() == "gemma4":
        b64_images = [base64.b64encode(b["data"]).decode("utf-8") for b in image_contents]
        try:
            payload = {
                "model": "gemma4",
                "prompt": prompt,
                "format": "json",
                "stream": False
            }
            if b64_images:
                payload["images"] = b64_images
            res = requests.post("http://127.0.0.1:11434/api/generate", json=payload, timeout=60)
            res.raise_for_status()
            return json.loads(res.json().get("response", "{}"))
        except requests.exceptions.ConnectionError:
            raise HTTPException(status_code=503, detail="Local Gemma 4 (Ollama) is not running on port 11434. Switch to Cloud API.")

    # Cloud Multimodal Engine
    contents = [prompt]
    for img in image_contents:
        contents.append(img)

    model = genai.GenerativeModel("gemini-3.8-flash")
    try:
        response = model.generate_content(
            contents,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.1
            )
        )
        return json.loads(response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/api/dispatch")
async def dispatch_issue(req: DispatchRequest):
    app_info = APP_REGISTRY.get(req.app_key.lower())
    if not app_info:
        raise HTTPException(status_code=400, detail="Invalid application key.")

    if req.target_type == "github":
        if not GITHUB_TOKEN:
            raise HTTPException(status_code=500, detail="GITHUB_TOKEN is missing in backend/.env")

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
