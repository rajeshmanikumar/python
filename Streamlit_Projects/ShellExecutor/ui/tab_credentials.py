import streamlit as st
from datetime import datetime
from core.models import ServerCredential
from core.storage import storage
from core.ssh_manager import ssh_manager


def render_credentials_tab():
    st.markdown("### 🖥️ Remote Server Management")
    st.caption("Register and manage your SSH server credentials with encrypted local storage.")

    col1, col2 = st.columns([1.1, 1.3], gap="large")

    with col1:
        st.markdown("#### ➕ Add New Server")
        
        # Check if we are editing an existing server
        edit_server_id = st.session_state.get("editing_server_id")
        existing_server = storage.get_server(edit_server_id) if edit_server_id else None

        if existing_server:
            st.info(f"✏️ Editing Server: **{existing_server.name}**")
            if st.button("✖️ Cancel Edit", key="cancel_edit_btn"):
                st.session_state.pop("editing_server_id", None)
                st.rerun()

        with st.form(key="server_credential_form"):
            name = st.text_input(
                "Friendly Server Name *",
                value=existing_server.name if existing_server else "",
                placeholder="e.g. Prod-App-01 or Staging-DB",
                help="A recognizable label for this remote machine"
            )

            c_host, c_port = st.columns([3, 1])
            with c_host:
                host = st.text_input(
                    "Server IP or Hostname *",
                    value=existing_server.host if existing_server else "",
                    placeholder="e.g. 192.168.1.120 or api.example.com",
                    help="IP address or FQDN of the remote server"
                )
            with c_port:
                port = st.number_input(
                    "SSH Port",
                    min_value=1,
                    max_value=65535,
                    value=existing_server.port if existing_server else 22,
                    help="Default SSH port is 22"
                )

            username = st.text_input(
                "SSH Username *",
                value=existing_server.username if existing_server else "ubuntu",
                placeholder="e.g. ubuntu, root, ec2-user, debian",
                help="Remote Linux/Unix user account"
            )

            auth_type = st.radio(
                "Authentication Method",
                options=["Password", "SSH Private Key"],
                index=0 if (not existing_server or existing_server.auth_type == "password") else 1,
                horizontal=True
            )

            password = None
            private_key = None
            passphrase = None

            if auth_type == "Password":
                password = st.text_input(
                    "SSH Password *",
                    type="password",
                    value=existing_server.password if (existing_server and existing_server.password) else "",
                    placeholder="••••••••••••",
                    help="Password will be encrypted using Fernet before saving."
                )
            else:
                private_key = st.text_area(
                    "Private Key (PEM / OpenSSH format) *",
                    value=existing_server.private_key if (existing_server and existing_server.private_key) else "",
                    placeholder="-----BEGIN OPENSSH PRIVATE KEY-----\n...\n-----END OPENSSH PRIVATE KEY-----",
                    height=130,
                    help="RSA, Ed25519, or ECDSA private key string."
                )
                passphrase = st.text_input(
                    "Key Passphrase (optional)",
                    type="password",
                    value=existing_server.passphrase if (existing_server and existing_server.passphrase) else "",
                    placeholder="Leave empty if key is unencrypted"
                )

            description = st.text_input(
                "Description / Tags (optional)",
                value=existing_server.description if existing_server else "",
                placeholder="e.g. Primary Kubernetes worker, PostgreSQL cluster node"
            )

            submit_label = "💾 Update Server" if existing_server else "💾 Save Server Credential"
            submitted = st.form_submit_button(submit_label, use_container_width=True, type="primary")

            if submitted:
                if not name.strip() or not host.strip() or not username.strip():
                    st.error("Please fill in Server Name, Host, and Username.")
                elif auth_type == "Password" and not password:
                    st.error("Please enter a password for Password authentication.")
                elif auth_type == "SSH Private Key" and not private_key:
                    st.error("Please paste the private key.")
                else:
                    new_cred = ServerCredential(
                        id=existing_server.id if existing_server else None,
                        name=name.strip(),
                        host=host.strip(),
                        port=int(port),
                        username=username.strip(),
                        auth_type="password" if auth_type == "Password" else "key",
                        password=password,
                        private_key=private_key,
                        passphrase=passphrase,
                        description=description.strip(),
                        updated_at=datetime.now().isoformat(),
                    )
                    storage.save_server(new_cred)
                    st.session_state.pop("editing_server_id", None)
                    st.success(f"✅ Successfully saved server '{name}'!")
                    st.rerun()

    with col2:
        st.markdown("#### 📋 Stored Remote Servers")
        servers = storage.list_servers()

        if not servers:
            st.info("No servers saved yet. Use the form on the left to add your first remote server.")
            
            # Quick demo server filler for instant UI exploration
            st.markdown("---")
            if st.button("💡 Add Sample Demo Server (for testing UI)", key="add_sample_btn"):
                sample = ServerCredential(
                    name="Demo-Ubuntu-Cloud",
                    host="192.168.1.100",
                    port=22,
                    username="ubuntu",
                    auth_type="password",
                    password="samplePassword123!",
                    description="Sample demo node for exploring the web GUI"
                )
                storage.save_server(sample)
                st.rerun()
        else:
            st.caption(f"Total configured servers: **{len(servers)}** (Stored encrypted in `data/servers.json`)")

            for srv in servers:
                with st.expander(f"🖥️ **{srv.name}** (`{srv.username}@{srv.host}:{srv.port}`)", expanded=True):
                    c_info1, c_info2 = st.columns([2, 1])
                    with c_info1:
                        st.markdown(f"**Host:** `{srv.host}` &nbsp;|&nbsp; **Port:** `{srv.port}`")
                        st.markdown(f"**User:** `{srv.username}` &nbsp;|&nbsp; **Auth:** `{srv.auth_type.upper()}`")
                        if srv.description:
                            st.caption(f"📝 {srv.description}")

                    with c_info2:
                        # Test connection button
                        test_key = f"test_btn_{srv.id}"
                        if st.button("⚡ Test Ping/SSH", key=test_key, use_container_width=True):
                            with st.spinner(f"Connecting to {srv.host}:{srv.port}..."):
                                ok, msg, info = ssh_manager.test_connection(srv)
                                if ok:
                                    st.success(f"**{msg}**")
                                    st.markdown(f"- **OS:** `{info.get('os_kernel')}`")
                                    st.markdown(f"- **User:** `{info.get('logged_as')}`")
                                    st.markdown(f"- **Uptime:** `{info.get('uptime')}`")
                                else:
                                    st.error(f"❌ Connection Failed:\n`{msg}`")

                    # Action buttons: Select, Edit, Delete
                    btn_c1, btn_c2, btn_c3 = st.columns([1.2, 1, 1])
                    with btn_c1:
                        if st.button("🚀 Select & Open Terminal", key=f"select_{srv.id}", type="secondary", use_container_width=True):
                            st.session_state["selected_server_id"] = srv.id
                            st.session_state["active_tab_index"] = 1
                            st.success(f"Selected {srv.name}! Switch to the **Terminal Execution** tab.")
                            st.rerun()

                    with btn_c2:
                        if st.button("✏️ Edit", key=f"edit_{srv.id}", use_container_width=True):
                            st.session_state["editing_server_id"] = srv.id
                            st.rerun()

                    with btn_c3:
                        if st.button("🗑️ Delete", key=f"del_{srv.id}", use_container_width=True):
                            storage.delete_server(srv.id)
                            st.warning(f"Deleted server '{srv.name}'.")
                            st.rerun()
