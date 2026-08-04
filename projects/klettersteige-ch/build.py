#!/usr/bin/env python3
"""Render index.html from routes.json. Run after editing routes.json:  python3 build.py"""
import json, html, pathlib, re

HERE = pathlib.Path(__file__).parent
routes = json.load(open(HERE / "routes.json"))

ENDPOINT = "https://script.google.com/macros/s/AKfycbyx858xfSCgHQ8RmbfbMsdzcmzrkNs_JZVmqeEBVrH-S6g8YJbI32CY7if-k8oTzg-eyQ/exec"
COMMENT_PROJECT = "klettersteige-nordalpen-ch"
STATUS_PROJECT = "klettersteige-ch-status"
ASSET_BASE = "https://html-comments.surge.sh/"

REGION_ORDER = [
    "Berner Oberland", "Wallis (north of the Rhône)", "Waadt & Freiburg",
    "Zentralschweiz", "Ostschweiz", "Graubünden", "Jura",
]

def band(grade):
    """Coarse difficulty band from the K-scale string — the hardest number wins."""
    nums = [int(n) for n in re.findall(r"K?(\d)", grade or "")]
    top = max(nums) if nums else 3
    if top <= 2: return ("easy", "K1–K2 · gentle")
    if top == 3: return ("mid", "K3 · moderate")
    if top == 4: return ("hard", "K4 · demanding")
    return ("extreme", "K5–K6 · severe")

def esc(x):
    return html.escape(str(x)) if x is not None else ""

cards = []
for i, r in enumerate(routes):
    b, blabel = band(r["grade"])
    lift = r.get("lift") or "—"
    # "lift" chip means the lift is effectively required — optional lifts don't count.
    ll = lift.lower()
    lift_needed = not (re.match(r"^\s*(none|no\b)", ll)
                       or "optional" in ll or "not needed" in ll or "none needed" in ll)
    dm = r.get("driveMin")
    drive_txt = (f"{dm // 60} h {dm % 60:02d}" if dm and dm >= 60 else (f"{dm} min" if dm else "—"))
    stats = [
        ("Drive there", drive_txt),
        ("Distance", f'{r["driveKm"]} km' if r.get("driveKm") else "—"),
        ("On the wire", r.get("ferrataTime") or "—"),
        ("Climb gain", (f'{r["gain"]} m' if isinstance(r.get("gain"), int) and r["gain"] > 0
                        else (f'{abs(r["gain"])} m down' if isinstance(r.get("gain"), int) else "—"))),
        ("Walk in", r.get("approachFoot") or r.get("approach", "—").split(" from")[0]),
        ("Walk out", r.get("descentFoot") or "—"),
    ]
    statrow = "".join(
        f'<div class="stat"><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>' for k, v in stats
    )
    thin = '<p class="thin-warn">Sparse data — verify locally before you commit to this one.</p>' if r.get("thin") else ""
    images = r.get("imgs") or ([r["img"]] if r.get("img") else [])
    pos = f' style="--imgpos:{esc(r["imgPos"])}"' if r.get("imgPos") else ""
    credit = f'<span class="credit">{esc(r.get("imgCredit") or "Wikimedia Commons")}</span>' if images else ""
    if len(images) > 1:
        slides = "".join(
            f'<img class="slide{" active" if j == 0 else ""}" src="{esc(url)}" alt="" '
            f'loading="{"eager" if j == 0 else "lazy"}">' for j, url in enumerate(images)
        )
        dots = "".join(
            f'<button class="gallery-dot{" active" if j == 0 else ""}" type="button" '
            f'data-slide="{j}" aria-label="Photo {j + 1} of {len(images)}" '
            f'aria-pressed="{"true" if j == 0 else "false"}"></button>'
            for j in range(len(images))
        )
        shot = (f'<div class="shot gallery" data-gallery="{len(images)}" tabindex="0" role="button" '
                f'aria-label="Open photos of {esc(r["name"])} full size"{pos}>'
                f'{slides}<span class="expand" aria-hidden="true">⤢</span>'
                f'<div class="gallery-dots">{dots}</div>{credit}</div>')
    else:
        inner = f'<img src="{esc(images[0])}" alt="" loading="lazy">' if images else ""
        attrs = (f' tabindex="0" role="button" aria-label="Open photo of {esc(r["name"])} full size"{pos}'
                 if images else "")
        shot = f'<div class="shot"{attrs}>{inner}{"<span class=\'expand\' aria-hidden=\'true\'>⤢</span>" if images else ""}{credit}</div>'
    cards.append(f'''
<article class="card" id="route-{esc(r["id"])}" data-id="{esc(r["id"])}" data-region="{esc(r["region"])}"
         data-band="{b}" data-lift="{'yes' if lift_needed else 'no'}"
         data-drive="{r.get('driveMin') or 9999}" data-type="{r.get('type') or 'ferrata'}"
         style="order:{i}"
         data-text="{esc((r['name'] + ' ' + r['base'] + ' ' + r['region'] + ' ' + r['canton'] + ' ' + (r.get('character') or '')).lower())}">
  {shot}
  <div class="body">
    <div class="chips"><span class="chip g-{b}">{esc(r["grade"])}</span><span class="chip ghost">{esc(r["canton"])}</span>
      {'<span class="chip ghost">lift</span>' if lift_needed else '<span class="chip ghost">no lift</span>'}
      {'<span class="chip warn">secured path, not a ferrata</span>' if r.get("type") == "secured" else ''}</div>
    <h3>{esc(r["name"])}</h3>
    <p class="where">{esc(r["base"])} · {esc(r["region"])}{f' · {r["summitAlt"]} m' if r.get("summitAlt") else ""}</p>
    <dl class="stats">{statrow}</dl>
    <p class="prose">{esc(r.get("character"))}</p>
    <p class="detail"><b>Approach.</b> {esc(r.get("approach"))}</p>
    <p class="detail"><b>Descent.</b> {esc(r.get("descent"))}</p>
    <p class="detail"><b>Lift.</b> {esc(lift)}</p>
    <p class="detail"><b>Season.</b> {esc(r.get("season"))}</p>
    {f'<p class="caveat">{esc(r.get("caveat"))}</p>' if r.get("caveat") else ""}
    {thin}
    <div class="actions">
      <button class="act want" data-act="want" aria-pressed="false">Want to go</button>
      <button class="act done" data-act="done" aria-pressed="false">Done</button>
      <a class="src" href="{esc(r.get("src"))}" target="_blank" rel="noopener">source ↗</a>
    </div>
  </div>
</article>''')

regions = [x for x in REGION_ORDER if any(r["region"] == x for r in routes)]
region_opts = "".join(f'<option value="{esc(x)}">{esc(x)}</option>' for x in regions)

CSS = """
*,*::before,*::after{box-sizing:border-box}
:root{
  --bg:#f6f5f1; --panel:#fffefb; --ink:#1f2724; --soft:#5d6b64; --line:#dcdcd3;
  --pine:#25543f; --pine-2:#357a5b; --rock:#8a7f6d; --alert:#a8442a; --gold:#d59b1e;
  --shadow:0 1px 2px #1f27240d, 0 8px 24px #1f27240f;
}
@media (prefers-color-scheme:dark){:root{
  --bg:#14181a; --panel:#1c2225; --ink:#e8ebe7; --soft:#9dada4; --line:#2e3739;
  --pine:#7fc4a1; --pine-2:#9ad9b8; --rock:#b3a894; --alert:#e8836a; --gold:#e8bb52;
  --shadow:0 1px 2px #0006, 0 10px 28px #0005;
}}
:root[data-theme=dark]{
  --bg:#14181a; --panel:#1c2225; --ink:#e8ebe7; --soft:#9dada4; --line:#2e3739;
  --pine:#7fc4a1; --pine-2:#9ad9b8; --rock:#b3a894; --alert:#e8836a; --gold:#e8bb52;
  --shadow:0 1px 2px #0006, 0 10px 28px #0005;
}
:root[data-theme=light]{
  --bg:#f6f5f1; --panel:#fffefb; --ink:#1f2724; --soft:#5d6b64; --line:#dcdcd3;
  --pine:#25543f; --pine-2:#357a5b; --rock:#8a7f6d; --alert:#a8442a; --gold:#d59b1e;
  --shadow:0 1px 2px #1f27240d, 0 8px 24px #1f27240f;
}
body{margin:0;background:var(--bg);color:var(--ink);
  font:16px/1.6 ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
  -webkit-text-size-adjust:100%}
.wrap{max-width:1180px;margin:0 auto;padding:0 20px}
a{color:var(--pine-2)}

header.top{border-bottom:1px solid var(--line);background:
  linear-gradient(180deg,color-mix(in srgb,var(--pine) 9%,transparent),transparent)}
header.top .wrap{padding-top:52px;padding-bottom:34px}
.kicker{text-transform:uppercase;letter-spacing:.16em;font-size:.7rem;font-weight:700;color:var(--pine-2);margin:0 0 12px}
h1{font-size:clamp(2rem,5vw,3.1rem);line-height:1.08;margin:0 0 14px;letter-spacing:-.02em;
   font-family:ui-serif,Georgia,"Iowan Old Style",serif;font-weight:600}
.lede{max-width:62ch;color:var(--soft);margin:0 0 4px;font-size:1.05rem}
.scope{max-width:70ch;font-size:.9rem;color:var(--soft);border-left:3px solid var(--line);
  padding:2px 0 2px 14px;margin:20px 0 0}
.scope b{color:var(--ink)}

.idbar{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-top:24px;font-size:.88rem}
.idbar input{font:inherit;padding:7px 11px;border:1px solid var(--line);border-radius:7px;
  background:var(--panel);color:var(--ink);min-width:180px}
.idbar .who{color:var(--soft)}
.idbar .who b{color:var(--pine-2)}
.idbar.anon .who b{color:var(--gold)}

.controls{position:sticky;top:0;z-index:40;background:color-mix(in srgb,var(--bg) 92%,transparent);
  backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}
.controls .wrap{display:flex;gap:10px;align-items:center;flex-wrap:wrap;padding-top:12px;padding-bottom:12px}
.tabs{display:flex;gap:2px;background:var(--panel);border:1px solid var(--line);border-radius:9px;padding:3px}
.tabs button{font:inherit;font-size:.86rem;font-weight:600;border:0;background:none;color:var(--soft);
  padding:6px 13px;border-radius:6px;cursor:pointer}
.tabs button[aria-selected=true]{background:var(--pine);color:#fff}
:root[data-theme=dark] .tabs button[aria-selected=true],
@media (prefers-color-scheme:dark){.tabs button[aria-selected=true]{color:#12211a}}
.tabs .n{opacity:.7;font-variant-numeric:tabular-nums}
select,input[type=search]{font:inherit;font-size:.88rem;padding:7px 10px;border:1px solid var(--line);
  border-radius:7px;background:var(--panel);color:var(--ink)}
input[type=search]{flex:1;min-width:150px}
.count{margin-left:auto;font-size:.82rem;color:var(--soft);font-variant-numeric:tabular-nums}
#themeBtn{font:inherit;font-size:.82rem;border:1px solid var(--line);background:var(--panel);
  color:var(--soft);border-radius:7px;padding:7px 10px;cursor:pointer}

main .wrap{padding-top:26px;padding-bottom:70px}
.grid{display:grid;gap:20px;grid-template-columns:repeat(auto-fill,minmax(330px,1fr))}
.card{background:var(--panel);border:1px solid var(--line);border-radius:13px;overflow:hidden;
  box-shadow:var(--shadow);display:flex;flex-direction:column}
.card.hide{display:none}
.shot{position:relative;aspect-ratio:16/9;background:color-mix(in srgb,var(--rock) 22%,var(--panel));overflow:hidden}
.shot img{width:100%;height:100%;object-fit:cover;object-position:var(--imgpos,center);display:block}
.shot[role=button]{cursor:zoom-in}
.shot .expand{position:absolute;right:7px;top:7px;width:26px;height:26px;border-radius:7px;
  background:#0009;color:#fff;display:grid;place-items:center;font-size:.82rem;line-height:1;
  opacity:0;transition:opacity .18s;pointer-events:none}
.shot:hover .expand,.shot:focus-visible .expand{opacity:1}
.shot:focus-visible{outline:2px solid var(--pine-2);outline-offset:2px}
@media (hover:none){.shot .expand{opacity:.85}}
.shot.gallery .slide{position:absolute;inset:0;opacity:0;transition:opacity .35s ease}
.shot.gallery .slide.active{opacity:1}
.gallery-dots{position:absolute;left:7px;bottom:6px;display:flex;gap:5px}
.gallery-dot{width:8px;height:8px;padding:0;border:1px solid #fff;background:#fff8;border-radius:50%;cursor:pointer}
.gallery-dot.active{background:#fff}
@media (prefers-reduced-motion:reduce){.shot.gallery .slide{transition:none}}
.credit{position:absolute;right:6px;bottom:5px;font-size:.6rem;line-height:1.3;color:#fff;
  background:#0009;padding:2px 6px;border-radius:4px;max-width:80%;overflow:hidden;
  text-overflow:ellipsis;white-space:nowrap}
.body{padding:16px 17px 15px;display:flex;flex-direction:column;flex:1}
.chips{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:9px}
.chip{font-size:.7rem;font-weight:700;letter-spacing:.03em;padding:3px 8px;border-radius:20px;
  border:1px solid transparent;white-space:nowrap}
.chip.ghost{background:none;border-color:var(--line);color:var(--soft);font-weight:600}
.chip.warn{background:color-mix(in srgb,var(--alert) 12%,transparent);color:var(--alert);
  border-color:color-mix(in srgb,var(--alert) 40%,transparent)}
.g-easy{background:#2f7d4f1f;color:#2f7d4f;border-color:#2f7d4f4d}
.g-mid{background:#b8891018;color:#96700c;border-color:#b889103d}
.g-hard{background:#c1571e1c;color:#b0531f;border-color:#c1571e40}
.g-extreme{background:#a32f2f1c;color:#9e3030;border-color:#a32f2f40}
@media (prefers-color-scheme:dark){
  .g-easy{color:#7fd3a0}.g-mid{color:#e3bd5c}.g-hard{color:#f0916a}.g-extreme{color:#f08a8a}}
:root[data-theme=dark] .g-easy{color:#7fd3a0}
:root[data-theme=dark] .g-mid{color:#e3bd5c}
:root[data-theme=dark] .g-hard{color:#f0916a}
:root[data-theme=dark] .g-extreme{color:#f08a8a}
.card h3{margin:0 0 3px;font-size:1.12rem;line-height:1.25;letter-spacing:-.01em;
  font-family:ui-serif,Georgia,serif;font-weight:600}
.where{margin:0 0 13px;font-size:.82rem;color:var(--soft)}
.stats{display:grid;grid-template-columns:1fr 1fr 1fr;gap:1px;margin:0 0 13px;
  background:var(--line);border:1px solid var(--line);border-radius:8px;overflow:hidden}
.stat{background:var(--panel);padding:7px 10px}
.stat dt{font-size:.63rem;text-transform:uppercase;letter-spacing:.09em;color:var(--soft);font-weight:700}
.stat dd{margin:1px 0 0;font-size:.87rem;font-weight:600;font-variant-numeric:tabular-nums}
.prose{margin:0 0 11px;font-size:.9rem}
.detail{margin:0 0 5px;font-size:.83rem;color:var(--soft)}
.detail b{color:var(--ink);font-weight:600}
.caveat{margin:10px 0 0;font-size:.82rem;color:var(--soft);border-left:3px solid var(--gold);
  padding:3px 0 3px 11px;background:color-mix(in srgb,var(--gold) 7%,transparent)}
.thin-warn{margin:9px 0 0;font-size:.79rem;color:var(--alert)}
.actions{display:flex;gap:7px;align-items:center;margin-top:auto;padding-top:14px}
.act{font:inherit;font-size:.8rem;font-weight:600;padding:6px 12px;border-radius:7px;cursor:pointer;
  border:1px solid var(--line);background:none;color:var(--soft)}
.act:hover{border-color:var(--pine-2);color:var(--pine-2)}
.act[aria-pressed=true].want{background:var(--gold);border-color:var(--gold);color:#231a02}
.act[aria-pressed=true].done{background:var(--pine);border-color:var(--pine);color:#fff}
:root[data-theme=dark] .act[aria-pressed=true].done{color:#12211a}
@media (prefers-color-scheme:dark){.act[aria-pressed=true].done{color:#12211a}}
.src{margin-left:auto;font-size:.76rem;color:var(--soft);text-decoration:none}
.src:hover{color:var(--pine-2)}
.empty{padding:60px 10px;text-align:center;color:var(--soft)}
.sync{position:fixed;left:16px;bottom:16px;z-index:60;background:var(--panel);border:1px solid var(--line);
  border-radius:8px;padding:6px 11px;font-size:.76rem;color:var(--soft);box-shadow:var(--shadow);display:none}
.sync.show{display:block}
.lb{position:fixed;inset:0;z-index:2000;background:#0b0e0ff7;display:none;align-items:center;
  justify-content:center;padding:56px 16px 92px}
.lb.open{display:flex}
.lb img{max-width:100%;max-height:100%;width:auto;height:auto;object-fit:contain;
  border-radius:5px;box-shadow:0 18px 60px #000a}
.lb button{position:absolute;background:#ffffff1a;border:1px solid #ffffff33;color:#fff;
  border-radius:10px;cursor:pointer;font:inherit;line-height:1}
.lb button:hover{background:#ffffff2e}
.lb-close{top:14px;right:16px;width:42px;height:42px;font-size:1.4rem}
.lb-nav{top:50%;transform:translateY(-50%);width:46px;height:64px;font-size:1.5rem}
.lb-prev{left:14px}.lb-next{right:14px}
.lb-cap{position:absolute;left:0;right:0;bottom:0;padding:16px 20px 22px;color:#cfd8d3;
  text-align:center;font-size:.83rem;background:linear-gradient(transparent,#000000cc);
  pointer-events:none}
.lb-cap b{display:block;font-size:1rem;font-weight:600;color:#fff;margin-bottom:3px;
  font-family:ui-serif,Georgia,serif}
.lb-count{opacity:.65;font-variant-numeric:tabular-nums;margin-left:8px}
@media (max-width:560px){.lb{padding:52px 8px 88px}.lb-nav{width:38px;height:54px}}
footer{border-top:1px solid var(--line);background:var(--panel)}
footer .wrap{padding:34px 20px 60px;font-size:.85rem;color:var(--soft)}
footer h2{font-size:.95rem;color:var(--ink);margin:0 0 8px}
footer p{max-width:74ch;margin:0 0 12px}
@media (max-width:560px){header.top .wrap{padding-top:34px}.grid{grid-template-columns:1fr}}
"""

JS = f"""
const ENDPOINT = {json.dumps(ENDPOINT)};
const PROJECT  = {json.dumps(STATUS_PROJECT)};
const DEFAULT_DONE = {json.dumps({r["id"]: {"names": r.get("doneFor", []), "date": r.get("doneDate")} for r in routes if r.get("doneFor")})};
const LS_NAME  = 'ks-name', LS_STATE = 'ks-state', LS_OUT = 'ks-outbox';

const $ = s => document.querySelector(s);
const cards = [...document.querySelectorAll('.card')];
cards.forEach((c, i) => c.dataset.order = i);
let me = localStorage.getItem(LS_NAME) || '';
let state = JSON.parse(localStorage.getItem(LS_STATE) || '{{}}');   // id -> 'want'|'done'
let outbox = JSON.parse(localStorage.getItem(LS_OUT) || '[]');
let view = 'all';
let epoch = 0;                        // bumped on every local edit, so a stale server read can't win

let touched = new Set();   // ids this person has explicitly set OR cleared

function applyDefaultDone() {{
  // A doneFor seed must not resurrect a mark the person deliberately removed: on the server
  // "cleared" looks identical to "never set", so we track explicit actions separately.
  if (!me) return;
  for (const [id, entry] of Object.entries(DEFAULT_DONE)) {{
    if (touched.has(id) || state[id]) continue;
    if (entry.names.some(name => name.toLowerCase() === me.toLowerCase())) state[id] = 'done';
  }}
}}

/* ---- mini photo rotations ---- */
for (const gallery of document.querySelectorAll('.gallery')) {{
  const slides = [...gallery.querySelectorAll('.slide')];
  const dots = [...gallery.querySelectorAll('.gallery-dot')];
  let index = 0, timer = null;
  const show = next => {{
    index = (next + slides.length) % slides.length;
    slides.forEach((slide, i) => slide.classList.toggle('active', i === index));
    dots.forEach((dot, i) => {{
      dot.classList.toggle('active', i === index);
      dot.setAttribute('aria-pressed', i === index);
    }});
  }};
  const stop = () => {{ if (timer) {{ clearInterval(timer); timer = null; }} }};
  const start = () => {{
    stop();
    if (!matchMedia('(prefers-reduced-motion: reduce)').matches)
      timer = setInterval(() => show(index + 1), 3500);
  }};
  dots.forEach((dot, i) => dot.addEventListener('click', () => {{ stop(); show(i); start(); }}));
  gallery._stop = stop; gallery._start = start;   // the lightbox pauses rotation while open
  gallery.addEventListener('mouseenter', stop);
  gallery.addEventListener('mouseleave', start);
  gallery.addEventListener('focusin', stop);
  gallery.addEventListener('focusout', start);
  start();
}}

/* ---- theme ---- */
const themeBtn = $('#themeBtn');
const savedTheme = localStorage.getItem('ks-theme');
if (savedTheme) document.documentElement.dataset.theme = savedTheme;
themeBtn.onclick = () => {{
  const cur = document.documentElement.dataset.theme
    || (matchMedia('(prefers-color-scheme:dark)').matches ? 'dark' : 'light');
  const next = cur === 'dark' ? 'light' : 'dark';
  document.documentElement.dataset.theme = next;
  localStorage.setItem('ks-theme', next);
}};

/* ---- identity ---- */
const nameInput = $('#nameInput');
function paintName() {{
  nameInput.value = me;
  $('#whoName').textContent = me || 'nobody yet';
  $('#idbar').classList.toggle('anon', !me);
}}
nameInput.addEventListener('change', () => {{
  me = nameInput.value.trim();
  localStorage.setItem(LS_NAME, me);
  touched = new Set();
  paintName(); applyDefaultDone(); paint(); pull();
}});

/* ---- persistence ---- */
function save() {{
  localStorage.setItem(LS_STATE, JSON.stringify(state));
  localStorage.setItem(LS_OUT, JSON.stringify(outbox));
}}
function flash(msg) {{
  const el = $('#sync'); el.textContent = msg; el.classList.add('show');
  clearTimeout(flash.t); flash.t = setTimeout(() => el.classList.remove('show'), 2600);
}}
async function post(rec) {{
  const res = await fetch(ENDPOINT, {{
    method: 'POST', headers: {{'Content-Type': 'text/plain;charset=utf-8'}},
    body: JSON.stringify(rec), keepalive: true
  }});
  const j = await res.json();
  if (!j.ok) throw new Error(j.error || 'rejected');
}}
let draining = null;
function drain() {{
  // One sender at a time: concurrent clicks would otherwise post the same record twice
  // and leave entries stranded in the outbox. Late callers chain onto the running pass.
  if (draining) {{ draining = draining.then(drainOnce); return draining; }}
  draining = drainOnce().finally(() => {{ draining = null; }});
  return draining;
}}
async function drainOnce() {{
  while (outbox.length) {{
    const rec = outbox[0];
    try {{ await post(rec); }}
    catch {{ flash(outbox.length + ' change(s) waiting to sync'); return; }}
    outbox.shift(); save();
  }}
  flash('Synced');
}}
function record(id, value) {{
  const rec = {{project: PROJECT, itemId: id, vote: value, voter: me || 'anonymous',
                session: navigator.userAgent.slice(0, 60)}};
  outbox.push(rec); save(); drain();
}}
async function pull() {{
  if (!me) return;
  if (draining) await draining.catch(() => {{}});   // don't read a snapshot mid-send
  const at = epoch;                                // ...and don't apply one that edits raced past
  try {{
    const r = await fetch(ENDPOINT + '?action=rows&project=' + encodeURIComponent(PROJECT));
    const j = await r.json();
    if (!j.ok) return;
    const mine = {{}}; const seen = new Set();
    for (const row of j.rows) {{                       // oldest first — last write wins
      if ((row.voter || '').toLowerCase() !== me.toLowerCase()) continue;
      seen.add(row.itemId);
      if (row.vote === 'none') delete mine[row.itemId];
      else if (row.vote === 'want' || row.vote === 'done') mine[row.itemId] = row.vote;
    }}
    for (const rec of outbox) {{                       // unsynced local wins over the server
      if ((rec.voter || '').toLowerCase() !== me.toLowerCase()) continue;
      seen.add(rec.itemId);
      if (rec.vote === 'none') delete mine[rec.itemId]; else mine[rec.itemId] = rec.vote;
    }}
    if (epoch !== at) return;                      // a click landed while we were fetching
    state = mine; touched = seen; applyDefaultDone(); save(); paint();
  }} catch {{ /* offline: keep the local copy */ }}
}}

/* ---- rendering ---- */
function paint() {{
  for (const c of cards) {{
    const s = state[c.dataset.id];
    c.querySelector('[data-act=want]').setAttribute('aria-pressed', s === 'want');
    c.querySelector('[data-act=done]').setAttribute('aria-pressed', s === 'done');
  }}
  filter();
}}
function filter() {{
  const q = $('#q').value.trim().toLowerCase();
  const reg = $('#region').value, bnd = $('#bandSel').value, lift = $('#liftSel').value;
  const drv = $('#driveSel').value;
  sortCards();
  let shown = 0;
  for (const c of cards) {{
    const s = state[c.dataset.id];
    const ok = (view === 'all' || s === view)
      && (!drv || +c.dataset.drive <= +drv)
      && (!reg || c.dataset.region === reg)
      && (!bnd || c.dataset.band === bnd)
      && (!lift || c.dataset.lift === lift)
      && (!q || c.dataset.text.includes(q));
    c.classList.toggle('hide', !ok);
    if (ok) shown++;
  }}
  $('#count').textContent = shown + ' of ' + cards.length + ' routes';
  $('#empty').style.display = shown ? 'none' : 'block';
  $('#nWant').textContent = Object.values(state).filter(v => v === 'want').length;
  $('#nDone').textContent = Object.values(state).filter(v => v === 'done').length;
}}

document.addEventListener('click', e => {{
  const btn = e.target.closest('.act'); if (!btn) return;
  const card = btn.closest('.card'), id = card.dataset.id, act = btn.dataset.act;
  if (!me) {{
    flash('Add your name first so your list is yours');
    nameInput.focus(); return;
  }}
  const next = state[id] === act ? 'none' : act;
  if (next === 'none') delete state[id]; else state[id] = next;
  touched.add(id); epoch++; save(); record(id, next); paint();
}});

const BAND_RANK = {{easy: 0, mid: 1, hard: 2, extreme: 3}};
function sortCards() {{
  const how = $('#sortSel').value;
  const key = c => {{
    switch (how) {{
      case 'drive':     return +c.dataset.drive;
      case 'driveDesc': return -c.dataset.drive;
      case 'grade':     return BAND_RANK[c.dataset.band] * 1000 + +c.dataset.drive / 100;
      case 'gradeDesc': return -BAND_RANK[c.dataset.band] * 1000 + +c.dataset.drive / 100;
      default:          return +c.dataset.order;
    }}
  }};
  [...cards].sort((a, b) => key(a) - key(b)).forEach((c, i) => c.style.order = i);
}}
for (const el of ['#q', '#region', '#bandSel', '#liftSel', '#driveSel', '#sortSel'])
  $(el).addEventListener('input', filter);
document.querySelectorAll('.tabs button').forEach(b => b.onclick = () => {{
  view = b.dataset.view;
  document.querySelectorAll('.tabs button').forEach(x => x.setAttribute('aria-selected', x === b));
  filter();
}});
addEventListener('online', drain);

/* ---- lightbox: cards crop to 16:9, this shows the whole frame ---- */
const lb = $('#lb'), lbImg = $('#lbImg');
let lbSrcs = [], lbAt = 0, lbReturn = null, lbGallery = null;

function lbShow(i) {{
  lbAt = (i + lbSrcs.length) % lbSrcs.length;
  lbImg.src = lbSrcs[lbAt];
  $('#lbCount').textContent = lbSrcs.length > 1 ? `${{lbAt + 1}} / ${{lbSrcs.length}}` : '';
  const multi = lbSrcs.length > 1 ? '' : 'none';
  $('#lbPrev').style.display = multi; $('#lbNext').style.display = multi;
}}
function lbOpen(shot, i) {{
  const imgs = [...shot.querySelectorAll('img')];
  if (!imgs.length) return;
  lbSrcs = imgs.map(im => im.currentSrc || im.src);
  $('#lbTitle').textContent = shot.closest('.card').querySelector('h3').textContent;
  $('#lbCredit').textContent = shot.querySelector('.credit')?.textContent || '';
  lbGallery = shot.classList.contains('gallery') ? shot : null;
  lbGallery?._stop?.();                       // don't rotate underneath the viewer
  lbReturn = document.activeElement;
  lb.classList.add('open');
  document.body.style.overflow = 'hidden';
  lbShow(i || 0);
  $('#lbClose').focus();
}}
function lbClose() {{
  if (!lb.classList.contains('open')) return;
  lb.classList.remove('open');
  document.body.style.overflow = '';
  lbImg.removeAttribute('src');
  lbGallery?._start?.(); lbGallery = null;
  lbReturn?.focus?.(); lbReturn = null;
}}
function openFromShot(shot) {{
  const slides = [...shot.querySelectorAll('.slide')];
  const active = slides.findIndex(s => s.classList.contains('active'));
  lbOpen(shot, active > 0 ? active : 0);      // open on whatever the carousel is showing
}}

document.addEventListener('click', e => {{
  if (e.target.closest('.gallery-dot')) return;          // dots switch slides, not open the viewer
  if (e.target.closest('.lb')) {{
    if (e.target.closest('#lbClose')) return lbClose();
    if (e.target.closest('#lbPrev'))  return lbShow(lbAt - 1);
    if (e.target.closest('#lbNext'))  return lbShow(lbAt + 1);
    if (e.target !== lbImg) lbClose();                   // click the backdrop to dismiss
    return;
  }}
  const shot = e.target.closest('.shot[role=button]');
  if (shot) openFromShot(shot);
}});
document.addEventListener('keydown', e => {{
  if (lb.classList.contains('open')) {{
    if (e.key === 'Escape') lbClose();
    else if (e.key === 'ArrowRight') lbShow(lbAt + 1);
    else if (e.key === 'ArrowLeft') lbShow(lbAt - 1);
    return;
  }}
  const shot = e.target.closest?.('.shot[role=button]');
  if (shot && (e.key === 'Enter' || e.key === ' ')) {{ e.preventDefault(); openFromShot(shot); }}
}});
let lbX = null;
lb.addEventListener('touchstart', e => {{ lbX = e.changedTouches[0].clientX; }}, {{passive: true}});
lb.addEventListener('touchend', e => {{
  if (lbX === null) return;
  const dx = e.changedTouches[0].clientX - lbX; lbX = null;
  if (Math.abs(dx) > 45 && lbSrcs.length > 1) lbShow(lbAt + (dx < 0 ? 1 : -1));
}}, {{passive: true}});

paintName(); applyDefaultDone(); paint(); pull(); drain();
"""

HTML = f"""<!doctype html>
<!-- GENERATED FILE — do not edit. Edit routes.json, then run: python3 build.py
     Adding photos? See AGENTS.md in this folder. -->
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow,noarchive,nosnippet,noimageindex">
<meta name="googlebot" content="noindex,nofollow">
<meta name="referrer" content="no-referrer">
<title>Klettersteige north of the Alps — Switzerland</title>
<style>{CSS}</style>
</head>
<body>

<header class="top"><div class="wrap">
  <p class="kicker">Personal planning page · not indexed</p>
  <h1>Klettersteige north of the Alps</h1>
  <p class="lede">Every via ferrata in Switzerland you can simply walk up to and climb — no guide,
     no ticket, no gate — outside Ticino and the south-facing valleys. {len(routes)} routes, each with the drive
     from Bergdietikon and the walk in and walk out spelled out, because the cable car is optional
     and the legs are not.</p>
  <p class="scope"><b>Scope.</b> All of Switzerland except Ticino, the Valais valleys south of the
     Rhône, and the Italian-facing Graubünden valleys (Bergell, Misox, Puschlav, Val Müstair).
     Guide-only routes, ticketed ferrata parks and commercial canyon courses are excluded.
     Where a lift exists it is named, and the on-foot alternative is given wherever one is practical.</p>
  <div class="idbar" id="idbar">
    <label for="nameInput">Your name</label>
    <input id="nameInput" type="text" placeholder="e.g. Lukas" autocomplete="name">
    <span class="who">Lists are saved for <b id="whoName">nobody yet</b></span>
  </div>
</div></header>

<div class="controls"><div class="wrap">
  <div class="tabs" role="tablist">
    <button data-view="all" role="tab" aria-selected="true">All</button>
    <button data-view="want" role="tab" aria-selected="false">Want to go <span class="n" id="nWant">0</span></button>
    <button data-view="done" role="tab" aria-selected="false">Done <span class="n" id="nDone">0</span></button>
  </div>
  <input id="q" type="search" placeholder="Search name, village, canton…">
  <select id="region"><option value="">All regions</option>{region_opts}</select>
  <select id="bandSel">
    <option value="">Any grade</option>
    <option value="easy">K1–K2 · gentle</option>
    <option value="mid">K3 · moderate</option>
    <option value="hard">K4 · demanding</option>
    <option value="extreme">K5–K6 · severe</option>
  </select>
  <select id="driveSel">
    <option value="">Any drive</option>
    <option value="60">≤ 1 h away</option>
    <option value="90">≤ 1½ h away</option>
    <option value="120">≤ 2 h away</option>
    <option value="180">≤ 3 h away</option>
  </select>
  <select id="sortSel">
    <option value="region">By region</option>
    <option value="drive">Nearest first</option>
    <option value="driveDesc">Furthest first</option>
    <option value="grade">Easiest first</option>
    <option value="gradeDesc">Hardest first</option>
  </select>
  <select id="liftSel">
    <option value="">Lift or not</option>
    <option value="no">No lift needed</option>
    <option value="yes">Lift involved</option>
  </select>
  <button id="themeBtn" type="button">Theme</button>
  <span class="count" id="count"></span>
</div></div>

<main><div class="wrap">
  <div class="grid">{''.join(cards)}</div>
  <p class="empty" id="empty" style="display:none">Nothing matches those filters yet.</p>
</div></main>

<div class="sync" id="sync"></div>

<div class="lb" id="lb" role="dialog" aria-modal="true" aria-label="Photo viewer">
  <img id="lbImg" alt="">
  <button class="lb-close" id="lbClose" type="button" aria-label="Close (Esc)">&times;</button>
  <button class="lb-nav lb-prev" id="lbPrev" type="button" aria-label="Previous photo">&#8249;</button>
  <button class="lb-nav lb-next" id="lbNext" type="button" aria-label="Next photo">&#8250;</button>
  <p class="lb-cap"><b id="lbTitle"></b><span id="lbCredit"></span><span class="lb-count" id="lbCount"></span></p>
</div>

<footer><div class="wrap">
  <h2>How to read this, and what not to trust</h2>
  <p><b>Grades</b> are the Hüsler K-scale (K1 easy → K6 extreme) as used in Switzerland; where a
     source gave the Schall A–F scale it is shown in brackets. A route's grade is its hardest move,
     not its average — several K4 routes here are K2 for all but ten metres.</p>
  <p><b>Times</b> are the source's own figures, not measured. "On the wire" is the secured section
     alone; the walk in and walk out are separate so you can see what a day actually costs if you
     skip the lift. Where a source gave no figure the field reads "—" rather than a guess.</p>
  <p><b>Sources.</b> Route selection follows the SAC/AT-Verlag guidebook <i>Die Klettersteige der
     Schweiz</i> (Hüsler &amp; Anker, 2020 edition, 100 routes), filtered to the scope above. Per-route
     figures come from myferrata.ch, bergsteigen.com, klettersteig.de, the SAC Tourenportal and the
     operators' own pages — each card links its source.</p>
  <p><b>Drive times</b> are road-routing from Bergdietikon AG to the nearest car park, via OSRM on
     OpenStreetMap data — free-flow, so no traffic, and optimistic on a summer Saturday. Car-free
     resorts point at the valley station you actually park at: Mürren → Stechelberg, Braunwald →
     Linthal, Melchsee-Frutt → Stöckalp. Leukerbad is routed entirely by road at 305 km; the
     Lötschberg car train from Kandersteg cuts that substantially. Alpine passes are assumed open,
     which for these summer routes is usually fair — but check Susten, Klausen and Grimsel in June.</p>
  <p><b>Photographs</b> are mostly freely licensed images from Wikimedia Commons showing the peak or the
     area, not necessarily the ferrata itself. Personal photos are labelled and credited on the image.</p>
  <p><b>Conditions change.</b> Cables get removed for winter, routes close for rockfall, lifts run to
     short summer timetables. The Senda ferrada Piz Mitgel above Savognin, for instance, was
     dismantled and is not listed. Check the operator before you drive.</p>
  <h2>Comments and lists</h2>
  <p>Select any text to leave a comment or a suggested edit — the button is bottom-right. Your
     <i>Want to go</i> and <i>Done</i> marks are keyed to the name you enter at the top and sync to a
     shared sheet; changes made offline queue up and send when you are back on the network.</p>
</div></footer>

<script>{JS}</script>
<script>
(function () {{
  window.HC_CONFIG = {{ endpoint: {json.dumps(ENDPOINT)}, project: {json.dumps(COMMENT_PROJECT)} }};
  var BASE = {json.dumps(ASSET_BASE)};
  var link = document.createElement('link');
  link.rel = 'stylesheet'; link.href = BASE + 'html-comments.css';
  document.head.appendChild(link);
  var s = document.createElement('script');
  s.src = BASE + 'html-comments.js';
  document.head.appendChild(s);
}})();
</script>
</body>
</html>
"""

(HERE / "index.html").write_text(HTML, encoding="utf-8")
print(f"wrote index.html — {len(routes)} routes, {sum(len(r.get('imgs') or ([r['img']] if r.get('img') else [])) for r in routes)} images")
