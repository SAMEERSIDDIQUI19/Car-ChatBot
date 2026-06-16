"""
AI Car Chatbot - Premium Automotive Dashboard
Single-port Streamlit app with local RAG pipeline.
Features: Working Dark/Light theme, Glassmorphism UI, Interactive Spec Cards
"""

import streamlit as st
from chatbot_engine import get_chatbot_engine
from typing import Dict, Any
import os

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Car Chatbot",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Force sidebar always open - MutationObserver + click block approach
st.markdown("""
<script>
(function() {
    function forceOpen() {
        // Find sidebar and remove collapsed state
        var sidebar = document.querySelector('[data-testid="stSidebar"]');
        if (sidebar && sidebar.getAttribute('aria-expanded') === 'false') {
            sidebar.setAttribute('aria-expanded', 'true');
        }
        if (sidebar) {
            sidebar.classList.remove('collapsed');
        }

        // Hide every possible collapse/toggle button inside the sidebar header
        var selectors = [
            '[data-testid="stSidebarNavCollapse"]',
            '[data-testid="collapsedControl"]',
            'button[aria-label="sidebar"]',
            'button[aria-label="Close sidebar"]',
            'button[aria-label="Collapse sidebar"]',
            '.stSidebarHeader button'
        ];
        selectors.forEach(function(sel) {
            document.querySelectorAll(sel).forEach(function(btn) {
                btn.style.setProperty('display', 'none', 'important');
                btn.style.setProperty('pointer-events', 'none', 'important');
                // Block click from propagating
                if (!btn._blocked) {
                    btn._blocked = true;
                    btn.addEventListener('click', function(e) {
                        e.preventDefault();
                        e.stopImmediatePropagation();
                    }, true);
                }
            });
        });
    }

    // MutationObserver watches the entire document for DOM changes
    var observer = new MutationObserver(forceOpen);
    observer.observe(document.documentElement, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ['class', 'aria-expanded']
    });

    // Also run on a short interval as a safety net
    forceOpen();
    setInterval(forceOpen, 300);
})();
</script>
""", unsafe_allow_html=True)

# ── Theme state ───────────────────────────────────────────────────────────────
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

is_dark = st.session_state.theme == "dark"

# ── Theme token definitions (Python-driven, NOT JS-driven) ────────────────────
# This is the key fix: inject CSS with actual hex values based on Python state,
# rather than relying on JS to flip data-theme attributes (which Streamlit strips).
if is_dark:
    BG_PRIMARY     = "#08090d"
    BG_SECONDARY   = "#0f1017"
    BG_CARD        = "rgba(255,255,255,0.04)"
    BG_CARD_HOVER  = "rgba(255,255,255,0.07)"
    BORDER         = "rgba(255,255,255,0.08)"
    BORDER_ACCENT  = "rgba(0,212,255,0.35)"
    TEXT_PRIMARY   = "#f0f2f8"
    TEXT_SECONDARY = "#8b8fa8"
    TEXT_MUTED     = "#50536a"
    SHADOW         = "0 8px 32px rgba(0,0,0,0.55)"
    INPUT_BG       = "rgba(255,255,255,0.05)"
    SIDEBAR_BG     = "#0c0d14"
    BADGE_BG       = "rgba(0,212,255,0.08)"
    BADGE_BORDER   = "rgba(0,212,255,0.18)"
    WELCOME_BG     = "rgba(255,255,255,0.03)"
    EXPANDER_BG    = "rgba(255,255,255,0.04)"
    MSG_HOVER_BG   = "rgba(255,255,255,0.07)"
else:
    BG_PRIMARY     = "#f5f6fb"
    BG_SECONDARY   = "#ffffff"
    BG_CARD        = "rgba(255,255,255,0.85)"
    BG_CARD_HOVER  = "rgba(255,255,255,1)"
    BORDER         = "rgba(0,0,0,0.08)"
    BORDER_ACCENT  = "rgba(0,140,200,0.35)"
    TEXT_PRIMARY   = "#1a1d2e"
    TEXT_SECONDARY = "#5a5e78"
    TEXT_MUTED     = "#9ca0b8"
    SHADOW         = "0 4px 24px rgba(0,0,0,0.10)"
    INPUT_BG       = "rgba(255,255,255,0.95)"
    SIDEBAR_BG     = "#ffffff"
    BADGE_BG       = "rgba(0,140,200,0.07)"
    BADGE_BORDER   = "rgba(0,140,200,0.2)"
    WELCOME_BG     = "rgba(255,255,255,0.8)"
    EXPANDER_BG    = "rgba(255,255,255,0.85)"
    MSG_HOVER_BG   = "rgba(255,255,255,1)"

ACCENT   = "#00d4ff" if is_dark else "#0088cc"
PURPLE   = "#7c3aed"
AMBER    = "#f59e0b"
GREEN    = "#10b981"

st.markdown(f"""
<style>
  /* ── Google Font ── */
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

  /* ── Reset & Base ── */
  * {{ box-sizing: border-box; }}

  html, body, .stApp {{
    background-color: {BG_PRIMARY} !important;
    color: {TEXT_PRIMARY} !important;
    font-family: 'Inter', system-ui, sans-serif !important;
  }}

  /* ── Hide only specific Streamlit chrome elements ── */
  #MainMenu {{ visibility: hidden; }}
  footer {{ visibility: hidden; }}
  .stDeployButton {{ display: none; }}
  
  /* Hide ALL sidebar collapse/toggle buttons */
  [data-testid="stSidebarNavCollapse"],
  [data-testid="collapsedControl"],
  button[aria-label="sidebar"],
  button[aria-label="Close sidebar"],
  button[aria-label="Collapse sidebar"],
  .stSidebarHeader button {{
    display: none !important;
    visibility: hidden !important;
    pointer-events: none !important;
    width: 0 !important;
    height: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
    border: none !important;
    overflow: hidden !important;
  }}
  
  /* Don't hide the header - it contains the sidebar toggle */
  /* Only hide the header content we don't want */
  header > div:first-child > div:last-child {{ display: none; }}

  /* ── Sidebar ── */
  section[data-testid="stSidebar"] {{
    background-color: {SIDEBAR_BG} !important;
    border-right: 1px solid {BORDER} !important;
  }}
  section[data-testid="stSidebar"] > div {{
    padding: 1.5rem 1rem !important;
  }}

  /* ── Main block ── */
  .main .block-container {{
    background-color: {BG_PRIMARY} !important;
    max-width: 1200px !important;
    padding: 1.5rem 2rem 3rem !important;
  }}

  /* ── Sidebar header ── */
  .sidebar-brand {{
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 1.25rem;
  }}
  .sidebar-brand-icon {{
    width: 38px; height: 38px;
    background: linear-gradient(135deg, {ACCENT}, {PURPLE});
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.1rem;
    flex-shrink: 0;
  }}
  .sidebar-brand-text {{
    font-size: 1rem;
    font-weight: 700;
    color: {TEXT_PRIMARY};
    line-height: 1.2;
  }}
  .sidebar-brand-sub {{
    font-size: 0.72rem;
    color: {TEXT_MUTED};
    font-weight: 400;
  }}

  /* ── Divider ── */
  hr {{
    border-color: {BORDER} !important;
    margin: 1rem 0 !important;
  }}

  /* ── Section labels ── */
  .sidebar-section-label {{
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: {TEXT_MUTED};
    margin: 1rem 0 0.5rem 0;
    padding-left: 2px;
  }}

  /* ── ALL buttons base ── */
  .stButton > button {{
    background: {BG_CARD} !important;
    color: {TEXT_SECONDARY} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 9px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    text-align: left !important;
    transition: all 0.2s ease !important;
    padding: 0.65rem 0.9rem !important;
    width: 100% !important;
    backdrop-filter: blur(8px) !important;
    box-shadow: {SHADOW} !important;
    line-height: 1.3 !important;
  }}
  .stButton > button:hover {{
    border-color: {ACCENT} !important;
    color: {ACCENT} !important;
    background: {BG_CARD_HOVER} !important;
    transform: translateX(3px) !important;
    box-shadow: 0 4px 20px rgba(0,212,255,0.12) !important;
  }}
  .stButton > button:active {{
    transform: translateX(1px) !important;
  }}

  /* ── Clear chat & theme buttons ── */
  .stButton > button[kind="secondary"] {{
    background: transparent !important;
    border-color: {BORDER} !important;
  }}

  /* ── Chat messages ── */
  [data-testid="stChatMessage"] {{
    background: {BG_CARD} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 14px !important;
    padding: 1rem 1.25rem !important;
    margin-bottom: 0.75rem !important;
    box-shadow: {SHADOW} !important;
    transition: background 0.2s, border-color 0.2s, transform 0.2s !important;
    backdrop-filter: blur(8px) !important;
  }}
  [data-testid="stChatMessage"]:hover {{
    background: {MSG_HOVER_BG} !important;
    border-color: {BORDER_ACCENT} !important;
    transform: translateY(-1px) !important;
  }}
  [data-testid="stChatMessage"] p,
  [data-testid="stChatMessage"] li,
  [data-testid="stChatMessage"] span {{
    color: {TEXT_PRIMARY} !important;
    line-height: 1.7 !important;
    font-size: 0.95rem !important;
  }}
  [data-testid="stChatMessage"] strong {{
    color: {TEXT_PRIMARY} !important;
    font-weight: 600 !important;
  }}

  /* ── Chat avatar ── */
  [data-testid="stChatMessage"] [data-testid="chatAvatarIcon-user"] svg,
  [data-testid="stChatMessage"] [data-testid="chatAvatarIcon-assistant"] svg {{
    color: {ACCENT} !important;
  }}

  /* ── Chat input ── */
  /* ── Chat input — exhaustive selectors to override Streamlit's defaults ── */
  [data-testid="stChatInput"],
  [data-testid="stChatInput"] > div,
  [data-testid="stChatInput"] > div > div,
  .stChatInput,
  .stChatInput > div {{
    background: {INPUT_BG} !important;
    background-color: {INPUT_BG} !important;
  }}
  [data-testid="stChatInput"] {{
    border: 1px solid {BORDER} !important;
    border-radius: 14px !important;
    backdrop-filter: blur(10px) !important;
    box-shadow: {SHADOW} !important;
    overflow: hidden !important;
  }}
  [data-testid="stChatInput"]:focus-within {{
    border-color: {ACCENT} !important;
    box-shadow: 0 0 0 3px rgba(0,212,255,0.1) !important;
  }}

  /* Target the textarea at every nesting level */
  [data-testid="stChatInput"] textarea,
  [data-testid="stChatInput"] div textarea,
  [data-testid="stChatInput"] > div textarea,
  [data-testid="stChatInput"] > div > div textarea {{
    background: {INPUT_BG} !important;
    background-color: {INPUT_BG} !important;
    color: {TEXT_PRIMARY} !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.95rem !important;
    border: none !important;
    caret-color: {ACCENT} !important;
  }}
  [data-testid="stChatInput"] textarea::placeholder,
  [data-testid="stChatInput"] div textarea::placeholder {{
    color: {TEXT_MUTED} !important;
    opacity: 1 !important;
  }}

  /* Send button inside chat input */
  [data-testid="stChatInput"] button {{
    background: transparent !important;
    color: {ACCENT} !important;
    border: none !important;
    box-shadow: none !important;
    transform: none !important;
    padding: 0.4rem !important;
    width: auto !important;
  }}
  [data-testid="stChatInput"] button:hover {{
    background: {BADGE_BG} !important;
    transform: scale(1.1) !important;
    border: none !important;
    color: {ACCENT} !important;
  }}

  /* Streamlit wraps the whole bottom bar — force it too */
  .stBottom, .stBottom > div, .stBottom > div > div {{
    background: {BG_PRIMARY} !important;
    background-color: {BG_PRIMARY} !important;
  }}

  /* ── Expander ── */
  details {{
    background: {EXPANDER_BG} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 10px !important;
    margin: 0.5rem 0 !important;
  }}
  details summary {{
    color: {TEXT_SECONDARY} !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    padding: 0.75rem 1rem !important;
  }}
  details summary:hover {{
    color: {ACCENT} !important;
  }}
  details[open] {{
    border-color: {BORDER_ACCENT} !important;
  }}

  /* ── Spec cards ── */
  .spec-card {{
    background: {BG_CARD};
    border: 1px solid {BORDER};
    border-left: 3px solid {ACCENT};
    border-radius: 12px;
    padding: 1rem 1.1rem;
    margin: 0.6rem 0;
    transition: all 0.2s ease;
    box-shadow: {SHADOW};
  }}
  .spec-card:hover {{
    transform: translateY(-3px);
    border-left-color: {PURPLE};
    box-shadow: 0 12px 36px rgba(0,0,0,0.25);
    background: {BG_CARD_HOVER};
  }}
  .spec-card-name {{
    color: {ACCENT};
    font-size: 1rem;
    font-weight: 700;
    margin-bottom: 0.65rem;
    display: flex;
    align-items: center;
    gap: 7px;
    letter-spacing: -0.01em;
  }}
  .spec-badges {{
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
  }}
  .spec-badge {{
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: {BADGE_BG};
    border: 1px solid {BADGE_BORDER};
    color: {TEXT_SECONDARY};
    border-radius: 7px;
    padding: 4px 10px;
    font-size: 0.78rem;
    font-weight: 500;
    transition: all 0.15s ease;
  }}
  .spec-badge:hover {{
    background: rgba(0,212,255,0.15);
    color: {TEXT_PRIMARY};
    transform: scale(1.04);
  }}
  .spec-badge .badge-label {{
    color: {TEXT_MUTED};
    font-size: 0.72rem;
    font-weight: 400;
    margin-right: 1px;
  }}

  /* ── Welcome screen ── */
  .welcome-wrap {{
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 60vh;
  }}
  .welcome-card {{
    text-align: center;
    padding: 3.5rem 3rem;
    background: {WELCOME_BG};
    border: 1px solid {BORDER};
    border-radius: 20px;
    box-shadow: {SHADOW};
    backdrop-filter: blur(20px);
    max-width: 680px;
    width: 100%;
    animation: fadeUp 0.5s ease;
  }}
  .welcome-icon {{
    font-size: 3rem;
    margin-bottom: 1rem;
    display: block;
  }}
  .welcome-card h2 {{
    font-size: 1.8rem;
    font-weight: 800;
    margin: 0 0 0.75rem;
    background: linear-gradient(135deg, {ACCENT}, {PURPLE});
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.03em;
  }}
  .welcome-card p {{
    color: {TEXT_SECONDARY};
    font-size: 1rem;
    line-height: 1.75;
    margin: 0 0 0.5rem;
  }}
  .welcome-hint {{
    display: inline-block;
    margin-top: 1.25rem;
    font-size: 0.82rem;
    color: {TEXT_MUTED};
    background: {BADGE_BG};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 6px 14px;
  }}

  /* ── Page header ── */
  .page-header {{
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    padding: 0.25rem 0 1.75rem 0;
    border-bottom: 1px solid {BORDER};
    margin-bottom: 2rem;
  }}
  .page-header h1 {{
    font-size: 2rem;
    font-weight: 800;
    margin: 0;
    letter-spacing: -0.04em;
    background: linear-gradient(130deg, {ACCENT} 0%, {PURPLE} 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.15;
  }}
  .page-header .page-sub {{
    font-size: 0.85rem;
    color: {TEXT_MUTED};
    margin: 0.35rem 0 0;
    font-weight: 400;
  }}
  .status-pill {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: {BADGE_BG};
    border: 1px solid {BADGE_BORDER};
    border-radius: 30px;
    padding: 5px 12px;
    font-size: 0.78rem;
    font-weight: 600;
    color: {GREEN};
    margin-top: 4px;
  }}
  .status-dot {{
    width: 6px; height: 6px;
    border-radius: 50%;
    background: {GREEN};
    animation: pulse 2s infinite;
  }}

  /* ── Thinking animation ── */
  .thinking-row {{
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 0.35rem 0;
  }}
  .thinking-dots {{
    display: flex; gap: 4px;
  }}
  .thinking-dots span {{
    width: 7px; height: 7px;
    border-radius: 50%;
    background: {ACCENT};
    animation: bounce 1.3s infinite;
  }}
  .thinking-dots span:nth-child(2) {{ animation-delay: 0.2s; }}
  .thinking-dots span:nth-child(3) {{ animation-delay: 0.4s; }}
  .thinking-label {{ color: {TEXT_MUTED}; font-size: 0.83rem; }}

  /* ── Scrollbar ── */
  ::-webkit-scrollbar {{ width: 5px; }}
  ::-webkit-scrollbar-track {{ background: transparent; }}
  ::-webkit-scrollbar-thumb {{
    background: {TEXT_MUTED};
    border-radius: 10px;
  }}

  /* ── Sidebar Toggle Button (when collapsed) ── */
  .sidebar-toggle-btn {{
    position: fixed;
    top: 1rem;
    left: 1rem;
    z-index: 9999;
    background: {BG_CARD} !important;
    backdrop-filter: blur(10px);
    border: 1px solid {BORDER} !important;
    border-radius: 50% !important;
    width: 48px !important;
    height: 48px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    cursor: pointer !important;
    transition: all 0.3s ease !important;
    box-shadow: {SHADOW} !important;
    font-size: 1.2rem !important;
  }}
  .sidebar-toggle-btn:hover {{
    border-color: {ACCENT} !important;
    transform: scale(1.1) !important;
  }}

  /* ── Animations ── */
  @keyframes fadeUp {{
    from {{ opacity: 0; transform: translateY(16px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
  }}
  @keyframes pulse {{
    0%, 100% {{ opacity: 1; }}
    50%       {{ opacity: 0.35; }}
  }}
  @keyframes bounce {{
    0%, 80%, 100% {{ transform: scale(0.7); opacity: 0.5; }}
    40%            {{ transform: scale(1);   opacity: 1;   }}
  }}
  .fade-in {{ animation: fadeUp 0.4s ease; }}

  /* ── Markdown tables ── */
  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.88rem;
    margin: 0.75rem 0;
  }}
  th {{
    background: {BADGE_BG} !important;
    color: {ACCENT} !important;
    font-weight: 600;
    text-align: left;
    padding: 8px 12px;
    border-bottom: 1px solid {BORDER_ACCENT};
  }}
  td {{
    color: {TEXT_PRIMARY} !important;
    padding: 7px 12px;
    border-bottom: 1px solid {BORDER};
  }}
  tr:hover td {{ background: {BG_CARD_HOVER} !important; }}
</style>
""", unsafe_allow_html=True)


# ── Auto-generate vector DB ────────────────────────────────────────────────────
if not os.path.exists("data/chroma_db"):
    st.info("📊 First run: building vector database from CSV data…")
    try:
        from ingest_data import ingest_data
        ingest_data()
        st.success("✅ Vector database ready!")
        st.rerun()
    except Exception as e:
        st.error(f"❌ Could not build vector database: {e}")
        st.stop()

# ── Session state ─────────────────────────────────────────────────────────────
if "messages"        not in st.session_state: st.session_state.messages        = []
if "chatbot_engine"  not in st.session_state: st.session_state.chatbot_engine  = None
if "engine_loaded"   not in st.session_state: st.session_state.engine_loaded   = False

# ── Auto-load engine ──────────────────────────────────────────────────────────
if not st.session_state.engine_loaded:
    try:
        st.session_state.chatbot_engine = get_chatbot_engine(use_ollama=False)
        st.session_state.engine_loaded  = True
    except Exception as e:
        st.error(f"❌ Engine failed to load: {e}")


# ── Helpers ───────────────────────────────────────────────────────────────────
def spec_card_html(metadata: Dict[str, Any]) -> str:
    name = f"{metadata.get('company','N/A')} {metadata.get('model','N/A')}"
    specs = [
        ("⚡", "HP",        metadata.get("horsepower")),
        ("🔄", "Torque",    metadata.get("torque")),
        ("🏎️", "Top Speed", metadata.get("top_speed")),
        ("⏱️", "0–100",    metadata.get("acceleration")),
        ("💰", "Price",     metadata.get("price")),
        ("⛽", "Fuel",      metadata.get("fuel_type")),
        ("🪑", "Seats",     metadata.get("seats")),
    ]
    badges = "".join(
        f'<span class="spec-badge"><span class="badge-label">{icon} {label}</span>{val}</span>'
        for icon, label, val in specs
        if val and str(val) not in ("N/A", "nan", "None", "")
    )
    return f"""
    <div class="spec-card fade-in">
        <div class="spec-card-name">🚗 {name}</div>
        <div class="spec-badges">{badges}</div>
    </div>"""


def run_query(q: str):
    """Run a query and append messages to session state."""
    st.session_state.messages.append({"role": "user", "content": q})
    try:
        result   = st.session_state.chatbot_engine.query(q)
        response = result["answer"]
        sources  = result.get("source_documents", [])
    except Exception as e:
        response = f"❌ Error: {e}"
        sources  = []
    st.session_state.messages.append({
        "role": "assistant", "content": response, "sources": sources
    })


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    # Brand
    st.markdown(f"""
    <div class="sidebar-brand">
        <div class="sidebar-brand-icon">🚗</div>
        <div>
            <div class="sidebar-brand-text">Car Assistant</div>
            <div class="sidebar-brand-sub">1,218+ models indexed</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Theme toggle — the actual working mechanism: flip Python state & rerun
    theme_label = "☀️  Switch to Light" if is_dark else "🌙  Switch to Dark"
    if st.button(theme_label, key="theme_toggle", use_container_width=True):
        st.session_state.theme = "light" if is_dark else "dark"
        st.rerun()

    st.divider()

    if st.button("🗑️  Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.markdown('<div class="sidebar-section-label">Quick Queries</div>', unsafe_allow_html=True)

    quick_queries = [
        "What's the fastest Ferrari?",
        "Electric cars under $50k",
        "Compare Porsche vs Ferrari",
        "Best sports cars for 2025",
        "Most fuel-efficient SUVs",
        "Show me all Lamborghini models",
        "Cars with highest horsepower",
        "Best luxury sedans under $100k",
        "Hybrid cars with good performance",
        "Cheapest sports cars available",
        "Cars with best acceleration",
        "Most expensive cars",
        "SUVs with 7+ seats",
        "Diesel cars with good fuel economy",
        "Convertibles under $80k",
    ]
    for q in quick_queries:
        if st.button(q, key=f"q_{q}", use_container_width=True):
            if not st.session_state.engine_loaded:
                st.warning("⚠️ Engine is still loading — please wait a moment.")
                st.stop()
            run_query(q)
            st.rerun()

    st.divider()
    st.markdown(f'<span style="font-size:0.72rem;color:{TEXT_MUTED};">Developed by Sameer Ahmed Siddiqui</span>', unsafe_allow_html=True)


# ── Page header ───────────────────────────────────────────────────────────────
engine_status = "" if st.session_state.engine_loaded else "Loading…"

st.markdown(f"""
<div class="page-header fade-in">
    <div>
        <h1>AI Car Assistant</h1>
        <p class="page-sub">Ask anything about performance, price, fuel type, or comparisons</p>
    </div>
    <div class="status-pill">
        <span class="status-dot"></span>{engine_status}
    </div>
</div>
""", unsafe_allow_html=True)


# ── Message history ───────────────────────────────────────────────────────────
if not st.session_state.messages:
    st.markdown(f"""
    <div class="welcome-wrap">
      <div class="welcome-card">
        <span class="welcome-icon">🏎️</span>
        <h2>What would you like to know?</h2>
        <p>Search across 1,218+ car specifications instantly.<br>
           Ask about performance, comparisons, prices, or anything else.</p>
        <span class="welcome-hint">💡 Try a quick query from the sidebar, or type below</span>
      </div>
    </div>
    """, unsafe_allow_html=True)
else:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            sources = msg.get("sources", [])
            if sources:
                with st.expander(f"🚗 View car specs ({len(sources[:3])} results)", expanded=False):
                    for src in sources[:3]:
                        st.markdown(spec_card_html(src.get("metadata", {})), unsafe_allow_html=True)


# ── Chat input ────────────────────────────────────────────────────────────────
if prompt := st.chat_input("Ask about any car, brand, or spec…"):
    if not st.session_state.engine_loaded:
        st.warning("⚠️ Engine is still loading — please try again in a moment.")
        st.stop()

    with st.chat_message("user"):
        st.markdown(prompt)

    # Greeting and general conversation detection (whole-word matching)
    import re as _re
    greetings = ["hello", "hi", "hey", "whatsup", "what's up", "whats up", "sup", "yo", "greetings"]
    prompt_lower = prompt.lower().strip()
    # Only match if the ENTIRE message (or a standalone word) is a greeting
    is_greeting = prompt_lower in greetings or any(
        bool(_re.fullmatch(r'[\W_]*' + _re.escape(g) + r'[\W_]*', prompt_lower)) for g in greetings
    )

    # General conversation patterns with context-aware responses
    general_responses = {
        ("how are you", "how r u", "how are u", "hows it going", "how's it going", "how you doing"):
            "I'm doing great, thanks for asking! Always ready to help you explore cars. What would you like to know?",
        ("what can you do", "what do you do", "what are your features", "what can you help with"):
            "I can help you with:\n- 🔍 Search 1,218+ car specs from 2025\n- ⚡ Compare cars side by side\n- 💰 Find cars within your budget\n- 🏎️ Discover top performers by speed or horsepower\n- ⛽ Filter by fuel type (electric, hybrid, diesel)\n\nJust ask me anything!",
        ("who are you", "what are you", "tell me about yourself", "introduce yourself"):
            "I'm an AI Car Assistant powered by a database of 1,218+ cars from 2025. I can answer questions about performance, specs, prices, fuel types, and comparisons. Think of me as your personal car expert!",
        ("thank you", "thanks", "thank u", "thx", "ty"):
            "You're welcome! Feel free to ask me anything else about cars anytime. 🚗",
        ("good morning", "good evening", "good afternoon", "good night"):
            "Hello! Hope you're having a great day. I'm here to help you find the perfect car. What would you like to know?",
        ("okay", "ok", "alright", "sure", "got it", "nice", "cool", "great", "awesome"):
            "Glad to help! Let me know if you have any other car questions. 😊",
    }

    general_response = None
    for keywords, reply in general_responses.items():
        if any(kw in prompt_lower for kw in keywords):
            general_response = reply
            break

    with st.chat_message("assistant"):
        if is_greeting:
            response = "Hey! What do you want to know about cars? I'm here to help you with any questions about performance, prices, comparisons, or specifications."
            sources = []
            st.markdown(response)
        elif general_response:
            response = general_response
            sources = []
            st.markdown(response)
        else:
            thinking_placeholder = st.empty()
            thinking_placeholder.markdown(f"""
            <div class="thinking-row">
                <div class="thinking-dots">
                    <span></span><span></span><span></span>
                </div>
                <span class="thinking-label">Searching database…</span>
            </div>
            """, unsafe_allow_html=True)

            try:
                result   = st.session_state.chatbot_engine.query(prompt)
                response = result["answer"]
                sources  = result.get("source_documents", [])
                
                # Check if no results found and try to extract company name
                if result["num_results"] == 0:
                    # Try to extract company name from the query
                    import re
                    # Common car companies
                    companies = ["toyota", "honda", "ford", "bmw", "mercedes", "audi", "tesla", "porsche", "ferrari", 
                               "lamborghini", "volkswagen", "hyundai", "kia", "nissan", "chevrolet", "mazda", "subaru",
                               "jaguar", "land rover", "lexus", "infiniti", "acura", "genesis", "volvo", "mini",
                               "maserati", "bentley", "rolls royce", "aston martin", "mclaren", "bugatti", "suzuki",
                               "mitsubishi", "dacia", "skoda", "seat", "fiat", "alfa romeo", "renault", "peugeot",
                               "citroen", "opel", "volvo", "jeep", "dodge", "chrysler", "ram", "gmc", "cadillac",
                               "buick", "lincoln", "acura", "infiniti", "genesis", "mini", "smart", "mg"]
                    
                    found_company = None
                    for company in companies:
                        if company in prompt_lower:
                            found_company = company
                            break
                    
                    if found_company:
                        # Query for cars from this company
                        company_result = st.session_state.chatbot_engine.query_by_company(found_company, n_results=5)
                        if company_result["num_results"] > 0:
                            # Format the response with the new message format
                            car_list = "\n".join([
                                f"{i+1}. {meta.get('company')} {meta.get('model')} - {meta.get('price')}"
                                for i, meta in enumerate(company_result["metadatas"][:5])
                            ])
                            response = f"Sorry for inconvenience I don't have that specific car information. I can provide you same brand new cars:\n\n{car_list}"
                            sources = company_result.get("source_documents", [])
                        else:
                            # Brand doesn't exist, show random cars
                            random_result = st.session_state.chatbot_engine.get_random_cars(n_results=5)
                            if random_result["num_results"] > 0:
                                car_list = "\n".join([
                                    f"{i+1}. {meta.get('company')} {meta.get('model')} - {meta.get('price')}"
                                    for i, meta in enumerate(random_result["metadatas"][:5])
                                ])
                                response = f"Sorry for inconvenience I don't have that specific car information. I can provide you some popular cars from our database:\n\n{car_list}"
                                sources = random_result.get("source_documents", [])
                            else:
                                response = "Sorry for inconvenience I don't have that specific car information. Our database contains cars from 2025. Would you like me to help you find something else?"
                    else:
                        # No company found, show random cars
                        random_result = st.session_state.chatbot_engine.get_random_cars(n_results=5)
                        if random_result["num_results"] > 0:
                            car_list = "\n".join([
                                f"{i+1}. {meta.get('company')} {meta.get('model')} - {meta.get('price')}"
                                for i, meta in enumerate(random_result["metadatas"][:5])
                            ])
                            response = f"Sorry for inconvenience I don't have that specific car information. I can provide you some popular cars from our database:\n\n{car_list}"
                            sources = random_result.get("source_documents", [])
                        else:
                            response = "Sorry for inconvenience I don't have that specific car information. Our database contains cars from 2025. Would you like me to help you find something else?"
                
            except Exception as e:
                response = f"❌ Error: {e}"
                sources  = []

            thinking_placeholder.markdown(response)

            if sources:
                with st.expander(f"🚗 View car specs ({len(sources[:3])} results)", expanded=True):
                    for src in sources[:3]:
                        st.markdown(spec_card_html(src.get("metadata", {})), unsafe_allow_html=True)

    st.session_state.messages.append({
        "role": "user", "content": prompt
    })
    st.session_state.messages.append({
        "role": "assistant", "content": response, "sources": sources
    })
