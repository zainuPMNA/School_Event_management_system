import html
import json

import streamlit as st
import streamlit.components.v1 as components

from database import run_query, get_event_info
from views.ui import hero, image_data_uri

HOUSE_COLORS = ["#6C5CE7", "#00B894", "#E17055", "#0984E3", "#FDCB6E", "#E84393", "#00CEC9", "#636E72"]


def _board_html(mode, houses, recent, done, total, school, event, year, logo_uri):
    houses_json = json.dumps(houses)
    max_pts = max([h["points"] for h in houses] + [1])
    pct_done = int(done * 100 / total) if total else 0

    recent_items = "".join(
        f'<div class="tick"><span class="medal">{"🥇🥈🥉"[r["position"] - 1]}</span>'
        f'<b>{html.escape(r["participant"])}</b> <span class="grp">{html.escape(r["group"] or "")}</span>'
        f'<span class="ev">{html.escape(r["program"])} · {html.escape(r["category"] or "")}</span></div>'
        for r in recent
    ) or '<div class="tick">Results will appear here as soon as scores are saved…</div>'

    logo_tag = f'<img class="logo" src="{logo_uri}">' if logo_uri else '<div class="logo emoji">🏆</div>'
    accent = "#e84393" if mode == "Arts" else "#6c5ce7"

    return f"""
<!doctype html><html><head><meta charset="utf-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap');
* {{ box-sizing: border-box; }}
body {{ margin:0; font-family:'Poppins',sans-serif; color:#fff; overflow:hidden;
  background: radial-gradient(1200px 600px at 10% -10%, {accent}55, transparent),
              radial-gradient(900px 500px at 110% 110%, #00b89455, transparent), #0f0c29; }}
.wrap {{ padding: 22px 26px; height: 100vh; display:flex; flex-direction:column; gap:16px; }}
header {{ display:flex; align-items:center; gap:16px; }}
.logo {{ height:64px; border-radius:12px; background:#fff; padding:4px; }}
.logo.emoji {{ font-size:46px; background:none; height:auto; }}
h1 {{ margin:0; font-size:28px; font-weight:800; letter-spacing:.5px; }}
.sub {{ opacity:.75; font-size:14px; }}
.live {{ margin-left:auto; display:flex; align-items:center; gap:8px; font-weight:600;
  background:rgba(255,255,255,.08); padding:8px 14px; border-radius:999px; }}
.dot {{ width:10px; height:10px; border-radius:50%; background:#ff4757; animation:pulse 1.4s infinite; }}
@keyframes pulse {{ 0% {{ box-shadow:0 0 0 0 #ff4757aa; }} 100% {{ box-shadow:0 0 0 14px #ff475700; }} }}
.progress {{ background:rgba(255,255,255,.08); border-radius:999px; height:12px; overflow:hidden; }}
.progress > div {{ height:100%; width:0; border-radius:999px; transition: width 1.6s cubic-bezier(.2,.8,.2,1);
  background: linear-gradient(90deg, #00b894, #55efc4, #00b894); background-size:200% 100%; animation: flow 3s linear infinite; }}
@keyframes flow {{ to {{ background-position: -200% 0; }} }}
.plabel {{ font-size:13px; opacity:.8; margin-top:4px; }}
.board {{ flex:1; display:flex; flex-direction:column; gap:12px; justify-content:center; }}
.row {{ display:flex; align-items:center; gap:14px; background:rgba(255,255,255,.06);
  border:1px solid rgba(255,255,255,.08); border-radius:16px; padding:12px 16px;
  opacity:0; transform: translateX(-30px); animation: slideIn .7s cubic-bezier(.2,.8,.2,1) forwards; }}
.row.first {{ border-color:#f9ca24; box-shadow:0 0 0 1px #f9ca2455, 0 0 28px #f9ca2433; }}
@keyframes slideIn {{ to {{ opacity:1; transform:none; }} }}
.rank {{ width:46px; font-size:30px; text-align:center; }}
.name {{ width:200px; font-size:20px; font-weight:700; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.bar {{ flex:1; height:30px; background:rgba(255,255,255,.07); border-radius:10px; overflow:hidden; }}
.fill {{ height:100%; width:0; border-radius:10px; transition: width 1.8s cubic-bezier(.2,.8,.2,1); position:relative; }}
.fill::after {{ content:""; position:absolute; inset:0; background:linear-gradient(90deg,transparent,rgba(255,255,255,.35),transparent);
  transform:translateX(-100%); animation: gloss 2.8s 1.6s ease-in-out infinite; }}
@keyframes gloss {{ to {{ transform:translateX(100%); }} }}
.pts {{ width:110px; text-align:right; font-size:28px; font-weight:800; font-variant-numeric: tabular-nums; }}
.crown {{ display:inline-block; animation: bob 1.8s ease-in-out infinite; }}
@keyframes bob {{ 0%,100% {{ transform:translateY(0) rotate(-8deg); }} 50% {{ transform:translateY(-6px) rotate(8deg); }} }}
.ticker {{ background:rgba(0,0,0,.3); border-radius:14px; overflow:hidden; white-space:nowrap; padding:10px 0; }}
.track {{ display:inline-block; padding-left:100%; animation: scroll {max(20, 6 * max(len(recent), 1))}s linear infinite; }}
.tick {{ display:inline-block; margin-right:48px; font-size:16px; }}
.tick .grp {{ background:rgba(255,255,255,.14); padding:2px 8px; border-radius:999px; font-size:12px; margin:0 6px; }}
.tick .ev {{ opacity:.75; }}
.medal {{ margin-right:6px; }}
@keyframes scroll {{ to {{ transform: translateX(-100%); }} }}
.empty {{ text-align:center; opacity:.7; font-size:20px; }}
canvas {{ position:fixed; inset:0; pointer-events:none; }}
</style></head><body>
<canvas id="confetti"></canvas>
<div class="wrap">
  <header>
    {logo_tag}
    <div><h1>{html.escape(school)}</h1><div class="sub">{html.escape(event)} {html.escape(str(year))} · {html.escape(mode)} Live Standings</div></div>
    <div class="live"><span class="dot"></span>LIVE</div>
  </header>
  <div>
    <div class="progress"><div id="prog"></div></div>
    <div class="plabel">{done} of {total} programs completed ({pct_done}%)</div>
  </div>
  <div class="board" id="board"></div>
  <div class="ticker"><div class="track">{recent_items}</div></div>
</div>
<script>
const houses = {houses_json};
const maxPts = {max_pts};
const colors = {json.dumps(HOUSE_COLORS)};
let prev = {{}};
try {{ prev = JSON.parse(localStorage.getItem('live_prev_{mode}') || '{{}}'); }} catch (e) {{}}

const board = document.getElementById('board');
if (!houses.length) board.innerHTML = '<div class="empty">No points yet — the race is about to begin! 🏁</div>';
const medals = ['👑','🥈','🥉'];
houses.forEach((h, i) => {{
  const row = document.createElement('div');
  row.className = 'row' + (i === 0 && h.points > 0 ? ' first' : '');
  row.style.animationDelay = (i * 0.12) + 's';
  const rank = i < 3 ? (i === 0 ? '<span class="crown">👑</span>' : medals[i]) : (i + 1);
  row.innerHTML = `<div class="rank">${{rank}}</div><div class="name"></div>
    <div class="bar"><div class="fill" style="background:linear-gradient(90deg, ${{colors[i % colors.length]}}, ${{colors[i % colors.length]}}aa)"></div></div>
    <div class="pts">0</div>`;
  row.querySelector('.name').textContent = h.name;
  board.appendChild(row);
  const fill = row.querySelector('.fill'), pts = row.querySelector('.pts');
  const from = prev[h.name] || 0, to = h.points;
  setTimeout(() => {{ fill.style.width = Math.max(2, to / maxPts * 100) + '%'; }}, 150 + i * 120);
  const start = performance.now(), dur = 1600;
  (function step(t) {{
    const k = Math.min(1, (t - start) / dur), e = 1 - Math.pow(1 - k, 3);
    pts.textContent = Math.round(from + (to - from) * e);
    if (k < 1) requestAnimationFrame(step);
  }})(start);
}});
setTimeout(() => {{ document.getElementById('prog').style.width = '{pct_done}%'; }}, 200);

// Confetti when the leader's score went up since the last refresh
const leader = houses[0];
const gained = leader && leader.points > 0 && (prev[leader.name] || 0) < leader.points;
try {{ localStorage.setItem('live_prev_{mode}', JSON.stringify(Object.fromEntries(houses.map(h => [h.name, h.points])))); }} catch (e) {{}}
if (gained) {{
  const cv = document.getElementById('confetti'), ctx = cv.getContext('2d');
  cv.width = innerWidth; cv.height = innerHeight;
  const bits = Array.from({{length: 160}}, () => ({{ x: Math.random() * cv.width, y: -20 - Math.random() * cv.height,
    r: 4 + Math.random() * 6, c: colors[Math.floor(Math.random() * colors.length)], vy: 2 + Math.random() * 3,
    vx: -1 + Math.random() * 2, a: Math.random() * 6 }}));
  let frames = 0;
  (function fall() {{
    ctx.clearRect(0, 0, cv.width, cv.height);
    bits.forEach(b => {{ b.y += b.vy; b.x += b.vx; b.a += 0.1;
      ctx.save(); ctx.translate(b.x, b.y); ctx.rotate(b.a); ctx.fillStyle = b.c; ctx.fillRect(-b.r/2, -b.r/2, b.r, b.r * 1.6); ctx.restore(); }});
    if (++frames < 260) requestAnimationFrame(fall); else ctx.clearRect(0, 0, cv.width, cv.height);
  }})();
}}
</script></body></html>"""


def _load(mode):
    houses_df = run_query("""
        SELECT g.name AS name, COALESCE(SUM(s.points_assigned), 0) AS points
        FROM groups g
        LEFT JOIN scores s ON s.group_name = g.name
             AND s.program_id IN (SELECT id FROM programs WHERE event_mode = ?)
        GROUP BY g.name
        ORDER BY points DESC, g.name ASC
    """, (mode,))
    houses = [{"name": r["name"], "points": int(r["points"])} for _, r in houses_df.iterrows()]

    recent_df = run_query("""
        SELECT COALESCE(st.name, s.student_or_group_leader) AS participant, s.group_name, s.position,
               p.name AS program, p.category
        FROM scores s
        JOIN programs p ON p.id = s.program_id
        LEFT JOIN students st ON st.id = s.student_id
        WHERE p.event_mode = ? AND s.position BETWEEN 1 AND 3
        ORDER BY s.id DESC LIMIT 12
    """, (mode,))
    recent = [{"participant": str(r["participant"]), "group": r["group_name"], "position": int(r["position"]),
               "program": str(r["program"]), "category": r["category"]} for _, r in recent_df.iterrows()]

    counts = run_query("""
        SELECT COUNT(*) AS total,
               SUM(CASE WHEN id IN (SELECT program_id FROM scores) THEN 1 ELSE 0 END) AS done
        FROM programs WHERE event_mode = ?
    """, (mode,))
    total = int(counts.iloc[0]["total"] or 0)
    done = int(counts.iloc[0]["done"] or 0)
    return houses, recent, done, total


def render():
    mode = st.session_state.get('event_mode', 'Sports')
    hero(f"Live {mode} Scoreboard", "Put this on the projector — it updates on its own as scores are saved.", "📺")

    c1, c2 = st.columns([3, 1])
    with c2:
        refresh = st.select_slider("Auto-refresh", options=[5, 10, 20, 30, 60], value=10, format_func=lambda s: f"every {s}s")
    with c1:
        st.caption("💡 Tip: collapse the sidebar (‹‹ at the top-left) and press **F11** for a clean full-screen display.")

    school, event, year, logo = get_event_info()
    logo_uri = image_data_uri(logo)

    @st.fragment(run_every=refresh)
    def board():
        houses, recent, done, total = _load(mode)
        components.html(_board_html(mode, houses, recent, done, total, school, event, year, logo_uri), height=620)

    board()
