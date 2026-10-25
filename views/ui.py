"""Shared look & feel: global CSS/animations, page headers, stat cards and admin login."""
import base64
import hashlib
import hmac
import html
import os

import streamlit as st

from database import get_setting, set_setting

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800&display=swap');

:root {
    --brand-1: #6C5CE7;
    --brand-2: #00B894;
    --brand-3: #FD79A8;
    --gold: #F9CA24;
    --card-bg: rgba(127, 127, 127, 0.07);
    --card-border: rgba(127, 127, 127, 0.18);
}

html, body, [class*="css"], .stMarkdown, .stButton button { font-family: 'Poppins', sans-serif; }

/* Every page fades & slides in */
.main .block-container, [data-testid="stMainBlockContainer"] {
    animation: pageIn .55s cubic-bezier(.2,.8,.2,1);
    padding-top: 2rem;
}
@keyframes pageIn { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: none; } }

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #2d1b69 0%, #4834d4 55%, #6c5ce7 100%);
}
[data-testid="stSidebar"] * { color: #f5f3ff !important; }
[data-testid="stSidebar"] input { color: #1e1b4b !important; }
[data-testid="stSidebar"] [role="radiogroup"] label {
    border-radius: 10px; padding: 4px 8px; transition: background .2s, transform .2s;
}
[data-testid="stSidebar"] [role="radiogroup"] label:hover {
    background: rgba(255,255,255,.12); transform: translateX(4px);
}
.sidebar-brand { text-align:center; padding: 4px 0 10px; }
.sidebar-brand img { max-width: 100%; border-radius: 12px; background: #fff; padding: 6px; }
.sidebar-brand .t { font-weight: 800; font-size: 1.15rem; margin-top: 6px; letter-spacing: .5px; }
.sidebar-brand .s { font-size: .8rem; opacity: .8; }

/* Page hero header */
.hero {
    position: relative; overflow: hidden;
    border-radius: 20px; padding: 26px 30px; margin-bottom: 22px;
    background: linear-gradient(120deg, var(--brand-1), #a29bfe 40%, var(--brand-2));
    background-size: 220% 220%;
    animation: heroShift 12s ease infinite;
    color: #fff; box-shadow: 0 12px 30px rgba(108, 92, 231, .30);
}
.hero.arts { background-image: linear-gradient(120deg, #e84393, #fd79a8 40%, #fdcb6e); box-shadow: 0 12px 30px rgba(232, 67, 147, .28); }
@keyframes heroShift { 0%,100% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } }
.hero h1 { color: #fff !important; margin: 0; padding: 0; font-weight: 800; font-size: 2rem; }
.hero p { margin: 6px 0 0; opacity: .92; font-size: 1rem; }
.hero .icon {
    position: absolute; right: 26px; top: 50%; transform: translateY(-50%);
    font-size: 4.2rem; opacity: .9; animation: floaty 3.5s ease-in-out infinite;
}
.hero::after {
    content: ""; position: absolute; top: -60%; left: -30%; width: 40%; height: 220%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,.22), transparent);
    transform: rotate(20deg); animation: shine 6s ease-in-out infinite;
}
@keyframes shine { 0% { left: -40%; } 60%,100% { left: 130%; } }
@keyframes floaty { 0%,100% { transform: translateY(-50%); } 50% { transform: translateY(-62%); } }

/* Stat cards */
.stat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 14px; margin-bottom: 18px; }
.stat-card {
    background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 16px;
    padding: 16px 18px; animation: popIn .5s cubic-bezier(.2,.8,.2,1) both;
    transition: transform .2s, box-shadow .2s;
}
.stat-card:hover { transform: translateY(-4px); box-shadow: 0 10px 22px rgba(0,0,0,.12); }
.stat-card .v { font-size: 1.9rem; font-weight: 800; background: linear-gradient(90deg, var(--brand-1), var(--brand-2));
    -webkit-background-clip: text; background-clip: text; color: transparent; }
.stat-card .l { font-size: .85rem; opacity: .75; }
.stat-card .e { font-size: 1.4rem; float: right; }
@keyframes popIn { from { opacity: 0; transform: scale(.92) translateY(10px); } to { opacity: 1; transform: none; } }

/* Podium */
.podium { display: flex; align-items: flex-end; justify-content: center; gap: 16px; margin: 10px 0 24px; }
.podium .step { text-align: center; width: 30%; max-width: 210px; }
.podium .block {
    border-radius: 14px 14px 6px 6px; color: #fff; font-weight: 800; font-size: 2rem;
    display: flex; align-items: center; justify-content: center;
    transform-origin: bottom; animation: rise .9s cubic-bezier(.2,.8,.2,1) both;
    box-shadow: inset 0 -8px 0 rgba(0,0,0,.12);
}
.podium .p1 .block { height: 170px; background: linear-gradient(180deg, #f9ca24, #f0932b); animation-delay: .35s; }
.podium .p2 .block { height: 125px; background: linear-gradient(180deg, #c7ecee, #95afc0); animation-delay: .15s; }
.podium .p3 .block { height: 95px;  background: linear-gradient(180deg, #e8a87c, #c0713b); animation-delay: 0s; }
.podium .name { font-weight: 700; font-size: 1.05rem; margin-bottom: 2px; animation: popIn .6s .8s both; }
.podium .pts { font-size: .9rem; opacity: .8; margin-bottom: 8px; animation: popIn .6s .9s both; }
.podium .medal { font-size: 2.2rem; animation: bounce 2s 1.2s ease-in-out infinite; display: inline-block; }
@keyframes rise { from { transform: scaleY(0); } to { transform: scaleY(1); } }
@keyframes bounce { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-8px); } }

/* Buttons & widgets */
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
    border-radius: 12px; font-weight: 600; transition: transform .15s, box-shadow .2s;
}
.stButton > button:hover, .stDownloadButton > button:hover, .stFormSubmitButton > button:hover {
    transform: translateY(-2px); box-shadow: 0 8px 18px rgba(108, 92, 231, .28);
}
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {
    background: linear-gradient(90deg, var(--brand-1), #8e7cf8); border: none;
}
[data-testid="stExpander"], [data-testid="stVerticalBlockBorderWrapper"] { border-radius: 14px; }
.stTabs [data-baseweb="tab"] { font-weight: 600; }
.stTabs [aria-selected="true"] { color: var(--brand-1) !important; }

@media print {
    .hero, [data-testid="stSidebar"], header { display: none !important; }
}
@media (max-width: 640px) {
    .hero { padding: 20px; } .hero h1 { font-size: 1.5rem; } .hero .icon { font-size: 2.6rem; right: 14px; }
}
</style>
"""


def inject_global_css():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def hero(title, subtitle="", icon="🏅"):
    mode_cls = "arts" if st.session_state.get('event_mode') == 'Arts' else ""
    st.markdown(
        f"""<div class="hero {mode_cls}">
              <h1>{html.escape(title)}</h1>
              <p>{html.escape(subtitle)}</p>
              <div class="icon">{icon}</div>
            </div>""",
        unsafe_allow_html=True,
    )


def stat_cards(items):
    """items: list of (emoji, value, label)."""
    cards = "".join(
        f'<div class="stat-card" style="animation-delay:{i * 0.08:.2f}s">'
        f'<span class="e">{e}</span><div class="v">{html.escape(str(v))}</div>'
        f'<div class="l">{html.escape(str(l))}</div></div>'
        for i, (e, v, l) in enumerate(items)
    )
    st.markdown(f'<div class="stat-grid">{cards}</div>', unsafe_allow_html=True)


def podium(rows):
    """rows: list of (name, points) ordered best first; shows the top three."""
    medals = ["🥇", "🥈", "🥉"]
    order = [1, 0, 2]  # 2nd, 1st, 3rd from left to right
    steps = []
    for idx in order:
        if idx >= len(rows):
            continue
        name, pts = rows[idx]
        steps.append(
            f'<div class="step p{idx + 1}"><div class="medal">{medals[idx]}</div>'
            f'<div class="name">{html.escape(str(name))}</div><div class="pts">{pts} pts</div>'
            f'<div class="block">{idx + 1}</div></div>'
        )
    st.markdown(f'<div class="podium">{"".join(steps)}</div>', unsafe_allow_html=True)


def image_data_uri(path):
    if not path or not os.path.exists(path):
        return None
    ext = os.path.splitext(path)[1].lower().lstrip(".")
    mime = "image/png" if ext == "png" else "image/jpeg"
    with open(path, "rb") as f:
        return f"data:{mime};base64,{base64.b64encode(f.read()).decode()}"


# ------------------ Admin password ------------------

def _hash_password(password, salt_hex=None):
    salt = bytes.fromhex(salt_hex) if salt_hex else os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return f"{salt.hex()}${digest.hex()}"


def set_admin_password(password):
    set_setting("admin_password", _hash_password(password) if password else None)


def admin_password_set():
    return bool(get_setting("admin_password"))


def check_admin_password(password):
    stored = get_setting("admin_password")
    if not stored:
        return True
    salt_hex, _ = stored.split("$", 1)
    return hmac.compare_digest(_hash_password(password, salt_hex), stored)


def is_admin():
    return not admin_password_set() or st.session_state.get("is_admin", False)


def sidebar_login():
    if not admin_password_set():
        st.sidebar.caption("🔓 No admin password set — anyone can edit. Set one in ⚙️ Settings → Security.")
        return
    if st.session_state.get("is_admin"):
        st.sidebar.success("🔐 Logged in as admin")
        if st.sidebar.button("Log out"):
            st.session_state["is_admin"] = False
            st.rerun()
    else:
        with st.sidebar.form("login_form", clear_on_submit=True):
            pwd = st.text_input("Admin password", type="password")
            if st.form_submit_button("🔑 Log in"):
                if check_admin_password(pwd):
                    st.session_state["is_admin"] = True
                    st.rerun()
                else:
                    st.error("Wrong password")


def require_admin():
    """Call at the top of pages that change data. Returns False (and shows a notice) when locked."""
    if is_admin():
        return True
    st.warning("🔒 This page changes event data. Please log in as admin from the sidebar to use it.")
    return False
