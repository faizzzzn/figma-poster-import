#!/usr/bin/env python3
"""Build the Figma Sites-ready restyle SVG: desktop 1440 + mobile 390 frames.
Real <text> elements (editable in Figma), id-named layers, embedded photos.
Sections are top-level groups so each can be framed (Ctrl+Alt+G) and moved
into Figma Sites section by section: Hero / About / Work / Process /
Capabilities / Contact.
"""
import base64, html as htmllib
from pathlib import Path

W = Path('/tmp/shots_work')

# ---------- tokens ----------
PAPER   = '#c9c8c3'
PAPER2  = '#d7d6d1'
INK     = '#171817'
MUTED   = '#5d5e5a'
LINE    = '#9d9d98'
BLACK   = '#0c0d0c'
WHITE   = '#f1f0eb'
DIM     = '#b5b4ae'
SIGNAL  = '#da5c32'   # light-bg accent
SIGNAL_D= '#ef7146'   # dark-bg accent
SANS = 'Manrope'
MONO = "'IBM Plex Mono'"

def b64(p):
    return base64.b64encode((W/p).read_bytes()).decode()

IMG = {n: b64(f'{n}.jpg') for n in
       ['enav', 'underoot', 'fabrication', 'hearing', 'cap']}

# OFS-01 vector diagram (from the live site), rescaled into place later
OFS = ('<g id="OFS diagram / Vectors" transform="translate(80,90) scale(0.78)">'
       '<path d="M125 75 L475 40 L555 170 L230 212 Z" fill="url(#steel)" stroke="#aeb1b1" stroke-width="2"/>'
       '<path d="M125 75 L230 212 L180 465 L65 356 Z" fill="#292d30" stroke="#85898a" stroke-width="2"/>'
       '<path d="M475 40 L555 170 L520 445 L405 338 Z" fill="#1b1e20" stroke="#85898a" stroke-width="2"/>'
       '<path d="M230 212 L555 170" fill="none" stroke="#ef7146" stroke-width="5"/>'
       '<path d="M180 465 L259 461 L288 426 L212 428 Z" fill="#da5c32"/>'
       '<path d="M520 445 L440 442 L415 409 L489 411 Z" fill="#da5c32"/>'
       '<path d="M152 112 L505 79" fill="none" stroke="#666b6d" stroke-width="2" stroke-dasharray="9 8"/>'
       '</g>')

parts = []
def add(s): parts.append(s)

def esc(t): return htmllib.escape(t, quote=False)

def text(gid, x, y, lines, size, fill, font=SANS, weight=400, ls=None,
         anchor='start', lh=None, style_extra=''):
    """One editable text layer; lines = list of strings (tspans)."""
    lh = lh or round(size * 1.04)
    tsp = ''.join(
        f'<tspan x="{x}" dy="{lh if i else 0}">{esc(l)}</tspan>'
        for i, l in enumerate(lines))
    ls_a = f' letter-spacing="{ls}"' if ls is not None else ''
    add(f'<text id="{gid}" x="{x}" y="{y}" font-family="{font}" font-size="{size}" '
        f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{ls_a}{style_extra}>{tsp}</text>')

def mono_label(gid, x, y, s, fill, size=12, anchor='start', ls='1.5'):
    text(gid, x, y, [s.upper()], size, fill, font=MONO, weight=500, ls=ls, anchor=anchor)

def rect(gid, x, y, w, h, fill, opacity=None, rx=0):
    o = f' opacity="{opacity}"' if opacity is not None else ''
    r = f' rx="{rx}"' if rx else ''
    add(f'<rect id="{gid}" x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"{o}{r}/>')

def image(gid, x, y, w, h, key):
    add(f'<image id="{gid}" x="{x}" y="{y}" width="{w}" height="{h}" '
        f'href="data:image/jpeg;base64,{IMG[key]}" preserveAspectRatio="xMidYMid slice"/>')

def rule(gid, x1, y1, x2, y2, color, w=1):
    add(f'<line id="{gid}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{w}"/>')

def button(gid, x, y, w, h, label, fill_bg, fill_tx, outline=None):
    if outline:
        add(f'<rect id="{gid} / Bg" x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="{outline}" stroke-width="1.5"/>')
    else:
        rect(f'{gid} / Bg', x, y, w, h, fill_bg)
    text(f'{gid} / Label', x + w/2, y + h/2 + 6, [label], 15, fill_tx,
         weight=600, anchor='middle', ls='0.3')

# ============================================================ DESKTOP
add('<defs><linearGradient id="steel" x1="0" y1="0" x2="1" y2="1">'
    '<stop offset="0" stop-color="#53585b"/><stop offset=".42" stop-color="#222629"/>'
    '<stop offset="1" stop-color="#101214"/></linearGradient>'
    '<linearGradient id="heroShade" x1="0" y1="0" x2="1" y2="0">'
    '<stop offset="0" stop-color="#070807" stop-opacity=".78"/>'
    '<stop offset=".55" stop-color="#070807" stop-opacity=".22"/>'
    '<stop offset="1" stop-color="#070807" stop-opacity=".1"/></linearGradient>'
    '<linearGradient id="heroShadeB" x1="0" y1="1" x2="0" y2="0">'
    '<stop offset="0" stop-color="#070807" stop-opacity=".76"/>'
    '<stop offset=".52" stop-color="#070807" stop-opacity="0"/></linearGradient></defs>')

add('<g id="DESKTOP 1440">')
DX = 0  # desktop x offset

# ---------------- HERO ----------------
add('<g id="Section — Hero (Desktop)">')
rect('Hero / Bg', DX, 0, 1440, 900, BLACK)
image('Hero / Photo (swap me)', DX, 0, 1440, 900, 'enav')
rect('Hero / Shade', DX, 0, 1440, 900, 'url(#heroShade)')
rect('Hero / Shade bottom', DX, 0, 1440, 900, 'url(#heroShadeB)')
text('Hero / Topbar left', DX+53, 42, ['Industrial designer · NID Haryana'], 13, WHITE, weight=600)
mono_label('Hero / Nav', DX+1387, 42, 'Work      Process      Contact      Portfolio ↓', WHITE, anchor='end')
rect('Hero / Kicker rule', DX+53, 452, 40, 2, SIGNAL_D)
mono_label('Hero / Kicker', DX+105, 458, 'Research  ·  Form  ·  Fabrication', WHITE)
text('Hero / Heading', DX+48, 640, ['Designing through'], 128, WHITE, weight=500, ls='-7', lh=112)
text('Hero / Heading accent', DX+278, 752, ['making.'], 128, SIGNAL_D, weight=500, ls='-7')
mono_label('Hero / Slide counter', DX+53, 812, '01 / 04', WHITE)
text('Hero / Slide title', DX+53, 852, ['eNav'], 40, WHITE, weight=500, ls='-1')
text('Hero / Slide subtitle', DX+53, 880, ['Motorcycle navigation · Hardware + UI'], 15, DIM)
button('Hero / CTA primary', DX+1050, 818, 150, 48, 'Selected work', SIGNAL_D, WHITE)
button('Hero / CTA secondary', DX+1214, 818, 160, 48, 'ATS résumé ↓', 'none', WHITE, outline=WHITE)
for i in range(4):
    c = SIGNAL_D if i == 2 else '#ffffff55'
    rule(f'Hero / Dot {i+1}', DX+1214+i*34, 892, DX+1214+i*34+24, 892, c, 2)
add('</g>')

# ---------------- ABOUT ----------------
AY = 980
add('<g id="Section — About (Desktop)">')
rect('About / Bg', DX, AY, 1440, 760, PAPER)
mono_label('About / Kicker', DX+53, AY+80, 'About  /  2026', SIGNAL)
text('About / Headline', DX+480, AY+150,
     ['Ideas become useful when', 'they survive material, tools and', 'use.'],
     76, INK, weight=500, ls='-3', lh=80)
text('About / Body', DX+480, AY+420,
     ["I'm a third-year Industrial Design student at NID Haryana,",
      'working across design research, product development and hands-on',
      'fabrication — from origami-fold sheet steel to low-distraction',
      'motorcycle hardware.'], 20, MUTED, lh=30)
rule('About / Rule', DX+480, AY+560, DX+1387, AY+560, LINE)
facts = [('B.Des · Industrial Design', 'NID Haryana, 2023–2027'),
         ('Fabrication-first', 'CAD, prototyping, workshop execution'),
         ('Open to internships', 'Industrial design roles in India')]
for i, (t, s) in enumerate(facts):
    x = DX + 480 + i*305
    if i: rule(f'About / Divider {i}', x-24, AY+590, x-24, AY+660, LINE)
    text(f'About / Fact {i+1} title', x, AY+616, [t], 17, INK, weight=700)
    text(f'About / Fact {i+1} sub', x, AY+642, [s], 15, MUTED)
add('</g>')

# ---------------- WORK ----------------
WY = 1820
add('<g id="Section — Selected work (Desktop)">')
rect('Work / Bg', DX, WY, 1440, 2960, PAPER)
text('Work / Title', DX+48, WY+150, ['Selected work'], 96, INK, weight=500, ls='-4')
text('Work / Intro', DX+1010, WY+92,
     ['Six projects spanning furniture, mobility,', 'assistive products, public systems,', 'physical making and procedural form.'],
     17, MUTED, lh=26)
rule('Work / Rule', DX+53, WY+190, DX+1387, WY+190, LINE)

projects = [
    ('OFS-01', 'Origami-Fold Steel Stool', '01 / Furniture', 'ofs',
     'Assembly', 'Press-brake folds and tab-and-slot press-fit joints replace welding and loose fasteners.',
     'Intent', 'Material, bend sequence and joining logic define the final form.'),
    ('eNav', 'Motorcycle Navigation', '02 / Mobility', 'enav',
     'Interaction', 'Glanceable directions without turning the ride into another screen session.',
     'Engineering', 'Legibility, power budget, BLE link and mount safety resolved in Datasheet Rev A.'),
    ('Hearing Aid', 'Dehumidifier', '03 / Assistive', 'hearing',
     'Direction', 'RF dielectric heating paired with desiccant regeneration.',
     'Opportunity', 'Designed to extend device life and simplify everyday care.'),
    ('Underoot', 'Public Furniture', '04 / Public realm', 'underoot',
     'System', 'A repeatable modular family rather than one isolated object.',
     'Longevity', 'Durability, repair and all-season use shape the construction logic.'),
    ('Fabrication', 'Studies', '05 / Making', 'fabrication',
     'Life-scale model', 'Proportion, ergonomics and manual shaping studied at full scale.',
     'Wearable study', 'Surface language and handcrafted construction through the Silver Gauntlet.'),
    ('Astroworld Cap', 'Procedural Build', '06 / 3D form', 'cap',
     'Model', 'Crown panels, curved brim, seams, eyelets, back strap and embroidered patch.',
     'Method', 'Scripted Blender construction with clean GLB, OBJ and STL outputs.'),
]
CW, CH, GAP = 655, 480, 24
for i, (t1, t2, tag, imgkey, l1, d1, l2, d2) in enumerate(projects):
    r, c = divmod(i, 2)
    x = DX + 53 + c*(CW+GAP)
    y = WY + 240 + r*760
    gid = f'Work / Card {i+1} {t1}'
    rect(f'{gid} / Photo bg', x, y, CW, CH, PAPER2)
    if imgkey == 'ofs':
        add(f'<g id="{gid} / Photo (vector diagram)">')
        rect(f'{gid} / diagram bg', x, y, CW, CH, '#171918')
        ofs_inner = OFS.split('>', 1)[1]
        add('<g transform="translate(' + str(x+60) + ',' + str(y+30) + ') scale(0.72)">' + ofs_inner)
        mono_label(f'{gid} / Note A', x+26, y+30, 'Single-sheet logic', '#aaa69e', size=10)
        mono_label(f'{gid} / Note B', x+CW-26, y+CH-22, 'Fold → Lock → Load', SIGNAL_D, size=10, anchor='end')
        add('</g>')
    else:
        image(f'{gid} / Photo (swap me)', x, y, CW, CH, imgkey)
    text(f'{gid} / Title', x, y+CH+52, [t1, t2], 38, INK, weight=500, ls='-1.5', lh=40)
    mono_label(f'{gid} / Tag', x+CW, y+CH+34, tag, SIGNAL, anchor='end')
    for j, (lab, desc) in enumerate([(l1, d1), (l2, d2)]):
        cx = x + j*335
        mono_label(f'{gid} / Label {j+1}', cx, y+CH+150, lab, INK, size=11)
        # wrap desc to ~38 chars
        words, lines, cur = desc.split(), [], ''
        for wd in words:
            if len(cur)+len(wd)+1 > 38: lines.append(cur); cur = wd
            else: cur = (cur+' '+wd).strip()
        lines.append(cur)
        text(f'{gid} / Desc {j+1}', cx, y+CH+172, lines, 15, MUTED, lh=22)
add('</g>')

# ---------------- PROCESS ----------------
PY = 4860
add('<g id="Section — Process (Desktop)">')
rect('Process / Bg', DX, PY, 1440, 900, BLACK)
text('Process / Title', DX+48, PY+170, ['One build loop.', 'Four modes.'], 88, WHITE, weight=500, ls='-4', lh=84)
text('Process / Intro', DX+1010, PY+120,
     ['The method moves from evidence to', 'physical proof. Scroll to follow', 'the sequence.'], 15, DIM, lh=22)
rule('Process / Rule', DX+53, PY+230, DX+1387, PY+230, '#393a38')
modes = [('01 / Frame', 'Research', 'Understand context, behaviour, constraints and the real failure worth solving.'),
         ('02 / Resolve', 'Design', 'Translate evidence into architecture, interaction and form.'),
         ('03 / Test', 'Prototype', 'Use models and mock-ups to expose weak assumptions early.'),
         ('04 / Make', 'Fabricate', 'Carry the design through materials, tooling and assembly logic.')]
for i, (tag, name, desc) in enumerate(modes):
    x = DX + 53 + i*345
    if i: rule(f'Process / Divider {i}', x-28, PY+300, x-28, PY+700, '#393a38')
    mono_label(f'Process / Mode {i+1} tag', x, PY+330, tag, SIGNAL_D)
    text(f'Process / Mode {i+1} name', x, PY+470, [name], 64, WHITE, weight=500, ls='-2')
    words, lines, cur = desc.split(), [], ''
    for wd in words:
        if len(cur)+len(wd)+1 > 34: lines.append(cur); cur = wd
        else: cur = (cur+' '+wd).strip()
    lines.append(cur)
    text(f'Process / Mode {i+1} desc', x, PY+560, lines, 15, DIM, lh=23)
rule('Process / Progress track', DX+53, PY+800, DX+1387, PY+800, '#393a38', 3)
rule('Process / Progress fill', DX+53, PY+800, DX+560, PY+800, SIGNAL_D, 3)
add('</g>')

# ---------------- CAPABILITIES ----------------
CY = 5840
add('<g id="Section — Capabilities (Desktop)">')
rect('Capabilities / Bg', DX, CY, 1440, 640, PAPER)
mono_label('Capabilities / Kicker', DX+53, CY+80, 'Capability', SIGNAL)
text('Capabilities / Title', DX+48, CY+150, ['Across the', 'whole build', 'loop.'], 72, INK, weight=500, ls='-3', lh=74)
caps = [('Design + Visualisation', 'Figma · Photoshop · Illustrator · InDesign · Procreate · KeyShot'),
        ('CAD + Engineering', 'SolidWorks · Rhino · Blender · Arduino IDE · Design for manufacture'),
        ('Fabrication', 'Sheet-metal folding · Welding · Woodworking · Wire forming · Manual model-making'),
        ('Systems + Interface', 'Android Studio · Unity · Interface prototyping · Research synthesis · Technical documentation')]
for i, (lab, items) in enumerate(caps):
    r, c = divmod(i, 2)
    x = DX + 480 + c*460
    y = CY + 80 + r*240
    if c == 0: rule(f'Capabilities / Row rule {r}', DX+480, y-24, DX+1387, y-24, LINE)
    else: rule(f'Capabilities / Col divider {r}', x-24, y-24, x-24, y+180, LINE)
    mono_label(f'Capabilities / Label {i+1}', x, y+6, lab, SIGNAL)
    words, lines, cur = items.split(' · '), [], ''
    for wd in words:
        if len((cur+' · '+wd).strip(' ·')) > 40: lines.append(cur); cur = wd
        else: cur = (cur+' · '+wd).strip(' ·')
    lines.append(cur)
    text(f'Capabilities / Items {i+1}', x, y+40, lines, 17, MUTED, lh=26)
rule('Capabilities / Bottom rule', DX+480, CY+560, DX+1387, CY+560, LINE)
add('</g>')

# ---------------- CONTACT ----------------
TY = 6560
add('<g id="Section — Contact + Footer (Desktop)">')
rect('Contact / Bg', DX, TY, 1440, 860, PAPER)
mono_label('Contact / Kicker', DX+53, TY+80, 'Contact', SIGNAL)
text('Contact / Headline', DX+48, TY+170,
     ["Let's make the idea", 'hold up in the real', 'world.'], 96, INK, weight=500, ls='-4', lh=94)
text('Contact / Body', DX+53, TY+500,
     ['Currently seeking industrial design internships where concept development,',
      'CAD, prototyping and fabrication belong to one process.'], 18, MUTED, lh=28)
button('Contact / Email btn', DX+53, TY+590, 140, 52, 'Email Faizan', SIGNAL, WHITE)
button('Contact / PDF btn', DX+207, TY+590, 170, 52, 'Portfolio PDF ↓', 'none', INK, outline=INK)
links = [('Email', 'faizanhaidri786@gmail.com'), ('Behance', 'behance.net/faizanhaidri ↗'),
         ('LinkedIn', 'linkedin.com/in/faizan-haidri ↗'), ('ATS résumé', 'PDF download ↓')]
for i, (lab, val) in enumerate(links):
    y = TY+120 + i*72
    rule(f'Contact / Link rule {i+1}', DX+950, y-34, DX+1387, y-34, LINE)
    text(f'Contact / Link {i+1} label', DX+950, y, [lab], 17, INK, weight=700)
    text(f'Contact / Link {i+1} value', DX+1387, y, [val], 16, MUTED, anchor='end')
rule('Footer / Rule', DX+53, TY+800, DX+1387, TY+800, LINE)
mono_label('Footer / Left', DX+53, TY+828, 'Industrial Design · NID Haryana', MUTED, size=11)
mono_label('Footer / Right', DX+1387, TY+828, 'Selected work · 2026', MUTED, size=11, anchor='end')
add('</g>')
add('</g>')  # end DESKTOP

# ============================================================ MOBILE
add('<g id="MOBILE 390">')
MX = 1600
def ph(gid, x, y, w, h, label='Photo — swap in Figma Sites', ly=0.5):
    rect(f'{gid} / Placeholder', x, y, w, h, '#a9a8a3')
    mono_label(f'{gid} / Placeholder label', x+w/2, y+h*ly, label, '#5d5e5a', size=10, anchor='middle')

def wrap(desc, n):
    words, lines, cur = desc.split(), [], ''
    for wd in words:
        if len(cur)+len(wd)+1 > n: lines.append(cur); cur = wd
        else: cur = (cur+' '+wd).strip()
    lines.append(cur)
    return lines

# ---- M HERO ----
add('<g id="Section — Hero (Mobile)">')
rect('M Hero / Bg', MX, 0, 390, 800, BLACK)
ph('M Hero / Photo', MX, 0, 390, 800, ly=0.25)
rect('M Hero / Shade', MX, 0, 390, 800, 'url(#heroShadeB)')
mono_label('M Hero / Topbar left', MX+20, 32, 'Industrial designer · NID Haryana', WHITE, size=10)
mono_label('M Hero / Topbar right', MX+370, 32, 'Portfolio ↓', WHITE, size=10, anchor='end')
rect('M Hero / Kicker rule', MX+20, 396, 28, 2, SIGNAL_D)
mono_label('M Hero / Kicker', MX+56, 402, 'Research · Form · Fabrication', WHITE, size=10)
text('M Hero / Heading', MX+18, 486, ['Designing', 'through'], 70, WHITE, weight=500, ls='-4', lh=68)
text('M Hero / Heading accent', MX+18, 622, ['making.'], 70, SIGNAL_D, weight=500, ls='-4')
mono_label('M Hero / Slide counter', MX+20, 668, '01 / 04', WHITE, size=10)
text('M Hero / Slide title', MX+20, 700, ['eNav'], 30, WHITE, weight=500, ls='-1')
text('M Hero / Slide subtitle', MX+20, 724, ['Motorcycle navigation · Hardware + UI'], 13, DIM)
button('M Hero / CTA primary', MX+20, 744, 140, 44, 'Selected work', SIGNAL_D, WHITE)
button('M Hero / CTA secondary', MX+168, 744, 150, 44, 'ATS résumé ↓', 'none', WHITE, outline=WHITE)
for i in range(4):
    c = SIGNAL_D if i == 0 else '#ffffff55'
    rule(f'M Hero / Dot {i+1}', MX+300+i*16, 768, MX+310+i*16, 768, c, 2)
add('</g>')

# ---- M ABOUT ----
MY = 880
add('<g id="Section — About (Mobile)">')
rect('M About / Bg', MX, MY, 390, 800, PAPER)
mono_label('M About / Kicker', MX+20, MY+52, 'About / 2026', SIGNAL, size=10)
text('M About / Headline', MX+18, MY+112,
     ['Ideas become useful', 'when they survive', 'material, tools and use.'], 44, INK, weight=500, ls='-2', lh=46)
text('M About / Body', MX+20, MY+300,
     wrap("I'm a third-year Industrial Design student at NID Haryana, working across design research, product development and hands-on fabrication.", 44),
     16, MUTED, lh=24)
for i, (t, su) in enumerate(facts):
    y = MY + 470 + i*100
    rule(f'M About / Rule {i}', MX+20, y-26, MX+370, y-26, LINE)
    text(f'M About / Fact {i+1}', MX+20, y, [t], 16, INK, weight=700)
    text(f'M About / Fact sub {i+1}', MX+20, y+26, [su], 14, MUTED)
add('</g>')

# ---- M WORK ----
WY2 = 1760
add('<g id="Section — Selected work (Mobile)">')
rect('M Work / Bg', MX, WY2, 390, 3900, PAPER)
text('M Work / Title', MX+18, WY2+84, ['Selected work'], 48, INK, weight=500, ls='-2')
text('M Work / Intro', MX+20, WY2+126,
     wrap('Six projects spanning furniture, mobility, assistive products, public systems, physical making and procedural form.', 46),
     14, MUTED, lh=20)
for i, (t1, t2, tag, imgkey, l1, d1, l2, d2) in enumerate(projects):
    y = WY2 + 220 + i*600
    gid = f'M Work / Card {i+1} {t1}'
    ph(gid, MX+20, y, 350, 250)
    text(f'{gid} / Title', MX+20, y+296, [t1, t2], 30, INK, weight=500, ls='-1', lh=32)
    mono_label(f'{gid} / Tag', MX+370, y+282, tag, SIGNAL, size=10, anchor='end')
    yy = y + 372
    for j, (lab, desc) in enumerate([(l1, d1), (l2, d2)]):
        mono_label(f'{gid} / Label {j+1}', MX+20, yy, lab, INK, size=10)
        text(f'{gid} / Desc {j+1}', MX+20, yy+22, wrap(desc, 46), 14, MUTED, lh=20)
        yy += 22 + 20*len(wrap(desc, 46)) + 26
add('</g>')

# ---- M PROCESS ----
PY2 = 5740
add('<g id="Section — Process (Mobile)">')
rect('M Process / Bg', MX, PY2, 390, 1420, BLACK)
text('M Process / Title', MX+18, PY2+92, ['One build loop.', 'Four modes.'], 40, WHITE, weight=500, ls='-2', lh=42)
text('M Process / Intro', MX+20, PY2+170,
     wrap('The method moves from evidence to physical proof. Scroll to follow the sequence.', 44),
     14, DIM, lh=20)
for i, (tag, name, desc) in enumerate(modes):
    y = PY2 + 300 + i*250
    rule(f'M Process / Rule {i}', MX+20, y-34, MX+370, y-34, '#393a38')
    mono_label(f'M Process / Mode {i+1} tag', MX+20, y, tag, SIGNAL_D, size=10)
    text(f'M Process / Mode {i+1} name', MX+20, y+66, [name], 54, WHITE, weight=500, ls='-2')
    text(f'M Process / Mode {i+1} desc', MX+20, y+102, wrap(desc, 44), 14, DIM, lh=20)
add('</g>')

# ---- M CONTACT ----
TY2 = 7240
add('<g id="Section — Contact + Footer (Mobile)">')
rect('M Contact / Bg', MX, TY2, 390, 1060, PAPER)
mono_label('M Contact / Kicker', MX+20, TY2+52, 'Contact', SIGNAL, size=10)
text('M Contact / Headline', MX+18, TY2+112,
     ["Let's make the idea", 'hold up in', 'the real world.'], 54, INK, weight=500, ls='-2.5', lh=56)
text('M Contact / Body', MX+20, TY2+330,
     wrap('Currently seeking industrial design internships where concept development, CAD, prototyping and fabrication belong to one process.', 44),
     15, MUTED, lh=22)
button('M Contact / Email btn', MX+20, TY2+450, 140, 48, 'Email Faizan', SIGNAL, WHITE)
button('M Contact / PDF btn', MX+168, TY2+450, 160, 48, 'Portfolio PDF ↓', 'none', INK, outline=INK)
for i, (lab, val) in enumerate(links):
    y = TY2 + 570 + i*78
    rule(f'M Contact / Link rule {i+1}', MX+20, y-24, MX+370, y-24, LINE)
    text(f'M Contact / Link {i+1} label', MX+20, y, [lab], 15, INK, weight=700)
    text(f'M Contact / Link {i+1} value', MX+20, y+24, [val], 14, MUTED)
rule('M Footer / Rule', MX+20, TY2+960, MX+370, TY2+960, LINE)
mono_label('M Footer', MX+20, TY2+986, 'Industrial Design · NID Haryana', MUTED, size=10)
mono_label('M Footer 2', MX+20, TY2+1006, 'Selected work · 2026', MUTED, size=10)
add('</g>')
add('</g>')  # end MOBILE

svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="2090" height="8500" '
       'viewBox="0 0 2090 8500">\n' + '\n'.join(parts) + '\n</svg>')
out = W / 'faizan_site_restyle.svg'
out.write_text(svg, encoding='utf-8')
print('wrote', out, len(svg)//1024, 'KB')
