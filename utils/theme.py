# utils/theme.py
"""Dark SaaS theme for the Maintenance Management System.

Presentation only: global CSS plus small HTML helpers (badges, metric cards,
page headers). Nothing here touches Supabase, Gemini or the database schema.
All user-supplied text is HTML-escaped before it is placed in markup.
"""
import html as _html

import streamlit as st

# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------
APP_NAME = "FacilityFlow"
APP_TAGLINE = "Facility maintenance management"

PRIORITY_COLORS = {
    "HIGH": "#EF4444",
    "MEDIUM": "#F59E0B",
    "LOW": "#22C55E",
}
STATUS_COLORS = {
    "OPEN": "#3B82F6",
    "IN PROGRESS": "#F59E0B",
    "RESOLVED": "#22C55E",
}
UNKNOWN_COLOR = "#64748B"
ACCENT = "#6366F1"
ACCENT_ALT = "#06B6D4"

# ---------------------------------------------------------------------------
# Icons (inline SVG, stroke based)
# ---------------------------------------------------------------------------
_ICON_PATHS = {
    "list": '<path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/>',
    "alert": '<circle cx="12" cy="12" r="9"/><path d="M12 8v4M12 16h.01"/>',
    "flame": '<path d="M12 3c1 3 4 4.5 4 8.5A4 4 0 0 1 12 16a4 4 0 0 1-4-4.5c0-1.5.8-2.6 1.6-3.5C10.5 7 11.5 5.5 12 3z"/><path d="M12 21a4 4 0 0 0 4-4"/>',
    "check": '<circle cx="12" cy="12" r="9"/><path d="m8.5 12.5 2.5 2.5 4.5-5"/>',
    "wrench": '<path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 0 0 5.4-5.4l-2.5 2.5-2.4-.6-.6-2.4z"/>',
    "user": '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
    "percent": '<path d="M19 5 5 19"/><circle cx="7" cy="7" r="2"/><circle cx="17" cy="17" r="2"/>',
}


def icon(name: str, size: int = 20) -> str:
    path = _ICON_PATHS.get(name, _ICON_PATHS["list"])
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        f'stroke="currentColor" stroke-width="2" stroke-linecap="round" '
        f'stroke-linejoin="round">{path}</svg>'
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def esc(value) -> str:
    """HTML-escape any value so database / AI text can never break the layout."""
    return _html.escape("" if value is None else str(value))


def esc_multiline(value) -> str:
    """Escape text and keep its line breaks (the markup is compacted, so use <br>)."""
    return esc(value).replace("\r\n", "\n").replace("\n", "<br>")


def _compact(markup: str) -> str:
    """Strip indentation so Markdown never treats the HTML as a code block."""
    return "".join(line.strip() for line in markup.splitlines())


def render(markup: str) -> None:
    st.markdown(_compact(markup), unsafe_allow_html=True)


def badge(text, kind: str = "neutral") -> str:
    """Return a coloured pill. kind: priority | status | category | neutral."""
    label = esc(text)
    key = str(text or "").strip().upper()
    color = UNKNOWN_COLOR
    if kind == "priority":
        color = PRIORITY_COLORS.get(key, UNKNOWN_COLOR)
    elif kind == "status":
        color = STATUS_COLORS.get(key, UNKNOWN_COLOR)
    elif kind == "category":
        color = ACCENT
    elif kind == "department":
        color = ACCENT_ALT
    return (
        f'<span class="mm-badge" style="--c:{color}">'
        f'<span class="mm-dot"></span>{label}</span>'
    )


def metric_card(label: str, value, icon_name: str, color: str, sub: str = "") -> str:
    return _compact(
        f"""
        <div class="mm-metric" style="--c:{color}">
            <div class="mm-metric-top">
                <span class="mm-metric-label">{esc(label)}</span>
                <span class="mm-metric-icon">{icon(icon_name)}</span>
            </div>
            <div class="mm-metric-value">{esc(value)}</div>
            <div class="mm-metric-sub">{esc(sub)}</div>
        </div>
        """
    )


def metric_row(cards: list) -> None:
    """Render a responsive row of metric cards (each item is metric_card HTML)."""
    render(f'<div class="mm-metric-grid">{"".join(cards)}</div>')


def page_header(title: str, subtitle: str = "") -> None:
    sub = f'<p class="mm-sub">{esc(subtitle)}</p>' if subtitle else ""
    render(f'<div class="mm-header"><h1>{esc(title)}</h1>{sub}</div>')


def section_title(title: str, hint: str = "") -> None:
    hint_html = f'<span class="mm-hint">{esc(hint)}</span>' if hint else ""
    render(f'<div class="mm-section"><h3>{esc(title)}</h3>{hint_html}</div>')


def sidebar_brand() -> None:
    render(
        f"""
        <div class="mm-brand">
            <div class="mm-brand-logo">{icon("wrench", 20)}</div>
            <div>
                <div class="mm-brand-name">{esc(APP_NAME)}</div>
                <div class="mm-brand-tag">{esc(APP_TAGLINE)}</div>
            </div>
        </div>
        """
    )


def sidebar_label(text: str) -> None:
    render(f'<div class="mm-side-label">{esc(text)}</div>')


def info_field(label: str, value_html: str) -> str:
    """One label/value cell for the issue-details grid (value_html is trusted HTML)."""
    return (
        f'<div class="mm-field"><div class="mm-field-label">{esc(label)}</div>'
        f'<div class="mm-field-value">{value_html}</div></div>'
    )


def text_block(text, empty_hint: bool = False) -> str:
    cls = "mm-text mm-text-muted" if empty_hint else "mm-text"
    return f'<div class="{cls}">{esc_multiline(text)}</div>'


def ai_card(title: str, body, accent: str = ACCENT) -> str:
    return _compact(
        f"""
        <div class="mm-ai" style="--c:{accent}">
            <div class="mm-ai-title">{esc(title)}</div>
            <div class="mm-ai-body">{esc_multiline(body)}</div>
        </div>
        """
    )


# ---------------------------------------------------------------------------
# Global CSS
# ---------------------------------------------------------------------------
_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
    --bg: #0B0F19;
    --surface: #111827;
    --surface-2: #151D2E;
    --border: #1F2A3D;
    --border-strong: #2A3850;
    --text: #E5E7EB;
    --muted: #94A3B8;
    --accent: #6366F1;
    --radius: 14px;
}

html, body, .stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.stApp {
    background:
        radial-gradient(1100px 500px at 85% -10%, rgba(99, 102, 241, 0.10), transparent 60%),
        var(--bg);
    color: var(--text);
}

/* Chrome: keep the sidebar toggle, hide the rest */
#MainMenu, footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }

.block-container {
    padding-top: 2.2rem;
    padding-bottom: 4rem;
    max-width: 1400px;
}

/* ---- Sidebar ---------------------------------------------------------- */
section[data-testid="stSidebar"] {
    background: #0D1321;
    border-right: 1px solid var(--border);
}
section[data-testid="stSidebar"] .block-container,
section[data-testid="stSidebar"] > div > div { padding-top: 1.2rem; }

.mm-brand { display: flex; align-items: center; gap: 12px; padding: 4px 6px 18px 6px; }
.mm-brand-logo {
    width: 38px; height: 38px; border-radius: 11px;
    display: flex; align-items: center; justify-content: center;
    color: #fff;
    background: #3B5BDB;
}
.mm-brand-name { font-weight: 700; font-size: 1.05rem; letter-spacing: -0.01em; color: #F3F4F6; }
.mm-brand-tag { font-size: 0.72rem; color: var(--muted); }

.mm-side-label {
    font-size: 0.68rem; font-weight: 600; letter-spacing: 0.09em;
    text-transform: uppercase; color: #64748B; margin: 14px 8px 6px 8px;
}

/* Navigation: plain st.button items. Each item sits in a container created with
   st.container(key="nav_<page>") / key="navactive_<page>" (the active page). Streamlit documents
   `key` as the supported way to style a container: it adds the class `st-key-<key>`.
   No Streamlit-internal structure is relied upon, and nothing is hidden. */
section[data-testid="stSidebar"] [class*="st-key-nav_"] button,
section[data-testid="stSidebar"] [class*="st-key-navactive_"] button {
    width: 100%;
    justify-content: flex-start;
    text-align: left;
    padding: 0.62rem 0.9rem;
    border-radius: 10px;
    border: 1px solid transparent;
    background: transparent;
    box-shadow: none;
    color: #C3CCDA;
    font-weight: 500;
    transition: background 0.15s ease, border-color 0.15s ease, color 0.15s ease;
}
/* The button's inner wrapper centres its content by default; align it left like a menu item. */
section[data-testid="stSidebar"] [class*="st-key-nav_"] button > div,
section[data-testid="stSidebar"] [class*="st-key-navactive_"] button > div {
    justify-content: flex-start;
}
section[data-testid="stSidebar"] [class*="st-key-nav_"] button p,
section[data-testid="stSidebar"] [class*="st-key-navactive_"] button p {
    color: inherit;
    font-size: 0.93rem;
    margin: 0;
    text-align: left;
}
section[data-testid="stSidebar"] [class*="st-key-nav_"] button:hover {
    background: rgba(148, 163, 184, 0.10);
    border-color: transparent;
    color: #FFFFFF;
}
section[data-testid="stSidebar"] [class*="st-key-navactive_"] button,
section[data-testid="stSidebar"] [class*="st-key-navactive_"] button:hover {
    background: linear-gradient(90deg, rgba(99, 102, 241, 0.26), rgba(99, 102, 241, 0.08));
    border-color: rgba(99, 102, 241, 0.45);
    color: #FFFFFF;
    font-weight: 600;
}
section[data-testid="stSidebar"] [class*="st-key-nav_"] button:focus-visible,
section[data-testid="stSidebar"] [class*="st-key-navactive_"] button:focus-visible {
    outline: 2px solid #818CF8;
    outline-offset: 2px;
}

.mm-side-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 12px; padding: 12px 14px; margin-top: 6px;
}
.mm-side-row { display: flex; justify-content: space-between; font-size: 0.82rem; padding: 3px 0; color: var(--muted); }
.mm-side-row b { color: var(--text); font-weight: 600; }
.mm-side-foot { font-size: 0.72rem; color: #64748B; margin-top: 14px; padding: 0 6px; line-height: 1.5; }
.mm-side-foot code { background: rgba(148, 163, 184, 0.12); color: #CBD5E1; padding: 1px 6px; border-radius: 6px; font-size: 0.7rem; }

/* ---- Page header ------------------------------------------------------ */
.mm-header { margin-bottom: 1.4rem; }
.mm-header h1 {
    font-size: 1.85rem; font-weight: 700; letter-spacing: -0.02em;
    margin: 0; padding: 0; color: #F9FAFB;
}
.mm-sub { color: var(--muted); margin: 4px 0 0 0; font-size: 0.95rem; }

.mm-section { display: flex; align-items: baseline; gap: 10px; margin: 1.6rem 0 0.7rem 0; }
.mm-section h3 { font-size: 1.05rem; font-weight: 600; margin: 0; padding: 0; color: #F3F4F6; letter-spacing: -0.01em; }
.mm-hint { color: #64748B; font-size: 0.82rem; }

/* ---- Small screens ----------------------------------------------------- */
@media (max-width: 640px) {
    .block-container { padding-left: 1rem; padding-right: 1rem; padding-top: 1.4rem; }
    .mm-header h1 { font-size: 1.5rem; }
    .mm-metric-value { font-size: 1.8rem; }
    div[data-testid="stForm"] { padding: 1rem; }
}

/* ---- Metric cards ----------------------------------------------------- */
.mm-metric-grid {
    display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 16px; margin-bottom: 0.4rem;
}
@media (max-width: 1100px) { .mm-metric-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 560px)  { .mm-metric-grid { grid-template-columns: 1fr; } }

.mm-metric {
    position: relative; overflow: hidden;
    background: linear-gradient(180deg, var(--surface-2), var(--surface));
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 18px 20px 16px 20px;
    transition: transform 0.15s ease, border-color 0.15s ease;
}
.mm-metric:hover { transform: translateY(-2px); border-color: var(--border-strong); }
.mm-metric::before {
    content: ""; position: absolute; left: 0; top: 0; right: 0; height: 3px;
    background: var(--c); opacity: 0.9;
}
.mm-metric::after {
    content: ""; position: absolute; right: -40px; top: -40px; width: 120px; height: 120px;
    background: radial-gradient(circle, var(--c), transparent 70%); opacity: 0.10;
}
.mm-metric-top { display: flex; justify-content: space-between; align-items: center; }
.mm-metric-label { font-size: 0.82rem; font-weight: 500; color: var(--muted); }
.mm-metric-icon {
    width: 34px; height: 34px; border-radius: 10px; display: flex; align-items: center; justify-content: center;
    color: var(--c); background: color-mix(in srgb, var(--c) 14%, transparent);
}
.mm-metric-value { font-size: 2.1rem; font-weight: 700; letter-spacing: -0.03em; line-height: 1.15; margin-top: 10px; color: #F9FAFB; }
.mm-metric-sub { font-size: 0.78rem; color: #64748B; margin-top: 2px; min-height: 1.1em; }

/* ---- Badges ----------------------------------------------------------- */
.mm-badge {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 3px 11px 3px 9px; border-radius: 999px;
    font-size: 0.76rem; font-weight: 600; letter-spacing: 0.01em; white-space: nowrap;
    color: var(--c);
    background: color-mix(in srgb, var(--c) 14%, transparent);
    border: 1px solid color-mix(in srgb, var(--c) 32%, transparent);
}
.mm-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--c); }

/* ---- Containers with border (panels) ---------------------------------- */
div[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div[data-testid="stVerticalBlock"]) {
    border-radius: var(--radius);
}
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--surface);
    border-color: var(--border) !important;
    border-radius: var(--radius) !important;
}
.mm-panel-title { font-size: 0.98rem; font-weight: 600; color: #F3F4F6; margin: 0 0 10px 0; }
.mm-panel-sub { font-size: 0.8rem; color: #64748B; margin: -6px 0 10px 0; }

/* ---- Issue detail ----------------------------------------------------- */
.mm-issue-title { font-size: 1.35rem; font-weight: 700; letter-spacing: -0.02em; color: #F9FAFB; margin: 0 0 4px 0; }
.mm-issue-loc { color: var(--muted); font-size: 0.9rem; margin-bottom: 16px; }
.mm-fields { margin-bottom: 6px; display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 14px; }
@media (max-width: 1100px) { .mm-fields { grid-template-columns: repeat(3, minmax(0, 1fr)); } }
@media (max-width: 640px)  { .mm-fields { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
.mm-field {
    background: rgba(148, 163, 184, 0.05); border: 1px solid var(--border);
    border-radius: 11px; padding: 11px 13px;
}
.mm-field-label { font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.07em; color: #64748B; margin-bottom: 6px; }
.mm-field-value { font-size: 0.95rem; font-weight: 600; color: #F3F4F6; word-break: break-word; }

.mm-text { color: #CBD5E1; font-size: 0.95rem; line-height: 1.65; white-space: pre-wrap; word-break: break-word; }
.mm-text-muted { color: #64748B; font-style: italic; }

.mm-ai {
    height: 100%;
    background: linear-gradient(180deg, color-mix(in srgb, var(--c) 9%, transparent), transparent);
    border: 1px solid color-mix(in srgb, var(--c) 28%, var(--border));
    border-left: 3px solid var(--c);
    border-radius: 12px; padding: 14px 16px;
}
.mm-ai-title { font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.09em; color: var(--c); margin-bottom: 8px; }
.mm-ai-body { color: #D5DBE6; font-size: 0.94rem; line-height: 1.65; white-space: pre-wrap; word-break: break-word; }
.mm-ai-chips { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 14px; align-items: center; }
.mm-ai-chips .mm-chip-label { font-size: 0.74rem; color: #64748B; text-transform: uppercase; letter-spacing: 0.07em; font-weight: 600; }

/* ---- Widgets ---------------------------------------------------------- */
div[data-baseweb="input"], div[data-baseweb="select"] > div, div[data-baseweb="textarea"] {
    background-color: #0F1626 !important;
    border-color: var(--border-strong) !important;
    border-radius: 10px !important;
}
div[data-baseweb="input"]:focus-within, div[data-baseweb="select"] > div:focus-within, div[data-baseweb="textarea"]:focus-within {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.18);
}
label[data-testid="stWidgetLabel"] p { font-size: 0.82rem; font-weight: 500; color: var(--muted); }

.stButton > button, .stFormSubmitButton > button, .stDownloadButton > button {
    border-radius: 10px; font-weight: 600; padding: 0.55rem 1.1rem;
    border: 1px solid var(--border-strong); background: #151D2E; color: var(--text);
    transition: all 0.15s ease;
}
.stButton > button:hover, .stFormSubmitButton > button:hover {
    border-color: var(--accent); color: #fff; background: #1A2340;
}
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"],
.stButton > button[kind="primaryFormSubmit"], .stFormSubmitButton > button[kind="primaryFormSubmit"],
button[data-testid="stBaseButton-primary"], button[data-testid="stBaseButton-primaryFormSubmit"] {
    background: linear-gradient(135deg, #6366F1, #7C3AED); border-color: transparent; color: #fff;
    box-shadow: 0 6px 18px rgba(99, 102, 241, 0.30);
}
.stButton > button[kind="primary"]:hover, .stFormSubmitButton > button[kind="primary"]:hover,
.stFormSubmitButton > button[kind="primaryFormSubmit"]:hover,
button[data-testid="stBaseButton-primary"]:hover, button[data-testid="stBaseButton-primaryFormSubmit"]:hover {
    filter: brightness(1.1); border-color: transparent;
}

div[data-testid="stForm"] {
    background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 1.4rem 1.5rem;
}

div[data-testid="stDataFrame"] {
    border: 1px solid var(--border); border-radius: 12px; overflow: hidden;
}

div[data-testid="stAlert"] { border-radius: 12px; }

hr { border-color: var(--border) !important; }

/* Scrollbars */
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-thumb { background: #243049; border-radius: 8px; }
::-webkit-scrollbar-track { background: transparent; }
"""


def inject_css() -> None:
    st.markdown(f"<style>{_CSS}</style>", unsafe_allow_html=True)


def style_figure(fig, height: int = 300):
    """Apply the dark, borderless look to a Plotly figure."""
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=8, t=8, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Segoe UI, sans-serif", color="#CBD5E1", size=12),
        legend=dict(font=dict(color="#CBD5E1"), bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(bgcolor="#111827", bordercolor="#2A3850", font=dict(color="#F3F4F6")),
    )
    fig.update_xaxes(gridcolor="#1B2538", zerolinecolor="#1B2538", linecolor="#1B2538", tickfont=dict(color="#94A3B8"))
    fig.update_yaxes(gridcolor="#1B2538", zerolinecolor="#1B2538", linecolor="#1B2538", tickfont=dict(color="#94A3B8"))
    return fig
