"""
AI Car Chatbot - Premium Automotive UI
Single-port Streamlit app with local RAG pipeline.
"""

import streamlit as st
from chatbot_engine import get_chatbot_engine
from typing import Dict, Any

# Page configuration
st.set_page_config(
    page_title="AI Car Chatbot",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium Automotive CSS
st.markdown("""
<style>
    /* ---- Base ---- */
    .stApp { background: #0d1117; }
    section[data-testid="stSidebar"] { background: #0d1117; border-right: 1px solid #1f6feb; }

    /* ---- Header ---- */
    .car-header {
        display: flex; align-items: center; gap: 12px;
        padding: 1rem 0 0.25rem 0;
    }
    .car-header h1 {
        font-size: 2rem; font-weight: 800; margin: 0;
        background: linear-gradient(90deg, #58a6ff, #1f6feb);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .car-header .subtitle {
        font-size: 0.9rem; color: #8b949e; margin: 0;
    }

    /* ---- Chat messages ---- */
    [data-testid="stChatMessage"] {
        background: #161b22 !important;
        border: 1px solid #30363d !important;
        border-radius: 12px !important;
        padding: 0.75rem 1rem !important;
        margin-bottom: 0.5rem !important;
    }
    [data-testid="stChatMessage"] p {
        color: #c9d1d9 !important;
    }

    /* ---- Spec card ---- */
    .spec-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-left: 4px solid #58a6ff;
        border-radius: 10px;
        padding: 1rem 1.25rem;
        margin: 0.4rem 0;
    }
    .spec-card .car-name {
        color: #58a6ff; font-size: 1rem; font-weight: 700; margin-bottom: 0.5rem;
    }
    .spec-badge {
        display: inline-block;
        background: #1f6feb22;
        border: 1px solid #1f6feb55;
        color: #c9d1d9;
        border-radius: 6px;
        padding: 2px 10px;
        font-size: 0.8rem;
        margin: 3px;
    }

    /* ---- Sidebar metric ---- */
    .db-metric {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 0.75rem 1rem;
        text-align: center;
        margin: 0.5rem 0;
    }
    .db-metric .num { font-size: 1.8rem; font-weight: 800; color: #58a6ff; }
    .db-metric .lbl { font-size: 0.75rem; color: #8b949e; text-transform: uppercase; letter-spacing: 0.06em; }

    /* ---- Quick query buttons ---- */
    .stButton > button {
        background: #161b22 !important;
        color: #c9d1d9 !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
        font-size: 0.82rem !important;
        text-align: left !important;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        border-color: #58a6ff !important;
        color: #58a6ff !important;
        background: #161b22 !important;
    }

    /* ---- Chat input ---- */
    [data-testid="stChatInput"] textarea {
        background: #161b22 !important;
        border: 1px solid #30363d !important;
        border-radius: 10px !important;
        color: #c9d1d9 !important;
    }
    [data-testid="stChatInput"] textarea:focus {
        border-color: #58a6ff !important;
    }

    /* ---- Thinking dots animation ---- */
    @keyframes blink { 0%,80%,100%{opacity:0} 40%{opacity:1} }
    .thinking span {
        display: inline-block;
        width: 8px; height: 8px;
        background: #58a6ff;
        border-radius: 50%;
        margin: 0 2px;
        animation: blink 1.4s infinite;
    }
    .thinking span:nth-child(2){ animation-delay: 0.2s; }
    .thinking span:nth-child(3){ animation-delay: 0.4s; }
    .thinking-label { color: #8b949e; font-size: 0.85rem; margin-left: 6px; }
</style>
""", unsafe_allow_html=True)

# ── Session State ──────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chatbot_engine" not in st.session_state:
    st.session_state.chatbot_engine = None
if "engine_loaded" not in st.session_state:
    st.session_state.engine_loaded = False

# ── Helpers ────────────────────────────────────────────────────────────────────
def initialize_engine():
    if st.session_state.engine_loaded:
        return True
    with st.spinner("Loading engine..."):
        try:
            st.session_state.chatbot_engine = get_chatbot_engine(use_ollama=False)
            st.session_state.engine_loaded = True
            return True
        except Exception as e:
            st.error(f"❌ Error: {e}")
            return False

def spec_card(metadata: Dict[str, Any]) -> str:
    name = f"{metadata.get('company','N/A')} {metadata.get('model','N/A')}"
    badges = {
        "⚡ HP": metadata.get("horsepower"),
        "🔄 Torque": metadata.get("torque"),
        "🏎️ Top Speed": metadata.get("top_speed"),
        "⏱️ 0-100": metadata.get("acceleration"),
        "💰 Price": metadata.get("price"),
        "⛽ Fuel": metadata.get("fuel_type"),
        "🪑 Seats": metadata.get("seats"),
    }
    badges_html = "".join(
        f'<span class="spec-badge">{k}: {v}</span>'
        for k, v in badges.items() if v and str(v) not in ("N/A", "nan", "None", "")
    )
    return f"""
    <div class="spec-card">
        <div class="car-name">🚗 {name}</div>
        <div>{badges_html}</div>
    </div>
    """

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🚗 Car Chatbot")
    st.divider()

    # Auto-load engine
    if not st.session_state.engine_loaded:
        initialize_engine()

    if st.session_state.engine_loaded:
        st.success("✅ Engine Ready", icon="✅")
    else:
        if st.button("🔄 Load Engine"):
            initialize_engine()
            st.rerun()

    st.divider()
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.markdown("**⚡ Quick Queries**")
    for q in [
        "What's the fastest Ferrari?",
        "Electric cars under $50k",
        "Compare Porsche vs Ferrari",
        "Best sports cars for 2025",
        "Most fuel-efficient SUVs",
    ]:
        if st.button(q, key=f"q_{q}", use_container_width=True):
            if not st.session_state.engine_loaded:
                st.warning("⚠️ Engine is loading, please wait...")
                st.stop()
            
            # Add user message
            st.session_state.messages.append({"role": "user", "content": q})
            
            # Generate response immediately
            try:
                result = st.session_state.chatbot_engine.query(q)
                response = result["answer"]
                sources = result.get("source_documents", [])
            except Exception as e:
                response = f"❌ Error: {e}"
                sources = []
            
            # Add assistant response
            st.session_state.messages.append({
                "role": "assistant",
                "content": response,
                "sources": sources
            })
            st.rerun()

    st.divider()
    st.caption("Developed by SAMEER AHMED SIDDIQUI")

# ── Main ───────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="car-header">
    <div>
        <h1>🚗 AI Car Assistant</h1>
        <p class="subtitle">Search 1,218+ car specs — ask anything about performance, price, or fuel type.</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Display existing messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander("� Car Specs", expanded=False):
                for src in msg["sources"][:3]:
                    st.markdown(spec_card(src.get("metadata", {})), unsafe_allow_html=True)

# ── Chat Input & Response ──────────────────────────────────────────────────────
if prompt := st.chat_input("Ask about any car..."):
    if not st.session_state.engine_loaded:
        st.warning("⚠️ Engine is loading, please wait a moment and try again.")
        st.stop()

    # Show user message immediately
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Show thinking indicator, then replace with real answer
    with st.chat_message("assistant"):
        thinking = st.empty()
        thinking.markdown("""
        <div class="thinking">
            <span></span><span></span><span></span>
            <span class="thinking-label">Searching through car database…</span>
        </div>
        """, unsafe_allow_html=True)

        try:
            result = st.session_state.chatbot_engine.query(prompt)
            response = result["answer"]
            sources = result.get("source_documents", [])
        except Exception as e:
            response = f"❌ Error: {e}"
            sources = []

        # Replace thinking with actual response
        thinking.markdown(response)

        if sources:
            with st.expander("� Car Specs", expanded=True):
                for src in sources:
                    st.markdown(spec_card(src.get("metadata", {})), unsafe_allow_html=True)

    # Persist to history
    st.session_state.messages.append({
        "role": "assistant",
        "content": response,
        "sources": sources
    })
