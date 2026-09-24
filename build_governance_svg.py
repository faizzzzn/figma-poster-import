#!/usr/bin/env python3
"""Build governance_map.svg — the simplified Women's Empowerment Governance Map.

Mirrors governance_simplified_board.py (Miro) 1:1: 5 tiers, money bus,
5 gap badges + detail cards, legend, how-to strip. Pasted into FigJam as
editable vector + text layers via import_poster.py --file-type figjam.

Usage: python3 build_governance_svg.py   -> writes governance_map.svg
"""
import html

W, H = 5600, 3400
CX = 2800

GREEN = "#30a46c"
GRAY = "#6b7280"
RED = "#e5484d"
DARK = "#374151"
BG = "#fbfaf7"

FONT = "Inter, -apple-system, 'Segoe UI', sans-serif"

parts = []


def esc(s):
    return html.escape(s, quote=False)


def rect(x, y, w, h, fill, stroke=None, sw=0, rx=18):
    s = (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
         f'fill="{fill}"')
    if stroke:
        s += f' stroke="{stroke}" stroke-width="{sw}"'
    return s + "/>"


def text_lines(x, y, lines, size, fill="#ffffff", anchor="middle",
               weight=None, spacing=1.25):
    """lines: list of (text, bold). Centered block starting at (x, y baseline)."""
    out = [f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" '
           f'fill="{fill}" text-anchor="{anchor}"'
           + (f' font-weight="{weight}"' if weight else "") + ">"]
    dy = round(size * spacing)
    for i, (t, b) in enumerate(lines):
        yy = y + i * dy if i else y
        tag = (f'<tspan x="{x}" dy="{dy if i else 0}"'
               + (" font-weight=\"bold\"" if b else "") + f">{esc(t)}</tspan>")
        out.append(tag)
    out.append("</text>")
    return "\n".join(out)


def box(cx, cy, w, h, fill, lines, tcolor="#ffffff", border=None,
        title_size=34, body_size=26):
    """lines: list of (text, is_title)."""
    x, y = cx - w / 2, cy - h / 2
    s = [rect(x, y, w, h, fill, stroke=border, sw=3 if border else 0)]
    # vertical centering: compute block height
    total = 0
    sizes = []
    for t, is_t in lines:
        sz = title_size if is_t else body_size
        sizes.append(sz)
        total += sz * 1.25
    total -= sizes[-1] * 0.25
    yy = cy - total / 2 + sizes[0] * 0.35
    t = [f'<text x="{cx}" y="{round(yy)}" font-family="{FONT}" '
         f'fill="{tcolor}" text-anchor="middle">']
    for i, ((txt, is_t), sz) in enumerate(zip(lines, sizes)):
        dy = round(sz * 1.25) if i else 0
        t.append(f'<tspan x="{cx}" dy="{dy}" font-size="{sz}"'
                 + (" font-weight=\"bold\"" if is_t else "")
                 + f">{esc(txt)}</tspan>")
    t.append("</text>")
    s.append("\n".join(t))
    return "\n".join(s)


def badge(cx, cy, txt):
    w, h = 150, 64
    return (rect(cx - w / 2, cy - h / 2, w, h, RED, rx=12) + "\n"
            + text_lines(cx, cy + 8, [(txt, True)], 22))


def arrow(x1, y1, x2, y2, color, width=4, dashed=False, marker=None):
    dash = ' stroke-dasharray="10 8"' if dashed else ""
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="{color}" stroke-width="{width}"{dash} '
            f'marker-end="url(#{marker})"/>' if marker else
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="{color}" stroke-width="{width}"{dash}/>')


def busbar(x1, y1, x2, y2, t=16):
    x, y = min(x1, x2), min(y1, y2)
    w, h = (abs(x2 - x1) or t), (abs(y2 - y1) or t)
    return rect(x, y, w, h, GREEN, rx=6)


def label(x, y, txt, size=24, fill="#6b7280", anchor="middle", bold=False):
    return (f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" '
            f'fill="{fill}" text-anchor="{anchor}"'
            + (" font-weight=\"bold\"" if bold else "") + f">{esc(txt)}</text>")


def build():
    p = []
    p.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" '
             f'height="{H}" viewBox="0 0 {W} {H}">')
    p.append("<defs>"
             '<marker id="mG" markerWidth="10" markerHeight="10" refX="8" '
             'refY="3" orient="auto"><path d="M0,0 L8,3 L0,6 Z" fill="' + GREEN + '"/></marker>'
             '<marker id="mX" markerWidth="10" markerHeight="10" refX="8" '
             'refY="3" orient="auto"><path d="M0,0 L8,3 L0,6 Z" fill="' + GRAY + '"/></marker>'
             "</defs>")
    p.append(rect(0, 0, W, H, BG, rx=0))

    # ---- title ----
    p.append(label(80, 100, "WOMEN\u2019S EMPOWERMENT \u2014 GOVERNANCE MAP",
                   64, "#1a1a1a", anchor="start", bold=True))
    p.append(label(80, 148, "India \u00b7 Sept 2026 \u2014 bold figures are new 2025\u201326 data",
                   28, "#595959", anchor="start"))

    # ---- band labels ----
    for txt, y in [("TIER 1 \u00b7 WORLD", 360), ("TIER 2 \u00b7 DELHI", 760),
                   ("TIER 3 \u00b7 STATE", 1180), ("TIER 4 \u00b7 GROUND", 1600),
                   ("TIER 5 \u00b7 SCHEMES", 2020)]:
        p.append(label(80, y + 8, txt, 24, "#9a9a9a", anchor="start"))

    # ---- TIER 1 ----
    t1 = [("UN Women", "norms + data"),
          ("CEDAW Committee", "India reports here"),
          ("UNFPA \u00b7 UNICEF", "program money"),
          ("World Bank \u00b7 ADB", "loans for schemes")]
    for i, (a, b) in enumerate(t1):
        p.append(box(CX - 1020 + i * 680, 360, 620, 150, "#e9e9ee",
                     [(a, True), (b, False)], tcolor="#1a1a1a"))

    # ---- TIER 2 ----
    p.append(box(CX - 1820, 760, 440, 170, "#e9e9ee",
                 [("NITI Aayog", True), ("tracks SDG 5", False)],
                 tcolor="#1a1a1a"))
    p.append(box(CX - 1290, 760, 520, 170, "#f59e0b",
                 [("Govt of India", True), ("budget + law", False)]))
    p.append(box(CX - 630, 760, 700, 230, "#2f5fd0",
                 [("MWCD", True),
                  ("Nirbhaya: \u20b98,212.85 cr allocated", False),
                  ("\u20b96,581.84 cr released/utilised", False),
                  ("Lok Sabha, Feb 2026", False)]))
    p.append(box(CX + 150, 760, 560, 170, "#d7e5ff",
                 [("Mission Shakti", True), ("Sambal + Samarthya", False)],
                 tcolor="#1a1a1a"))
    p.append(box(CX + 760, 760, 560, 170, "#d7e5ff",
                 [("Mission Vatsalya", True), ("child protection", False)],
                 tcolor="#1a1a1a"))
    p.append(box(CX + 1370, 760, 560, 170, "#d7e5ff",
                 [("Attached bodies", True), ("NCPCR \u00b7 CARA \u00b7 NIPCCD", False)],
                 tcolor="#1a1a1a"))
    p.append(box(CX + 1920, 760, 440, 170, "#e9e9ee",
                 [("NCW", True), ("complaints \u2192 MWCD", False)],
                 tcolor="#1a1a1a"))
    p.append(box(CX - 630, 935, 560, 90, "#ffffff",
                 [("FTSCs: 775 functional \u00b7 extended to Sep 2026", False)],
                 tcolor="#1a1a1a", border="#2f5fd0",
                 title_size=26, body_size=26))

    # ---- TIER 3 ----
    p.append(box(CX - 1260, 1180, 560, 170, "#d9f2e3",
                 [("WCD Dept", True), ("state schemes", False)],
                 tcolor="#1a1a1a"))
    p.append(box(CX - 610, 1180, 640, 200, "#bfe8cf",
                 [("State Mission Authority", True),
                  ("runs Nirbhaya money in-state", False)],
                 tcolor="#1a1a1a"))
    p.append(box(CX + 40, 1180, 560, 170, "#d9f2e3",
                 [("One Stop Centre", True), ("crisis help under one roof", False)],
                 tcolor="#1a1a1a"))
    p.append(label(CX + 40, 1180 + 97 + 24,
                   "991 centres \u00b7 15.2L women helped (Jun 2026)",
                   24, "#1a1a1a", bold=True))
    p.append(box(CX + 650, 1180, 560, 170, "#d9f2e3",
                 [("Child Protection Unit", True), ("CWC \u00b7 JJB", False)],
                 tcolor="#1a1a1a"))
    p.append(box(CX + 1260, 1180, 560, 170, "#d9f2e3",
                 [("Nari Adalat", True), ("women-run justice", False)],
                 tcolor="#1a1a1a"))

    # ---- TIER 4 ----
    g4 = [("Panchayat", "50% seats reserved"),
          ("District Admin", "DC \u00b7 DPO \u00b7 police"),
          ("Block \u00b7 PHC", "the last office"),
          ("Anganwadi", "2L+ centres"),
          ("ASHA Worker", "honorarium, not salary")]
    for i, (a, b) in enumerate(g4):
        fill = "#ffe1a8" if a == "ASHA Worker" else "#fff3d6"
        p.append(box(CX - 1220 + i * 610, 1600, 560 if a != "Panchayat" else 520,
                     160, fill, [(a, True), (b, False)], tcolor="#1a1a1a"))

    # ---- TIER 5 ----
    p.append(box(CX - 720, 2020, 760, 230, "#ffe8d6",
                 [("SAMBAL \u2014 safety", True),
                  ("One Stop Centre \u00b7 181 helpline", False),
                  ("BBBP \u00b7 Nari Adalat", False),
                  ("181: 99L+ women (Feb 2026)", False)],
                 tcolor="#1a1a1a"))
    p.append(box(CX + 100, 2020, 760, 230, "#ffe8d6",
                 [("SAMARTHYA \u2014 support", True),
                  ("PMMVY \u00b7 Shakti Sadan \u00b7 Sakhi Niwas \u00b7 Palna", False),
                  ("SRB 918\u2192929", False)],
                 tcolor="#1a1a1a"))
    p.append(box(CX + 820, 2020, 560, 180, "#ffe8d6",
                 [("Poshan 2.0", True)], tcolor="#1a1a1a"))

    # ---- money bus (green bars) ----
    p.append(busbar(1855 - 8, 1000, 1855 + 8, 1900))          # bus-v trunk
    p.append(busbar(1855, 1000 - 8, 2950, 1000 + 8))          # bus-h1
    p.append(busbar(1855, 1050 - 8, 3560, 1050 + 8))          # bus-h2
    p.append(busbar(1855, 1890 - 8, 2490, 1890 + 8))          # bus-f2
    p.append(busbar(2490 - 8, 1890, 2490 + 8, 2200))          # bus-drop
    p.append(busbar(2080, 2200 - 8, 3620, 2200 + 8))          # bus-h3

    # ---- connectors: money down (green) ----
    p.append(arrow(1770, 760, 1820, 760, GREEN, 5, marker="mG"))          # goi->mwcd
    p.append(arrow(2950, 845, 2950, 992, GREEN, 4, marker="mG"))          # shakti->bus
    p.append(arrow(3560, 845, 3560, 1042, GREEN, 4, marker="mG"))        # vatsalya->bus
    p.append(arrow(2080, 2192, 2080, 2135, GREEN, 4, marker="mG"))       # bus->sambal
    p.append(arrow(2900, 2192, 2900, 2135, GREEN, 4, marker="mG"))       # bus->samarthya
    p.append(arrow(3620, 2192, 3620, 2110, GREEN, 4, marker="mG"))       # bus->poshan
    p.append(arrow(2170, 875, 2190, 1080, GREEN, 5, marker="mG"))       # mwcd->sma
    p.append(arrow(2190, 1280, 2170, 1520, GREEN, 5, marker="mG"))      # sma->dist
    p.append(arrow(2450, 1600, 2500, 1600, GREEN, 5, marker="mG"))       # dist->block
    p.append(arrow(3060, 1600, 3720, 1600, GREEN, 5, marker="mG"))       # block->asha
    p.append(arrow(1510, 845, 2170, 1520, GREEN, 4, marker="mG"))       # goi->dist
    p.append(arrow(2520, 760, 2670, 760, GREEN, 4, marker="mG"))         # mwcd->shakti
    p.append(arrow(3230, 760, 3280, 760, GREEN, 4, marker="mG"))         # shakti->vatsalya
    p.append(arrow(3840, 760, 3890, 760, GREEN, 4, marker="mG"))         # vatsalya->attached
    for i, wx in enumerate([1780, 2460, 3140, 3820]):
        p.append(arrow(wx, 435, 1510, 675, GRAY, 2, marker="mX"))        # world->goi
    p.append(arrow(1200, 760, 1820, 760, GREEN, 3, marker="mG"))         # niti->mwcd

    # ---- connectors: reports up (gray dashed, over the money line) ----
    p.append(arrow(3720, 1600, 3060, 1600, GRAY, 2, True, "mX"))         # asha->block
    p.append(arrow(2500, 1600, 2450, 1600, GRAY, 2, True, "mX"))         # block->dist
    p.append(arrow(2170, 1520, 2190, 1280, GRAY, 2, True, "mX"))        # dist->sma
    p.append(arrow(2190, 1080, 2170, 875, GRAY, 2, True, "mX"))          # sma->mwcd

    # ---- connector captions ----
    p.append(label(2140, 420, "treaty duty", 22))
    p.append(label(1510, 730, "tracks SDG 5", 22))
    p.append(label(1795, 730, "funds + mandate", 22))
    p.append(label(3255, 730, "all under MWCD", 22))
    p.append(label(1900, 1180, "\u20b9 + schemes", 22))
    p.append(label(2330, 980, "reports up \u2014 patchy \u2715", 22))

    # ---- gap badges ----
    p.append(badge(CX + 1405, 1480, "GAP 1"))
    p.append(badge(CX - 365, 1320, "GAP 2"))
    p.append(badge(CX - 425, 1480, "GAP 3"))
    p.append(badge(CX + 405, 1865, "GAP 4"))
    p.append(badge(CX - 855, 1320, "GAP 5"))

    # ---- gap detail cards ----
    p.append(label(80, 2320, "THE 5 GAPS \u2014 where the system leaks",
                   26, RED, anchor="start", bold=True))
    gaps = [
        ("GAP 1 \u00b7 ASHA PAY DISPUTE",
         ["Honorarium, not salary \u2014 states delay or deny it.",
          "2026 protests: AP, Telangana, WB",
          "\u2192 bites: ASHA Worker (Tier 4)"]),
        ("GAP 2 \u00b7 BUDGET UNDERSPEND",
         ["Nirbhaya: \u20b98,212.85 cr allocated \u2192",
          "\u20b96,581.84 cr released/utilised (Lok Sabha, Feb 2026)",
          "2025-26 grant \u20b9278 cr: lowest ever",
          "\u2192 bites: MWCD \u2192 State money pipe"]),
        ("GAP 3 \u00b7 UNEVEN SCALING",
         ["Pilots work; scale-up fails.",
          "Mahila Police Volunteers: only 13 states",
          "WB: 8 of 123 FTSCs work",
          "\u2192 bites: State \u2192 District handoff"]),
        ("GAP 4 \u00b7 PMMVY PAYOUT GAP",
         ["Enrolled \u2260 money received.",
          "Enrolment counted as success; the money lags",
          "\u2192 bites: Samarthya / PMMVY (Tier 5)"]),
        ("GAP 5 \u00b7 REPORTING GAP",
         ["Most violence never enters the system.",
          "NARI 2025: 2 in 3 harassment cases never reported",
          "\u2192 bites: the reports-up chain"]),
    ]
    for i, (head, lines) in enumerate(gaps):
        gx = CX - 2040 + i * 1020
        p.append(rect(gx - 490, 2400, 980, 320, "#ffffff",
                      stroke=RED, sw=3))
        p.append(text_lines(gx, 2470,
                            [(head, True)] + [(l, False) for l in lines],
                            24, fill="#1a1a1a"))

    # ---- legend ----
    ly = 2980
    p.append(rect(20, ly - 32, 150, 16, GREEN, rx=4))
    p.append(label(190, ly, "money flows down", 22, "#1a1a1a", anchor="start"))
    p.append('<line x1="520" y1="%d" x2="670" y2="%d" stroke="%s" '
             'stroke-width="3" stroke-dasharray="10 8"/>' % (ly - 24, ly - 24, GRAY))
    p.append(label(690, ly, "reports flow up (patchy \u2715)", 22, "#1a1a1a",
                   anchor="start"))
    p.append(badge(1360 + 75, ly - 2, "GAP n"))
    p.append(label(1530, ly, "gap badge \u2192 detail card below", 22, "#1a1a1a",
                   anchor="start"))
    p.append(label(2900, ly, "25 boxes \u00b7 2 arrow types \u00b7 draw it on one sheet",
                   22, "#6b7280", anchor="start"))

    # ---- how-to strip ----
    p.append(rect(80, 3155, 5440, 130, DARK, rx=18))
    p.append(label(2800, 3235,
                   "HOW TO COPY ON A SHEET \u2014 1 draw the 5 bands \u00b7 "
                   "2 place the 25 boxes \u00b7 3 ink the green money chain going down "
                   "\u00b7 4 dashed gray reports going up \u00b7 5 stick the 5 red "
                   "GAP badges where it leaks",
                   24, "#ffffff", bold=True))

    p.append("</svg>")
    return "\n".join(p)


if __name__ == "__main__":
    Path = __import__("pathlib").Path
    out = Path(__file__).parent / "governance_map.svg"
    out.write_text(build(), encoding="utf-8")
    print("wrote", out, out.stat().st_size, "bytes")
