#!/usr/bin/env python3
"""Generate Faizan Haidri's portfolio WEBSITE as editable Figma artboards.

12 SVGs -> website_svg_portfolio/ :
  01-main-desktop.svg / 02-main-mobile.svg
  03..12 : desktop + mobile case-study page per project
    (Silver Gauntlet, Single Barrel Rifle, eNav, Underroot, Hearing Aid Dehumidifier)

All text is real SVG <text> -> pastes into Figma as editable text layers;
map fonts to Fraunces / IBM Plex Mono on first open. Photos are base64 JPEG
(unaltered, aspect-fit only). Dark Junca-style theme.

Run:  python3 build_portfolio_figma.py
"""
import base64
import io
import os
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image

HERE = Path(__file__).resolve().parent
IMG_DIR = HERE / "portfolio_img"
OUT = HERE / "website_svg_portfolio"

# ---------- palette (dark, Junca language) ----------
BG = "#0a0a0c"
PANEL = "#121216"
PANEL2 = "#16161b"
WHITE = "#f5f4f0"
GRAY = "#a7a7b3"
FAINT = "#6d6d78"
HAIR = "#26262d"
VIOLET = "#8b5cf6"
ORANGE = "#ff6a3d"
BLUE = "#3b82f6"

SERIF = "Fraunces, Georgia, 'Times New Roman', serif"
MONO = "'IBM Plex Mono', 'SFMono-Regular', Consolas, monospace"

# ---------- image embedding ----------
_b64cache = {}

def b64img(name):
    """Resized JPEG -> base64 data URI (cached). Source files are pre-sized."""
    if name not in _b64cache:
        im = Image.open(IMG_DIR / name).convert("RGB")
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=75, optimize=True)
        _b64cache[name] = ("data:image/jpeg;base64," +
                           base64.b64encode(buf.getvalue()).decode("ascii"),
                           im.size[0], im.size[1])
    return _b64cache[name]

def wrap(text, fs, max_w, serif=False):
    """Greedy word wrap -> list of lines."""
    avg = fs * (0.48 if serif else 0.62)
    words, lines, cur = text.split(), [], ""
    for wd in words:
        t = (cur + " " + wd).strip()
        if len(t) * avg <= max_w or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines

_uid = [0]
def uid():
    _uid[0] += 1
    return f"c{_uid[0]}"

class Page:
    def __init__(self, w):
        self.w = w
        self.mobile = w < 1000
        self.pad = 24 if self.mobile else 80
        self.parts = []
        self.y = 0
        self.defs = []

    # ---- primitives ----
    def rect(self, x, y, w, h, fill, stroke="none", rx=0, opacity=1.0, sw=1.5):
        self.parts.append(
            f'<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" rx="{rx:.0f}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}" opacity="{opacity:.2f}"/>')

    def line(self, x1, y1, x2, y2, stroke=HAIR, sw=1.5, opacity=1.0):
        self.parts.append(
            f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" '
            f'stroke="{stroke}" stroke-width="{sw}" opacity="{opacity:.2f}"/>')

    def glow(self, cx, cy, rx, ry, color, opacity=0.16):
        gid = uid()
        self.defs.append(
            f'<radialGradient id="{gid}"><stop offset="0" stop-color="{color}" '
            f'stop-opacity="{opacity:.2f}"/><stop offset="1" stop-color="{color}" '
            f'stop-opacity="0"/></radialGradient>')
        self.parts.append(
            f'<ellipse cx="{cx:.0f}" cy="{cy:.0f}" rx="{rx:.0f}" ry="{ry:.0f}" '
            f'fill="url(#{gid})"/>')

    def text(self, x, y, s, fs, fill=WHITE, serif=False, anchor="start",
             weight=400, style="", ls=None, opacity=1.0):
        fam = SERIF if serif else MONO
        st = f' font-style="{style}"' if style else ""
        wt = f' font-weight="{weight}"' if weight != 400 else ""
        lsp = f' letter-spacing="{ls:.1f}"' if ls else ""
        op = f' opacity="{opacity:.2f}"' if opacity != 1.0 else ""
        self.parts.append(
            f'<text x="{x:.0f}" y="{y:.0f}" font-family="{fam}" font-size="{fs}" '
            f'fill="{fill}" text-anchor="{anchor}"{st}{wt}{lsp}{op}>{escape(s)}</text>')

    def para(self, x, y, s, fs, max_w, fill=GRAY, serif=False, lh=1.7,
             weight=400, style="", anchor="start", ls=None):
        cx = x + max_w / 2 if anchor == "middle" else x
        for ln in wrap(s, fs, max_w, serif):
            self.text(cx, y, ln, fs, fill, serif, anchor=anchor,
                      weight=weight, style=style, ls=ls)
            y += fs * lh
        return y

    def eyebrow(self, x, y, s, fs=12, color=FAINT):
        self.text(x, y, s.upper(), fs, color, ls=fs * 0.22)
        return y + fs * 2.6

    def image(self, x, y, w, h, name, rx=18, bg=PANEL):
        """Aspect-fit photo in a rounded box (unaltered pixels)."""
        uri, iw, ih = b64img(name)
        s = min(w / iw, h / ih)
        dw, dh = iw * s, ih * s
        ix, iy = x + (w - dw) / 2, y + (h - dh) / 2
        cid = uid()
        self.defs.append(
            f'<clipPath id="{cid}"><rect x="{x:.0f}" y="{y:.0f}" '
            f'width="{w:.0f}" height="{h:.0f}" rx="{rx:.0f}"/></clipPath>')
        self.parts.append(
            f'<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" '
            f'rx="{rx:.0f}" fill="{bg}"/>')
        self.parts.append(
            f'<g clip-path="url(#{cid})"><image x="{ix:.0f}" y="{iy:.0f}" '
            f'width="{dw:.0f}" height="{dh:.0f}" href="{uri}" '
            f'xlink:href="{uri}"/></g>')

    def save(self, fname):
        h = int(self.y + 60)
        body = "\n".join(self.parts)
        defs = ("\n<defs>\n" + "\n".join(self.defs) + "\n</defs>"
                if self.defs else "")
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" '
               f'xmlns:xlink="http://www.w3.org/1999/xlink" '
               f'width="{self.w}" height="{h}" viewBox="0 0 {self.w} {h}">'
               f"{defs}\n"
               f'<rect x="0" y="0" width="{self.w}" height="{h}" fill="{BG}"/>\n'
               f"{body}\n</svg>")
        OUT.mkdir(exist_ok=True)
        (OUT / fname).write_text(svg, encoding="utf-8")
        kb = len(svg.encode("utf-8")) // 1024
        print(f"  {fname}: {self.w}x{h}  {kb}KB")


# =====================================================================
# CONTENT
# =====================================================================
HERO_LINE = "I build physical products and digital experiences."
EXPERTISE = "Industrial Design · UI/UX · Fabrication · Research · Electronics"
PROCESS = ["Research-backed", "Ask how and why", "Prototype", "Analyse",
           "Final work"]
DRIVES = "Curiosity keeps me driven — driven by observation."
HOW = [
    ("01", "Hands-on fabrication",
     "Workshop, wood, metal, casting — rifle, gauntlet, underroot.",
     "hero-rifle.jpg"),
    ("02", "Electronics & prototyping",
     "ESP-32, custom PCBs, Arduino — the eNav build.",
     "enav-bt.jpg"),
    ("03", "Research-backed process",
     "User studies, market benchmarks, HMWs — hearing aid research.",
     "hearing-title.jpg"),
    ("04", "3D & visualization",
     "CAD, renders, space visualization — product renders.",
     "underroot-viz.jpg"),
]
BIO = ("I'm Faizan Haidri, a designer working at the intersection of ideas "
       "and execution. I translate complex concepts into clear, functional "
       "solutions by blending design thinking with hands-on experimentation. "
       "My approach is rooted in observation and thoughtful articulation — "
       "I take the time to deeply understand problems before shaping outcomes.")
BIO2 = ("With a minimal, form-driven sensibility, I focus on creating "
        "solutions that are not only efficient but meaningful and refined. "
        "Curiosity has always driven my process, leading me to explore across "
        "disciplines and continuously expand my skill set.")
FACTS = [
    ("EDUCATION", "4th Year, B.Des Industrial Design — National Institute of "
                  "Design, Haryana (2023–2027)"),
    ("PREVIOUSLY", "Rockvale Academy, Kalimpong, West Bengal"),
    ("SOFTWARE", "Photoshop · Illustrator · InDesign · Figma · Procreate · "
                 "SolidWorks · Android Studio · Unity Hub · Arduino IDE"),
    ("ADVANCED", "Photography · Research · Management · Leather craft · "
                 "Clay modelling"),
    ("PERSONAL", "Highly organised · Curious by nature · Flexible & adaptive · "
                 "Reliable"),
    ("LANGUAGES", "English · Hindi · Urdu"),
    ("INTERESTS", "Trekking · Football · Gym"),
]
FAQS = [
    ("Where are you studying?",
     "4th year B.Des Industrial Design at the National Institute of Design, "
     "Haryana — graduating 2027."),
    ("What software do you work in?",
     "Photoshop, Illustrator, InDesign, Figma, Procreate, SolidWorks, "
     "Android Studio, Unity Hub and Arduino IDE."),
    ("What kind of work do you do?",
     "Physical products, electronics, UI/UX and fabrication — always "
     "research-backed, always prototyped by hand."),
    ("How do I reach you?",
     "faizanhaidri786@gmail.com · +91 8709314929"),
]

PROJECTS = [
    dict(slug="gauntlet", no="01 / 05", title="The Silver Gauntlet",
         tags="Wearable · Metalwork · NID Haryana",
         hero="hero-gauntlet.jpg",
         desc=("Inspired by medieval knight armor and dark fantasy aesthetics. "
               "The project focused on translating aggression, protection, and "
               "structure into wearable form, becoming one of my earliest deep "
               "studies into surface language, detailing, and handcrafted "
               "construction."),
         steps=[
            ("INSPIRATION", "Medieval armor, dark fantasy",
             "Inspired by medieval knight armor and dark fantasy aesthetics — "
             "studying how articulated plates translate aggression, protection, "
             "and structure into wearable form.",
             "gauntlet-inspo.jpg"),
            ("JOINT STUDIES", "Figuring out the connection of joints",
             "Iterative joint studies in sheet metal — cutting, folding, and "
             "riveting finger segments to find connections that flex like "
             "real knuckles.",
             "gauntlet-studies.jpg"),
            ("FINAL", "The articulated gauntlet",
             "The finished piece — a deep study in surface language, detailing, "
             "and handcrafted construction.",
             "hero-gauntlet.jpg"),
            ("DETAIL", "Process close-up",
             "Hand-formed segments and riveted joints, fitted and finished "
             "entirely by hand.",
             "gauntlet-joints.jpg"),
         ]),
    dict(slug="rifle", no="02 / 05", title="Single Barrel Rifle",
         tags="Workshop · Material exploration · NID Haryana",
         hero="hero-rifle.jpg",
         desc=("A life-scale model inspired by traditional bolt action rifles "
               "and their mechanical precision. The project explored "
               "proportion, ergonomics, and material shaping through intensive "
               "manual fabrication techniques, with a focus on understanding "
               "structural detailing and physical form development."),
         steps=[
            ("WORKSHOP", "Workshop & material exploration",
             "Semester 2 — exploring proportion, ergonomics, and material "
             "shaping through intensive manual fabrication techniques.",
             "rifle-workshop.jpg"),
            ("TOOLING", "The spokeshave",
             "Discovered during the build — a spokeshave shapes curved "
             "surfaces better than any planer, and became the key tool for "
             "carving the stock.",
             "rifle-spokeshave.jpg"),
            ("CONSTRUCTION", "Barrel & stock",
             "The barrel is a mild steel rod, sleeved precisely into a stock "
             "carved from a single piece of teak wood.",
             "rifle-stock.jpg"),
            ("FINAL", "Life-scale model",
             "A life-scale model inspired by traditional bolt action rifles — "
             "a study in structural detailing and physical form development.",
             "rifle-final.jpg"),
         ]),
    dict(slug="enav", no="03 / 05", title="eNav",
         tags="Smart wearable · Electronics · NID Haryana",
         hero="hero-enav.jpg",
         desc=("A low-distraction navigation device designed to create a "
               "smoother and safer riding experience. eNav seamlessly connects "
               "with smartphone navigation while presenting only essential "
               "information through a focused interface, reducing visual "
               "clutter and helping riders stay present on the road."),
         steps=[
            ("CONCEPT", "Time, motion and Direction",
             "A smart wearable system — a low-distraction navigation device "
             "for a smoother, safer riding experience, presenting only "
             "essential information through a focused interface.",
             "hero-enav.jpg"),
            ("DIGITAL PROTOTYPING", "ESP-32 DevKit V1",
             "Digital prototyping on the ESP-32 DevKit V1 — the Raspberry Pi "
             "was explored and set aside for size and power.",
             "enav-breadboard.jpg"),
            ("TEST RUN", "Arduino IDE",
             "Test runs through the Arduino IDE — mock code validated through "
             "the serial monitor before hardware was committed.",
             "enav-serial.jpg"),
            ("CUSTOM PCB", "Plug-and-play board",
             "A custom plug-and-play PCB, designed and hand-built on a DIY "
             "soldering board after studying how PCB layers route.",
             "enav-pcb.jpg"),
            ("DISPLAY", "Live from the phone",
             "The display is fed live from the phone via a third-party app to "
             "the ESP — the full Google Navigation interface would embed via "
             "the Navigation API.",
             "enav-display.jpg"),
         ]),
    dict(slug="underroot", no="04 / 05", title="Underroot",
         tags="Public furniture · Concrete & wood · NID Haryana",
         hero="hero-underroot.jpg",
         desc=("A public furniture designed to endure changing environments "
               "and everyday use over decades. Built around comfort, openness, "
               "and durability, it creates a space for people to pause, "
               "lounge, read, or simply exist within the rhythm of a public "
               "environment across all seasons."),
         steps=[
            ("BRIEF", "Design brief",
             "Outdoor public furniture — ergonomic, for all age groups and "
             "multiple seating postures; built to endure changing environments "
             "and everyday use over decades. A space to pause, lounge, read, "
             "or simply exist within the rhythm of a public environment across "
             "all seasons.",
             None),
            ("MODEL", "Miniature sun-board model",
             "A miniature sun-board model with metal mesh reinforcement to "
             "study the shell's structure before committing to full scale.",
             "underroot-model.jpg"),
            ("MATERIAL", "White cement pour",
             "Pouring white cement with dyes to preview the final finish — "
             "testing color, texture, and cure.",
             "underroot-pour.jpg"),
            ("TECHNICAL", "1:1 CAD & mold mapping",
             "Technical drawing translated to a 1:1 CAD print, mapped on the "
             "floor for mold layout and screwing positions.",
             "underroot-cad.jpg"),
            ("VISUALIZATION", "3D space visualization",
             "3D visualization of the piece in its public setting — testing "
             "scale, sightlines, and presence.",
             "underroot-render.jpg"),
            ("FINAL", "Underroot, in use",
             "Truss, mold, and cast preparation through to the finished "
             "piece. Guided by Dyutiman Moulik — 8 weeks.",
             "underroot-final.jpg"),
         ]),
    dict(slug="hearing", no="05 / 05", title="Hearing Aid Dehumidifier",
         tags="Research · Medical product · Ongoing",
         hero="hero-hearing.jpg",
         desc=("A product designed to address moisture-related damage in "
               "hearing aids, where compact electronic components are "
               "constantly exposed to humidity from daily use. The project "
               "focuses on creating a reliable and accessible dehumidifying "
               "solution that improves device longevity, maintenance, and "
               "overall user care through a compact and user-friendly system."),
         steps=[
            ("RESEARCH", "Common user problems",
             "Battery issues from moisture · earwax + moisture blocking "
             "components · static noise & feedback · malfunction / reduced "
             "lifespan · difficult maintenance · discomfort during sleep. "
             "Causes: sweat, humid weather, stepping out of AC rooms, "
             "accidental splash or drop — leading to corrosion and oxidation.",
             None),
            ("PROBLEM", "Problem statement",
             "Moisture is a major cause of hearing aid damage, yet existing "
             "solutions fail at safe, reliable, efficient moisture removal. "
             "Goal: a compact, user-friendly dehumidifying solution — without "
             "harmful heat.",
             None),
            ("BENCHMARK", "Market study",
             "PerfectDry LUX (USA, ₹8,000–12,000) — 45-min cycle, UV-C · "
             "Zephyr by Dry & Store (USA, ₹8,000–12,000) — 8-hr cycle · "
             "Global II by Dry & Store (USA, ₹15,000–20,000) — UV-C · Enlinea "
             "desiccant jar (India, ₹200–500) — silica gel · generic electric "
             "dry box (India/China, ₹4,000–6,000). Where they fail: they leave "
             "RH at 25–30% against the <10% needed; unregulated heat corrodes "
             "circuits and batteries; no RH measurement or certification.",
             None),
            ("HMW", "How might we",
             "Prevent condensation inside a closed system · define safe "
             "temperature limits · stay safe under overheating, leaks, or "
             "saturation · remove deep moisture without damage · fit the daily "
             "routine · minimize interaction, maximize effectiveness · "
             "portable, one-hand, intuitive · effortless and reliable for "
             "elderly users.",
             None),
            ("MATERIAL", "Molecular sieve research",
             "Zeolites — 3–10 angstrom pores that trap H2O, CO2, and N2. "
             "Aggressive absorption even at low humidity, pulling down to 10% "
             "RH — where silica gel's curve goes gradual.",
             "hearing-sieve.jpg"),
            ("TESTING", "Desiccant testing",
             "Hands-on desiccant trials comparing absorption behavior — "
             "validating the sieve's edge at the low-humidity end that hearing "
             "aids need.",
             "hearing-desiccant.jpg"),
            ("SYSTEM", "Feature integration",
             "Faraday cage (layered copper / polyester / polypropylene) + RF "
             "dielectric heating at 13.56 MHz + channeled airflow + UV-C + "
             "reusable molecular-sieve 3A cartridge + silicone gasket.",
             "hearing-arch.jpg"),
            ("ARCHITECTURE", "Product architecture",
             "Exploded: outer body · inner housing · parallel plate for "
             "dielectric heating · UV-C · silicon gasket · cartridge housing "
             "· hinge · Type-C · button.",
             "hearing-exploded.jpg"),
            ("ELECTRONICS", "Block diagram & power",
             "RF generator at 13.56 MHz → microcontroller → controlled "
             "airflow, all inside the Faraday cage. Power: Li-ion / Li-Po "
             "3.7V, USB-C, 3000–5000 mAh.",
             "hearing-title.jpg"),
            ("FINAL", "Renders & dimensions",
             "Final renders at 80 × 101.4 mm — a compact, user-friendly system "
             "for device longevity, maintenance, and everyday user care. "
             "Guided by Dyutiman Moulik — 8 weeks.",
             "hero-hearing.jpg"),
         ]),
]


# =====================================================================
# MAIN PAGE — shared section builders (width-parameterized)
# =====================================================================
def sec_nav(p):
    x = p.pad
    p.y = 0
    if not p.mobile:
        p.rect(0, 0, p.w, 88, BG, opacity=1.0)
        p.text(x, 54, "Faizan Haidri", 20, WHITE, serif=True)
        links = ["Work", "About", "Process", "Contact"]
        lx = p.w - x - 150
        for ln in reversed(links):
            p.text(lx, 54, ln, 13, GRAY)
            lx -= len(ln) * 9 + 44
        p.rect(p.w - x - 140, 26, 140, 38, "none", WHITE, rx=19, sw=1.5)
        p.text(p.w - x - 70, 51, "LET'S TALK", 12, WHITE, anchor="middle",
               ls=1.5)
        p.y = 88
    else:
        p.text(x, 48, "Faizan Haidri", 17, WHITE, serif=True)
        p.rect(p.w - x - 118, 18, 118, 34, "none", WHITE, rx=17, sw=1.5)
        p.text(p.w - x - 59, 41, "LET'S TALK", 11, WHITE, anchor="middle",
               ls=1.2)
        p.y = 72
    p.line(x, p.y, p.w - x, p.y, HAIR, 1)
    p.y += 8


def sec_hero(p):
    x = p.pad
    cw = p.w - 2 * x
    p.glow(x + cw * 0.78, 330, 420, 300, VIOLET, 0.14)
    p.glow(x + cw * 0.12, 620, 380, 260, ORANGE, 0.10)
    p.y += 110 if not p.mobile else 64
    p.y = p.eyebrow(x, p.y, "Portfolio — Industrial Design")
    p.y += 14
    fs = 92 if not p.mobile else 42
    p.y = p.para(x, p.y, HERO_LINE, fs, cw, WHITE, serif=True, lh=1.08)
    p.y += 26
    p.text(x, p.y, "©2026  ·  IST --:--  ·  NID Haryana, India", 13, FAINT,
           ls=1.2)
    p.y += 60 if not p.mobile else 40
    ih = 640 if not p.mobile else 220
    p.image(x, p.y, cw, ih, "enav-glow.jpg", rx=24)
    p.y += ih + 40
    p.text(x, p.y, "eNav — smart wearable navigation device, live prototype",
           12, FAINT, style="italic")
    p.y += 20


def sec_expertise(p):
    x = p.pad
    cw = p.w - 2 * x
    p.y += 110 if not p.mobile else 70
    p.y = p.eyebrow(x, p.y, "Expertise")
    fs = 30 if not p.mobile else 19
    for ln in wrap(EXPERTISE, fs, cw, True):
        p.text(x + cw / 2, p.y, ln, fs, WHITE, serif=True, anchor="middle")
        p.y += fs * 1.5
    p.y += 20


def sec_process(p):
    x = p.pad
    cw = p.w - 2 * x
    p.y += 100 if not p.mobile else 60
    p.y = p.eyebrow(x, p.y, "Process")
    tfs = 64 if not p.mobile else 34
    p.y = p.para(x, p.y, "How I work, in five steps.", tfs, cw, WHITE,
                 serif=True, lh=1.2)
    p.y += 30
    nfs, rfs = (15, 34) if not p.mobile else (12, 22)
    for i, title in enumerate(PROCESS, 1):
        p.line(x, p.y, p.w - x, p.y, HAIR, 1)
        p.y += 44 if not p.mobile else 34
        p.text(x, p.y, f"{i:02d}", nfs, VIOLET, ls=1.5)
        p.text(x + (70 if not p.mobile else 48), p.y, title, rfs, WHITE,
               serif=True)
        p.y += rfs * 1.6
    p.line(x, p.y, p.w - x, p.y, HAIR, 1)
    p.y += 10


def sec_work(p):
    x = p.pad
    cw = p.w - 2 * x
    p.y += 110 if not p.mobile else 70
    p.y = p.eyebrow(x, p.y, "Selected work")
    tfs = 64 if not p.mobile else 34
    p.y = p.para(x, p.y, "Selected work.", tfs, cw, WHITE, serif=True, lh=1.2)
    p.y += 40
    for pr in PROJECTS:
        ih = 700 if not p.mobile else 210
        p.image(x, p.y, cw, ih, pr["hero"], rx=24)
        p.y += ih + 30
        p.y = p.para(x, p.y, f'{pr["no"]}  ·  {pr["tags"]}'.upper(),
                     11.5, cw, FAINT, lh=1.6, ls=1.5)
        p.y += 12
        cfs = 44 if not p.mobile else 28
        p.y = p.para(x, p.y, pr["title"], cfs, cw, WHITE, serif=True, lh=1.2)
        p.y += 8
        p.y = p.para(x, p.y, pr["desc"], 15 if not p.mobile else 13.5, cw,
                     GRAY, lh=1.75)
        p.y += 18
        p.text(x, p.y, "READ THE CASE STUDY ↗", 13, ORANGE, ls=1.5)
        p.y += 90 if not p.mobile else 60


def sec_drives(p):
    x = p.pad
    cw = p.w - 2 * x
    p.y += 110 if not p.mobile else 70
    p.y = p.eyebrow(x, p.y, "( What drives me )", fs=13)
    fs = 56 if not p.mobile else 30
    p.y = p.para(x, p.y, DRIVES, fs, cw - 120, WHITE, serif=True, lh=1.25,
                 anchor="middle")
    p.y += 20


def sec_how(p):
    x = p.pad
    cw = p.w - 2 * x
    p.y += 100 if not p.mobile else 60
    p.y = p.eyebrow(x, p.y, "How I work")
    for i, (no, title, line, img) in enumerate(HOW):
        p.line(x, p.y, p.w - x, p.y, HAIR, 1)
        p.y += 36
        if not p.mobile:
            p.image(x, p.y, 300, 190, img, rx=14)
            tx = x + 340
            p.text(tx, p.y + 34, no, 14, VIOLET, ls=1.5)
            p.text(tx, p.y + 74, title, 30, WHITE, serif=True)
            p.text(tx, p.y + 108, line, 14, GRAY)
            p.y += 226
        else:
            p.image(x, p.y, cw, 190, img, rx=14)
            p.y += 214
            p.text(x, p.y, no, 12, VIOLET, ls=1.5)
            p.y += 26
            p.text(x, p.y, title, 22, WHITE, serif=True)
            p.y += 36
            p.text(x, p.y, line, 12.5, GRAY)
            p.y += 40
    p.line(x, p.y, p.w - x, p.y, HAIR, 1)
    p.y += 10


def sec_about(p):
    x = p.pad
    cw = p.w - 2 * x
    p.y += 110 if not p.mobile else 70
    p.y = p.eyebrow(x, p.y, "About")
    tfs = 64 if not p.mobile else 34
    p.y = p.para(x, p.y, "Faizan Haidri.", tfs, cw, WHITE, serif=True, lh=1.2)
    p.y += 36
    if not p.mobile:
        p.image(x, p.y, 420, 560, "portrait-maker.jpg", rx=20)
        tx, tw = x + 470, cw - 470
    else:
        p.image(x, p.y, cw, 420, "portrait-maker.jpg", rx=20)
        p.y += 448
        tx, tw = x, cw
    ty = p.y
    ty = p.para(tx, ty, BIO, 16, tw, GRAY, lh=1.8)
    ty += 18
    ty = p.para(tx, ty, BIO2, 16, tw, GRAY, lh=1.8)
    p.y = max(p.y + (590 if not p.mobile else 0), ty + 40)
    for k, v in FACTS:
        p.text(x, p.y, k, 12, VIOLET, ls=1.8)
        p.y += 28
        p.y = p.para(x, p.y, v, 15 if not p.mobile else 13.5, cw - 20,
                     WHITE, lh=1.7)
        p.y += 26


def sec_faq(p):
    x = p.pad
    cw = p.w - 2 * x
    p.y += 60 if not p.mobile else 40
    p.y = p.eyebrow(x, p.y, "FAQ")
    for q, a in FAQS:
        p.line(x, p.y, p.w - x, p.y, HAIR, 1)
        p.y += 36 if not p.mobile else 30
        qfs = 22 if not p.mobile else 17
        for ln in wrap(q, qfs, cw - 60, True):
            p.text(x, p.y, ln, qfs, WHITE, serif=True)
            p.y += qfs * 1.35
        p.y += 6
        p.y = p.para(x, p.y, a, 14.5 if not p.mobile else 13, cw - 20, GRAY,
                     lh=1.75)
        p.y += 30
        p.text(p.w - x - 8, p.y - 30, "+", 24, FAINT, anchor="end")
    p.line(x, p.y, p.w - x, p.y, HAIR, 1)
    p.y += 10


def sec_footer(p, big=True):
    x = p.pad
    cw = p.w - 2 * x
    p.y += 120 if not p.mobile else 80
    p.glow(x + cw * 0.5, p.y + 200, 500, 260, BLUE, 0.10)
    p.glow(x + cw * 0.2, p.y + 420, 380, 240, VIOLET, 0.10)
    p.y = p.eyebrow(x, p.y, "Contact")
    fs = 76 if not p.mobile else 38
    p.y = p.para(x, p.y, "Let's build something.", fs, cw, WHITE, serif=True,
                 lh=1.1)
    p.y += 40
    bw, bh = (300, 56) if not p.mobile else (280, 50)
    p.rect(x, p.y, bw, bh, WHITE, rx=bh // 2)
    p.text(x + bw / 2, p.y + bh / 2 + 5, "faizanhaidri786@gmail.com",
           14 if not p.mobile else 12.5, BG, anchor="middle")
    p.y += bh + 70
    cols = [
        ("SITEMAP", ["Work", "About", "Process", "Contact"]),
        ("SOCIALS", ["Behance — behance.net/faizanhaidri",
                     "LinkedIn — linkedin.com/in/faizan-haidri"]),
        ("CONTACT", ["+91 8709314929", "faizanhaidri786@gmail.com"]),
    ]
    if not p.mobile:
        cx = x
        for head, items in cols:
            p.text(cx, p.y, head, 12, FAINT, ls=1.8)
            iy = p.y + 34
            for it in items:
                p.text(cx, iy, it, 14, GRAY)
                iy += 30
            cx += 400
        p.y += 34 + 30 * 2 + 70
    else:
        for head, items in cols:
            p.text(x, p.y, head, 11, FAINT, ls=1.8)
            p.y += 30
            for it in items:
                for ln in wrap(it, 13, cw - 10):
                    p.text(x, p.y, ln, 13, GRAY)
                    p.y += 24
            p.y += 26
        p.y += 30
    p.line(x, p.y, p.w - x, p.y, HAIR, 1)
    p.y += 34
    p.text(x, p.y, "©2026 Faizan Haidri", 12, FAINT, ls=1.2)
    p.text(p.w - x, p.y, "NID Haryana, India", 12, FAINT, anchor="end", ls=1.2)
    p.y += 20


def build_main(w):
    p = Page(w)
    sec_nav(p)
    sec_hero(p)
    sec_expertise(p)
    sec_process(p)
    sec_work(p)
    sec_drives(p)
    sec_how(p)
    sec_about(p)
    sec_faq(p)
    sec_footer(p)
    return p


# =====================================================================
# CASE-STUDY PAGES
# =====================================================================
def build_case(pr, w, nxt):
    p = Page(w)
    x = p.pad
    cw = p.w - 2 * x

    # mini nav
    p.y = 0
    p.text(x, 52, "←  All work", 13, GRAY, ls=1.2)
    p.text(p.w - x, 52, "Faizan Haidri", 17, WHITE, serif=True, anchor="end")
    p.line(x, 84, p.w - x, 84, HAIR, 1)
    p.y = 92

    # header
    p.glow(x + cw * 0.8, 300, 400, 280, VIOLET, 0.12)
    p.y += 70 if not p.mobile else 44
    p.y = p.para(x, p.y, pr["no"].upper() + "  ·  " + pr["tags"].upper(),
                 11.5, cw, FAINT, lh=1.6, ls=1.6)
    p.y += 16
    tfs = 72 if not p.mobile else 36
    p.y = p.para(x, p.y, pr["title"], tfs, cw, WHITE, serif=True, lh=1.08)
    p.y += 26
    p.y = p.para(x, p.y, pr["desc"], 15.5 if not p.mobile else 13.5, cw,
                 GRAY, lh=1.8)
    p.y += 50
    ih = 700 if not p.mobile else 220
    p.image(x, p.y, cw, ih, pr["hero"], rx=24)
    p.y += ih + 90

    # research steps — exact order
    for i, (label, title, body, img) in enumerate(pr["steps"], 1):
        sfs = 30 if not p.mobile else 22
        if not p.mobile:
            tw = 700
            p.text(x, p.y, f"STEP {i:02d} — {label}", 12, VIOLET, ls=1.6)
            p.y += 38
            p.y = p.para(x, p.y, title, sfs, tw, WHITE, serif=True, lh=1.2)
            p.y += 10
            ty = p.para(x, p.y, body, 15, tw, GRAY, lh=1.8)
            if img:
                iw2 = 480
                ix = p.w - x - iw2
                ih2 = 380
                p.image(ix, p.y - 10, iw2, ih2, img, rx=16)
                p.y = max(ty, p.y - 10 + ih2) + 80
            else:
                p.y = ty + 80
        else:
            p.text(x, p.y, f"STEP {i:02d} — {label}", 11, VIOLET, ls=1.4)
            p.y += 32
            p.y = p.para(x, p.y, title, sfs, cw, WHITE, serif=True, lh=1.2)
            p.y += 8
            p.y = p.para(x, p.y, body, 13.5, cw, GRAY, lh=1.75)
            p.y += 24
            if img:
                p.image(x, p.y, cw, 240, img, rx=14)
                p.y += 264
            p.y += 44

    # next project + mini footer
    p.line(x, p.y, p.w - x, p.y, HAIR, 1)
    p.y += 60
    p.text(x, p.y, "NEXT PROJECT →", 12, FAINT, ls=1.8)
    p.y += 44
    nfs = 44 if not p.mobile else 28
    p.text(x, p.y, nxt["title"], nfs, WHITE, serif=True)
    p.y += nfs * 1.4 + 70
    p.line(x, p.y, p.w - x, p.y, HAIR, 1)
    p.y += 34
    if not p.mobile:
        p.text(x, p.y, "faizanhaidri786@gmail.com  ·  +91 8709314929", 12,
               FAINT, ls=1.0)
        p.text(p.w - x, p.y, "©2026 Faizan Haidri", 12, FAINT, anchor="end",
               ls=1.0)
    else:
        p.text(x, p.y, "faizanhaidri786@gmail.com", 11.5, FAINT)
        p.y += 26
        p.text(x, p.y, "+91 8709314929  ·  ©2026 Faizan Haidri", 11.5, FAINT)
    p.y += 20
    return p


def main():
    print("generating portfolio Figma artboards...")
    specs = [
        ("01-main-desktop.svg", lambda: build_main(1440)),
        ("02-main-mobile.svg", lambda: build_main(390)),
    ]
    names = ["03", "05", "07", "09", "11"]
    for n, pr in zip(names, PROJECTS):
        nxt = PROJECTS[(PROJECTS.index(pr) + 1) % len(PROJECTS)]
        specs.append((f"{n}-case-{pr['slug']}-desktop.svg",
                      lambda pr=pr, nxt=nxt: build_case(pr, 1440, nxt)))
        specs.append((f"{int(n) + 1:02d}-case-{pr['slug']}-mobile.svg",
                      lambda pr=pr, nxt=nxt: build_case(pr, 390, nxt)))
    for fname, fn in specs:
        fn().save(fname)
    print("done.")


if __name__ == "__main__":
    main()
