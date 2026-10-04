import json
import re
import requests
from typing import List, Tuple, Optional
from core.models import AIAnalysisResult, CriticalityLevel

DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "gemma4:latest"

# Heuristic patterns for rule-based analysis & fallback safety
DANGER_PATTERNS = [
    (r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)\s+", "Recursive forceful file deletion (rm -rf)"),
    (r"\bmkfs\b", "Disk filesystem formatting (mkfs)"),
    (r"\bdd\s+if=", "Low-level raw block disk writing (dd)"),
    (r">\s*/dev/sd[a-z]", "Direct raw block device overwriting"),
    (r"\b(shutdown|reboot|poweroff|init\s+0|init\s+6)\b", "System shutdown or reboot command"),
    (r"\biptables\s+-F\b", "Flushing firewall rules entirely"),
    (r"\bdrop\s+(database|table)\b", "Database deletion query"),
    (r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:", "Fork bomb process exhaustion"),
    (r"\bchmod\s+-R\s+777\s+/", "Universal write permissions applied to root filesystem"),
    (r"\bkill\s+-9\s+1\b", "Killing init/systemd (PID 1)"),
    (r"\btruncate\s+-s\s+0\s+/", "Truncating system root files"),
]

WARNING_PATTERNS = [
    (r"\bsystemctl\s+(restart|stop|reload|disable)\b", "Service interruption or disablement"),
    (r"\b(kill|pkill|killall)\b", "Process termination signal"),
    (r"\b(apt|apt-get|yum|dnf|pacman|zypper)\s+(install|remove|purge|upgrade|dist-upgrade)\b", "Package manager modification"),
    (r"\bdocker\s+(stop|rm|rmi|prune|kill)\b", "Container or image removal/stoppage"),
    (r"\bgit\s+reset\s+--hard\b", "Hard reset of git repository discarding uncommitted changes"),
    (r"\b(chmod|chown)\s+-R\b", "Recursive permission or ownership change"),
    (r"\bcrontab\s+-r\b", "Removing user crontab schedule"),
    (r"\buserdel\b", "User account deletion"),
    (r"\bmv\b.*(\*|\.tar|\.zip)", "Bulk file move or rename operation"),
]

USUAL_PATTERNS = [
    (r"\b(ls|ll|dir|pwd|cd)\b", "Directory and file navigation / listing"),
    (r"\b(cat|head|tail|less|more|grep|awk|sed|wc)\b", "File reading or text filtering"),
    (r"\b(df|du|free|top|htop|vmstat|iostat|uptime)\b", "System resource and disk inspection"),
    (r"\b(ps|pgrep|pstree)\b", "Process listing"),
    (r"\b(ip|ifconfig|netstat|ss|ping|curl|wget|traceroute)\b", "Network diagnostic inspection"),
    (r"\b(whoami|id|uname|hostname|date|env|printenv|echo)\b", "System metadata inspection"),
]


def check_ollama_status(url: str = DEFAULT_OLLAMA_URL) -> Tuple[bool, str, List[str]]:
    """Check if Ollama is accessible and retrieve available models."""
    try:
        resp = requests.get(f"{url.rstrip('/')}/api/tags", timeout=3)
        if resp.status_code == 200:
            data = resp.json()
            models = [m.get("name") for m in data.get("models", []) if m.get("name")]
            return True, f"Ollama online ({len(models)} models available)", models
        return False, f"Ollama returned HTTP {resp.status_code}", []
    except Exception as e:
        return False, f"Cannot reach Ollama at {url}: {str(e)}", []


def clean_json_response(text: str) -> dict:
    """Safely extracts JSON from an LLM response string."""
    if not text:
        return {}
    cleaned = text.strip()
    # Strip markdown code fences
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"```\s*$", "", cleaned, flags=re.MULTILINE)
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except Exception:
        # Regex search for first JSON object
        match = re.search(r"\{[\s\S]*\}", cleaned)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass
    return {}


def heuristic_analysis(command: str) -> AIAnalysisResult:
    """Fast fallback rule-based analyzer when Ollama is offline or fails."""
    cmd_lower = command.lower()

    # Check Danger
    for pattern, desc in DANGER_PATTERNS:
        if re.search(pattern, cmd_lower):
            return AIAnalysisResult(
                criticality=CriticalityLevel.DANGER,
                summary=f"Detected high-risk pattern: {desc}.",
                risks="Permanent data loss, service crash, or severe system disruption may occur.",
                recommendation="Review the target path and parameters carefully before proceeding. Ensure recent backups exist.",
                model_used="Heuristic Guardrail Engine",
                command_analyzed=command,
                is_fallback=True,
            )

    # Check Warning
    for pattern, desc in WARNING_PATTERNS:
        if re.search(pattern, cmd_lower):
            return AIAnalysisResult(
                criticality=CriticalityLevel.WARNING,
                summary=f"Detected state-modifying operation: {desc}.",
                risks="Modifies running services, packages, or process states.",
                recommendation="Verify service dependencies and impacts on connected clients.",
                model_used="Heuristic Guardrail Engine",
                command_analyzed=command,
                is_fallback=True,
            )

    # Default Usual
    return AIAnalysisResult(
        criticality=CriticalityLevel.USUAL,
        summary="Standard administrative or diagnostic command.",
        risks="Low operational risk. Standard execution parameters.",
        recommendation="Proceed with execution when ready.",
        model_used="Heuristic Guardrail Engine",
        command_analyzed=command,
        is_fallback=True,
    )


def analyze_command(
    command: str,
    ollama_url: str = DEFAULT_OLLAMA_URL,
    model_name: str = DEFAULT_MODEL,
    timeout_sec: int = 25
) -> AIAnalysisResult:
    """
    Analyzes a shell command using Ollama API with fallback to heuristic rules.
    Returns structured AIAnalysisResult with criticality (Usual, Warning, Danger).
    """
    stripped_cmd = command.strip()
    if not stripped_cmd:
        return AIAnalysisResult(
            criticality=CriticalityLevel.USUAL,
            summary="Empty command string.",
            risks="None",
            recommendation="Enter a command to execute.",
            command_analyzed="",
            model_used="N/A",
        )

    # First check heuristic: if critical danger pattern is matched, baseline is set
    fallback_res = heuristic_analysis(stripped_cmd)

    prompt = f"""You are a Linux and Unix DevOps security expert evaluating a command before it runs on a remote server.
Analyze the following shell command for execution risk, side-effects, and criticality:

COMMAND TO EVALUATE:
```bash
{stripped_cmd}
```

CRITICALITY DEFINITIONS:
- "Usual": Read-only diagnostics, file viewing, status inspection (e.g., ls, cat, df, top, ping, ps, grep, echo, pwd). Harmless.
- "Warning": Modifies system state, restarts services, installs packages, changes configurations, high resource usage (e.g., systemctl restart, apt install, docker stop, git pull, chmod, chown).
- "Danger": Destructive, permanent file deletion, disk formatting, kernel panic, firewall flush, system shutdown/reboot (e.g., rm -rf, mkfs, dd, iptables -F, drop database, kill -9 1, shutdown).

Return STRICTLY a JSON object with this exact structure:
{{
  "criticality": "Usual" | "Warning" | "Danger",
  "summary": "1 concise sentence describing what this command does",
  "risks": "1-2 sentences detailing potential risks, outage likelihood, or blast radius",
  "recommendation": "1 actionable safety recommendation or best practice"
}}"""

    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.1,
            "top_p": 0.9,
        }
    }

    try:
        url = f"{ollama_url.rstrip('/')}/api/generate"
        response = requests.post(url, json=payload, timeout=timeout_sec)

        if response.status_code == 200:
            raw_text = response.json().get("response", "")
            data = clean_json_response(raw_text)

            crit_raw = str(data.get("criticality", "")).strip().capitalize()
            if crit_raw == "Danger" or fallback_res.criticality == CriticalityLevel.DANGER:
                criticality = CriticalityLevel.DANGER
            elif crit_raw == "Warning" or fallback_res.criticality == CriticalityLevel.WARNING:
                criticality = CriticalityLevel.WARNING
            else:
                criticality = CriticalityLevel.USUAL

            summary = data.get("summary") or fallback_res.summary
            risks = data.get("risks") or fallback_res.risks
            rec = data.get("recommendation") or fallback_res.recommendation

            return AIAnalysisResult(
                criticality=criticality,
                summary=summary,
                risks=risks,
                recommendation=rec,
                model_used=model_name,
                command_analyzed=stripped_cmd,
                is_fallback=False,
            )
        else:
            # Fall back to heuristic
            fallback_res.summary += f" (Ollama error: HTTP {response.status_code})"
            return fallback_res

    except Exception as e:
        # Fall back to heuristic gracefully
        fallback_res.summary += f" (Ollama unreachable, used heuristic engine)"
        return fallback_res
