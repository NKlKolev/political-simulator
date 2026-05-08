PARTY_COLORS = {
    "democratic_alliance": "#3B82F6",
    "citizens_union": "#1E3A5F",
    "national_front": "#DC2626",
    "social_democrats": "#E11D48",
    "green_future": "#16A34A",
    "liberal_democrats": "#D97706"
}

PARTY_SHORT = {
    "democratic_alliance": "DA",
    "citizens_union": "CU",
    "national_front": "NF",
    "social_democrats": "SD",
    "green_future": "GF",
    "liberal_democrats": "LD"
}

TYPE_ICONS = {
    "economic": "💰",
    "political": "🏛️",
    "corruption": "🔍",
    "social": "🗣️",
    "security": "🚔",
    "environmental": "🌿",
    "foreign_policy": "🌍",
    "media": "📺",
    "institutional": "⚖️",
    "foreign": "🌍"
}

SEVERITY_COLORS = {1: "#22C55E", 2: "#EAB308", 3: "#F97316", 4: "#EF4444", 5: "#7C2D12"}
SEVERITY_LABELS = {1: "Minor", 2: "Moderate", 3: "Serious", 4: "Critical", 5: "Existential"}


def get_indicator_color(value, inverse=False):
    if inverse:
        value = 100 - value
    if value >= 70:
        return "#22C55E"
    elif value >= 50:
        return "#EAB308"
    elif value >= 30:
        return "#F97316"
    else:
        return "#EF4444"


def get_trend_arrow(current, target=50):
    if current > target + 10:
        return "▲"
    elif current < target - 10:
        return "▼"
    return "→"


CSS = """
<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@500;600;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
    /* Hide Streamlit chrome for game-like feel — but keep sidebar toggle */
    #MainMenu { visibility: hidden !important; }
    footer { visibility: hidden !important; }
    .stDeployButton { display: none !important; }
    [data-testid="stToolbar"] { display: none !important; }
    [data-testid="stDecoration"] { display: none !important; }
    .reportview-container .main footer { visibility: hidden !important; }
    /* Keep header structure (so sidebar toggle works) but make it transparent */
    header[data-testid="stHeader"] {
        background: transparent !important;
        height: 2.5rem !important;
    }
    /* Sidebar collapse/expand button MUST stay visible */
    [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapsedControl"],
    button[kind="header"] {
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
        z-index: 999999 !important;
    }

    /* Tighter top padding now that header is hidden */
    .block-container {
        padding-top: 1rem !important;
        max-width: 1400px !important;
    }

    /* Game fonts */
    html, body, .stApp, * {
        font-family: 'Inter', 'Helvetica Neue', sans-serif !important;
    }
    h1, h2, h3, .game-title {
        font-family: 'Cinzel', 'Georgia', serif !important;
        letter-spacing: 0.02em !important;
    }

    /* Background — subtle radial gradient + dotted pattern */
    html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main, .block-container {
        background-color: #0a0f1a !important;
        background-image:
            radial-gradient(circle at 20% 0%, rgba(59, 130, 246, 0.08), transparent 50%),
            radial-gradient(circle at 80% 100%, rgba(139, 92, 246, 0.06), transparent 50%),
            radial-gradient(circle at 50% 50%, rgba(15, 23, 42, 0.5), transparent 70%);
        color: #f1f5f9 !important;
        background-attachment: fixed !important;
    }
    .stApp::before {
        content: "";
        position: fixed;
        inset: 0;
        pointer-events: none;
        background-image: radial-gradient(circle, rgba(255,255,255,0.02) 1px, transparent 1px);
        background-size: 20px 20px;
        z-index: 0;
    }

    /* Smooth fade-in for content */
    @keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }
    .block-container > div:first-child > div:first-child { animation: fadeIn 0.35s ease-out; }

    /* Pulse animation for critical resources */
    @keyframes pulseGlow {
        0%, 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); }
        50% { box-shadow: 0 0 12px 4px rgba(239, 68, 68, 0.6); }
    }
    .pulse-critical { animation: pulseGlow 2s ease-in-out infinite; }

    /* Button polish: hover lift + glow */
    .stButton button {
        transition: all 0.15s ease !important;
        font-weight: 500 !important;
    }
    .stButton button:hover:not(:disabled) {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3) !important;
        border-color: #3B82F6 !important;
    }
    .stButton button[kind="primary"]:hover:not(:disabled) {
        box-shadow: 0 4px 16px rgba(59, 130, 246, 0.5) !important;
    }

    /* Hover lift for cards */
    .game-card, [data-testid="stExpander"] {
        transition: transform 0.15s ease, box-shadow 0.15s ease !important;
    }
    .game-card:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4);
    }

    /* Tab styling - more game-like */
    button[data-baseweb="tab"] {
        border-radius: 8px 8px 0 0 !important;
        padding: 0.5rem 1.2rem !important;
        font-weight: 500 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(180deg, #1e3a5f, #1e293b) !important;
        border-bottom: 2px solid #3B82F6 !important;
    }

    /* Sidebar polish */
    section[data-testid="stSidebar"] {
        border-right: 1px solid #1e293b !important;
        box-shadow: 4px 0 20px rgba(0, 0, 0, 0.3);
    }

    /* Scrollbar styling */
    ::-webkit-scrollbar { width: 10px; height: 10px; }
    ::-webkit-scrollbar-track { background: #0f172a; }
    ::-webkit-scrollbar-thumb { background: #334155; border-radius: 5px; }
    ::-webkit-scrollbar-thumb:hover { background: #475569; }
    section[data-testid="stSidebar"], section[data-testid="stSidebar"] > div {
        background-color: #1e293b !important;
    }
    [data-testid="stHeader"] {
        background-color: #0f172a !important;
    }
    /* Force all text to be readable */
    body, .stApp, p, span, div, h1, h2, h3, h4, h5, h6, label, li, td, th {
        color: #f1f5f9 !important;
    }
    .stMarkdown, .stMarkdown p, .stMarkdown span, .stMarkdown div, .stMarkdown li {
        color: #f1f5f9 !important;
    }
    /* Streamlit metric labels and values */
    [data-testid="stMetricLabel"], [data-testid="stMetricLabel"] * { color: #cbd5e1 !important; }
    [data-testid="stMetricValue"], [data-testid="stMetricValue"] * { color: #f1f5f9 !important; }
    [data-testid="stMetricDelta"], [data-testid="stMetricDelta"] * { color: #cbd5e1 !important; }
    /* Sidebar text */
    section[data-testid="stSidebar"] *, section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] div { color: #f1f5f9 !important; }
    /* Tab labels */
    button[data-baseweb="tab"], button[data-baseweb="tab"] * { color: #cbd5e1 !important; }
    button[data-baseweb="tab"][aria-selected="true"], button[data-baseweb="tab"][aria-selected="true"] * { color: #f1f5f9 !important; }
    /* Buttons */
    .stButton button { color: #f1f5f9 !important; background-color: #1e293b !important; border: 1px solid #334155 !important; }
    .stButton button:disabled { color: #64748b !important; background-color: #0f172a !important; border-color: #1e293b !important; }
    .stButton button[kind="primary"] { background-color: #2563eb !important; border-color: #3B82F6 !important; color: white !important; }
    /* Selectbox / inputs */
    .stSelectbox label, .stNumberInput label, .stTextInput label, .stSelectbox div, .stNumberInput div, .stTextInput div {
        color: #f1f5f9 !important;
    }
    [data-baseweb="select"] > div { background-color: #1e293b !important; color: #f1f5f9 !important; }
    .stNumberInput input, .stTextInput input { background-color: #1e293b !important; color: #f1f5f9 !important; }
    /* Expander headers */
    [data-testid="stExpander"] summary, [data-testid="stExpander"] summary *,
    details summary, details summary * { color: #f1f5f9 !important; }
    [data-testid="stExpander"] { background-color: #1e293b !important; border: 1px solid #334155 !important; border-radius: 8px !important; }
    /* Tables */
    .stDataFrame, .stDataFrame * { color: #f1f5f9 !important; }
    table { color: #f1f5f9 !important; }
    /* Captions and small text */
    small, .caption, [data-testid="stCaptionContainer"] { color: #cbd5e1 !important; }
    /* Info / warning / error / success boxes — keep their accent colors */
    [data-testid="stAlert"] { color: #f1f5f9 !important; }
    /* Allow inline color overrides via style attribute */
    [style*="color:"] {}

    .main-header {
        background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
    }
    .main-header * { color: white !important; }
    .game-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 0.75rem;
        color: #f1f5f9;
    }
    .news-item {
        background: #0f172a;
        border-left: 4px solid #3b82f6;
        padding: 0.5rem 0.75rem;
        margin-bottom: 0.4rem;
        border-radius: 4px;
        font-size: 0.88rem;
    }
    .event-card {
        background: #1c1917;
        border: 2px solid #dc2626;
        border-radius: 10px;
        padding: 1.2rem;
        margin-bottom: 1rem;
    }
    .event-card-moderate {
        border-color: #f97316;
    }
    .event-card-minor {
        border-color: #eab308;
    }
    .indicator-bar {
        height: 8px;
        border-radius: 4px;
        background: #1e293b;
        overflow: hidden;
        margin-top: 4px;
    }
    .seat-bar {
        display: inline-block;
        height: 20px;
        margin: 1px;
        border-radius: 2px;
    }
    .party-tag {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: bold;
        margin: 2px;
    }
    .metric-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 0.75rem;
        text-align: center;
    }
    .metric-value {
        font-size: 1.4rem;
        font-weight: bold;
    }
    .metric-label {
        font-size: 0.75rem;
        color: #94a3b8;
    }
    .status-good { color: #22c55e; }
    .status-warn { color: #eab308; }
    .status-bad  { color: #ef4444; }
    .status-crit { color: #7c2d12; }
    .coalition-badge {
        background: #1d4ed8;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
    }
    .opposition-badge {
        background: #7f1d1d;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
    }
</style>
"""


def inject_css():
    import streamlit as st
    st.markdown(CSS, unsafe_allow_html=True)


def safe_html(html_str):
    """Render HTML stripped of leading indentation so Streamlit's markdown
    parser doesn't treat 4+ space-indented HTML lines as code blocks."""
    import textwrap
    import streamlit as st
    cleaned = textwrap.dedent(html_str).strip()
    cleaned = "\n".join(line.lstrip() for line in cleaned.splitlines())
    st.markdown(cleaned, unsafe_allow_html=True)


def progress_bar_html(value, color="#3b82f6", label="", show_value=True):
    pct = max(0, min(100, value))
    val_str = f"{int(value)}%" if show_value else ""
    return f"""
    <div style="margin-bottom:4px">
      <div style="display:flex;justify-content:space-between;font-size:0.8rem;color:#94a3b8">
        <span>{label}</span><span>{val_str}</span>
      </div>
      <div class="indicator-bar">
        <div style="width:{pct}%;height:100%;background:{color};border-radius:4px;transition:width 0.3s"></div>
      </div>
    </div>"""


def metric_html(label, value, color="#e2e8f0", suffix=""):
    return f"""
    <div class="metric-card">
      <div class="metric-value" style="color:{color}">{value}{suffix}</div>
      <div class="metric-label">{label}</div>
    </div>"""
