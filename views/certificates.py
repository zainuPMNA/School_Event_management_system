import html

import streamlit as st
import streamlit.components.v1 as components
from database import run_query, get_event_info
from views.ui import hero, image_data_uri

PLACES = {1: ("First Place", "🥇", "#D4AF37"), 2: ("Second Place", "🥈", "#9EA7B3"), 3: ("Third Place", "🥉", "#CD7F32")}

CERT_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Great+Vibes&family=Cinzel:wght@600;800&family=Poppins:wght@400;600&display=swap');
.certificate-container {
    position: relative; text-align: center; background: #fffdf6; color: #333;
    padding: 46px 50px 36px; margin: 0 auto 34px; max-width: 980px;
    border: 14px solid var(--c); outline: 3px solid var(--c); outline-offset: -26px;
    border-radius: 6px; box-shadow: 0 14px 34px rgba(0,0,0,.15);
    font-family: 'Poppins', sans-serif; animation: certIn .7s cubic-bezier(.2,.8,.2,1) both;
}
@keyframes certIn { from { opacity: 0; transform: translateY(24px) scale(.97); } to { opacity: 1; transform: none; } }
.certificate-container .logo { height: 70px; margin-bottom: 6px; }
.certificate-container .school { font-family: 'Cinzel', serif; font-size: 22px; font-weight: 800; color: #2c3e50; letter-spacing: 1px; }
.certificate-container .eventname { font-size: 14px; color: #7f8c8d; margin-bottom: 14px; }
.cert-header { font-family: 'Cinzel', serif; font-size: 38px; font-weight: 800; color: var(--c); letter-spacing: 3px; text-transform: uppercase; }
.cert-body { font-size: 19px; margin: 10px 0; }
.cert-name { font-family: 'Great Vibes', cursive; font-size: 58px; color: #2c3e50; margin: 6px 0; line-height: 1.2; }
.cert-place { display: inline-block; font-size: 22px; font-weight: 600; color: #fff; background: var(--c);
    padding: 6px 26px; border-radius: 999px; margin: 6px 0; }
.cert-event { font-family: 'Cinzel', serif; font-size: 28px; color: #c0392b; font-weight: 800; }
.cert-medal { position: absolute; top: 30px; right: 44px; font-size: 64px; }
.cert-sign { display: flex; justify-content: space-around; margin-top: 46px; font-size: 14px; color: #555; }
.cert-sign div { border-top: 1px solid #999; padding-top: 6px; width: 26%; }
@media print {
    header[data-testid="stHeader"], [data-testid="stSidebar"], [data-testid="stToolbar"], footer,
    .stSelectbox, .stAlert, .stButton, .stCheckbox, .hero, .stMarkdown h3, hr { display: none !important; }
    .main .block-container, [data-testid="stMainBlockContainer"] { max-width: 100% !important; padding: 0 !important; }
    .certificate-container { page-break-after: always; box-shadow: none !important; margin: 0 auto !important; animation: none; }
}
</style>
"""


def _certificate(name, group, place_text, medal, color, prog_name, school, event, year, logo_uri, participation=False):
    logo = f'<img class="logo" src="{logo_uri}">' if logo_uri else ""
    title = "Certificate of Participation" if participation else "Certificate of Achievement"
    achievement = (
        '<div class="cert-body">for enthusiastic participation in</div>' if participation else
        f'<div class="cert-body">for outstanding performance and securing</div><div class="cert-place">{place_text}</div>'
        '<div class="cert-body">in the event</div>'
    )
    group_line = f" of <b>{html.escape(str(group))}</b>" if group else ""
    # Strip indentation: Markdown would otherwise render indented HTML as a code block
    return "".join(line.strip() for line in f"""
    <div class="certificate-container" style="--c:{color}">
        <div class="cert-medal">{medal}</div>
        {logo}
        <div class="school">{html.escape(school)}</div>
        <div class="eventname">{html.escape(event)} {html.escape(str(year))}</div>
        <div class="cert-header">{title}</div>
        <div class="cert-body">This is proudly presented to</div>
        <div class="cert-name">{html.escape(str(name))}</div>
        <div class="cert-body">{group_line}</div>
        {achievement}
        <div class="cert-event">{html.escape(prog_name)}</div>
        <div class="cert-sign"><div>Coordinator</div><div>Chairman</div><div>Principal</div></div>
    </div>""".splitlines())


def render():
    current_mode = st.session_state.get('event_mode', 'Sports')
    hero(f"{current_mode} Winner Certificates", "Generate beautiful certificates and print them or save them as PDF (Ctrl+P).", "🏅")

    df_prog = run_query("""
        SELECT DISTINCT p.id, p.name, p.type, p.category, p.gender
        FROM programs p JOIN scores s ON p.id = s.program_id
        WHERE p.event_mode = ?
        ORDER BY p.category, p.name
    """, (current_mode,))

    if df_prog.empty:
        st.info("No events have scores logged yet. Add some scores to generate certificates!")
        return

    labels = [f"{r['name']} — {r['category']} {r['gender']} ({r['type']})" for _, r in df_prog.iterrows()]
    idx = st.selectbox("Select an Event", range(len(labels)), format_func=lambda i: labels[i])
    prog = df_prog.iloc[idx]
    prog_id = int(prog['id'])
    prog_name = f"{prog['name']} ({prog['category']} {prog['gender']})"

    include_participation = st.checkbox("Also include participation certificates for everyone else in this event")

    df_winners = run_query("""
        SELECT s.position, COALESCE(st.name, s.student_or_group_leader) AS name, s.group_name
        FROM scores s LEFT JOIN students st ON st.id = s.student_id
        WHERE s.program_id = ?
        ORDER BY CASE WHEN s.position BETWEEN 1 AND 3 THEN s.position ELSE 99 END, name
    """, (prog_id,))
    winners = df_winners[df_winners['position'].between(1, 3)]
    others = df_winners[~df_winners['position'].between(1, 3)]

    if winners.empty and not include_participation:
        st.warning("No 1st, 2nd or 3rd place winners found for this event.")
        return

    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"### {len(winners) + (len(others) if include_participation else 0)} certificate(s) ready")
    with col2:
        print_btn = st.button("🖨️ Print / Save as PDF", type="primary")

    school, event, year, logo = get_event_info()
    logo_uri = image_data_uri(logo)

    parts = [CERT_CSS]
    for _, row in winners.iterrows():
        place_text, medal, color = PLACES[int(row['position'])]
        parts.append(_certificate(row['name'], row['group_name'], place_text, medal, color, prog_name, school, event, year, logo_uri))
    if include_participation:
        for _, row in others.iterrows():
            parts.append(_certificate(row['name'], row['group_name'], "", "🎖️", "#6C5CE7", prog_name, school, event, year, logo_uri, participation=True))
    st.markdown("".join(parts), unsafe_allow_html=True)

    st.info("💡 Tip: in the print dialog choose **Landscape** and turn on **Background graphics** for the best result.")

    if print_btn:
        components.html("<script>window.parent.print();</script>", height=0)
