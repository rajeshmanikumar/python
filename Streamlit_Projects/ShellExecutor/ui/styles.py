def get_custom_css() -> str:
    return """
    <style>
    /* Global enhancements */
    @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    code, pre, .terminal-text {
        font-family: 'Fira Code', 'Cascadia Code', Consolas, monospace !important;
    }

    /* Terminal container */
    .terminal-box {
        background-color: #0d1117;
        border: 1px solid #30363d;
        border-radius: 8px;
        color: #e6edf3;
        padding: 14px 16px;
        overflow-y: auto;
        white-space: pre-wrap;
        word-break: break-all;
        font-family: 'Fira Code', monospace;
        font-size: 13px;
        line-height: 1.5;
        box-shadow: inset 0 2px 6px rgba(0, 0, 0, 0.4);
    }
    
    .terminal-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background-color: #161b22;
        border: 1px solid #30363d;
        border-bottom: none;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        padding: 8px 14px;
        font-family: 'Fira Code', monospace;
        font-size: 12px;
        color: #8b949e;
    }

    .terminal-dots {
        display: flex;
        gap: 6px;
    }

    .dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        display: inline-block;
    }
    .dot-red { background: #ff5f56; }
    .dot-yellow { background: #ffbd2e; }
    .dot-green { background: #27c93f; }

    /* Badges */
    .badge-usual {
        background-color: rgba(16, 185, 129, 0.15);
        color: #10b981;
        border: 1px solid #10b981;
        border-radius: 6px;
        padding: 4px 10px;
        font-weight: 600;
        font-size: 13px;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }

    .badge-warning {
        background-color: rgba(245, 158, 11, 0.15);
        color: #f59e0b;
        border: 1px solid #f59e0b;
        border-radius: 6px;
        padding: 4px 10px;
        font-weight: 600;
        font-size: 13px;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }

    .badge-danger {
        background-color: rgba(239, 68, 68, 0.18);
        color: #ef4444;
        border: 1px solid #ef4444;
        border-radius: 6px;
        padding: 4px 10px;
        font-weight: 700;
        font-size: 13px;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        animation: pulse-danger 2s infinite;
    }

    @keyframes pulse-danger {
        0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); }
        70% { box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); }
        100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
    }

    /* Server cards */
    .server-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 12px;
        transition: border-color 0.2s;
    }
    .server-card:hover {
        border-color: #58a6ff;
    }

    /* Modal card */
    .modal-impact-card {
        border-radius: 10px;
        padding: 16px;
        margin: 12px 0;
        border: 1px solid;
    }
    .modal-impact-usual {
        background-color: rgba(16, 185, 129, 0.08);
        border-color: rgba(16, 185, 129, 0.35);
    }
    .modal-impact-warning {
        background-color: rgba(245, 158, 11, 0.08);
        border-color: rgba(245, 158, 11, 0.35);
    }
    .modal-impact-danger {
        background-color: rgba(239, 68, 68, 0.1);
        border-color: rgba(239, 68, 68, 0.45);
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 15px;
        font-weight: 600;
        padding: 10px 18px;
    }
    </style>
    """
