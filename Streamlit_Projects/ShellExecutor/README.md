# ⚡ ShellExecutor Pro

**ShellExecutor Pro** is an enterprise-grade Python Web Application built with **Streamlit** to manage remote Linux/Unix servers and execute shell scripts safely. It features **Ollama AI-powered pre-execution guardrails** that assess command impact criticality (`Usual`, `Warning`, `Danger`) and prompt an interactive approval modal before any command touches the remote server.

---

## 🌟 Key Features

### 🖥️ Tab 1: Remote Server Credentials Management
- **Full Credential Lifecycle**: Add, edit, test, and delete remote server credentials.
- **Support for All Auth Types**:
  - Password authentication.
  - SSH Private Key (RSA, Ed25519, ECDSA) with optional passphrase.
- **AES-Fernet Local Encryption**: Sensitive credentials (passwords, private keys, passphrases) are encrypted on disk in `data/servers.json` using AES-Fernet keys (`data/.secret.key`).
- **Instant Connection Test**: Tests SSH handshake, reports latency in milliseconds, remote OS kernel version, uptime, and user identity.

### 💻 Tab 2: Terminal & Shell Script Execution
- **Server Selection**: Dropdown with connection status indicators.
- **Multiple Input Methods**:
  - Single commands or multi-line shell scripts.
  - Upload `.sh` or `.bash` script files directly.
  - Pre-built preset commands (`df -h`, `free -m`, `ps aux`, `uptime`, `ss -tulpn`, `docker ps`, etc.).
- **3 Execution Modes**:
  1. **Usual / Synchronous Mode**: Executes directly and streams stdout/stderr live into the terminal console.
  2. **Async Background Mode**: Runs in a non-blocking background thread with an active job tracker.
  3. **Nohup Background Mode**: Executes detached via `nohup bash -c '...' > /tmp/shellexec_<ts>.log 2>&1 & echo $!`. Captures remote PID, provides a remote process monitor (`ps -p <PID>`), log tailer, and process termination (`kill -15 <PID>`).
- **Adjustable Bottom Terminal**:
  - Dynamic height slider (150px to 850px).
  - Modern terminal aesthetics (dark obsidian background, monospace Fira Code font, mac-style window controls).
  - One-click **Download Log** (.log file) and **Clear Console**.

### 🛡️ AI Impact Criticality Guardrail (Ollama API)
- Connects to local or remote **Ollama API** (`http://localhost:11434`).
- Automatically scans installed models (e.g., `gemma4:latest`, `llama3`, `mistral`, etc.).
- Evaluates shell commands against 3 criticality tiers:
  - 🟢 **Usual**: Safe, read-only diagnostic commands (`ls`, `df`, `cat`, `uptime`, `ps`, `ping`).
  - 🟡 **Warning**: State-changing operations, service restarts, package installations (`systemctl restart`, `apt install`, `docker stop`, `chmod`).
  - 🔴 **DANGER**: Destructive operations, file wipes, formatting, reboots (`rm -rf`, `mkfs`, `dd`, `iptables -F`, `reboot`, `drop database`).
- **Interactive Approval Modal Dialog**:
  - Renders a prominent modal dialog displaying the criticality badge, summary, blast radius risk analysis, and safety recommendations.
  - **Approve & Execute** button (runs the command in the requested mode).
  - **Reject & Abort** button (cancels execution and logs the rejection to the console).
- **Defense in Depth**: Features a built-in heuristic guardrail engine that ensures catastrophic commands are intercepted even if Ollama is unreachable.

### 🛡️ Tab 3: AI Safety Inspector Sandbox
- Test and inspect how Ollama analyzes any arbitrary shell script without connecting to or running it on a remote server.

---

## 🚀 Quick Start

### 1. Requirements
- Python 3.10+
- [Ollama](https://ollama.com/) running locally (`ollama serve`) with any model pulled (e.g. `ollama run gemma4:latest`)

### 2. Installation
Clone or navigate to the project directory:
```bash
cd ShellExecutor
```

Create a virtual environment and install dependencies:
```bash
# Using uv (recommended for ultra-fast setup):
uv venv .venv
uv pip install --python .\.venv\Scripts\python.exe -r requirements.txt

# Or using standard pip:
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Run the App
- **Windows (Double-click or run):**
  ```cmd
  run.bat
  ```
- **PowerShell:**
  ```powershell
  .\run.ps1
  ```
- **Direct CLI:**
  ```bash
  .\.venv\Scripts\streamlit run app.py
  ```

Open your browser to: **http://localhost:8501**

---

## 📁 Project Structure

```
ShellExecutor/
│
├── core/
│   ├── __init__.py
│   ├── models.py            # Dataclasses (ServerCredential, AIAnalysisResult, ExecutionResult, ExecutionMode)
│   ├── storage.py           # Encrypted local credential store with Fernet encryption (CRUD)
│   ├── ssh_manager.py       # SSH client manager (sync streaming, async threads, nohup daemons)
│   └── ai_analyzer.py       # Ollama API caller & heuristic fallback rule engine
│
├── ui/
│   ├── __init__.py
│   ├── styles.py            # Custom CSS for dark modern terminal, glowing status chips, badges
│   ├── tab_credentials.py   # Page/Tab 1: Add/Edit/Delete/Test Remote Server Credentials
│   └── tab_terminal.py      # Page/Tab 2: Terminal Execution, AI Approval Modal, Resizable Output
│
├── data/                    # Generated at runtime (git-ignored)
│   ├── .secret.key          # Fernet symmetric encryption key
│   └── servers.json         # Encrypted server records
│
├── app.py                   # Streamlit main application entrypoint
├── requirements.txt         # Python dependencies
├── run.bat                  # One-click Windows CMD runner
├── run.ps1                  # One-click PowerShell runner
└── README.md                # Project documentation
```

---

## 🔒 Security Best Practices
- Passwords and SSH private keys are never stored in plain text.
- Pseudo-terminal (PTY) allocation ensures proper terminal emulation on remote Unix systems.
- Every command is intercepted by the AI approval modal before execution, preventing accidental destruction of production systems.
