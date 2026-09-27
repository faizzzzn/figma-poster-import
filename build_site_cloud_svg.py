#!/usr/bin/env python3
"""Build the Figma Sites-ready SVG for the CLOUD redesign of Faizan's site.
Sky-blue glassmorphism, Fraunces + IBM Plex Mono, desktop 1440 + mobile 390
artboards stacked vertically. Real <text> elements (editable in Figma),
id-named layers, base64-embedded real project photos.
Sections are top-level groups so each can be framed (Ctrl+Alt+G) and moved
into Figma Sites section by section: Hero / About / Work / Process / Contact.
The interactive web cloud is represented statically as layered vector blobs.
"""
import base64, html as htmllib
from pathlib import Path

W = Path('/tmp/cloud_figma/work')   # extracted real project JPEGs
OUT = Path('/tmp/cloud_figma/faizan_site_cloud.svg')

# ---------- tokens ----------
SKY_TOP = '#EAF3FA'
SKY_MID = '#A9CCE3'
SKY_LOW = '#7FB2D9'
DEEP    = '#1B3A5C'   # deep sky accent
INK     = '#10283D'   # deep navy ink for text on light
MUTED   = '#41607E'
LINE    = '#1B3A5C'   # lines drawn with opacity
WHITE   = '#FFFFFF'
PAPER   = '#F2F8FD'   # pale panel bg
ACCENT  = '#2E86C1'   # sky-blue accent for mono labels
FRA = 'Fraunces'
MONO = "'IBM Plex Mono'"

def b64(p):
    return base64.b64encode((W / p).read_bytes()).decode()

IMG = {n: b64(f'{n}.jpg') for n in
       ['enav', 'aid', 'underoot', 'fabrication', 'cap']}

parts = []
def add(s): parts.append(s)
def esc(t): return htmllib.escape(t, quote=False)

def text(gid, x, y, lines, size, fill, font=FRA, weight=400, ls=None,
         anchor='start', lh=None, style_extra=''):
    lh = lh or round(size * 1.06)
    tsp = ''.join(
        f'<tspan x="{x}" dy="{lh if i else 0}">{esc(l)}</tspan>'
        for i, l in enumerate(lines))
    ls_a = f' letter-spacing="{ls}"' if ls is not None else ''
    add(f'<text id="{gid}" x="{x}" y="{y}" font-family="{font}" font-size="{size}" '
        f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{ls_a}{style_extra}>{tsp}</text>')

def mono(gid, x, y, s, fill, size=12, anchor='start', ls='1.6', weight=500):
    text(gid, x, y, [s.upper()], size, fill, font=MONO, weight=weight, ls=ls, anchor=anchor)

def rect(gid, x, y, w, h, fill, opacity=None, rx=0, stroke=None, sw=1.5):
    o = f' opacity="{opacity}"' if opacity is not None else ''
    r = f' rx="{rx}"' if rx else ''
    st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ''
    add(f'<rect id="{gid}" x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"{o}{r}{st}/>')

def image(gid, x, y, w, h, key):
    add(f'<image id="{gid}" x="{x}" y="{y}" width="{w}" height="{h}" '
        f'href="data:image/jpeg;base64,{IMG[key]}" preserveAspectRatio="xMidYMid slice"/>')

def rule(gid, x1, y1, x2, y2, color, w=1, opacity=None):
    o = f' opacity="{opacity}"' if opacity is not None else ''
    add(f'<line id="{gid}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{w}"{o}/>')

def ellipse(gid, cx, cy, rx, ry, fill, opacity=None):
    o = f' opacity="{opacity}"' if opacity is not None else ''
    add(f'<ellipse id="{gid}" cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{fill}"{o}/>')

def glass_panel(gid, x, y, w, h, rx=24, op=0.55):
    """Translucent white glass panel; Faizan adds Figma blur."""
    rect(f'{gid} / Glass', x, y, w, h, WHITE, opacity=op, rx=rx,
         stroke=WHITE, sw=1.5)

def glass_pill(gid, x, y, w, h, label, tx_fill=INK, size=13):
    rect(f'{gid} / Bg', x, y, w, h, WHITE, opacity=0.6, rx=h/2, stroke=WHITE, sw=1.5)
    text(f'{gid} / Label', x + w/2, y + h/2 + 5, [label.upper()], size, tx_fill,
         font=MONO, weight=500, anchor='middle', ls='1.2')

def cloud(gid, cx, cy, s=1.0, op=1.0):
    """Static stylized cloud: layered soft ellipses."""
    blobs = [(0, 0, 190, 74), (-150, 22, 130, 56), (150, 24, 140, 58),
             (-70, -42, 120, 52), (80, -44, 130, 54), (-230, 40, 90, 40),
             (230, 42, 95, 42), (0, -70, 100, 40)]
    add(f'<g id="{gid}" opacity="{op}">')
    for i, (dx, dy, rx, ry) in enumerate(blobs):
        ellipse(f'{gid} / Puff {i+1}', cx + dx*s, cy + dy*s, rx*s, ry*s,
                WHITE, opacity=0.85)
    for i, (dx, dy, rx, ry) in enumerate([(-110, 55, 120, 40), (120, 58, 130, 42), (0, 70, 150, 44)]):
        ellipse(f'{gid} / Shade {i+1}', cx + dx*s, cy + dy*s, rx*s, ry*s,
                '#CFE4F2', opacity=0.7)
    add('</g>')

def wrap(desc, n):
    words, lines, cur = desc.split(), [], ''
    for wd in words:
        if len(cur) + len(wd) + 1 > n:
            lines.append(cur); cur = wd
        else:
            cur = (cur + ' ' + wd).strip()
    lines.append(cur)
    return lines

# ============ defs ============
add('<defs>'
    '<linearGradient id="skyHero" x1="0" y1="0" x2="0" y2="1">'
    f'<stop offset="0" stop-color="{SKY_TOP}"/><stop offset=".55" stop-color="{SKY_MID}"/>'
    f'<stop offset="1" stop-color="{SKY_LOW}"/></linearGradient>'
    '<linearGradient id="skyDeep" x1="0" y1="0" x2="0" y2="1">'
    f'<stop offset="0" stop-color="#2A5A8A"/><stop offset="1" stop-color="{DEEP}"/></linearGradient>'
    '<linearGradient id="skySoft" x1="0" y1="0" x2="0" y2="1">'
    f'<stop offset="0" stop-color="{PAPER}"/><stop offset="1" stop-color="#DCEBF6"/></linearGradient>'
    '</defs>')

# ============================================================ DESKTOP
add('<g id="DESKTOP 1440">')
DX = 0

# ---------------- HERO ----------------
add('<g id="Section — Hero (Desktop)">')
rect('Hero / Sky', DX, 0, 1440, 900, 'url(#skyHero)')
cloud('Hero / Cloud back', DX+360, 300, 1.15, 0.75)
cloud('Hero / Cloud front', DX+1060, 560, 1.5, 0.95)
cloud('Hero / Cloud small', DX+1200, 180, 0.7, 0.6)
mono('Hero / Eyebrow', DX+72, 120, 'Industrial designer — NID Haryana', INK, size=13)
text('Hero / Headline', DX+64, 330, ['Faizan', 'Haidri'], 168, INK, weight=600, ls='-8', lh=150)
text('Hero / Subline', DX+72, 420, ['I prototype what I design.'], 30, INK,
     weight=400, style_extra=' font-style="italic"')
glass_panel('Hero / Nav pill', DX+72, 500, 560, 64, rx=32, op=0.55)
nav_items = ['About', 'Work', 'Process', 'Contact']
for i, n in enumerate(nav_items):
    mono(f'Hero / Nav {n}', DX+120+i*130, 539, n, INK, size=13)
text('Hero / Reveal hint', DX+72, 640,
     ['Move your cursor — the cloud parts', 'to reveal the work beneath.'], 17, MUTED, lh=26)
mono('Hero / Scroll cue', DX+72, 830, 'Move to reveal — scroll ↓', INK, size=12)
mono('Hero / Meta right', DX+1368, 830, 'Portfolio · 2026', INK, size=12, anchor='end')
add('</g>')

# ---------------- ABOUT ----------------
AY = 980
add('<g id="Section — About (Desktop)">')
rect('About / Bg', DX, AY, 1440, 1060, 'url(#skySoft)')
cloud('About / Cloud deco', DX+1180, AY+180, 0.8, 0.5)
mono('About / Kicker', DX+72, AY+110, 'About / 2026', ACCENT)
text('About / Heading', DX+64, AY+220, ['About'], 120, INK, weight=600, ls='-5')
text('About / Body', DX+72, AY+330,
     ['4th-year B.Des Industrial Design student at the National',
      'Institute of Design Haryana, graduating 2027. I work from',
      'close observation to clear, functional outcomes — taking',
      'complex ideas apart and refining them into minimal,',
      'form-driven solutions.'], 21, MUTED, lh=32)
text('About / Pull quote', DX+72, AY+600,
     ['“Curiosity keeps me driven —', 'driven by observation.”'], 44, INK,
     weight=500, lh=52, style_extra=' font-style="italic"')
# two-column lists
glass_panel('About / Software card', DX+72, AY+740, 620, 220, rx=24, op=0.6)
mono('About / Software title', DX+112, AY+792, 'Software expertise', ACCENT)
for i, s in enumerate(['Rhino', 'Figma', 'Android Studio', 'Illustrator', 'Photoshop']):
    text(f'About / Software {i+1}', DX+112, AY+832+i*30, [s], 19, INK, weight=500)
glass_panel('About / Craft card', DX+740, AY+740, 620, 220, rx=24, op=0.6)
mono('About / Craft title', DX+780, AY+792, 'Craft & skills', ACCENT)
for i, s in enumerate(['Leather craft', 'Wood working', 'Ergonomics', 'Form studies', 'Rapid prototyping']):
    text(f'About / Craft {i+1}', DX+780, AY+832+i*30, [s], 19, INK, weight=500)
# links row
links = [('Behance', 'behance.net/faizanhaidri'),
         ('LinkedIn', 'linkedin.com/in/faizan-haidri'),
         ('Email', 'faizanhaidri786@gmail.com')]
for i, (lab, val) in enumerate(links):
    x = DX + 72 + i*420
    rule(f'About / Link rule {i+1}', x, AY+1000, x+380, AY+1000, LINE, 1, opacity=0.3)
    mono(f'About / Link {i+1} label', x, AY+990, lab, ACCENT, size=11)
    text(f'About / Link {i+1} value', x, AY+1024, [val], 16, INK, weight=500)
add('</g>')

# ---------------- WORK ----------------
WY = 2120
add('<g id="Section — Work (Desktop)">')
rect('Work / Bg', DX, WY, 1440, 2400, PAPER)
mono('Work / Kicker', DX+72, WY+100, 'Selected work', ACCENT)
text('Work / Heading', DX+64, WY+210, ['Work'], 120, INK, weight=600, ls='-5')
text('Work / Intro', DX+900, WY+130,
     ['Five builds across mobility, assistive products,', 'public systems and physical making — every one', 'prototyped by hand.'], 17, MUTED, lh=26)

projects = [
    ('01', 'eNav', 'enav', 'Motorcycle navigation display',
     'Hardware + UI for glanceable directions on the move.'),
    ('02', 'Hearing Aid Dehumidifier', 'aid', 'Assistive product',
     'RF dielectric heating paired with desiccant regeneration.'),
    ('03', 'Underoot', 'underoot', 'Public furniture',
     'A repeatable modular family for the public realm.'),
    ('04', 'Fabrication Studies', 'fabrication', 'Making',
     'Silver Gauntlet wearable and life-scale models in metal, wood, wire.'),
    ('05', 'Astroworld Cap', 'cap', 'Procedural 3D form',
     'Scripted Blender build — clean GLB, OBJ and STL outputs.'),
]
CW, CH, GAP = 640, 420, 40
for i, (num, title, imgkey, tag, desc) in enumerate(projects):
    r, c = divmod(i, 2)
    x = DX + 72 + c*(CW+GAP)
    y = WY + 280 + r*620
    gid = f'Work / Card {num} {title}'
    glass_panel(f'{gid} / Frame', x, y, CW, CH+150, rx=28, op=0.45)
    add(f'<g id="{gid} / Photo clip"><clipPath id="clip{i}"><rect x="{x+16}" y="{y+16}" width="{CW-32}" height="{CH}" rx="18"/></clipPath>')
    add(f'<image id="{gid} / Photo (swap me)" x="{x+16}" y="{y+16}" width="{CW-32}" height="{CH}" '
        f'href="data:image/jpeg;base64,{IMG[imgkey]}" preserveAspectRatio="xMidYMid slice" clip-path="url(#clip{i})"/>')
    add('</g>')
    mono(f'{gid} / Index', x+32, y+CH+62, num, ACCENT, size=12)
    text(f'{gid} / Title', x+32, y+CH+100, [title], 34, INK, weight=600, ls='-1')
    mono(f'{gid} / Tag', x+CW-32, y+CH+62, tag, MUTED, size=11, anchor='end')
    text(f'{gid} / Desc', x+32, y+CH+132, wrap(desc, 52), 15, MUTED, lh=22)
# note panel (fills 6th grid slot)
nx, ny = DX + 72 + 1*(CW+GAP), WY + 280 + 2*620
glass_panel('Work / More panel', nx, ny, CW, CH+150, rx=28, op=0.6)
text('Work / More heading', nx+40, ny+120, ['Full case studies live in', 'the 71-page portfolio deck.'], 30, INK, weight=500, lh=38)
mono('Work / More meta', nx+40, ny+CH+60, 'Process photos · drawings · datasheets', MUTED, size=11)
add('</g>')

# ---------------- PROCESS ----------------
PY = 4600
add('<g id="Section — Process (Desktop)">')
rect('Process / Bg', DX, PY, 1440, 1080, 'url(#skyDeep)')
cloud('Process / Cloud deco', DX+300, PY+900, 1.2, 0.35)
mono('Process / Kicker', DX+72, PY+110, 'How I work', WHITE, size=13)
text('Process / Heading', DX+64, PY+220, ['One build loop.', 'Five stages.'], 96, WHITE, weight=600, ls='-4', lh=92)
stages = [
    ('01', 'Research-backed', 'Every build starts with evidence — context, behaviour, constraints.'),
    ('02', 'Ask how & why', 'Interrogate the problem until the real failure shows itself.'),
    ('03', 'Prototype', 'Models and mock-ups expose weak assumptions early.'),
    ('04', 'Analysis', 'Test, measure, refine — let the material answer back.'),
    ('05', 'Final work', 'Resolved form, engineered to hold up in the real world.'),
]
for i, (num, name, desc) in enumerate(stages):
    x = DX + 72 + i*272
    if i:
        rule(f'Process / Divider {i}', x-24, PY+330, x-24, PY+640, WHITE, 1, opacity=0.25)
    mono(f'Process / Stage {num} num', x, PY+360, num, '#9CC3E5', size=13)
    text(f'Process / Stage {num} name', x, PY+420, [name], 30, WHITE, weight=600, ls='-1')
    text(f'Process / Stage {num} desc', x, PY+470, wrap(desc, 26), 15, '#CFE0F0', lh=23)
rule('Process / Strip rule', DX+72, PY+760, DX+1368, PY+760, WHITE, 1, opacity=0.25)
mono('Process / Strip label', DX+72, PY+750, 'Hands-on by nature', '#9CC3E5', size=11)
text('Process / Strip', DX+72, PY+820,
     ['crafty · meticulous · knack for fixing broken things · systems thinking ·',
      'UI/UX · Android Studio · research · rapid prototyping'], 20, WHITE, lh=30)
add('</g>')

# ---------------- CONTACT ----------------
CY = 5760
add('<g id="Section — Contact (Desktop)">')
rect('Contact / Sky', DX, CY, 1440, 900, 'url(#skyHero)')
cloud('Contact / Cloud back', DX+1100, CY+220, 1.3, 0.8)
cloud('Contact / Cloud front', DX+350, CY+680, 1.1, 0.9)
mono('Contact / Kicker', DX+72, CY+130, 'Contact', ACCENT)
text('Contact / Headline', DX+64, CY+330,
     ["Let's build", "what's next."], 150, INK, weight=600, ls='-7', lh=140)
text('Contact / Sub', DX+72, CY+470,
     ['Industrial design internships — where concept, CAD,', 'prototyping and fabrication belong to one process.'],
     19, MUTED, lh=29)
glass_pill('Contact / Email CTA', DX+72, CY+560, 400, 68, 'faizanhaidri786@gmail.com', INK, size=14)
mono('Contact / Footer Behance', DX+72, CY+800, 'Behance — behance.net/faizanhaidri', INK, size=11)
mono('Contact / Footer LinkedIn', DX+560, CY+800, 'LinkedIn — linkedin.com/in/faizan-haidri', INK, size=11)
mono('Contact / Footer meta', DX+1368, CY+800, 'Faizan Haidri · 2026', INK, size=11, anchor='end')
add('</g>')
add('</g>')  # end DESKTOP

# ============================================================ MOBILE
add('<g id="MOBILE 390">')
MX = 1600

def ph(gid, x, y, w, h, label='Photo — swap in Figma Sites'):
    rect(f'{gid} / Placeholder', x, y, w, h, '#B9CFE2', rx=18)
    mono(f'{gid} / Placeholder label', x+w/2, y+h/2, label, MUTED, size=9, anchor='middle', ls='1')

# ---- M HERO ----
add('<g id="Section — Hero (Mobile)">')
rect('M Hero / Sky', MX, 0, 390, 780, 'url(#skyHero)')
cloud('M Hero / Cloud', MX+195, 330, 0.62, 0.9)
mono('M Hero / Eyebrow', MX+24, 96, 'Industrial designer — NID Haryana', INK, size=10)
text('M Hero / Headline', MX+20, 250, ['Faizan', 'Haidri'], 84, INK, weight=600, ls='-4', lh=78)
text('M Hero / Subline', MX+24, 340, ['I prototype what I design.'], 17, INK,
     style_extra=' font-style="italic"')
glass_panel('M Hero / Nav pill', MX+24, 420, 342, 56, rx=28, op=0.55)
for i, n in enumerate(['About', 'Work', 'Process', 'Contact']):
    mono(f'M Hero / Nav {n}', MX+52+i*82, 455, n, INK, size=10)
text('M Hero / Reveal hint', MX+24, 540,
     ['Move your finger — the cloud parts', 'to reveal the work beneath.'], 14, MUTED, lh=21)
mono('M Hero / Scroll cue', MX+24, 730, 'Swipe to reveal — scroll ↓', INK, size=10)
add('</g>')

# ---- M ABOUT ----
MY = 860
add('<g id="Section — About (Mobile)">')
rect('M About / Bg', MX, MY, 390, 1150, 'url(#skySoft)')
mono('M About / Kicker', MX+24, MY+70, 'About / 2026', ACCENT, size=10)
text('M About / Heading', MX+20, MY+140, ['About'], 64, INK, weight=600, ls='-3')
text('M About / Body', MX+24, MY+210,
     wrap('4th-year B.Des Industrial Design student at the National Institute of Design Haryana, graduating 2027. I work from close observation to clear, functional outcomes.', 42),
     16, MUTED, lh=24)
text('M About / Pull quote', MX+24, MY+430,
     ['“Curiosity keeps me driven —', 'driven by observation.”'], 28, INK,
     weight=500, lh=36, style_extra=' font-style="italic"')
glass_panel('M About / Software card', MX+24, MY+580, 342, 210, rx=20, op=0.6)
mono('M About / Software title', MX+48, MY+622, 'Software expertise', ACCENT, size=10)
for i, s in enumerate(['Rhino', 'Figma', 'Android Studio', 'Illustrator', 'Photoshop']):
    text(f'M About / Software {i+1}', MX+48, MY+654+i*28, [s], 16, INK, weight=500)
glass_panel('M About / Craft card', MX+24, MY+810, 342, 210, rx=20, op=0.6)
mono('M About / Craft title', MX+48, MY+852, 'Craft & skills', ACCENT, size=10)
for i, s in enumerate(['Leather craft', 'Wood working', 'Ergonomics', 'Form studies', 'Rapid prototyping']):
    text(f'M About / Craft {i+1}', MX+48, MY+884+i*28, [s], 16, INK, weight=500)
mono('M About / Links label', MX+24, MY+1060, 'Find me', ACCENT, size=10)
text('M About / Links', MX+24, MY+1090,
     ['behance.net/faizanhaidri', 'linkedin.com/in/faizan-haidri', 'faizanhaidri786@gmail.com'],
     14, INK, weight=500, lh=24)
add('</g>')

# ---- M WORK ----
WY2 = 2090
add('<g id="Section — Work (Mobile)">')
rect('M Work / Bg', MX, WY2, 390, 3050, PAPER)
mono('M Work / Kicker', MX+24, WY2+64, 'Selected work', ACCENT, size=10)
text('M Work / Heading', MX+20, WY2+130, ['Work'], 64, INK, weight=600, ls='-3')
y = WY2 + 190
for i, (num, title, imgkey, tag, desc) in enumerate(projects):
    gid = f'M Work / Card {num} {title}'
    ph(gid, MX+24, y, 342, 220)
    mono(f'{gid} / Index', MX+24, y+262, num, ACCENT, size=10)
    text(f'{gid} / Title', MX+24, y+292, [title], 28, INK, weight=600, ls='-1')
    mono(f'{gid} / Tag', MX+24, y+322, tag, MUTED, size=10)
    text(f'{gid} / Desc', MX+24, y+350, wrap(desc, 44), 14, MUTED, lh=20)
    y += 350 + 20*len(wrap(desc, 44)) + 90
glass_panel('M Work / More panel', MX+24, y, 342, 180, rx=20, op=0.6)
text('M Work / More heading', MX+48, y+80,
     ['Full case studies in the', '71-page portfolio deck.'], 22, INK, weight=500, lh=28)
add('</g>')

# ---- M PROCESS ----
PY2 = WY2 + 3050 + 80
add('<g id="Section — Process (Mobile)">')
rect('M Process / Bg', MX, PY2, 390, 1420, 'url(#skyDeep)')
mono('M Process / Kicker', MX+24, PY2+64, 'How I work', WHITE, size=10)
text('M Process / Heading', MX+20, PY2+130, ['One build loop.', 'Five stages.'], 44, WHITE, weight=600, ls='-2', lh=46)
yy = PY2 + 280
for i, (num, name, desc) in enumerate(stages):
    rule(f'M Process / Rule {i}', MX+24, yy-30, MX+366, yy-30, WHITE, 1, opacity=0.25)
    mono(f'M Process / Stage {num} num', MX+24, yy, num, '#9CC3E5', size=10)
    text(f'M Process / Stage {num} name', MX+24, yy+44, [name], 30, WHITE, weight=600, ls='-1')
    text(f'M Process / Stage {num} desc', MX+24, yy+84, wrap(desc, 42), 14, '#CFE0F0', lh=21)
    yy += 84 + 21*len(wrap(desc, 42)) + 70
text('M Process / Strip', MX+24, yy+10,
     wrap('crafty · meticulous · knack for fixing broken things · systems thinking · UI/UX · Android Studio · research · rapid prototyping', 40),
     15, WHITE, lh=24)
add('</g>')

# ---- M CONTACT ----
CY2 = PY2 + 1420 + 80
add('<g id="Section — Contact (Mobile)">')
rect('M Contact / Sky', MX, CY2, 390, 760, 'url(#skyHero)')
cloud('M Contact / Cloud', MX+195, CY2+560, 0.62, 0.85)
mono('M Contact / Kicker', MX+24, CY2+64, 'Contact', ACCENT, size=10)
text('M Contact / Headline', MX+20, CY2+200,
     ["Let's build", "what's next."], 68, INK, weight=600, ls='-3', lh=64)
glass_pill('M Contact / Email CTA', MX+24, CY2+330, 330, 60, 'faizanhaidri786@gmail.com', INK, size=12)
text('M Contact / Links', MX+24, CY2+450,
     ['behance.net/faizanhaidri', 'linkedin.com/in/faizan-haidri'], 14, INK, weight=500, lh=26)
mono('M Contact / Meta', MX+24, CY2+700, 'Faizan Haidri · 2026', INK, size=10)
add('</g>')
add('</g>')  # end MOBILE

TOTAL_H = CY2 + 760 + 40
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="2090" height="{TOTAL_H}" '
       f'viewBox="0 0 2090 {TOTAL_H}">\n' + '\n'.join(parts) + '\n</svg>')
OUT.write_text(svg, encoding='utf-8')
print('wrote', OUT, len(svg)//1024, 'KB')
