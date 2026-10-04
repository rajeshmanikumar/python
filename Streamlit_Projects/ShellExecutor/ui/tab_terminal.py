import time
import html
import streamlit as st
from datetime import datetime
from core.models import ExecutionMode, CriticalityLevel, ServerCredential
from core.storage import storage
from core.ssh_manager import ssh_manager, ACTIVE_JOBS
from core.ai_analyzer import analyze_command, DEFAULT_OLLAMA_URL, DEFAULT_MODEL


# Common quick shell command presets
PRESET_COMMANDS = {
    "-- Select Preset (Optional) --": "",
    "System Uptime & Load (uptime)": "uptime",
    "Disk Space Usage (df -h)": "df -h",
    "Memory Usage (free -m)": "free -m",
    "Top 10 Memory Consuming Processes": "ps aux --sort=-%mem | head -n 11",
    "Top 10 CPU Consuming Processes": "ps aux --sort=-%cpu | head -n 11",
    "Network Listening Ports (ss -tulpn)": "ss -tulpn 2>/dev/null || netstat -tulpn",
    "OS & Kernel Details (uname -a)": "uname -a; cat /etc/os-release 2>/dev/null | head -n 8",
    "Docker Container Status": "docker ps -a 2>/dev/null || echo 'Docker not running'",
    "Systemd Failed Services": "systemctl --failed 2>/dev/null",
    "Nginx Status Check": "systemctl status nginx 2>/dev/null",
    "Test Destructive (Warning simulation)": "systemctl restart nginx",
    "Test Dangerous (Danger simulation)": "rm -rf /tmp/test_dir_danger/*",
}


@st.dialog("🛡️ AI Command Safety & Impact Analysis", width="large")
def show_ai_approval_dialog():
    """
    Native Streamlit modal dialog showing AI impact criticality analysis
    with Approve / Reject buttons before executing on the remote server.
    """
    analysis = st.session_state.get("pending_ai_analysis")
    pending_cmd = st.session_state.get("pending_command", "")
    pending_mode = st.session_state.get("pending_mode", ExecutionMode.NORMAL)
    selected_server = st.session_state.get("active_server")

    if not analysis or not selected_server:
        st.error("No pending command or server context.")
        if st.button("Close"):
            st.rerun()
        return

    crit = analysis.criticality
    crit_value = crit.value if hasattr(crit, "value") else str(crit)

    # Visual badge and alert style based on criticality
    if crit_value == "Danger":
        st.markdown(
            """
            <div style="background: rgba(239, 68, 68, 0.15); border: 2px solid #ef4444; border-radius: 8px; padding: 14px; margin-bottom: 15px;">
                <span class="badge-danger">🔴 CRITICALITY: DANGER</span>
                <p style="margin-top: 8px; margin-bottom: 0; color: #fca5a5; font-weight: 500;">
                    High-risk or destructive operation detected! Executing this command may lead to irreversible data loss, kernel panic, or system outage.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    elif crit_value == "Warning":
        st.markdown(
            """
            <div style="background: rgba(245, 158, 11, 0.15); border: 2px solid #f59e0b; border-radius: 8px; padding: 14px; margin-bottom: 15px;">
                <span class="badge-warning">🟡 CRITICALITY: WARNING</span>
                <p style="margin-top: 8px; margin-bottom: 0; color: #fcd34d; font-weight: 500;">
                    State-modifying or service-impacting command. Verify dependencies before proceeding.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div style="background: rgba(16, 185, 129, 0.12); border: 2px solid #10b981; border-radius: 8px; padding: 14px; margin-bottom: 15px;">
                <span class="badge-usual">🟢 CRITICALITY: USUAL</span>
                <p style="margin-top: 8px; margin-bottom: 0; color: #6ee7b7; font-weight: 500;">
                    Safe / Read-only administrative command. Minimal or no operational risk detected.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(f"**Target Host:** `{selected_server.username}@{selected_server.host}:{selected_server.port}` ({selected_server.name})")
    st.markdown(f"**Execution Mode:** `{pending_mode.upper()}` &nbsp;|&nbsp; **AI Model:** `{analysis.model_used}`")

    st.markdown("##### 📜 Command to Execute:")
    st.code(pending_cmd, language="bash")

    st.markdown("##### 🔍 AI Impact Assessment:")
    st.markdown(f"**Summary:** {analysis.summary}")
    st.markdown(f"**Potential Risks:** {analysis.risks}")
    st.markdown(f"**Recommendation:** {analysis.recommendation}")

    st.markdown("---")
    c_approve, c_reject = st.columns([1, 1], gap="medium")

    with c_approve:
        approve_label = "✅ Approve & Run Command"
        if crit_value == "Danger":
            approve_label = "⚠️ I Understand the Risk - Force Execute"
        if st.button(approve_label, type="primary", use_container_width=True):
            st.session_state["execute_approved"] = True
            st.session_state["modal_open"] = False
            st.rerun()

    with c_reject:
        if st.button("❌ Reject & Abort", type="secondary", use_container_width=True):
            # Record rejection in terminal history
            ts = datetime.now().strftime("%H:%M:%S")
            rejection_log = (
                f"\n[{ts}] ❌ COMMAND REJECTED BY USER\n"
                f"Target: {selected_server.name} ({selected_server.host})\n"
                f"Command: {pending_cmd}\n"
                f"Criticality: {crit_value}\n"
                f"AI Summary: {analysis.summary}\n"
                f"{'='*60}\n"
            )
            current_out = st.session_state.get("terminal_output", "")
            st.session_state["terminal_output"] = current_out + rejection_log
            st.session_state["pending_ai_analysis"] = None
            st.session_state["pending_command"] = None
            st.session_state["modal_open"] = False
            st.warning("Command execution was rejected.")
            st.rerun()


def render_terminal_tab():
    servers = storage.list_servers()

    if not servers:
        st.warning("⚠️ No remote servers configured. Please add a server in the **Server Credentials** tab first.")
        return

    # Server selection bar
    server_names = {s.id: f"{s.name} ({s.username}@{s.host})" for s in servers}
    saved_selected_id = st.session_state.get("selected_server_id", servers[0].id)
    if saved_selected_id not in server_names:
        saved_selected_id = servers[0].id

    c_sel1, c_sel2 = st.columns([2.5, 1.5])
    with c_sel1:
        chosen_server_id = st.selectbox(
            "Select Remote Server:",
            options=list(server_names.keys()),
            format_func=lambda x: server_names.get(x, x),
            index=list(server_names.keys()).index(saved_selected_id),
            key="server_select_box"
        )
        selected_server = storage.get_server(chosen_server_id)
        st.session_state["active_server"] = selected_server
        st.session_state["selected_server_id"] = chosen_server_id

    with c_sel2:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        btn_c1, btn_c2 = st.columns(2)
        with btn_c1:
            if st.button("⚡ Test Link", use_container_width=True):
                with st.spinner("Pinging SSH..."):
                    ok, msg, info = ssh_manager.test_connection(selected_server)
                    if ok:
                        st.success(f"Online ({info.get('latency_ms')}ms)")
                    else:
                        st.error("Offline")
        with btn_c2:
            if st.button("🧹 Clear Logs", use_container_width=True):
                st.session_state["terminal_output"] = ""
                st.rerun()

    st.markdown("---")

    # Command Execution Controls
    col_input, col_settings = st.columns([2.6, 1.4], gap="medium")

    with col_settings:
        st.markdown("#### ⚙️ Execution Options")

        mode_choice = st.radio(
            "Execution Mode:",
            options=[
                ("Usual / Synchronous (Live Output)", ExecutionMode.NORMAL),
                ("Async (Background Thread)", ExecutionMode.ASYNC),
                ("Nohup (Remote Background Daemon)", ExecutionMode.NOHUP),
            ],
            format_func=lambda x: x[0],
            index=0,
            help="Choose how the command is executed on the remote machine."
        )[1]

        if mode_choice == ExecutionMode.NOHUP:
            st.info("ℹ️ **Nohup Mode**: Executes detached on remote server with `nohup ... & echo $!`. Tracks PID & writes output to `/tmp/shellexec_<ts>.log`.")
        elif mode_choice == ExecutionMode.ASYNC:
            st.info("ℹ️ **Async Mode**: Runs in a background worker thread. UI stays responsive while job runs.")
        else:
            st.info("ℹ️ **Usual Mode**: Synchronous execution with real-time live streaming output.")

        st.markdown("##### 🤖 AI Safety Settings")
        bypass_ai = st.checkbox("Bypass AI Safety Check (Direct Run)", value=False, help="Skip AI criticality evaluation and execute immediately.")
        
        ollama_url = st.session_state.get("ollama_url", DEFAULT_OLLAMA_URL)
        ollama_model = st.session_state.get("ollama_model", DEFAULT_MODEL)
        st.caption(f"Engine: `{ollama_model}` @ `{ollama_url}`")

    with col_input:
        st.markdown("#### 💻 Command / Script Input")

        preset_key = st.selectbox("Quick Preset Commands:", options=list(PRESET_COMMANDS.keys()), index=0)
        default_cmd = PRESET_COMMANDS.get(preset_key, "")

        input_type = st.radio(
            "Input Format:",
            options=["Command / Multi-line Script", "Upload Shell Script (.sh)"],
            horizontal=True
        )

        uploaded_cmd = ""
        if input_type == "Upload Shell Script (.sh)":
            uploaded_file = st.file_uploader("Upload .sh or .bash script file", type=["sh", "bash", "txt"])
            if uploaded_file is not None:
                uploaded_cmd = uploaded_file.read().decode("utf-8", errors="replace")
                st.caption(f"Loaded script: `{uploaded_file.name}` ({len(uploaded_cmd.splitlines())} lines)")

        command_text = st.text_area(
            "Shell Script / Command:",
            value=uploaded_cmd if uploaded_cmd else (default_cmd if default_cmd else st.session_state.get("cmd_input_val", "")),
            height=140,
            placeholder="e.g. uname -a\nsystemctl status nginx\ndf -h",
            help="Enter one or multiple bash commands. Multi-line scripts will be executed in sequence."
        )

        c_exec_btn, c_space = st.columns([1.5, 2])
        with c_exec_btn:
            run_clicked = st.button("🚀 Run Command / Script", type="primary", use_container_width=True)

    # Handle execution trigger
    if run_clicked:
        if not command_text.strip():
            st.error("Please enter a command to execute.")
        else:
            st.session_state["pending_command"] = command_text.strip()
            st.session_state["pending_mode"] = mode_choice

            if bypass_ai:
                st.session_state["execute_approved"] = True
            else:
                with st.spinner("🔍 AI (Ollama) analyzing command impact & criticality..."):
                    ai_result = analyze_command(
                        command=command_text.strip(),
                        ollama_url=ollama_url,
                        model_name=ollama_model,
                    )
                    st.session_state["pending_ai_analysis"] = ai_result
                    st.session_state["modal_open"] = True

    # Check if modal should open
    if st.session_state.get("modal_open", False):
        show_ai_approval_dialog()

    # If approved by user in modal or bypassed
    if st.session_state.get("execute_approved", False):
        st.session_state["execute_approved"] = False
        cmd_to_run = st.session_state.pop("pending_command", command_text.strip())
        mode_to_run = st.session_state.pop("pending_mode", mode_choice)
        ai_analysis = st.session_state.pop("pending_ai_analysis", None)
        crit_tag = ai_analysis.criticality.value if ai_analysis else "Bypassed"

        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        server = selected_server

        # Output banner
        header_banner = (
            f"\n{'='*70}\n"
            f"⚡ [{ts}] EXECUTING COMMAND\n"
            f"Host: {server.username}@{server.host}:{server.port} ({server.name})\n"
            f"Mode: {mode_to_run.upper()} | Criticality: {crit_tag}\n"
            f"Command:\n{cmd_to_run}\n"
            f"{'-'*70}\n"
        )
        current_out = st.session_state.get("terminal_output", "")
        st.session_state["terminal_output"] = current_out + header_banner

        if mode_to_run == ExecutionMode.NORMAL:
            # Synchronous with live streaming
            status_placeholder = st.empty()
            stream_box = st.empty()
            live_output = []

            def on_stream_chunk(chunk: str):
                live_output.append(chunk)
                stream_box.code("".join(live_output)[-3000:], language="bash")

            with status_placeholder:
                with st.spinner(f"Executing on {server.name}..."):
                    res = ssh_manager.execute_sync(server, cmd_to_run, stream_callback=on_stream_chunk)

            status_placeholder.empty()
            stream_box.empty()

            footer = (
                f"\n{'-'*70}\n"
                f"🏁 COMPLETED: Exit Code: {res.exit_code} | Duration: {res.duration_sec}s | Status: {res.status.upper()}\n"
                f"{'='*70}\n"
            )
            final_content = (res.stdout or "") + (f"\nSTDERR:\n{res.stderr}" if res.stderr else "")
            st.session_state["terminal_output"] += final_content + footer
            st.rerun()

        elif mode_to_run == ExecutionMode.NOHUP:
            with st.spinner(f"Launching nohup background daemon on {server.name}..."):
                res = ssh_manager.execute_nohup(server, cmd_to_run)
                footer = (
                    f"{res.stdout}\n"
                    f"Remote PID: {res.remote_pid}\n"
                    f"Log File: {res.remote_log_file}\n"
                    f"Status: {res.status.upper()} | Completed in: {res.duration_sec}s\n"
                    f"{'='*70}\n"
                )
                st.session_state["terminal_output"] += footer
                st.session_state["last_nohup_job"] = res
                st.success(f"Nohup process started! PID: `{res.remote_pid}`. Check the Nohup monitor below.")
                st.rerun()

        elif mode_to_run == ExecutionMode.ASYNC:
            with st.spinner(f"Starting async background task..."):
                res = ssh_manager.execute_async(server, cmd_to_run)
                footer = (
                    f"Async task launched in background worker thread!\n"
                    f"Job ID: {res.job_id}\n"
                    f"Check progress in the Active Jobs panel.\n"
                    f"{'='*70}\n"
                )
                st.session_state["terminal_output"] += footer
                st.success(f"Async job `{res.job_id}` running in background.")
                st.rerun()

    # BOTTOM PAGE: Output Terminal with Adjustable Size
    st.markdown("---")
    
    # Adjustable Terminal Header Controls
    t_col1, t_col2, t_col3, t_col4 = st.columns([2, 1.8, 1, 1])
    with t_col1:
        st.markdown("#### 📺 Terminal Output Console")
    with t_col2:
        # Adjustable size slider
        terminal_height = st.slider(
            "Terminal Height (px):",
            min_value=150,
            max_value=850,
            value=st.session_state.get("terminal_height_val", 380),
            step=25,
            key="terminal_height_slider",
            help="Adjust the vertical height of the terminal output panel."
        )
        st.session_state["terminal_height_val"] = terminal_height
    with t_col3:
        st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
        # Download log
        term_text = st.session_state.get("terminal_output", "Shell Executor Ready.\n")
        st.download_button(
            label="💾 Download",
            data=term_text,
            file_name=f"terminal_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
            mime="text/plain",
            use_container_width=True
        )
    with t_col4:
        st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
        if st.button("🧹 Clear", key="clear_term_bot", use_container_width=True):
            st.session_state["terminal_output"] = ""
            st.rerun()

    # Terminal rendering
    term_text = st.session_state.get("terminal_output", "")
    if not term_text.strip():
        term_text = f"[{datetime.now().strftime('%H:%M:%S')}] ShellExecutor ready. Select a server and run a command above.\n"

    # Terminal window styling
    escaped_output = html.escape(term_text)
    terminal_html = f"""
    <div style="margin-bottom: 20px;">
        <div class="terminal-header">
            <div class="terminal-dots">
                <span class="dot dot-red"></span>
                <span class="dot dot-yellow"></span>
                <span class="dot dot-green"></span>
            </div>
            <span>{selected_server.username}@{selected_server.host} &mdash; bash</span>
            <span>UTF-8</span>
        </div>
        <div class="terminal-box" style="height: {terminal_height}px;">{escaped_output}</div>
    </div>
    """
    st.markdown(terminal_html, unsafe_allow_html=True)

    # Nohup & Async Jobs Management Section
    st.markdown("---")
    with st.expander("🛠️ Nohup Background Daemons & Async Tasks Monitor", expanded=False):
        c_nohup, c_async = st.columns(2, gap="large")

        with c_nohup:
            st.markdown("##### 🛡️ Remote Nohup Process Inspector")
            last_nohup = st.session_state.get("last_nohup_job")
            
            check_pid_input = st.number_input(
                "Remote PID to check / monitor:",
                min_value=1,
                value=last_nohup.remote_pid if (last_nohup and last_nohup.remote_pid) else 1000,
                step=1
            )
            log_path_input = st.text_input(
                "Remote Log File Path:",
                value=last_nohup.remote_log_file if (last_nohup and last_nohup.remote_log_file) else "/tmp/shellexec_sample.log"
            )

            btn_n1, btn_n2, btn_n3 = st.columns(3)
            with btn_n1:
                if st.button("🔍 Check PID Status", key="btn_check_pid"):
                    is_running, stat_msg = ssh_manager.check_remote_pid(selected_server, int(check_pid_input))
                    if is_running:
                        st.success(f"🟢 **Process Running**: {stat_msg}")
                    else:
                        st.info(f"⚪ {stat_msg}")

            with btn_n2:
                if st.button("📜 Tail Log (50 lines)", key="btn_tail_log"):
                    log_content = ssh_manager.tail_remote_log(selected_server, log_path_input, lines=50)
                    st.code(log_content if log_content else "[Log file is empty]", language="bash")

            with btn_n3:
                if st.button("🛑 Kill PID (SIGTERM)", key="btn_kill_pid"):
                    ok, k_msg = ssh_manager.kill_remote_pid(selected_server, int(check_pid_input), signal=15)
                    if ok:
                        st.warning(f"Sent SIGTERM: {k_msg}")
                    else:
                        st.error(f"Error: {k_msg}")

        with c_async:
            st.markdown("##### ⚡ Async Background Jobs Registry")
            if not ACTIVE_JOBS:
                st.caption("No async jobs have been launched in this session yet.")
            else:
                for j_id, job in list(ACTIVE_JOBS.items()):
                    with st.container():
                        st.markdown(f"**Job ID:** `{job.job_id}` &nbsp;|&nbsp; **Status:** `{job.status.upper()}`")
                        st.caption(f"Host: `{job.server_host}` | Mode: `{job.mode}` | Duration: `{job.duration_sec}s`")
                        if job.stdout or job.stderr:
                            with st.expander(f"Show Output ({job.job_id})"):
                                st.code((job.stdout or "") + (f"\nSTDERR:\n{job.stderr}" if job.stderr else ""), language="bash")
                        st.markdown("---")
