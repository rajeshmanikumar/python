import streamlit as st
from core.models import ServerCredential
from core.storage import storage
from core.ai_analyzer import check_ollama_status, DEFAULT_OLLAMA_URL, DEFAULT_MODEL, analyze_command
from ui.styles import get_custom_css
from ui.tab_credentials import render_credentials_tab
from ui.tab_terminal import render_terminal_tab

# Page configuration
st.set_page_config(
    page_title="ShellExecutor Pro - AI Guarded Remote Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject custom modern styles
st.markdown(get_custom_css(), unsafe_allow_html=True)

# Initialize Session State
if "terminal_output" not in st.session_state:
    st.session_state["terminal_output"] = ""
if "terminal_height_val" not in st.session_state:
    st.session_state["terminal_height_val"] = 380
if "modal_open" not in st.session_state:
    st.session_state["modal_open"] = False
if "execute_approved" not in st.session_state:
    st.session_state["execute_approved"] = False
if "ollama_url" not in st.session_state:
    st.session_state["ollama_url"] = DEFAULT_OLLAMA_URL
if "ollama_model" not in st.session_state:
    st.session_state["ollama_model"] = DEFAULT_MODEL


# SIDEBAR: Status & Settings
with st.sidebar:
    st.markdown("## ⚡ ShellExecutor Pro")
    st.caption("AI-Guarded Remote SSH Script & Command Platform")

    st.markdown("---")
    st.markdown("### 🤖 Ollama AI Guardrail")

    ollama_url_input = st.text_input(
        "Ollama Endpoint:",
        value=st.session_state.get("ollama_url", DEFAULT_OLLAMA_URL),
        help="Local or remote Ollama server URL"
    )
    st.session_state["ollama_url"] = ollama_url_input

    # Ollama status check
    is_online, status_msg, available_models = check_ollama_status(ollama_url_input)

    if is_online:
        st.markdown(f'<span class="badge-usual">🟢 Ollama Online</span>', unsafe_allow_html=True)
        if available_models:
            current_model = st.session_state.get("ollama_model", DEFAULT_MODEL)
            default_index = available_models.index(current_model) if current_model in available_models else 0
            chosen_model = st.selectbox(
                "Select AI Model:",
                options=available_models,
                index=default_index,
                help="Model used to analyze command safety before execution."
            )
            st.session_state["ollama_model"] = chosen_model
        else:
            st.warning("No models found in Ollama. Pull a model (e.g., `ollama pull gemma4:latest`).")
    else:
        st.markdown(f'<span class="badge-danger">🔴 Ollama Offline</span>', unsafe_allow_html=True)
        st.caption(status_msg)
        st.info("ℹ️ Heuristic rule guardrails will automatically protect commands if Ollama is unreachable.")

    if st.button("🔄 Refresh Ollama Models", use_container_width=True):
        st.rerun()

    st.markdown("---")
    st.markdown("### 🔒 Security Status")
    st.markdown("- **Storage Encryption:** `AES-Fernet (Active)`")
    st.markdown("- **Safety Guardrail:** `Pre-Execution AI Modal`")
    st.markdown("- **Shell Protocol:** `SSH v2 (Paramiko)`")

    st.markdown("---")
    st.caption("ShellExecutor Pro v1.0.0 &bull; Built with Streamlit & Ollama")


# MAIN HEADER
st.title("⚡ ShellExecutor Pro")
st.caption("Execute shell scripts securely on remote Linux/Unix servers with AI impact analysis and approval.")

# TAB NAVIGATION
tab_names = ["🖥️ 1. Server Credentials", "💻 2. Terminal & Script Execution", "🛡️ 3. AI Safety Inspector"]
tab_creds, tab_term, tab_ai = st.tabs(tab_names)

with tab_creds:
    render_credentials_tab()

with tab_term:
    render_terminal_tab()

with tab_ai:
    st.markdown("### 🛡️ AI Command Safety Inspector & Sandbox")
    st.caption("Directly test and inspect how Ollama classifies shell commands without running them on any server.")

    test_cmd = st.text_area(
        "Enter shell command to test AI classification:",
        value="rm -rf /var/log/nginx/* && systemctl restart nginx",
        height=100
    )

    if st.button("🔍 Analyze Impact Criticality", type="primary"):
        with st.spinner("Analyzing command with Ollama..."):
            res = analyze_command(
                command=test_cmd,
                ollama_url=st.session_state.get("ollama_url", DEFAULT_OLLAMA_URL),
                model_name=st.session_state.get("ollama_model", DEFAULT_MODEL)
            )

            c1, c2, c3 = st.columns(3)
            with c1:
                crit = res.criticality.value if hasattr(res.criticality, "value") else str(res.criticality)
                if crit == "Danger":
                    st.error(f"Criticality: 🔴 **{crit.upper()}**")
                elif crit == "Warning":
                    st.warning(f"Criticality: 🟡 **{crit.upper()}**")
                else:
                    st.success(f"Criticality: 🟢 **{crit.upper()}**")
            with c2:
                st.metric("Model Used", res.model_used)
            with c3:
                st.metric("Engine", "Heuristic Fallback" if res.is_fallback else "Ollama LLM")

            st.markdown("##### 📋 Analysis Result")
            st.markdown(f"- **Summary:** {res.summary}")
            st.markdown(f"- **Risks & Blast Radius:** {res.risks}")
            st.markdown(f"- **Safety Recommendation:** {res.recommendation}")
