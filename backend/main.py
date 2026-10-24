import os
import json
from fastapi import FastAPI, Form, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import requests
from dotenv import load_dotenv
import base64

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI(title="CrashSight API", version="2.0")

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
        "context": "You are a C/C++ video engineer for VLC. Focus on codecs, hardware acceleration, and demuxing."
    },
    "vscode": {
        "name": "VS Code",
        "has_github": True,
        "github_owner": "microsoft",
        "github_repo": "vscode",
        "website_support": "https://code.visualstudio.com/docs/supporting/troubleshoot",
        "context": "You are a TypeScript/Electron engineer for VS Code. Focus on extension host, LSP, and memory."
    },
    "obs": {
        "name": "OBS Studio",
        "has_github": True,
        "github_owner": "obsproject",
        "github_repo": "obs-studio",
        "website_support": "https://obsproject.com/forum/categories/troubleshooting-and-support.17/",
        "context": "You are a Graphics/C++ engineer for OBS Studio. Focus on NVENC encoders and game hooks."
    },
    "discord": {
        "name": "Discord",
        "has_github": False,
        "github_owner": None,
        "github_repo": None,
        "website_support": "https://support.discord.com/hc/en-us/requests/new",
        "context": "You are an Electron/WebRTC engineer for Discord. Focus on RTC audio socket drops and cache."
    },
    "blinkit": {
        "name": "Blinkit",
        "has_github": False,
        "github_owner": None,
        "github_repo": None,
        "website_support": "https://blinkit.com/faq",
        "context": "You are an app performance engineer for Blinkit. Focus on session drops and checkout sync."
    }
}

class LocationLookupRequest(BaseModel):
    app_key: str
    target_type: str  # "github" or "website"

class DispatchRequest(BaseModel):
    app_key: str
    target_type: str
    report_markdown: str

@app.post("/api/locate-target")
async def locate_target(req: LocationLookupRequest):
    app_info = APP_REGISTRY.get(req.app_key.lower())
    if not app_info:
        raise HTTPException(status_code=404, detail="Unknown app")

    if req.target_type == "github":
        if not app_info["has_github"]:
            return {
                "available": False,
                "reason": "This software is proprietary and does not offer a public GitHub issues board.",
                "recommended": "website"
            }
        return {
            "available": True,
            "target": f"https://github.com/AtharvVhanalkar/CrashSight",
            "destination_label": f"GitHub Issues ({app_info['name']})"
        }
    else:
        return {
            "available": True,
            "target": app_info["website_support"],
            "destination_label": f"{app_info['name']} Official Support Desk"
        }
def run_local_gemma4(prompt: str, images_b64: list[str] = None) -> dict:
    """Dispatches multimodal crash analysis directly to local Gemma 4 runtime."""
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
            detail="Local Gemma 4 engine is not running. Please start it with 'ollama run gemma4'."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemma 4 inference failed: {str(e)}")
@app.post("/api/analyze")
async def analyze_crash(
    app_key: str = Form(...),
    description: str = Form(...),
    files: list[UploadFile] = File(default=[])
):
    app_info = APP_REGISTRY.get(app_key.lower())
    if not app_info:
        raise HTTPException(status_code=400, detail="Invalid application key.")

    prompt = f"""
    {app_info['context']}

    CRASH INCIDENT REPORT:
    Target App: {app_info['name']}
    User Description: {description}

    Instructions:
    1. Determine if this issue is user-repairable via a safe local workaround.
    2. Provide a safe terminal command or exact action step.
    3. Generate a structured technical bug report in markdown format.

    Respond STRICTLY in valid JSON matching:
    {{
      "error_class": "string",
      "root_cause": "string",
      "safe_command": "string",
      "has_github": {str(app_info['has_github']).lower()},
      "markdown_bug_report": "string"
    }}
    """
    
    contents = [prompt]
    if files:
        for f in files:
            if f.content_type.startswith("image/"):
                contents.append({"mime_type": f.content_type, "data": await f.read()})

    model = genai.GenerativeModel("gemini-3.8-flash")
    response = model.generate_content(
        contents,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            temperature=0.2
        )
    )
    return json.loads(response.text)

@app.post("/api/dispatch")
async def dispatch_issue(req: DispatchRequest):
    app_info = APP_REGISTRY.get(req.app_key.lower())
    if not app_info:
        raise HTTPException(status_code=400, detail="Invalid application key.")

    if req.target_type == "github":
        token = os.getenv("GITHUB_TOKEN")
        target_owner = "AtharvVhanalkar"
        target_repo = "CrashSight"
        
        res = requests.post(
            f"https://api.github.com/repos/{target_owner}/{target_repo}/issues",
            json={
                "title": f"[{app_info['name']}] Autonomous Crash Triage",
                "body": req.report_markdown
            },
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.v3+json"}
        )
        if res.status_code == 201:
            return {"status": "success", "url": res.json().get("html_url")}
        raise HTTPException(status_code=500, detail=f"GitHub API Error: {res.text}")
    else:
        return {"status": "success", "url": app_info["website_support"]}