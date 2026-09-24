#!/usr/bin/env python3
"""Sidhi systemic-layer infographic -> Figma-ready SVG (2400 wide, dark editorial).

The 8 structures + 4 mental models below the 53 deaths. Matches the visual
language of sidhi_maternal_deaths.svg (build_svg.py).
"""
import html

W = 2400
BG = "#0d0d11"; PANEL = "#141419"; LINE = "#26262f"
INK = "#f2efe6"; MUTED = "#9d9ba6"
RED = "#e5484d"; TEAL = "#2dd4bf"; AMBER = "#f5a524"; PURPLE = "#8e4ec6"
SERIF = "Georgia, 'Times New Roman', serif"
SANS = "'Inter', -apple-system, 'Helvetica Neue', Arial, sans-serif"
MONO = "ui-monospace, 'SF Mono', Menlo, Consolas, monospace"

o = []
def add(s): o.append(s)
def esc(s): return html.escape(s, quote=False)
def txt(x, y, s, size, fill=INK, anchor="start", fam=SANS, wt="400", ls=None, op=1.0):
    st = f'x="{x}" y="{y}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-family="{fam}" font-weight="{wt}"'
    if ls: st += f' letter-spacing="{ls}"'
    if op != 1.0: st += f' opacity="{op}"'
    add(f'<text {st}>{esc(s)}</text>')
def rect(x, y, w, h, fill, rx=18, stroke=None, sw=0, op=1.0):
    st = f'x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}"'
    if stroke: st += f' stroke="{stroke}" stroke-width="{sw}"'
    if op != 1.0: st += f' opacity="{op}"'
    add(f'<rect {st}/>')
def line(x1, y1, x2, y2, stroke, sw=2, op=1.0):
    add(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{sw}" opacity="{op}"/>')
def wrap(s, n):
    words, lines, cur = s.split(), [], ""
    for w in words:
        if len(cur) + 1 + len(w) > n:
            lines.append(cur); cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur: lines.append(cur)
    return lines

M = 120
CW = W - 2 * M  # 2160 content width

y = 0
rect_pad = []  # not needed; y flows

def section_head(kicker):
    global y
    txt(M, y, kicker, 36, MUTED, fam=MONO, ls=4); y += 80

def card(tag, title, body, source, accent):
    global y
    lines = wrap(body, 62)
    assert len(lines) <= 3, "body too long: " + body
    h = 36 + 64 + 28 + 52 + 26 + len(lines) * 58 + 34 + 44 + 40
    rect(M, y, CW, h, PANEL, stroke=LINE, sw=2)
    rect(M + 4, y + 4, 10, h - 8, accent, rx=5)  # left accent bar
    # chip
    rect(M + 48, y + 40, 110, 68, accent, rx=10)
    txt(M + 103, y + 88, tag, 40, "#ffffff", anchor="middle", wt="700")
    txt(M + 190, y + 88, title, 46, INK, wt="700")
    by = y + 168
    for ln in lines:
        txt(M + 190, by, ln, 38, INK); by += 58
    txt(M + 190, by + 34, "\u21b3 " + source, 32, MUTED, fam=MONO)
    y += h + 36

# ------------------------------- build -------------------------------
y = 110
txt(M, y, "SYSTEMS RESEARCH  \u00b7  SEPT 2026  \u00b7  SIDHI, MADHYA PRADESH", 34, RED, fam=MONO, ls=4); y += 120
txt(M, y, "The system", 190, INK, fam=SERIF, wt="700"); y += 40
txt(M, y + 150, "below the deaths", 190, INK, fam=SERIF, wt="700"); y += 215
for s in wrap("8 structures and 4 mental models that produce maternal deaths \u2014 what sits below the events in Sidhi.", 58):
    txt(M, y, s, 44, MUTED); y += 62
y += 30
line(M, y, W - M, y, LINE, 2); y += 90

# iceberg strip
section_head("THE ICEBERG \u2014 WHAT YOU SEE \u2192 WHAT RUNS IT")
ice = [
    ("EVENTS", "53 deaths in a year", "what the news counts", "#6b7280"),
    ("PATTERNS", "transit deaths \u00b7 anaemia \u00b7 ignored warnings", "what keeps recurring", "#6b7280"),
    ("STRUCTURES", "8 \u2014 the system design", "what produces the patterns", RED),
    ("MODELS", "4 \u2014 the assumptions", "what the design assumes", PURPLE),
]
pw, pgap, ph = (CW - 3 * 40) / 4, 40, 300
for i, (label, big, small, c) in enumerate(ice):
    x = M + i * (pw + pgap)
    rect(x, y, pw, ph, PANEL, stroke=LINE, sw=2)
    rect(x, y, pw, 12, c, rx=0)
    txt(x + 36, y + 78, label, 36, c, fam=MONO, ls=3, wt="700")
    for j, ln in enumerate(wrap(big, 22)):
        txt(x + 36, y + 140 + j * 46, ln, 38, INK)
    txt(x + 36, y + 252, small, 30, MUTED)
y += ph + 90
line(M, y, W - M, y, LINE, 2); y += 90

# structures
section_head("STRUCTURES \u2014 8  \u00b7  THE SYSTEM DESIGN THAT PRODUCES THE DEATHS")
structures = [
    ("S1", "POSTS SANCTIONED, NEVER FILLED",
     "75\u201385% specialist shortfall at CHCs, year after year. No ob-gyn + anaesthetist on duty means no C-sections below district level.",
     "Rural Health Statistics (MoHFW)", RED),
    ("S2", "FRUs EXIST ON PAPER ONLY",
     "Hundreds of facilities carry the First Referral Unit tag but can't do C-sections or transfusions. The referral chain has no middle rung.",
     "NHM Common Review Missions", RED),
    ("S3", "STORAGE ALLOWED, SEPARATION DENIED",
     "Lower facilities may only store whole blood. PPH and anaemia need components \u2014 platelets, FFP, packed cells \u2014 not whole blood.",
     "National Blood Policy; NACO", RED),
    ("S4", "PAID FOR THE EVENT, NOT THE OUTCOME",
     "JSY rewards the delivery; JSSK's \u201cfree\u201d package leaks into out-of-pocket payments. Money follows the countable output.",
     "NFHS-5; JSSK evaluations", RED),
    ("S5", "AN AUDIT LOOP THAT NEVER CLOSES",
     "MDSR mandates 24-hour notification and response, but reviews end at form-filling and reporting invites blame. Lessons die in files.",
     "MDSR Operational Guidelines (2017)", RED),
    ("S6", "BUDGET EXISTS, MONEY DOESN'T MOVE",
     "NHM funds stall Centre \u2192 state \u2192 district. Unspent balances and delayed releases while facilities lack basics.",
     "CAG Performance Audit of NHM", RED),
    ("S7", "AMBULANCES ARE TRANSPORT, NOT CARE",
     "108 / Janani Express guarantee a vehicle \u2014 often no paramedic, no oxygen. 13 of Sidhi's 53 died in transit.",
     "108 evaluations (GVK-EMRI)", RED),
    ("S8", "THE ANAEMIA CHAIN BREAKS EARLY",
     "IFA and Hb-testing break between procurement and the woman: 52.9% of MP's pregnant women are anaemic. Survivable bleeds kill.",
     "NFHS-5 MP; Anemia Mukt Bharat", RED),
]
for tag, title, body, src, c in structures:
    card(tag, title, body, src, c)
y += 54
line(M, y, W - M, y, LINE, 2); y += 90

# mental models
section_head("MENTAL MODELS \u2014 4  \u00b7  THE ASSUMPTIONS BAKED INTO THE DESIGN")
models = [
    ("M1", "INSTITUTIONAL DELIVERY = SAFE DELIVERY",
     "The metric counts where women deliver, not what happens there. 89% institutional births; Sidhi MMR 211 vs 87 national.",
     "NFHS-5; SRS Bulletin", PURPLE),
    ("M2", "A NOTICE IS ACCOUNTABILITY",
     "The reflex to failure is paper \u2014 notices, committees, WhatsApp directions \u2014 with no link to postings, budgets, consequences.",
     "Indian Express; NHRC notice 2 Jun 2026", PURPLE),
    ("M3", "LOW-RISK MEANS SAFE",
     "Most PPH/eclampsia deaths had no prior flags. The system staffs for the average delivery, not the emergency.",
     "Thaddeus & Maine (1994)", PURPLE),
    ("M4", "TRIBAL NEGLECT AS BACKGROUND NORMAL",
     "The disciplining feedback loop \u2014 political voice, media, litigation \u2014 is weakest where ST women live. Neglect is the stable equilibrium.",
     "Expert Committee on Tribal Health (2018)", PURPLE),
]
for tag, title, body, src, c in models:
    card(tag, title, body, src, c)
y += 54

# verdict
rect(M, y, CW, 300, "#1a0505", stroke=RED, sw=3)
txt(M + 60, y + 105, "THE VERDICT", 40, RED, fam=MONO, ls=4, wt="700")
for i, ln in enumerate(wrap("The system delivers scale better than outcomes \u2014 89% institutional births, MMR 211 in Sidhi vs 87 national. Intervention happened; the failure continues.", 60)):
    txt(M + 60, y + 175 + i * 56, ln, 40, INK)
y += 300 + 90

# footer
for ln in wrap("Sources named on each card \u00b7 Event anchor: Indian Express investigation, 29 May 2026 \u00b7 MP MMR reads 159 vs 135 across sources \u2014 audit the SRS table before presenting.", 72):
    txt(M, y, ln, 32, MUTED, fam=MONO); y += 50
y += 90

H = int(y)
bg = [f'<rect x="0" y="0" width="{W}" height="{H}" rx="0" fill="{BG}"/>',
      f'<rect x="0" y="0" width="{W}" height="10" rx="0" fill="{RED}"/>']
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
       + "\n".join(bg + o) + "</svg>")
import xml.dom.minidom
xml.dom.minidom.parseString(svg)  # fail fast on malformed XML
with open("sidhi_systemic_layer.svg", "w") as f:
    f.write(svg)
n_text = svg.count("<text")
print("wrote sidhi_systemic_layer.svg %dx%d, %d text nodes" % (W, H, n_text))
