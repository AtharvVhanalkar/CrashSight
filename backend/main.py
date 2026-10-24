from fastapi import FastAPI, Form, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import your custom Agents and Schemas
from gemma_agent import analyze_crash, APP_CONFIGS
from github_agent import dispatch_issue
from schemas import DispatchRequest

app = FastAPI(title="CrashSight API", version="1.0")

# CRITICAL: Allow the frontend (running on a different port/file) to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/analyze")
async def api_analyze_crash(
    app_name: str = Form(...),
    app_type: str = Form(...),
    description: str = Form(...),
    files: list[UploadFile] = File(default=[])
):
    """
    Endpoint 1: Receives the screenshot and text from the UI, passes it to Agent Skill 1 (Gemma 4).
    """
    try:
        # Pass the inputs to your Gemma triage engine
        result = analyze_crash(app_name, app_type, description, files)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemma Engine Error: {str(e)}")

@app.post("/api/dispatch")
async def api_dispatch_issue(request: DispatchRequest):
    """
    Endpoint 2: Receives the finalized report and triggers Agent Skill 2 (GitHub API).
    """
    # 1. Route to the correct SaaS client repository using the dictionary
    app_key = request.app_name.lower().replace(" ", "")
    config = APP_CONFIGS.get(app_key)
    
    if not config:
        # Fallback to your own repository if they test a random app name not in the dictionary
        repo_owner = "AtharvVhanalkar"  
        repo_name = "CrashSight"             
    else:
        repo_owner = config["github_owner"]
        repo_name = config["github_repo"]

    title = f"[CrashSight Automated Report] Incident in {request.app_name}"
    
    # 2. Trigger the GitHub Agent
    response = dispatch_issue(
        repo_owner=repo_owner,
        repo_name=repo_name,
        title=title,
        body=request.report_markdown
    )

    if response["status"] == "success":
        return response
    else:
        raise HTTPException(status_code=500, detail=response["message"])

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)