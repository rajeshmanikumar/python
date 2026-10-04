# ⚖️ DecisionMaker - Ollama AI Decision Engine

**DecisionMaker** is a high-speed AI decisioning Streamlit application powered by local Ollama models and specialized decision models like Together AI's **Tev1** (`tev1:4b`, `tev1:0.8b`).

---

## 🌟 Key Features

1. **Pick Any Ollama Model on Sidebar**:
   - Automatically queries your local Ollama instance (`http://localhost:11434/api/tags`) to discover installed models.
   - Detects and highlights native decision models (`tev1:4b`, `tev1:0.8b`, `nimble`).
   - Seamlessly falls back to structured JSON generation for general models (`qwen3.8`, `llama3`, `mistral`, etc.).

2. **Big TextArea Input**:
   - Easy paste and editing for context/state (customer support tickets, business policies, contract terms, emails, etc.).

3. **Three Decision Modes**:
   - **`Options` (Multiple Choice)**: 
     - **Dynamic Option Manager**: Add as many custom options as you need with individual name, criteria/description, and remove buttons.
     - Highlights the winning choice in a vibrant hero badge with percentage confidence.
     - Displays complete probability breakdown bars for all candidate options.
   - **`Yes / No` (Binary Decision)**:
     - Calibrated binary classification using Tev1's `noul` probability metric.
     - Highlights the decision with green `✅ YES` or red `❌ NO` badges and probability distribution.
   - **`Score` (Rating / Gauge with Colors)**:
     - Multi-level rubric scoring.
     - Visualized with a **Plotly Colored Gauge** (red/yellow/green color bands) and a **Custom Gradient Scorebar** with needle position.
     - Full probability breakdown across each level.

4. **Presets & Developer Transparency**:
   - One-click presets for Return Policy Check (Yes/No), Support Ticket Routing (Options), and Urgency Rating (Score).
   - Raw JSON response inspector for developer inspection and debugging.

---

## 🚀 Quickstart

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Make Sure Ollama is Running
Pull the `tev1:4b` decision model if you haven't already:
```bash
ollama pull tev1:4b
```

### 3. Launch the Streamlit App
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.
