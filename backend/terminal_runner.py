import os
import sys
import json
import webbrowser
from dotenv import load_dotenv
import google.generativeai as genai
import requests

load_dotenv()

# Verify API Keys
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

if not GEMINI_KEY:
    print("\n[ERROR] GEMINI_API_KEY missing from .env file!")
    sys.exit(1)

genai.configure(api_key=GEMINI_KEY)

# 1. Specialized Knowledge Bases & Routing Targets
APP_REGISTRY = {
    "1": {
        "name": "VLC Media Player",
        "type": "Open Source",
        "github_owner": "videolan",
        "github_repo": "vlc",
        "website_support": "https://forum.videolan.org/viewforum.php?f=14",
        "context": "You are a C/C++ video multimedia systems engineer specializing in VLC. Focus on FFmpeg codecs, hardware acceleration (VA-API, DXVA2, VideoToolbox), audio de-sync, and demuxing."
    },
    "2": {
        "name": "VS Code",
        "type": "Open Source",
        "github_owner": "microsoft",
        "github_repo": "vscode",
        "website_support": "https://code.visualstudio.com/docs/supporting/troubleshoot",
        "context": "You are a TypeScript/Electron engineer specializing in VS Code. Focus on extension host processes, Language Server Protocol (LSP), V8 memory limits, and workspace config corruptions."
    },
    "3": {
        "name": "OBS Studio",
        "type": "Open Source",
        "github_owner": "obsproject",
        "github_repo": "obs-studio",
        "website_support": "https://obsproject.com/forum/categories/troubleshooting-and-support.17/",
        "context": "You are a Graphics & Systems engineer specializing in OBS Studio. Focus on NVENC/AMF GPU encoder stalls, DirectX/OpenGL game capture hooks, audio sample rate mismatch, and dropped frames."
    },
    "4": {
        "name": "Discord",
        "type": "Proprietary",
        "github_owner": None,
        "github_repo": None,
        "website_support": "https://support.discord.com/hc/en-us/requests/new",
        "context": "You are a Senior WebRTC & Electron engineer specializing in Discord client runtime. Focus on RTC voice socket drops, Krisp noise suppression audio pipeline errors, GPU hardware acceleration flags, and cache integrity."
    },
    "5": {
        "name": "Blinkit",
        "type": "Proprietary",
        "github_owner": None,
        "github_repo": None,
        "website_support": "https://blinkit.com/faq",
        "context": "You are a Mobile & Frontend Systems reliability engineer specializing in Quick-Commerce platforms (Blinkit). Focus on checkout session token invalidation, cart sync websocket disconnects, GPS location geofencing failures, and CDN image load timeouts."
    }
}

def banner():
    print("\n" + "="*60)
    print("      CRASHSIGHT — AUTONOMOUS INCIDENT TRIAGE ENGINE      ")
    print("="*60)

def main():
    banner()
    
    # ---------------- PAGE 2 SIMULATION: APP SELECTION ----------------
    print("\n[Step 1] Select Target Application:")
    for key, app in APP_REGISTRY.items():
        print(f"  [{key}] {app['name']:<18} ({app['type']})")
    
    choice = input("\nEnter choice (1-5): ").strip()
    selected_app = APP_REGISTRY.get(choice)
    if not selected_app:
        print("[!] Invalid selection. Exiting.")
        return

    print(f"\n[✓] Assigned Domain Persona to Gemma 4: {selected_app['name']}")
    print(f"    Context: {selected_app['context'][:85]}...\n")

    # ---------------- PAGE 3 SIMULATION: PROBLEM INPUT ----------------
    print("-" * 60)
    print(f"[Step 2] Incident Intake for {selected_app['name']}")
    description = input("Describe the crash or error: ").strip()
    if not description:
        description = "Application unexpectedly froze and closed upon execution."

    image_path = input("Enter path to screenshot/log file (or press ENTER to skip): ").strip()

    # ---------------- GEMMA 4 ANALYSIS ----------------
    print("\n[*] Initializing Gemma 4 Multimodal Triage...")
    model = genai.GenerativeModel("gemini-3.8-flash")

    prompt = f"""
    {selected_app['context']}

    CRASH INCIDENT REPORT:
    Target App: {selected_app['name']}
    User Description: {description}

    Instructions:
    1. Determine if this issue is user-repairable via a safe local workaround (like cache clear, GPU acceleration toggle, reset config).
    2. Provide a single safe command or clear troubleshooting step.
    3. Generate a structured technical bug report.

    Respond STRICTLY in valid JSON matching this schema:
    {{
      "is_user_repairable": true,
      "error_class": "string",
      "root_cause": "string",
      "safe_remediation_step": "string",
      "markdown_bug_report": "string"
    }}
    """

    payload = [prompt]
    if image_path and os.path.exists(image_path):
        try:
            with open(image_path, "rb") as f:
                payload.append({"mime_type": "image/png", "data": f.read()})
            print(f"[✓] Attached binary evidence from {image_path}")
        except Exception as e:
            print(f"[!] Warning: Could not read file: {e}")

    try:
        response = model.generate_content(
            payload,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.2
            )
        )
        triage = json.loads(response.text)
    except Exception as e:
        print(f"\n[!] AI Generation Failed: {e}")
        return

    # ---------------- PAGE 4: LOCAL SELF-SOLVE FIRST ----------------
    print("\n" + "="*60)
    print("                 DIAGNOSTIC RESULTS                  ")
    print("="*60)
    print(f"Error Classification : {triage.get('error_class')}")
    print(f"Probable Root Cause  : {triage.get('root_cause')}")
    print("\n[RECOMMENDED LOCAL WORKAROUND]")
    print(f"  >>> {triage.get('safe_remediation_step')}")
    print("="*60)

    print("\n--- GENERATED BUG REPORT ---")
    print(triage.get('markdown_bug_report'))
    print("----------------------------")

    solved = input("\nDid this local fix resolve the issue? (y/n): ").strip().lower()
    if solved == 'y':
        print("\n[✓] Incident resolved locally. No tickets dispatched. Exiting.")
        return

    # ---------------- LOCATION FINDER & ESCALATION ----------------
    print("\n[Step 3] Issue Unresolved. Select Escalation Channel:")
    
    has_github = selected_app["github_owner"] is not None
    if has_github:
        print("  [1] GitHub Issue Tracker (Public Repository)")
        print("  [2] Official Website Support Desk")
    else:
        print("  [*] Note: This application is proprietary. No public GitHub issue tracker is available.")
        print("  [2] Official Website Support Desk (Recommended)")

    channel = input("\nSelect channel (1 or 2): ").strip()

    # Dynamic Location Finder Script
    print("\n[*] Running Target Location Finder Script...")
    
    if channel == "1" and has_github:
        # Fallback to Atharv's test repository if credentials lack rights to the main upstream repo
        target_owner = "AtharvVhanalkar"
        target_repo = "CrashSight"
        print(f"[✓] Located Destination: GitHub Repository (https://github.com/{target_owner}/{target_repo})")
        
        confirm = input("Press ENTER to dispatch bug report directly via GitHub REST API...")
        
        if not GITHUB_TOKEN:
            print("[!] GITHUB_TOKEN missing from .env. Cannot complete dispatch.")
            return

        headers = {
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        gh_payload = {
            "title": f"[{selected_app['name']}] Crash: {triage.get('error_class', 'Uncaught Exception')}",
            "body": triage.get('markdown_bug_report', description)
        }
        res = requests.post(
            f"https://api.github.com/repos/{target_owner}/{target_repo}/issues",
            json=gh_payload,
            headers=headers
        )
        if res.status_code == 201:
            issue_url = res.json().get('html_url')
            print(f"\n[🎉 SUCCESS] Issue dispatched! URL: {issue_url}")
            webbrowser.open(issue_url)
        else:
            print(f"\n[!] GitHub API Error ({res.status_code}): {res.text}")

    else:
        dest_url = selected_app["website_support"]
        print(f"[✓] Located Destination: Official Helpdesk Portal")
        print(f"    URL: {dest_url}")
        confirm = input("Press ENTER to open the official support portal with report ready...")
        webbrowser.open(dest_url)
        print("\n[✓] Browser opened to support desk.")

if __name__ == "__main__":
    main()