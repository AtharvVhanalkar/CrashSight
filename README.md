# CrashSight — Autonomous Incident Triage & Self-Healing Agent

> Multimodal in-situ crash diagnosis, one-click safe client remediation, and automated repository escalation powered by Gemma 4 and Gemini.

---

## ⚡ Overview

Traditional crash reporting tools (Apple Crash Reporter, Windows Error Reporting, and Crashlytics) act as one-way telemetry systems: they collect raw crash data for future developer sprints while leaving the end user stranded with a broken application.

**CrashSight inverts this paradigm:**

1. **Edge Self-Healing First:** Diagnoses root causes using visual screenshots and symptoms, then generates and executes safe local remediation commands, such as cache clearing, lockfile cleanup, and GPU flag toggling, to restore functionality immediately.
2. **Dual-Engine Inference:** Supports fully air-gapped local inference via **Gemma 4 (Ollama)** or cloud-based multimodal analysis via the **Gemini API**.
3. **Autonomous Escalation:** When a crash originates from an upstream code defect that cannot be fixed locally, CrashSight prepares a reproduction-ready issue for submission to GitHub or the application's official support desk.

---

## 🧭 Pre-Flight Checklist (Cold-Restart Guide)

Follow these steps whenever starting CrashSight for a live demo.

### 1. Start Ollama (Local Gemma 4)

If you are using local inference, start the Gemma 4 model:

```bash
ollama run gemma4
```

If the model is not installed, pull it first:

```bash
ollama pull gemma4
```

### 2. Free Port 8000

If the backend fails with `[Errno 48] Address already in use`, stop the process occupying port 8000.

**macOS / Linux:**

```bash
lsof -ti :8000 | xargs kill -9 2>/dev/null || true
```

> **Note:** This command forcefully terminates processes using port 8000. Make sure the process is safe to stop before running it.

### 3. Verify API Keys

Check that the `backend/.env` file contains the required environment variables:

```env
GEMINI_API_KEY=your_gemini_api_key_here
GITHUB_TOKEN=your_github_personal_access_token_here
```

Ensure the credentials are valid and have the permissions required for the features you intend to use.

### 4. Launch the Backend from a Native Terminal

On macOS, launch Uvicorn from the native Terminal.app if VS Code's integrated terminal triggers macOS privacy permission prompts when executing remediation commands.

Grant only the permissions necessary for the application's intended operations.

---

## 🛠️ Prerequisites & Dependencies

Before installing CrashSight, ensure the following tools are available.

| Dependency | Requirement | Purpose |
|---|---|---|
| Python | 3.10 or higher | Backend runtime |
| Git | Recent version | Repository management |
| Node.js | Optional, depending on frontend tooling | JavaScript development |
| curl | Available in the system shell | HTTP requests and API testing |
| Ollama | Optional | Local Gemma 4 inference |

### Required Python Libraries

Install the required dependencies using the project's requirements file:

```bash
pip install -r requirements.txt
```

Alternatively, install the core dependencies manually:

```bash
pip install fastapi uvicorn python-multipart google-generativeai python-dotenv pydantic requests
```

> **Note:** The manually listed packages are a baseline. The `requirements.txt` file should be treated as the source of truth for the project's actual dependencies.

---

## ⚙️ Step-by-Step Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/AtharvVhanalkar/CrashSight.git
cd CrashSight
```

### Step 2: Set Up the Python Virtual Environment

Navigate to the backend directory:

```bash
cd backend
```

Create a virtual environment:

```bash
python3 -m venv venv
```

Activate it using the appropriate command for your operating system.

**macOS / Linux:**

```bash
source venv/bin/activate
```

**Windows — Command Prompt:**

```cmd
venv\Scripts\activate.bat
```

**Windows — PowerShell:**

```powershell
.\venv\Scripts\Activate.ps1
```

Install the project dependencies:

```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables

Create a `.env` file inside the `backend/` directory.

Add the following variables:

```env
GEMINI_API_KEY=your_gemini_api_key_here
GITHUB_TOKEN=your_github_personal_access_token_here
```

Replace the placeholder values with your actual credentials.

**Environment variable details:**

- `GEMINI_API_KEY`: Used for cloud-based Gemini inference.
- `GITHUB_TOKEN`: Used for authenticated GitHub operations, such as creating issues, when supported by the backend implementation.

**GitHub permissions:** Grant only the minimum permissions necessary for the intended repository operations. For private repositories, ensure the token has access to the target repository and the required issue-management permissions.

**Security recommendations:**

- Never commit your `.env` file or API tokens to Git.
- Add `.env` to `.gitignore`.
- Use placeholder values in example configuration files.
- Rotate any credentials that are accidentally exposed.

Example `.gitignore` entries:

```gitignore
.env
venv/
__pycache__/
*.py[cod]
```

---

## 🚀 Launching the Platform

### Step 1: Start the FastAPI Backend

Ensure that you are inside the `backend/` directory and that your virtual environment is activated.

Start the server:

```bash
uvicorn main:app --reload
```

The backend should be accessible at:

- **API Base URL:** http://127.0.0.1:8000
- **Interactive API Documentation:** http://127.0.0.1:8000/docs

Keep the terminal running while using the application.

### Step 2: Open the Frontend

Choose either of the following options.

**Option A: Open Directly**

Open `frontend/index.html` in your browser using Finder or File Explorer.

**Option B: Use VS Code Live Server**

Serve the frontend using the Live Server extension.

The frontend will typically be available at:

```text
http://localhost:5500
```

Ensure that the frontend's configured API base URL matches the backend address and that browser requests are permitted by the backend's CORS configuration.

---

## 🧠 Core Capabilities

### 1. Multimodal Crash Diagnosis

Analyze crash symptoms and visual evidence to help identify potential root causes.

### 2. Local Self-Healing

Generate remediation recommendations for recoverable client-side problems, including:

- Application cache cleanup
- Lockfile cleanup
- GPU acceleration configuration changes
- Other supported local recovery operations

Remediation actions should be validated before execution and should avoid destructive changes.

### 3. Dual-Engine AI Inference

Choose between two inference approaches:

- **Local inference:** Gemma 4 through Ollama, where supported by the backend implementation.
- **Cloud inference:** Gemini API for hosted AI analysis.

Local inference can reduce dependence on cloud connectivity, but a fully air-gapped deployment also requires all necessary models and dependencies to be available locally.

### 4. Automated Issue Escalation

When an issue cannot be resolved locally, CrashSight can prepare structured reports containing diagnostic context and reproduction information for escalation to a repository or support team.

The available escalation destinations depend on the application's integration and backend configuration.

---

## 📱 Supported Applications

CrashSight targets several applications with different diagnostic contexts and escalation destinations.

| Application | Application Type | Diagnostic Context | Escalation Target |
|---|---|---|---|
| VLC Media Player | Open Source | Codec failures, demuxer pipeline, GPU acceleration | GitHub / VideoLAN |
| VS Code | Open Source | V8 heap, Language Server Protocol (LSP), extension hosts | GitHub / Microsoft |
| OBS Studio | Open Source | NVENC encoding, DirectX/Metal hooks, audio jitter | GitHub / obsproject |
| Discord | Proprietary | WebRTC ICE negotiation, voice gateways, GPU cache | Official Support Portal |
| Blinkit | Proprietary | Cart synchronization, WebSocket connections, checkout tokens, geofencing | Customer Support Desk |

> **Note:** Application support and automated escalation depend on the diagnostic rules and integrations implemented in the current version. Listing an application does not imply that every recovery action or escalation endpoint is already configured.

---

## 🧰 Troubleshooting Matrix

| Error Symptom | Possible Root Cause | Recommended Fix |
|---|---|---|
| `[Errno 48] Address already in use` | Port 8000 is occupied by another process or a previous backend instance. | Identify the process using port 8000 and stop it if appropriate. |
| macOS "Data Access Blocked" popup | macOS privacy controls may be restricting an operation launched from the integrated development environment. | Try launching Uvicorn from the native Terminal.app and review the requested permissions. |
| `No matching processes belonging to you` | The targeted process may already have exited, or it may belong to another user. | Check whether the backend is still running before retrying the cleanup command. |
| `Failed to fetch` | The backend may not be running, the API base URL may be incorrect, or the browser request may be blocked by CORS. | Start Uvicorn, verify the API URL, and inspect the browser console and backend logs. |
| `404 gemini-2.5-flash` | The configured model identifier may be unavailable for the selected API or account. | Verify the supported model identifiers for your Gemini API configuration and update the backend model setting. |
| Invalid API key | The API credential may be missing, invalid, or incorrectly configured. | Check the `backend/.env` file and restart the backend after updating the configuration. |
| GitHub issue creation fails | The GitHub token may be invalid or lack the necessary repository permissions. | Verify the token, repository access, and issue-management permissions. |
| Ollama connection fails | Ollama may not be running, or the requested model may not be installed. | Start Ollama and verify that the configured model is available locally. |

### Useful Backend Commands

**Start the backend:**

```bash
uvicorn main:app --reload
```

**Check whether port 8000 is occupied (macOS / Linux):**

```bash
lsof -i :8000
```

**Stop the process using port 8000 (macOS / Linux):**

```bash
lsof -ti :8000 | xargs kill -9 2>/dev/null || true
```

**Verify the API documentation:**

Open:

```text
http://127.0.0.1:8000/docs
```

---

## 🔒 Security & Safe Remediation

CrashSight is designed to help users recover from application failures without unnecessarily exposing sensitive diagnostic data or making risky system changes.

Recommended safeguards include:

- **Validate remediation commands:** Allow only explicitly supported operations.
- **Avoid arbitrary shell execution:** Never execute unrestricted AI-generated shell commands without validation and appropriate authorization.
- **Request user confirmation:** Explain the impact of potentially disruptive remediation actions before execution.
- **Protect diagnostic data:** Avoid exposing credentials, personal information, or sensitive memory contents in crash reports.
- **Secure API credentials:** Keep tokens in environment variables and never publish them in source control.
- **Use least-privilege access:** Limit permissions for local processes and external API integrations.
- **Preserve user data:** Prefer reversible recovery operations and back up important configuration files before modifying them.

---

## 🗺️ Project Structure

The primary directories used in the setup instructions are:

```text
CrashSight/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── .env
│   └── venv/
└── frontend/
    └── index.html
```

> **Note:** This is an illustrative structure based on the setup instructions. Additional files, modules, and directories may exist in the actual repository. The `.env` file should remain local and must not be committed.

---

## 🔮 Future Improvements

Potential areas for further development include:

- Expanded application-specific diagnostic rules
- More comprehensive local recovery workflows
- Improved crash reproduction and diagnostic reporting
- Additional repository and support integrations
- Stronger remediation validation and rollback support
- Enhanced offline inference capabilities
- Automated testing for recovery operations
- Improved observability, logging, and failure analysis

---

## 🤝 Contributing

Contributions, bug reports, and feature suggestions are welcome.

To contribute:

1. Fork the repository.
2. Create a feature branch.
3. Implement and test your changes.
4. Submit a pull request with a clear description of the changes.

For bugs, include the relevant error message, steps to reproduce the issue, and diagnostic information that can be shared safely.

---



## 👨‍💻 Repository

**GitHub:** https://github.com/AtharvVhanalkar/CrashSight

---

**CrashSight — Diagnose locally. Recover safely. Escalate intelligently.**
