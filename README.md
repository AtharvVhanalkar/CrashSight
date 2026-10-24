# 👁️ CrashSight

[![Hacktoberfest](https://img.shields.io/badge/Hacktoberfest-2026-blueviolet.svg)](#) [![Gemma 4](https://img.shields.io/badge/Best_Use_of-Gemma_4-emerald.svg)](#) [![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](#)

**An autonomous, multimodal crash triage agent bridging the gap between vague user bug reports and complex system telemetry.** 
Built for the **Best Use of Gemma 4** track at Hacktoberfest Hack Day Pune.

---

## 🛑 The Problem
When software crashes, users submit vague screenshots ("the screen froze") with zero technical context. Meanwhile, the actual diagnostic data is buried in cryptic, unreadable system logs (like macOS `.ips` or Windows `.evtx` files). Developers waste countless hours manually trying to correlate a visual UI glitch with a low-level hex stack trace to figure out what actually broke.

## ⚡ The Solution
CrashSight is an enterprise-grade B2B SaaS triage engine. Users drag and drop an error screenshot alongside a crash log file into a single web UI. Gemma 4’s multimodal AI cross-references the visual state with the log data to:
1. **Provide a "Solution-First" Gate:** Instantly suggest a safe, local fix to the user (e.g., "Clear your cache"), drastically reducing developer ticket spam.
2. **Automate Ticket Dispatch:** If unresolved, the agent automatically synthesizes the visual and log data into a highly structured, developer-ready Markdown report and dispatches it directly to the relevant GitHub repository via the REST API.

---

## 🧠 Best Use of Gemma 4 (Key Features)

* **Multimodal Telemetry Fusion:** We push Gemma 4 beyond basic text generation by simultaneously feeding it visual data (UI screenshots) and unstructured system telemetry (logs). 
* **Dynamic B2B Context Injection:** CrashSight operates as a scalable routing engine. Based on the target application (e.g., VLC, VS Code, OBS), the backend injects a specialized system prompt into Gemma 4. The model dynamically shifts its persona from a "C++ Video Codec Engineer" to a "TypeScript Electron Expert," ensuring highly accurate, domain-specific bug reports.
* **Confidence Scoring & Triage:** Gemma 4 evaluates the crash signature and outputs a strict JSON payload containing the root cause, confidence score, subsystem identification, and a boolean gate for user-level repairability.

---

## 🏗️ System Architecture

Our architecture is split into a lightning-fast, OS-agnostic frontend and a robust Python backend.

* **Frontend (Vanilla Stack):** A zero-dependency Single Page Application (SPA) built with HTML5, Tailwind CSS, and Vanilla JavaScript. Features dynamic loading states, asynchronous aura animations, and Drag-and-Drop file processing.
* **Backend (FastAPI):** An asynchronous Python server handling CORS, multipart file uploads, and API routing.
* **AI Layer (Google GenAI):** Direct integration with Google's API to leverage Gemma 4 for multimodal processing.
* **Integration Layer:** Native Python requests to the GitHub REST API for authenticated issue dispatch.

### Directory Structure
```text
crashsight/
├── demo-assets/               # Dummy logs and screenshots for OS-agnostic live demos
├── frontend/                  
│   └── index.html             # Main Dashboard UI & Vanilla JS logic
└── backend/                   
    ├── main.py                # FastAPI server, Routes, and CORS middleware
    ├── gemma_agent.py         # AI logic and APP_CONFIGS dictionary
    ├── github_agent.py        # GitHub REST API dispatch logic
    ├── requirements.txt       # Python dependencies
    └── .env                   # Secret keys (Git-ignored)