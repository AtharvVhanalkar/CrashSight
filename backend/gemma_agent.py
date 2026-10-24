import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from schemas import TriageResponse

# Load the API Keys
load_dotenv()

# Configure the Google GenAI SDK
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# B2B SaaS Application Routing Dictionary
APP_CONFIGS = {
    "vlc": {
        "display_name": "VLC Media Player",
        "github_owner": "videolan",
        "github_repo": "vlc",
        "gemma_context": "You are a Senior C++ engineer debugging VLC Media Player. Focus on media codecs, hardware acceleration hardware, frame drops, and audio/video sync anomalies."
    },
    "vscode": {
        "display_name": "Visual Studio Code",
        "github_owner": "microsoft",
        "github_repo": "vscode",
        "gemma_context": "You are a Senior TypeScript/Electron engineer debugging VS Code. Focus on extension host crashes, infinite loops in language servers, Electron window freezing, and memory leaks."
    },
    "obs": {
        "display_name": "OBS Studio",
        "github_owner": "obsproject",
        "github_repo": "obs-studio",
        "gemma_context": "You are a Senior C/C++ engineer debugging OBS Studio. Focus on NVENC GPU encoding crashes, capture card driver failures, and rendering pipeline bottlenecks."
    },
    "blender": {
        "display_name": "Blender 3D",
        "github_owner": "blender",
        "github_repo": "blender",
        "gemma_context": "You are a Senior Python and C++ graphics engineer debugging Blender. Focus on CUDA/OptiX render crashes, mesh geometry memory limits, and OpenGL viewport glitches."
    },
    "brave": {
        "display_name": "Brave Browser",
        "github_owner": "brave",
        "github_repo": "brave-browser",
        "gemma_context": "You are a Senior Chromium/Rust engineer debugging Brave Browser. Focus on V8 JavaScript engine faults, WebGL context losses, and adblocker list memory overflows."
    }
}

def analyze_crash(app_name: str, app_type: str, description: str, uploaded_files: list = None) -> dict:
    """
    Agent Skill 1: Multimodal Triage using Gemma 4.
    """
    # Standardize the app name to match dictionary keys
    app_key = app_name.lower().replace(" ", "")
    
    # Retrieve specific context, fallback to generic if app isn't in our SaaS list
    context = APP_CONFIGS.get(app_key, {}).get(
        "gemma_context", 
        f"You are a Senior Software Engineer debugging a critical failure in {app_name}."
    )

    prompt = f"""
    {context}
    
    A user has reported a software crash. 
    Application Environment: {app_type}
    User Description: {description}
    
    Analyze the provided visual evidence and description. Determine the technical root cause.
    Provide a safe terminal or PowerShell command to attempt a local fix (e.g., clearing caches or disabling hardware acceleration).
    """

    # We use a Gemma 4 equivalent model hosted on AI Studio for speed
    model = genai.GenerativeModel('gemini-2.5-flash') 

    # Prepare multimodal payload
    contents = [prompt]
    
    # If the frontend sent images/logs, append their raw bytes to the payload
    if uploaded_files:
        for file in uploaded_files:
            if file.content_type.startswith("image/"):
                contents.append({
                    "mime_type": file.content_type, 
                    "data": file.file.read()
                })

    # Execute generation forcing strict JSON output mapped to our Pydantic schema
    response = model.generate_content(
        contents,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=TriageResponse,
            temperature=0.2, # Low temperature for highly analytical, deterministic output
        )
    )
    
    return json.loads(response.text)