import os
import time
import json
import requests
import streamlit as st
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="DecisionMaker | Ollama AI Decision Engine",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS STYLING ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .main-header {
        padding: 0.5rem 0 1.5rem 0;
        border-bottom: 1px solid rgba(128, 128, 128, 0.2);
        margin-bottom: 1.5rem;
    }
    
    .brand-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #6366F1 0%, #3B82F6 50%, #10B981 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        display: inline-block;
        margin: 0;
    }
    
    .brand-subtitle {
        font-size: 0.95rem;
        color: #64748B;
        margin-top: 0.25rem;
    }
    
    .decision-badge-yes {
        background: linear-gradient(135deg, #059669 0%, #10B981 100%);
        color: white !important;
        font-size: 2.2rem;
        font-weight: 800;
        padding: 1.2rem 2.5rem;
        border-radius: 16px;
        text-align: center;
        box-shadow: 0 10px 25px -5px rgba(16, 185, 129, 0.4);
        letter-spacing: 1px;
    }
    
    .decision-badge-no {
        background: linear-gradient(135deg, #DC2626 0%, #EF4444 100%);
        color: white !important;
        font-size: 2.2rem;
        font-weight: 800;
        padding: 1.2rem 2.5rem;
        border-radius: 16px;
        text-align: center;
        box-shadow: 0 10px 25px -5px rgba(239, 68, 68, 0.4);
        letter-spacing: 1px;
    }
    
    .decision-badge-choice {
        background: linear-gradient(135deg, #4F46E5 0%, #6366F1 100%);
        color: white !important;
        font-size: 2rem;
        font-weight: 800;
        padding: 1.2rem 2.5rem;
        border-radius: 16px;
        text-align: center;
        box-shadow: 0 10px 25px -5px rgba(99, 102, 241, 0.4);
    }
    
    .decision-badge-score {
        background: linear-gradient(135deg, #4F46E5 0%, #06B6D4 100%);
        color: white !important;
        font-size: 2rem;
        font-weight: 800;
        padding: 1.2rem 2.5rem;
        border-radius: 16px;
        text-align: center;
        box-shadow: 0 10px 25px -5px rgba(79, 70, 229, 0.4);
        margin-bottom: 1.25rem;
    }
    
    .option-card-winner {
        border: 2px solid #6366F1 !important;
        background: rgba(99, 102, 241, 0.08) !important;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.75rem;
    }
    
    .option-card-standard {
        border: 1px solid rgba(128, 128, 128, 0.2);
        background: rgba(128, 128, 128, 0.03);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.75rem;
    }
    
    .scorebar-container {
        width: 100%;
        background-color: #e2e8f0;
        border-radius: 9999px;
        height: 24px;
        position: relative;
        overflow: hidden;
        margin: 1rem 0;
        box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    .scorebar-fill {
        height: 100%;
        border-radius: 9999px;
        background: linear-gradient(90deg, #EF4444 0%, #F59E0B 35%, #3B82F6 70%, #10B981 100%);
        transition: width 1s ease-in-out;
    }
    
    .metric-pill {
        display: inline-flex;
        align-items: center;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        background: rgba(99, 102, 241, 0.1);
        color: #4F46E5;
        margin-right: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


# --- HELPER FUNCTIONS ---
def fetch_ollama_models(ollama_url: str):
    """Fetch installed Ollama models from API tags endpoint."""
    try:
        res = requests.get(f"{ollama_url.rstrip('/')}/api/tags", timeout=3)
        if res.status_code == 200:
            data = res.json()
            models = [m.get("name") for m in data.get("models", [])]
            return models, None
        return [], f"HTTP {res.status_code}: {res.text}"
    except Exception as e:
        return [], str(e)


def call_decision_model(ollama_url: str, model: str, state_text: str, question_type: str, instructions: str, criteria):
    """
    Call Ollama model.
    Tries Tev1 /v1/systemone endpoint first.
    If not supported (e.g. general model), falls back to Ollama /api/generate with JSON format.
    """
    base_url = ollama_url.rstrip("/")
    start_time = time.time()
    
    # 1. Prepare systemone question payload
    systemone_payload = {
        "model": model,
        "state": state_text,
        "questions": {
            "decision": {
                "type": "noul" if question_type == "Yes/No" else ("score" if question_type == "Score" else "choice"),
                "instructions": instructions,
                "criteria": criteria
            }
        }
    }
    
    # Attempt native systemone endpoint
    try:
        sys_res = requests.post(f"{base_url}/v1/systemone", json=systemone_payload, timeout=90)
        elapsed = time.time() - start_time
        
        if sys_res.status_code == 200:
            res_json = sys_res.json()
            answer = res_json.get("answers", {}).get("decision", {})
            return {
                "success": True,
                "endpoint": "/v1/systemone",
                "answer": answer,
                "raw": res_json,
                "elapsed_sec": round(elapsed, 2)
            }
    except Exception:
        pass  # Fallback to chat/generate below
    
    # 2. Fallback to standard Ollama /api/generate with JSON prompt
    prompt_builder = f"""You are an objective AI Decision Maker acting as a high-precision classifier.
CONTEXT (STATE):
\"\"\"
{state_text}
\"\"\"

QUESTION / INSTRUCTION:
{instructions}

"""
    if question_type == "Yes/No":
        prompt_builder += f"""Evaluate if the answer to the question is YES (True) or NO (False).
Return a valid JSON object ONLY with:
{{
  "decision": "Yes" or "No",
  "probability_yes": float between 0.0 and 1.0 (confidence that answer is Yes),
  "confidence": float between 0.0 and 1.0,
  "reasoning": "brief explanation"
}}
"""
    elif question_type == "Options":
        prompt_builder += f"""Choose the single best option matching the context from the following criteria:
{json.dumps(criteria, indent=2)}

Return a valid JSON object ONLY with:
{{
  "choice": "exact chosen option key from criteria",
  "confidence": float between 0.0 and 1.0,
  "probabilities": {{ "option_key": float_prob_summing_to_1, ... }},
  "reasoning": "brief explanation"
}}
"""
    elif question_type == "Score":
        prompt_builder += f"""Evaluate and rate the context on the following rubric levels (ordered 0 to {len(criteria)-1}):
{json.dumps(criteria, indent=2)}

Return a valid JSON object ONLY with:
{{
  "score": float weighted level between 0 and {len(criteria)-1},
  "confidence": float between 0.0 and 1.0,
  "probabilities": {{ "0": prob_level_0, "1": prob_level_1, ... }},
  "reasoning": "brief explanation"
}}
"""

    gen_payload = {
        "model": model,
        "prompt": prompt_builder,
        "format": "json",
        "stream": False,
        "options": {
            "temperature": 0.0
        }
    }
    
    try:
        gen_res = requests.post(f"{base_url}/api/generate", json=gen_payload, timeout=90)
        elapsed = time.time() - start_time
        if gen_res.status_code == 200:
            gen_data = gen_res.json()
            parsed = json.loads(gen_data.get("response", "{}"))
            
            # Format normalized response to resemble systemone answer
            if question_type == "Yes/No":
                prob_yes = parsed.get("probability_yes", 0.9 if str(parsed.get("decision", "")).lower() == "yes" else 0.1)
                answer = {
                    "type": "noul",
                    "noul": float(prob_yes),
                    "confidence": parsed.get("confidence", 0.9),
                    "reasoning": parsed.get("reasoning", "")
                }
            elif question_type == "Options":
                answer = {
                    "type": "choice",
                    "choice": parsed.get("choice"),
                    "probabilities": parsed.get("probabilities", {}),
                    "confidence": parsed.get("confidence", 0.9),
                    "reasoning": parsed.get("reasoning", "")
                }
            elif question_type == "Score":
                legend_dict = {str(i): crit for i, crit in enumerate(criteria)}
                answer = {
                    "type": "score",
                    "score": float(parsed.get("score", 0.0)),
                    "legend": legend_dict,
                    "probabilities": parsed.get("probabilities", {}),
                    "confidence": parsed.get("confidence", 0.9),
                    "reasoning": parsed.get("reasoning", "")
                }
            
            return {
                "success": True,
                "endpoint": "/api/generate (JSON Fallback)",
                "answer": answer,
                "raw": gen_data,
                "elapsed_sec": round(elapsed, 2)
            }
        else:
            return {"success": False, "error": f"HTTP {gen_res.status_code}: {gen_res.text}"}
    except Exception as ex:
        return {"success": False, "error": str(ex)}


# --- INITIALIZE SESSION STATE ---
if "options_list" not in st.session_state:
    st.session_state.options_list = [
        {"name": "Approve", "desc": "Request satisfies all conditions and policies."},
        {"name": "Review Needed", "desc": "Request has ambiguous or borderline details requiring manual review."},
        {"name": "Reject", "desc": "Request clearly violates conditions or exceeds limits."}
    ]

if "score_levels" not in st.session_state:
    st.session_state.score_levels = ["Low", "Moderate", "High", "Critical"]

if "input_text" not in st.session_state:
    st.session_state.input_text = ""

if "question_prompt" not in st.session_state:
    st.session_state.question_prompt = ""


# --- SIDEBAR: LOGO, OLLAMA CONFIGURATION & MODEL PICKER ---
with st.sidebar:
    logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
        st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)
    
    st.markdown("### ⚙️ Ollama Configuration")
    
    ollama_url = st.text_input(
        "Ollama Host URL",
        value="http://localhost:11434",
        help="Default URL for local Ollama server"
    )
    
    col_ref, col_stat = st.columns([1, 1.2])
    with col_ref:
        refresh_btn = st.button("🔄 Refresh", use_container_width=True)
    
    models, err = fetch_ollama_models(ollama_url)
    
    with col_stat:
        if models:
            st.success("🟢 Connected")
        else:
            st.error("🔴 Disconnected")
    
    if err and not models:
        st.caption(f"⚠️ {err}")
        st.info("Ensure Ollama is running (`ollama serve`).")
    
    st.markdown("---")
    st.markdown("### 🤖 Select Decision Model")
    
    # Prioritize tev1 models if available
    tev1_models = [m for m in models if "tev1" in m.lower() or "nimble" in m.lower()]
    other_models = [m for m in models if m not in tev1_models]
    all_available = tev1_models + other_models
    
    default_index = 0
    if "tev1:4b" in all_available:
        default_index = all_available.index("tev1:4b")
    elif "tev1" in all_available:
        default_index = all_available.index("tev1")
    
    if all_available:
        selected_model = st.selectbox(
            "Pick Ollama Model",
            options=all_available,
            index=default_index,
            help="Select Tev1 for high-speed native SystemOne decision inference."
        )
    else:
        # Fallback text input if connection down
        selected_model = st.text_input(
            "Model Name",
            value="tev1:4b",
            help="Type your installed Ollama model name"
        )
    
    # Model info banner
    if "tev1" in selected_model.lower():
        st.markdown("""
        <div style="background: rgba(16, 185, 129, 0.1); border-left: 4px solid #10B981; padding: 0.6rem; border-radius: 6px; font-size: 0.85rem;">
            <b>⚡ Native Decision Model Detected</b><br/>
            <code>tev1</code> uses Ollama's <code>/v1/systemone</code> endpoint for ultra-fast single-pass classification.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background: rgba(59, 130, 246, 0.1); border-left: 4px solid #3B82F6; padding: 0.6rem; border-radius: 6px; font-size: 0.85rem;">
            <b>🧠 General LLM Selected</b><br/>
            Will run with structured decision schema and fallback inference.
        </div>
        """, unsafe_allow_html=True)


# --- MAIN HEADER ---
st.markdown("""
<div class="main-header">
    <h1 class="brand-title">⚖️ DecisionMaker</h1>
    <p class="brand-subtitle">Fast, deterministic AI classification and decisioning powered by local Ollama models</p>
</div>
""", unsafe_allow_html=True)


# --- TOP LAYOUT: INPUT & CONFIGURATION ---
col_left, col_right = st.columns([1.1, 1.0], gap="large")

with col_left:
    st.markdown("### 1️⃣ Input Context (State)")
    input_text = st.text_area(
        "Copy or paste the text / context to evaluate:",
        value=st.session_state.input_text,
        height=220,
        placeholder="e.g. Paste customer message, transaction data, code review diff, business proposal, or policy text here...",
        key="main_input_area"
    )
    st.session_state.input_text = input_text

    st.markdown("### 2️⃣ Decision Mode")
    if "choice_mode" not in st.session_state:
        st.session_state.choice_mode = "Options"
        
    choice_mode = st.radio(
        "Choose Decision Type:",
        options=["Options", "Yes/No", "Score"],
        horizontal=True,
        index=["Options", "Yes/No", "Score"].index(st.session_state.choice_mode),
        key="choice_mode_radio"
    )
    st.session_state.choice_mode = choice_mode

    # Question / Instructions input
    default_instruction = "Select the best option"
    if choice_mode == "Yes/No":
        default_instruction = "Does this context meet the criteria?"
    elif choice_mode == "Score":
        default_instruction = "Rate the context on the rubric scale"

    question_prompt = st.text_input(
        "Question / Decision Instruction:",
        value=st.session_state.question_prompt if st.session_state.question_prompt else default_instruction,
        placeholder="What question should the AI answer based on the text above?"
    )
    st.session_state.question_prompt = question_prompt


with col_right:
    st.markdown("### 3️⃣ Decision Criteria & Options")
    
    # -------------------------------------------------------------
    # CASE 1: ONLY IF OPTIONS - DYNAMIC MULTIPLE OPTIONS MANAGEMENT
    # -------------------------------------------------------------
    if choice_mode == "Options":
        st.caption("Provide the candidate choices. The AI model will evaluate each option against the input text.")
        
        # Action bar: Add Option button
        col_btn1, col_btn2 = st.columns([1, 1])
        with col_btn1:
            if st.button("➕ Add Another Option", use_container_width=True):
                st.session_state.options_list.append({
                    "name": f"Option {len(st.session_state.options_list) + 1}",
                    "desc": "Description of this option"
                })
                st.rerun()
        with col_btn2:
            if st.button("🧹 Reset Defaults", use_container_width=True):
                st.session_state.options_list = [
                    {"name": "Approve", "desc": "Criteria fully met"},
                    {"name": "Needs Review", "desc": "Ambiguous conditions"},
                    {"name": "Reject", "desc": "Violates conditions"}
                ]
                st.rerun()

        # Dynamic Options list editor
        options_to_remove = []
        for idx, opt in enumerate(st.session_state.options_list):
            with st.container(border=True):
                row_cols = st.columns([1.5, 2.5, 0.4])
                with row_cols[0]:
                    new_name = st.text_input(f"Option {idx + 1} Name", value=opt["name"], key=f"opt_name_{idx}")
                    st.session_state.options_list[idx]["name"] = new_name
                with row_cols[1]:
                    new_desc = st.text_input(f"Criteria / Description", value=opt["desc"], key=f"opt_desc_{idx}")
                    st.session_state.options_list[idx]["desc"] = new_desc
                with row_cols[2]:
                    st.write("") # Spacer
                    st.write("") # Spacer
                    if len(st.session_state.options_list) > 2:
                        if st.button("❌", key=f"del_opt_{idx}", help="Delete this option"):
                            options_to_remove.append(idx)
                    else:
                        st.caption("Min 2")
        
        if options_to_remove:
            for idx in sorted(options_to_remove, reverse=True):
                st.session_state.options_list.pop(idx)
            st.rerun()

    # -------------------------------------------------------------
    # CASE 2: YES / NO
    # -------------------------------------------------------------
    elif choice_mode == "Yes/No":
        st.caption("Binary decision mode (True or False / Yes or No).")
        with st.container(border=True):
            st.markdown("#### Binary Criteria Configuration")
            yes_desc = st.text_input("Criteria for 'YES' (True):", value="The context fulfills the condition or statement.")
            no_desc = st.text_input("Criteria for 'NO' (False):", value="The context does not fulfill the condition or statement.")
            st.info("💡 Tev1 computes the exact calibrated probability for Yes / True.")

    # -------------------------------------------------------------
    # CASE 3: SCORE
    # -------------------------------------------------------------
    elif choice_mode == "Score":
        st.caption("Rating rubric from lowest (Level 0) to highest.")
        
        score_preset = st.selectbox(
            "Load Scale Preset:",
            options=["Custom", "4-Level Urgency (Low -> Critical)", "3-Level Sentiment (Negative -> Positive)", "5-Star Rating (1 -> 5 Stars)"],
            index=0
        )
        
        if score_preset == "4-Level Urgency (Low -> Critical)":
            st.session_state.score_levels = ["Low", "Moderate", "High", "Critical"]
        elif score_preset == "3-Level Sentiment (Negative -> Positive)":
            st.session_state.score_levels = ["Negative", "Neutral", "Positive"]
        elif score_preset == "5-Star Rating (1 -> 5 Stars)":
            st.session_state.score_levels = ["1 Star - Terrible", "2 Stars - Poor", "3 Stars - Average", "4 Stars - Good", "5 Stars - Outstanding"]

        st.markdown("**Rubric Levels (lowest to highest):**")
        col_add_s, col_rem_s = st.columns([1, 1])
        with col_add_s:
            if st.button("➕ Add Level", use_container_width=True):
                st.session_state.score_levels.append(f"Level {len(st.session_state.score_levels)}")
                st.rerun()
        with col_rem_s:
            if len(st.session_state.score_levels) > 2:
                if st.button("➖ Remove Top Level", use_container_width=True):
                    st.session_state.score_levels.pop()
                    st.rerun()

        for idx, lvl in enumerate(st.session_state.score_levels):
            new_lvl = st.text_input(f"Level {idx}:", value=lvl, key=f"score_lvl_{idx}")
            st.session_state.score_levels[idx] = new_lvl


# --- ACTION BUTTON ---
st.markdown("---")
col_act1, col_act2, col_act3 = st.columns([1.5, 2, 1.5])
with col_act2:
    run_decision = st.button("🚀 Analyze & Make Decision", type="primary", use_container_width=True)


# --- DECISION EXECUTION & OUTPUT AREA ---
if run_decision:
    if not input_text.strip():
        st.warning("⚠️ Please provide input text in the textarea above before running the decision.")
    elif not question_prompt.strip():
        st.warning("⚠️ Please enter a Question / Decision Instruction.")
    else:
        # Prepare criteria based on choice mode
        if choice_mode == "Options":
            # Map name to description (filtering out empty names)
            criteria_payload = {}
            for item in st.session_state.options_list:
                k = item["name"].strip()
                if k:
                    criteria_payload[k] = item["desc"].strip() or k
            
            if len(criteria_payload) < 2:
                st.error("Please provide at least 2 distinct options.")
                st.stop()
        elif choice_mode == "Yes/No":
            criteria_payload = {
                "true": yes_desc.strip() if "yes_desc" in locals() and yes_desc else "Condition is met.",
                "false": no_desc.strip() if "no_desc" in locals() and no_desc else "Condition is not met."
            }
        elif choice_mode == "Score":
            criteria_payload = [lvl.strip() for lvl in st.session_state.score_levels if lvl.strip()]
            if len(criteria_payload) < 2:
                st.error("Please provide at least 2 score levels.")
                st.stop()

        with st.spinner(f"Evaluating decision using {selected_model}..."):
            result = call_decision_model(
                ollama_url=ollama_url,
                model=selected_model,
                state_text=input_text,
                question_type=choice_mode,
                instructions=question_prompt,
                criteria=criteria_payload
            )

        if not result.get("success"):
            st.error(f"❌ Error during decision inference: {result.get('error')}")
        else:
            answer = result.get("answer", {})
            elapsed = result.get("elapsed_sec")
            endpoint = result.get("endpoint")
            
            st.markdown("## 🎯 AI Decision Result")
            st.markdown(f"""
            <span class="metric-pill">Model: {selected_model}</span>
            <span class="metric-pill">Endpoint: {endpoint}</span>
            <span class="metric-pill">Latency: {elapsed}s</span>
            """, unsafe_allow_html=True)
            st.write("")

            # =========================================================
            # OUTPUT 1: YES / NO WITH CHOICE HIGHLIGHTED
            # =========================================================
            if choice_mode == "Yes/No":
                out_col1, out_col2 = st.columns([1.2, 1.0], gap="large")
                # For noul, answer contains 'noul' which is prob of True
                prob_yes = float(answer.get("noul", 0.5))
                prob_no = 1.0 - prob_yes
                decision_is_yes = prob_yes >= 0.5
                chosen_label = "YES" if decision_is_yes else "NO"
                confidence = prob_yes if decision_is_yes else prob_no
                
                with out_col1:
                    st.markdown("#### Selected Decision")
                    if decision_is_yes:
                        st.markdown(f"""
                        <div class="decision-badge-yes">
                            ✅ YES
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="decision-badge-no">
                            ❌ NO
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.write("")
                    st.markdown(f"**Confidence:** `{confidence * 100:.1f}%`")
                    if "reasoning" in answer and answer["reasoning"]:
                        st.info(f"**Reasoning:** {answer['reasoning']}")

                with out_col2:
                    st.markdown("#### Probability Distribution")
                    st.write(f"**YES / True:** `{prob_yes * 100:.1f}%`")
                    st.progress(min(max(prob_yes, 0.0), 1.0))
                    
                    st.write(f"**NO / False:** `{prob_no * 100:.1f}%`")
                    st.progress(min(max(prob_no, 0.0), 1.0))
                    
                    # Highlight comparison card
                    st.markdown(f"""
                    <div style="margin-top: 1rem; padding: 1rem; border-radius: 10px; background: rgba(128,128,128,0.05); border: 1px solid rgba(128,128,128,0.2);">
                        <b>Decision Summary:</b><br/>
                        The AI determined with <b>{confidence * 100:.1f}%</b> certainty that the answer is 
                        <b style="color: {'#10B981' if decision_is_yes else '#EF4444'}; font-size: 1.1rem;">{chosen_label}</b>.
                    </div>
                    """, unsafe_allow_html=True)

            # =========================================================
            # OUTPUT 2: OPTIONS WITH CHOSEN CHOICE HIGHLIGHTED
            # =========================================================
            elif choice_mode == "Options":
                out_col1, out_col2 = st.columns([1.2, 1.0], gap="large")
                chosen_opt = answer.get("choice")
                probabilities = answer.get("probabilities", {})
                confidence = answer.get("confidence", 0.0)

                with out_col1:
                    st.markdown("#### Chosen Option Highlighted")
                    st.markdown(f"""
                    <div class="decision-badge-choice">
                        🏆 {chosen_opt}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.write("")
                    st.markdown(f"**Confidence Level:** `{confidence * 100:.1f}%`" if confidence else "")
                    if "reasoning" in answer and answer["reasoning"]:
                        st.info(f"**Reasoning:** {answer['reasoning']}")

                with out_col2:
                    st.markdown("#### Candidate Options & Probability Breakdown")
                    
                    # Sort options by probability if available, otherwise preserve order
                    for opt_key, opt_desc in criteria_payload.items():
                        prob = probabilities.get(opt_key, 0.0) if probabilities else (1.0 if opt_key == chosen_opt else 0.0)
                        is_winner = (opt_key == chosen_opt)
                        
                        card_class = "option-card-winner" if is_winner else "option-card-standard"
                        badge_winner = " <span style='background:#6366F1; color:white; padding:2px 8px; border-radius:12px; font-size:0.75rem; font-weight:700;'>SELECTED</span>" if is_winner else ""
                        
                        st.markdown(f"""
                        <div class="{card_class}">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <strong style="font-size:1.05rem;">{opt_key}{badge_winner}</strong>
                                <span style="font-family:'JetBrains Mono',monospace; font-weight:700; color:{'#6366F1' if is_winner else '#64748B'};">
                                    {prob * 100:.1f}%
                                </span>
                            </div>
                            <div style="font-size:0.85rem; color:#64748B; margin-top:4px;">{opt_desc}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        st.progress(min(max(float(prob), 0.0), 1.0))

            # =========================================================
            # OUTPUT 3: SCORE IN A SCOREBAR / GAUGE WITH COLORS
            # =========================================================
            elif choice_mode == "Score":
                raw_score = float(answer.get("score", 0.0))
                legend = answer.get("legend", {})
                probabilities = answer.get("probabilities", {})
                confidence = answer.get("confidence", 0.0)
                
                # Number of levels
                num_levels = len(criteria_payload)
                max_level_idx = max(num_levels - 1, 1)
                
                # Nearest level label
                nearest_idx = int(round(raw_score))
                nearest_idx = max(0, min(nearest_idx, num_levels - 1))
                
                if isinstance(legend, dict):
                    level_label = legend.get(str(nearest_idx), criteria_payload[nearest_idx])
                elif isinstance(legend, list) and nearest_idx < len(legend):
                    level_label = legend[nearest_idx]
                else:
                    level_label = criteria_payload[nearest_idx]

                # Full-Width Prominent Final Decision Hero Badge
                st.markdown(f"""
                <div class="decision-badge-score">
                    ⭐ Final Decision: <b>{level_label}</b> &nbsp;&nbsp;•&nbsp;&nbsp; Score: <b>{raw_score:.2f}</b> / {max_level_idx}
                </div>
                """, unsafe_allow_html=True)

                score_col1, score_col2 = st.columns([1.3, 1.0], gap="large")

                with score_col1:
                    st.markdown("#### Score Gauge")
                    
                    # Clean level title above gauge so it is NEVER cut off
                    st.markdown(f"""
                    <div style="text-align: center; font-size: 1.35rem; font-weight: 700; color: #1E293B; margin-bottom: 2px;">
                        {level_label}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Calibrated Plotly Gauge WITHOUT embedded title (prevents clipping)
                    fig = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=raw_score,
                        domain={'x': [0.04, 0.96], 'y': [0.02, 0.98]},
                        number={
                            'font': {'size': 38, 'family': 'Inter', 'color': '#4F46E5'},
                            'suffix': f" / {max_level_idx}",
                            'valueformat': ".2f"
                        },
                        gauge={
                            'axis': {
                                'range': [0, max_level_idx],
                                'tickwidth': 2,
                                'tickcolor': "#94A3B8",
                                'tickmode': 'linear',
                                'tick0': 0,
                                'dtick': 1
                            },
                            'bar': {'color': "#4F46E5", 'thickness': 0.28},
                            'bgcolor': "#F8FAFC",
                            'borderwidth': 1.5,
                            'bordercolor': "#CBD5E1",
                            'steps': [
                                {'range': [0, max_level_idx * 0.33], 'color': '#FEE2E2'},
                                {'range': [max_level_idx * 0.33, max_level_idx * 0.66], 'color': '#FEF3C7'},
                                {'range': [max_level_idx * 0.66, max_level_idx], 'color': '#DCFCE7'}
                            ],
                            'threshold': {
                                'line': {'color': "#0F172A", 'width': 4},
                                'thickness': 0.75,
                                'value': raw_score
                            }
                        }
                    ))
                    fig.update_layout(
                        height=230,
                        margin=dict(l=20, r=20, t=10, b=10),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)"
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    # Multi-colored Scorebar with needle indicator
                    score_percentage = (raw_score / max_level_idx) * 100
                    st.markdown("##### Scorebar (Gradient Spectrum)")
                    st.markdown(f"""
                    <div style="position:relative; margin-top: 0.5rem; margin-bottom: 1.5rem; overflow: visible;">
                        <div class="scorebar-container" style="overflow: visible;">
                            <div class="scorebar-fill" style="width: 100%;"></div>
                            <div style="position:absolute; top: -6px; left: calc({min(max(score_percentage, 1.5), 98.5)}% - 7px); width: 14px; height: 36px; background: #0F172A; border: 2px solid #FFFFFF; border-radius: 4px; box-shadow: 0 3px 8px rgba(0,0,0,0.35);"></div>
                        </div>
                        <div style="display:flex; justify-content:space-between; font-size:0.8rem; color:#64748B; margin-top: 6px;">
                            <span>Level 0: {criteria_payload[0]}</span>
                            <span>Level {max_level_idx}: {criteria_payload[-1]}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                with score_col2:
                    st.markdown("#### Probability Distribution Across Levels")
                    for idx, crit_name in enumerate(criteria_payload):
                        prob = probabilities.get(str(idx), 0.0) if probabilities else 0.0
                        is_current = (idx == nearest_idx)
                        st.write(f"**Level {idx} ({crit_name}):** `{float(prob) * 100:.1f}%`" + (" 📍 *(Closest)*" if is_current else ""))
                        st.progress(min(max(float(prob), 0.0), 1.0))
                    
                    st.write("")
                    st.markdown(f"**Confidence Metric:** `{confidence * 100:.1f}%`" if confidence else "")
                    if "reasoning" in answer and answer["reasoning"]:
                        st.info(f"**Reasoning:** {answer['reasoning']}")

            # Developer Transparency: Raw JSON expander
            with st.expander("🔍 View Raw Ollama Response"):
                st.json(result.get("raw", {}))
