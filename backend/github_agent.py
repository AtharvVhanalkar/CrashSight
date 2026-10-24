import os
import requests
from dotenv import load_dotenv

# Load the keys from your .env file
load_dotenv()

def dispatch_issue(repo_owner: str, repo_name: str, title: str, body: str) -> dict:
    """
    Agent Skill 2: Autonomously routes the Markdown report to the target GitHub repository.
    """
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return {"status": "error", "message": "GitHub token missing from environment."}

    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    payload = {
        "title": title,
        "body": body
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 201:
        return {"status": "success", "url": response.json().get('html_url')}
    else:
        return {"status": "error", "message": response.text}