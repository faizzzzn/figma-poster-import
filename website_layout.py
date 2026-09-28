#!/usr/bin/env python3
"""Generate the Kaam x RozgaarSetu WEBSITE as editable Figma artboards.

Two full-page layouts, rendered from the same content as kaam-website.html:
  - website-desktop.svg  (1440 wide, multi-column grids)
  - website-mobile.svg   (390 wide, single column)

All text is real SVG <text> -> pastes into Figma as editable text layers,
map fonts to Fraunces / IBM Plex Mono on first open.
Run:  python3 website_layout.py   ->  outputs website_svg/
"""
import os
from xml.sax.saxutils import escape

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "website_svg")

# ---------- palette ----------
SKY0, SKY1 = "#F4FAFF", "#D8EBFB"
INK, INK_SOFT, FAINT = "#0B2E4E", "#2C5A80", "#5E87A8"
ACCENT, ACCENT_DEEP = "#2E9BE6", "#14608F"
CARD, STROKE = "#FFFFFF", "#82B9E6"
GREEN = "#2D9C6E"

SERIF = "Fraunces, Georgia, 'Times New Roman', serif"
MONO = "'IBM Plex Mono', 'SFMono-Regular', Consolas, monospace"


def wtext(text, fs, max_w, serif=False):
    """Greedy word wrap. Returns list of lines."""
    avg = fs * (0.50 if serif else 0.60)
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


class Page:
    def __init__(self, w, name):
        self.w, self.name = w, name
        self.parts = []
        self.y = 0

    # ---- primitives ----
    def rect(self, x, y, w, h, fill, stroke="none", rx=0, opacity=1.0, sw=1.5):
        self.parts.append(
            f'<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" rx="{rx}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}" opacity="{opacity:.2f}"/>')

    def line(self, x1, y1, x2, y2, stroke, sw=1.5, opacity=1.0):
        self.parts.append(
            f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" '
            f'stroke="{stroke}" stroke-width="{sw}" opacity="{opacity:.2f}"/>')

    def circle(self, cx, cy, r, fill, stroke="none", sw=1.5):
        self.parts.append(
            f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r:.0f}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{sw}"/>')

    def text(self, x, y, s, fs, fill=INK, serif=False, anchor="start", weight=400,
             style="", ls=None, opacity=1.0):
        fam = SERIF if serif else MONO
        st = f' font-style="{style}"' if style else ""
        wt = f' font-weight="{weight}"' if weight != 400 else ""
        lsp = f' letter-spacing="{ls}px"' if ls else ""
        op = f' opacity="{opacity:.2f}"' if opacity != 1.0 else ""
        self.parts.append(
            f'<text x="{x:.0f}" y="{y:.0f}" font-family="{fam}" font-size="{fs}" '
            f'fill="{fill}" text-anchor="{anchor}"{st}{wt}{lsp}{op}>{escape(s)}</text>')

    def para(self, x, y, s, fs, max_w, fill=INK_SOFT, serif=False, lh=1.7,
             weight=400, style=""):
        """Wrapped paragraph. Returns new y (baseline of last line + leading)."""
        for ln in wtext(s, fs, max_w, serif):
            self.text(x, y, ln, fs, fill, serif, weight=weight, style=style)
            y += fs * lh
        return y

    def glass_card(self, x, y, w, h, rx=26):
        self.rect(x, y, w, h, CARD, STROKE, rx, 0.72, 1.5)
        self.rect(x + 1.5, y + 1.5, w - 3, h - 3, "#FFFFFF", "none", rx - 2, 0.25)

    def bg_card(self, x, y, w, h, rx=26, opacity=0.72):
        """Card background string — insert into parts BEFORE content so it sits behind."""
        return (f'<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" rx="{rx}" '
                f'fill="{CARD}" stroke="{STROKE}" stroke-width="1.5" opacity="{opacity:.2f}"/>')

    def tag(self, x, y, s, fs=11):
        self.text(x, y, s.upper(), fs, ACCENT_DEEP, ls=fs * 0.28)
        return y + fs * 2.4

    def cpara(self, cx, y, s, fs, max_w, fill=INK, serif=False, lh=1.4,
              weight=400, style=""):
        """Wrapped paragraph, centered. Returns new y."""
        for ln in wtext(s, fs, max_w, serif):
            self.text(cx, y, ln, fs, fill, serif, anchor="middle", weight=weight, style=style)
            y += fs * lh
        return y

    # ---- section header ----
    def sec_head(self, no, title_lines, lede, pad_x, title_fs):
        x = pad_x
        self.y += 110
        self.tag(x, self.y, no)
        for tl in title_lines:
            for ln in wtext(tl, title_fs, self.w - 2 * pad_x - 10, True):
                self.text(x, self.y, ln, title_fs, INK, serif=True)
                self.y += title_fs * 1.15
        self.y += 18
        self.y = self.para(x, self.y, lede, int(title_fs * 0.34), self.w - 2 * pad_x - 60)
        self.y += 40
        return self.y

    def save(self):
        h = int(self.y + 120)
        body = "\n".join(self.parts)
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{h}" '
               f'viewBox="0 0 {self.w} {h}">\n'
               f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
               f'<stop offset="0" stop-color="{SKY0}"/><stop offset="1" stop-color="{SKY1}"/>'
               f'</linearGradient></defs>\n'
               f'<rect width="{self.w}" height="{h}" fill="url(#bg)"/>\n{body}\n</svg>')
        os.makedirs(OUT, exist_ok=True)
        p = os.path.join(OUT, self.name)
        open(p, "w", encoding="utf-8").write(svg)
        print("wrote", p, f"({self.w}x{h})")


# =====================================================================
# CONTENT (mirrors kaam-website.html copy)
# =====================================================================
METHODS = [
    ("Method 01", "Field interviews",
     "Conversations with workers at transit hubs and with hirers — canteen managers, households, small contractors — about how a hire actually comes together, step by step."),
    ("Method 02", "Persona building",
     "Field-based and composite profiles of both sides of the market — what they want, what they do today, and where it breaks."),
    ("Method 03", "Empathy & journey maps",
     'Walking the full arc from "I need work / I need workers" to payday — marking every workaround, wait, and moment of doubt.'),
    ("Method 04", "Affinity mapping",
     "Clustering interview notes into themes: discovery, trust, verification, payment, and the last mile — so patterns, not anecdotes, drove the design."),
    ("Method 05", "Competitive analysis",
     "Urban Company, Broomees and others assign anonymous service workers. Kaam is a direct-hire identity platform instead — workers as individuals with portable reputations."),
    ("Method 06", "Cold-start analysis",
     "Mapping how the system earns trust with zero history — who verifies whom first, and what makes the first hire feel safe."),
]
FINDINGS = [
    ("Finding 01", "Hiring runs on referrals — or legwork. There is no reliable channel.",
     '"The only way hiring worked was through referrals — or by manually going and searching in the market." Hirers travel to villages, spread the word, and hope. Some days it works. Some days the canteen runs short-staffed.'),
    ("Finding 02", "Workers are invisible without a phone, network, or English.",
     "Work exists nearby, but discovery runs on word of mouth. No phone, no network, no English — and you are invisible to the market around you."),
    ("Finding 03", "Every hire is a gamble for the hirer.",
     "Strangers, no verification, no track record. Delays in staffing hit service quality directly — and reviews follow. Risk, fear and safety concerns sit underneath every new hire."),
    ("Finding 04", "Money and attendance live on paper and memory.",
     "Khata handled by the hirer or a brother; attendance on a register or in someone's head. When wages are disputed, there is no record to settle it."),
    ("Finding 05", "At the decision point, existing tools turn text-heavy.",
     "Listings collapse into dense text exactly where a worker must decide. The four things workers actually ask — pay, start time, distance, and who else trusts this hirer — are buried or missing."),
]
OBSERVED = [
    ("Observation 01", "The village trip is the hiring pipeline.",
     "Hirers manually travel to nearby villages or send word through contacts. It costs a day, and it still fails often enough that short-staffing is routine."),
    ("Observation 02", "15–20 workers run a mess — managed informally.",
     "A canteen or mess runs on 15–20 workers, more during events and mass crowds. Rosters, khata and wages are handled by the hirer or a family member, on paper or memory."),
    ("Observation 03", "Referrals do two jobs: matchmaking and the last mile.",
     "A referral doesn't just introduce — it tells the worker how to reach the site, what to bring, whom to ask for. Any system that only matches, without carrying that last-mile context, leaves the hardest part unsolved."),
    ("Observation 04", "Voice is the natural input; typing is the barrier.",
     "Speaking a phone number is easy. Tapping it out in English on a touchscreen is not. The mic is a primary input, not an accessory."),
    ("Observation 05", "Public screens change behaviour.",
     "On a shared kiosk, people hesitate to enter personal details where others can watch. Masked numbers, a visible privacy promise, and a session that wipes itself are what make the first tap possible."),
    ("Observation 06", "Trust is borrowed, never assumed.",
     "Nobody trusts a stranger's listing. They trust that someone accountable checked — which is why a badge must always state its source, never hide behind a generic checkmark."),
]
STEPS = [
    ("A shared surface where need meets availability",
     "Instead of two private struggles, one public meeting point: kiosks at bus stands, auto spots and railway stations — exactly where workers already gather and wait."),
    ("Voice and icon first — no English, no typing required",
     "Hindi-first onboarding with Aadhaar scan + voice input. Speak the number or tap the numpad; icons carry the meaning where words would exclude."),
    ("Pay first, then everything else",
     "Job cards lead with the four things workers actually ask: pay per day, start time, distance, and rating — the text-heavy decision point, rebuilt."),
    ("Honest verification",
     'Badges always state their source — "Verified hirer · checked by Kaam" — because trust is borrowed from someone accountable, never assumed.'),
    ("The job survives without a smartphone",
     "Token code + SMS to a basic phone + printable slip. No app to install, no data needed — the loop closes over the technology workers already have."),
    ("The referral's last mile, built in",
     "Requirements and how-to-reach are shown before acceptance — what to bring, whom to ask for, how far it is. The system carries the context a referral used to carry."),
    ("Privacy on a public screen",
     "Masked numbers, a visible privacy promise, session auto-wipe with an inactivity countdown — so the first tap doesn't feel like exposure."),
    ("Skills become visible tags",
     "Sponsored Skill India / PMKVY courses complete into verified skill tags on the worker's profile — cooking, masonry, driving, housekeeping. Reputation stops being only stars; it becomes provable skill."),
    ("Trust with a paper trail",
     "Workers give consent-based self-declaration of no criminal record, linked to the local police station for verification — the same check households already ask for, now with a record. Identity is anchored to e-Shram (Ministry of Labour & Employment), which already covers unorganised and rural workers."),
]
KIOSK_BULLETS = [
    "32″ tilted floor kiosk — 1920×1080, built for arm's-length touch",
    "Voice is a primary input, not an accessory",
    "Category grid with live job counts — no empty-list disappointment",
    "Token + SMS + print slip — no smartphone needed",
    "Session wipes itself; numbers stay masked on a public screen",
]
APP_BULLETS = [
    "Post-a-job flow with kiosk visibility built in",
    "Trust-point shortlisting — reputation, not just availability",
    "Verified worker profiles with bidirectional ratings",
    "Attendance logs that settle wage disputes with a record",
    "Bilingual interface — Hindi and English throughout",
]
DIFFERS = [
    ("Urban Company",
     "A service marketplace: customers book a service, the platform assigns an anonymous partner. Workers need a smartphone, the partner app, training — and pay ~25% commission plus kit and lead costs. Built for metro households."),
    ("Broomees",
     "Organized domestic-help staffing for metros: trained at their centers, booked on subscription. Same trust primitives (Aadhaar, police verification) — but locked inside a metro product the kiosk worker will never open."),
    ("BetterPlace",
     "B2B workforce lifecycle for enterprises — hiring, verification, payroll for companies like Amazon and Flipkart. Serves the employer, not the canteen owner or the small contractor."),
    ("Kaam × RozgaarSetu",
     "Direct hire, not a service. The hirer hires a person, and her reputation travels with her. No degree, no certificate, no smartphone needed — the kiosk meets workers where they already wait, and the worker never pays."),
]
REVENUE = [
    ("Revenue 01", "Hirer placement fee",
     "Posting is free; a small fee lands on a successful hire — or a monthly plan for contractors hiring crew after crew. The hirer pays for a problem removed, not for browsing."),
    ("Revenue 02", "Paid verification add-ons",
     "Police-linked verification and certified skill tags as premium checks, bought by hirers who want extra assurance — safety as a service, not a tax on workers."),
    ("Revenue 03", "Sponsored skill courses",
     "Training partners, NSDC-aligned bodies and CSR funds sponsor Skill India courses. They pay for a pipeline of verified, skilled workers; workers upskill free and hirers see the tags."),
    ("Revenue 04", "Kiosk sponsorship",
     "Kiosks at bus stands and stations carry sponsor branding — CSR money from companies that already spend on skilling and livelihoods, in exchange for visible presence where workers gather."),
]
PERSONAS = [
    ("hirer", "Hirer · field-based", "भ", "Bhagat Singh", "39 · Canteen & mess · Umri, Haryana",
     "Everyday meals and canteen orders served smoothly, no delay — under strict food regulations where compliance is non-negotiable.",
     "Hires 15–20 workers through village word of mouth; travels to villages himself to spread requirements. Khata handled by him or his brother.",
     "Hiring is a gamble — sometimes it works, sometimes the canteen runs short-staffed. New hires are strangers: no verification, no track record.",
     "Verified workers with ratings on his phone; attendance logs that end khata disputes."),
    ("hirer", "Hirer · sample", "मी", "Meera Sharma", "44 · Household employer · South Delhi",
     "Reliable domestic help she can trust inside her home — cooking and cleaning, six days a week.",
     "Asks neighbours, tries agencies that charge a month's salary as commission. Every agency worker quits within weeks; the search restarts.",
     "Safety fears with strangers at home; no way to check a worker's history; agency fees with zero accountability.",
     "Verified profiles with source-stated badges and bidirectional ratings — trust she can inspect, not just hope for."),
    ("hirer", "Hirer · sample", "ब", "Balraj Yadav", "51 · Building contractor · Noida",
     "8–12 site workers on day one of every project — masons, helpers, mixers — without losing a week to assembling a crew.",
     "Hires through mistri referrals and the morning labour chowk. Attendance on a paper register; wages settled in cash on memory.",
     "Workers don't show up and there's no backup list. Wage disputes with no record poison the next project's hiring.",
     "One post reaches kiosks across hotspots; attendance logs both sides can see."),
    ("worker", "Worker · sample", "सु", "Sunita Devi", "38 · Domestic worker · Delhi",
     "Steady monthly work in 3–4 houses — enough to keep her children in school without depending on any single employer.",
     "Finds work through neighbours. No phone of her own — uses her husband's; cannot read English, manages with Hindi and voice notes.",
     "When a house drops her, income stops with no notice. Her years of good work leave no trace — every new house starts at zero trust.",
     "A portable reputation that travels with her; jobs found by voice at a kiosk, confirmed by SMS."),
    ("worker", "Worker · sample", "र", "Ramesh Kumar", "34 · Construction worker · Bihar → Delhi",
     "Daily wages without the daily uncertainty — know the night before whether tomorrow pays.",
     "Gathers at the labour chowk at dawn; waits to be picked. Some days chosen, some days not. Basic keypad phone, no data.",
     "The wait itself is the tax — hours unpaid, every morning. Contractors he's worked for can't find him again when they need him.",
     "Job cards with pay, distance and start time the evening before; a token that holds his place."),
    ("worker", "Worker · sample", "इ", "Imran Sheikh", "27 · Driver / delivery · Delhi",
     "Trade gig fluctuations for one steady monthly driving or delivery job.",
     "Has a basic smartphone but rations mobile data; juggles two gig apps. Asks at auto stands about monthly openings.",
     "Gig ratings don't transfer anywhere — 4.8 stars on an app means nothing to a canteen owner hiring a driver.",
     "One verified identity and portable ratings that any hirer on the system can read."),
]


def persona_card_height(p, cw, fs, h3_fs):
    """Pre-compute card height from wrapped text."""
    _, _, _, name, sub, goal, beh, fru, gives = p
    y = 30 + 26                       # role label + gap
    sub_lines = len(wtext(sub.upper(), 10.5, cw - 150, False))
    y += 74 + max(0, sub_lines - 1) * 15 + 14   # avatar row (+ wrapped sub)
    for label, txt in [("Goal", goal), ("Behaviour & workarounds", beh),
                       ("Frustrations", fru), ("What the system gives", gives)]:
        y += 12 + 20                  # label
        y += len(wtext(txt, fs, cw - 60, False)) * fs * 1.7 + 10
    return y + 24


def render(W, name):
    pg = Page(W, name)
    desktop = W >= 1000
    pad = 120 if desktop else 24
    body = 15 if desktop else 12.5
    h3 = 26 if desktop else 20
    title_fs = 58 if desktop else 34
    gap = 22
    cw = W - 2 * pad  # content width

    # ---------- nav mock ----------
    pg.y = 40
    nw = 640 if desktop else W - 32
    nx = (W - nw) / 2
    pg.rect(nx, pg.y, nw, 64, CARD, STROKE, 32, 0.55)
    pg.text(nx + 30, pg.y + 40, "Kaam × RozgaarSetu", 17, INK, serif=True)
    links = ["Research", "Findings", "Observed", "Gap", "Solution", "Revenue", "Personas"]
    lx = nx + nw - 30
    if desktop:
        for ln in reversed(links):
            pg.text(lx, pg.y + 39, ln, 12.5, INK_SOFT, anchor="end")
            lx -= len(ln) * 8.5 + 26
    pg.y += 64

    # ---------- hero ----------
    pg.y += 110
    cx = W / 2
    pg.rect(cx - 170, pg.y, 340, 46, CARD, STROKE, 23, 0.55)
    pg.text(cx, pg.y + 30, "FINAL RESEARCH COMPILATION", 12, ACCENT_DEEP, anchor="middle", ls=3.4)
    pg.y += 46 + 44
    if desktop:
        for hl in ["The gap was never skill.", "It was connection."]:
            pg.text(cx, pg.y, hl, 96, INK, serif=True, anchor="middle")
            pg.y += 96 * 1.12
    else:
        pg.y = pg.cpara(cx, pg.y, "The gap was never skill. It was connection.", 44, cw, INK, serif=True, lh=1.15)
        pg.y += 12
    pg.y += 18
    sub = ("Kaam × RozgaarSetu — a two-surface hiring system for India's informal workforce. "
           "A Hindi-first worker kiosk meets a hirer-side mobile app, bridging the world of "
           "referrals and the world of non-digital users.")
    # centered sub: wrap then draw centered lines
    lines = wtext(sub, body, 880 if desktop else 330, False)
    for ln in lines:
        pg.text(cx, pg.y, ln, body, INK_SOFT, anchor="middle")
        pg.y += body * 1.75
    pg.y += 22
    chips = ["Role · UI/UX research + prototyping", "Surfaces · kiosk + mobile app",
             "Method · field interviews, personas, journey maps", "Tools · Figma + FigJam"]
    if desktop:
        widths = [len(c) * body * 0.58 + 52 for c in chips]
        rows, cur, curw = [], [], 0
        for c, wch in zip(chips, widths):
            if cur and curw + gap + wch > cw:
                rows.append((cur, curw)); cur, curw = [], 0
            cur.append((c, wch)); curw += (gap if cur else 0) + wch
        if cur:
            rows.append((cur, curw))
        for row, roww in rows:
            x = cx - roww / 2
            for c, wch in row:
                pg.rect(x, pg.y, wch, 44, CARD, STROKE, 14, 0.62)
                pg.text(x + 26, pg.y + 29, c, body, INK_SOFT)
                x += wch + gap
            pg.y += 44 + 14
        pg.y -= 14
    else:
        for c in chips:
            clines = wtext(c, body, cw - 40, False)
            chh = 26 + len(clines) * body * 1.5 + 16
            pg.rect(pad, pg.y, cw, chh, CARD, STROKE, 12, 0.62)
            cy = pg.y + 26 + body * 0.8
            for ln in clines:
                pg.text(pad + 20, cy, ln, body, INK_SOFT)
                cy += body * 1.5
            pg.y += chh + 10
        pg.y -= 10
    pg.y += 44 if desktop else 30
    if desktop:
        bw, bh = 240, 58
        pg.rect(cx - bw - 10, pg.y, bw, bh, ACCENT_DEEP, "none", 29)
        pg.text(cx - bw / 2 - 10, pg.y + 37, "READ THE RESEARCH", 13.5, "#FFFFFF", anchor="middle", ls=1)
        pg.rect(cx + 10, pg.y, bw, bh, CARD, STROKE, 29, 0.5)
        pg.text(cx + bw / 2 + 10, pg.y + 37, "MEET THE PEOPLE", 13.5, ACCENT_DEEP, anchor="middle", ls=1)
        pg.y += bh
    else:
        bw, bh = cw, 54
        pg.rect(pad, pg.y, bw, bh, ACCENT_DEEP, "none", 27)
        pg.text(pad + bw / 2, pg.y + 35, "READ THE RESEARCH", 13, "#FFFFFF", anchor="middle", ls=1)
        pg.y += bh + 12
        pg.rect(pad, pg.y, bw, bh, CARD, STROKE, 27, 0.5)
        pg.text(pad + bw / 2, pg.y + 35, "MEET THE PEOPLE", 13, ACCENT_DEEP, anchor="middle", ls=1)
        pg.y += bh

    # ---------- 01 research ----------
    pg.sec_head("01 — Research", ["How the research was done"],
                "The study stayed close to the ground: the people who hire and the people who wait "
                "for work. Six methods, one goal — understand how hiring actually happens when there "
                "is no platform in the picture.", pad, title_fs)
    cols = 3 if desktop else 1
    colw = (cw - gap * (cols - 1)) / cols
    # compute heights per row
    rows = [METHODS[i:i + cols] for i in range(0, len(METHODS), cols)]
    for row in rows:
        hs = []
        for (tag, t, d) in row:
            h = 30 + 26 + h3 * 1.3 + 10
            h += len(wtext(d, body, colw - 88, False)) * body * 1.7 + 44
            hs.append(h)
        rh = max(hs)
        for j, (tag, t, d) in enumerate(row):
            x = pad + j * (colw + gap)
            pg.glass_card(x, pg.y, colw, rh)
            pg.tag(x + 44, pg.y + 44 + 12, tag)
            y = pg.y + 44 + 12 + 26
            pg.text(x + 44, y, t, h3, INK, serif=True, weight=500)
            y += h3 * 1.3 + 12
            pg.para(x + 44, y, d, body, colw - 88)
        pg.y += rh + gap
    pg.y -= gap

    # ---------- 02 findings ----------
    pg.sec_head("02 — Findings", ["What the research found"],
                "Five findings kept repeating across interviews, on both sides of the market.",
                pad, title_fs)
    idx = len(pg.parts)
    y0 = pg.y
    y = y0 + 44
    for i, (tag, t, d) in enumerate(FINDINGS):
        pg.tag(pad + 44, y, tag)
        y += 26
        pg.text(pad + 44, y, t, h3, INK, serif=True, weight=500)
        # wrap title manually for narrow
        lines = wtext(t, h3, cw - 88, True)
        if len(lines) > 1:
            pg.parts.pop()
            for ln in lines:
                pg.text(pad + 44, y, ln, h3, INK, serif=True, weight=500)
                y += h3 * 1.25
            y += 10
        else:
            y += h3 * 1.25 + 10
        y = pg.para(pad + 44, y, d, body, cw - 88)
        y += 30
        if i < len(FINDINGS) - 1:
            pg.line(pad + 44, y - 8, pad + cw - 44, y - 8, STROKE, 1.5, 0.4)
    card_h = y - y0 + 20
    pg.parts.insert(idx, pg.bg_card(pad, y0, cw, card_h))
    pg.y = y0 + card_h

    # ---------- 03 observed ----------
    pg.sec_head("03 — Observed", ["What was observed through research"],
                "Not opinions — behaviours. The workarounds people have built because nothing better exists.",
                pad, title_fs)
    idx = len(pg.parts)
    y0 = pg.y
    y = y0 + 44
    for i, (tag, t, d) in enumerate(OBSERVED):
        pg.tag(pad + 44, y, tag)
        y += 26
        lines = wtext(t, h3, cw - 88, True)
        for ln in lines:
            pg.text(pad + 44, y, ln, h3, INK, serif=True, weight=500)
            y += h3 * 1.25
        y += 10
        y = pg.para(pad + 44, y, d, body, cw - 88)
        y += 30
        if i < len(OBSERVED) - 1:
            pg.line(pad + 44, y - 8, pad + cw - 44, y - 8, STROKE, 1.5, 0.4)
    card_h = y - y0 + 20
    pg.parts.insert(idx, pg.bg_card(pad, y0, cw, card_h))
    pg.y = y0 + card_h

    # ---------- 04 gap ----------
    pg.sec_head("04 — How the gap was removed", ["From findings to design moves"],
                "Each finding became a decision. Nothing decorative — every move answers something the field said.",
                pad, title_fs)
    idx = len(pg.parts)
    y0 = pg.y
    y = y0 + 44
    for i, (t, d) in enumerate(STEPS):
        pg.circle(pad + 44 + 26, y + 8, 26, ACCENT_DEEP)
        pg.text(pad + 44 + 26, y + 16, str(i + 1), 22, "#FFFFFF", serif=True, anchor="middle")
        tx = pad + 44 + 78
        lines = wtext(t, h3, cw - 88 - 78, True)
        for ln in lines:
            pg.text(tx, y + 10, ln, h3, INK, serif=True, weight=500)
            y += h3 * 1.25
        y += 8
        y = pg.para(tx, y, d, body, cw - 88 - 78)
        y += 26
        if i < len(STEPS) - 1:
            pg.line(pad + 44, y - 6, pad + cw - 44, y - 6, STROKE, 1.5, 0.35)
    card_h = y - y0 + 20
    pg.parts.insert(idx, pg.bg_card(pad, y0, cw, card_h))
    pg.y = y0 + card_h

    # ---------- 05 solution ----------
    pg.sec_head("05 — Final solution", ["Two surfaces, one bridge"],
                "The final system doesn't ask either side to change how they live. It meets workers "
                "where they wait and hirers where they post — and turns referrals into portable, "
                "verifiable reputation.", pad, title_fs)
    cols = 2 if desktop else 1
    colw = (cw - gap * (cols - 1)) / cols
    surfaces = [
        ("Surface 01 · Worker side", "Kaam — the kiosk",
         "A Hindi-first, voice/icon-first touchscreen kiosk for transit hotspots. Walk up, choose a language, register with Aadhaar or a spoken phone number, pick a work category, and see live job cards — pay first, always.",
         KIOSK_BULLETS),
        ("Surface 02 · Hirer side", "RozgaarSetu — the mobile app",
         "The hirer's end of the bridge: post a job once, and it appears on kiosks across hotspots. Shortlist by trust points, hire verified workers, and keep attendance that both sides can see.",
         APP_BULLETS),
    ]
    st_fs0 = 34 if desktop else 26
    srows = [surfaces[i:i + cols] for i in range(0, len(surfaces), cols)]
    for srow in srows:
        hs = []
        for (stag, t, d, bullets) in srow:
            h = 44 + 26
            h += len(wtext(t, st_fs0, colw - 88, True)) * st_fs0 * 1.3 + 14
            h += len(wtext(d, body, colw - 88, False)) * body * 1.7 + 26
            for blt in bullets:
                h += len(wtext(blt, body, colw - 118, False)) * body * 1.7 + 10
            h += 44
            hs.append(h)
        rh = max(hs)
        for j, (stag, t, d, bullets) in enumerate(srow):
            x = pad + j * (colw + gap)
            pg.glass_card(x, pg.y, colw, rh)
            pg.tag(x + 44, pg.y + 56, stag)
            y = pg.y + 56 + 26
            st_fs = 34 if desktop else 26
            for ln in wtext(t, st_fs, colw - 88, True):
                pg.text(x + 44, y, ln, st_fs, INK, serif=True, weight=500)
                y += st_fs * 1.3
            y += 14
            y = pg.para(x + 44, y, d, body, colw - 88)
            y += 18
            for blt in bullets:
                pg.text(x + 44, y, "→", body, ACCENT_DEEP)
                y = pg.para(x + 74, y, blt, body, colw - 118)
                y += 10
        pg.y += rh + gap
    pg.y -= gap

    # bridge quote
    idx = len(pg.parts)
    y0 = pg.y
    y = y0 + 52
    qfs = 34 if desktop else 22
    y = pg.para(pad + 44, y, "Referrals become reputation. Word of mouth becomes a record. "
                "And the worker with no phone, no English and no network is visible to the market at last.",
                qfs, cw - 88, INK, serif=True, lh=1.4)
    y += 16
    if desktop:
        pg.text(pad + 44, y, "THE BRIDGE — WHAT THE TWO SURFACES DO TOGETHER", 11.5, FAINT, ls=2.8)
        y += 52
    else:
        for ln in wtext("THE BRIDGE — WHAT THE TWO SURFACES DO TOGETHER", 10, cw - 88, False):
            pg.text(pad + 44, y, ln, 10, FAINT, ls=1.2)
            y += 16
        y += 36
    pg.parts.insert(idx, pg.bg_card(pad, y0, cw, y - y0))
    pg.y = y

    # institutional layer
    idx = len(pg.parts)
    y0 = pg.y
    y = y0 + 52
    pg.tag(pad + 44, y, "The institutional layer")
    y += 30
    qfs2 = 26 if desktop else 19
    y = pg.para(pad + 44, y, "The system doesn't stand alone — it plugs into the state's existing rails.",
                qfs2, cw - 88, INK, serif=True, lh=1.4)
    y += 30
    inst = [
        ("Identity", "e-Shram · Ministry of Labour & Employment. The national database of unorganised and rural workers becomes the identity anchor — Kaam profiles link to it instead of rebuilding trust from zero."),
        ("Skills", "Skill India / PMKVY courses, sponsored. Training partners sponsor courses; on completion, verified skill tags land on the worker's profile — free upskilling, visible to every hirer."),
        ("Safety", "Consent + local police station. Workers self-declare no criminal record with explicit consent; verification routes through the local police station — the check households already trust, now on record."),
    ]
    icols = 3 if desktop else 1
    icolw = (cw - 88 - gap * (icols - 1)) / icols
    irows = [inst[i:i + icols] for i in range(0, len(inst), icols)]
    ih = 0
    for irow in irows:
        ih = max(ih, max(30 + len(wtext(d, body, icolw - 20, False)) * body * 1.7 for _, d in irow) + 70)
    for irow in irows:
        for j, (t, d) in enumerate(irow):
            x = pad + 44 + j * (icolw + gap)
            pg.tag(x, y, t)
            pg.para(x, y + 30, d, body, icolw - 20)
            if desktop and j < len(irow) - 1:
                pg.line(x + icolw + gap / 2, y - 6, x + icolw + gap / 2, y + ih - 40, STROKE, 1.5, 0.35)
        y += ih
    pg.parts.insert(idx, pg.bg_card(pad, y0, cw, y - y0 + 44))
    pg.y = y + 44

    # differs
    idx = len(pg.parts)
    y0 = pg.y
    y = y0 + 52
    pg.tag(pad + 44, y, "How Kaam differs")
    y += 30
    y = pg.para(pad + 44, y, "Existing platforms digitize workers who are already reachable.",
                qfs2, cw - 88, INK, serif=True, lh=1.4)
    y = pg.para(pad + 44, y, "Kaam reaches workers nobody has digitized yet.",
                qfs2, cw - 88, ACCENT_DEEP, serif=True, lh=1.4, style="italic")
    y += 30
    dcols = 2 if desktop else 1
    dcolw = (cw - 88 - gap * (dcols - 1)) / dcols
    rows = [DIFFERS[i:i + dcols] for i in range(0, len(DIFFERS), dcols)]
    for row in rows:
        rhs = [40 + len(wtext(d, body, dcolw - 20, False)) * body * 1.7 + 30 for _, d in row]
        rhm = max(rhs) + 20
        for j, (t, d) in enumerate(row):
            x = pad + 44 + j * (dcolw + gap)
            pg.tag(x, y, t)
            pg.para(x, y + 30, d, body, dcolw - 20)
        y += rhm + gap
    y -= gap
    pg.parts.insert(idx, pg.bg_card(pad, y0, cw, y - y0 + 44))
    pg.y = y + 44

    # ---------- 06 revenue ----------
    pg.sec_head("06 — Revenue model", ["How it sustains itself"],
                "Money comes from hirers, sponsors, and institutions — the sides with budget.",
                pad, title_fs)
    # rule banner
    bh = 190 if desktop else 260
    pg.rect(pad, pg.y, cw, bh, ACCENT_DEEP, "none", 26)
    pg.tag(pad + 50, pg.y + 52, "The one rule")
    pg.parts[-1] = pg.parts[-1].replace(ACCENT_DEEP + '"', '#9FD4F5"')  # lighten tag text
    qlines = wtext("The worker never pays. Charging daily-wage workers would kill adoption and betray the trust the system is built on.",
                   30 if desktop else 22, cw - 100, True)
    y = pg.y + 52 + 34
    for ln in qlines:
        pg.text(pad + 50, y, ln, 30 if desktop else 22, "#FFFFFF", serif=True)
        y += (30 if desktop else 22) * 1.4
    pg.y += bh + gap
    rcols = 2 if desktop else 1
    rcolw = (cw - gap * (rcols - 1)) / rcols
    rows = [REVENUE[i:i + rcols] for i in range(0, len(REVENUE), rcols)]
    for row in rows:
        hs = []
        for (tag, t, d) in row:
            h = 44 + 26 + h3 * 1.3 + 10 + len(wtext(d, body, rcolw - 88, False)) * body * 1.7 + 44
            hs.append(h)
        rh = max(hs)
        for j, (tag, t, d) in enumerate(row):
            x = pad + j * (rcolw + gap)
            pg.glass_card(x, pg.y, rcolw, rh)
            pg.tag(x + 44, pg.y + 56, tag)
            yy = pg.y + 56 + 26
            pg.text(x + 44, yy, t, h3, INK, serif=True, weight=500)
            yy += h3 * 1.3 + 12
            pg.para(x + 44, yy, d, body, rcolw - 88)
        pg.y += rh + gap
    # institutional quote
    idx = len(pg.parts)
    y0 = pg.y
    y = y0 + 52
    pg.tag(pad + 44, y, "Revenue 05 — Institutional")
    y += 30
    for ln in wtext("Service fees from government partnership — e-Shram onboarding and state labour-department integrations, paid per worker brought into the formal fold.",
                    qfs2, cw - 88, True):
        pg.text(pad + 44, y, ln, qfs2, INK, serif=True)
        y += qfs2 * 1.4
    y += 44
    pg.parts.insert(idx, pg.bg_card(pad, y0, cw, y - y0))
    pg.y = y

    # ---------- 07 personas ----------
    pg.sec_head("07 — Personas", ["The people on both sides"],
                "Three hirers, three workers. Bhagat Singh is field-based; the rest are sample "
                "profiles built from the research patterns.", pad, title_fs)
    pcols = 3 if desktop else 1
    pcolw = (cw - gap * (pcols - 1)) / pcols
    rows = [PERSONAS[i:i + pcols] for i in range(0, len(PERSONAS), pcols)]
    for row in rows:
        hs = [persona_card_height(p, pcolw, body, h3) for p in row]
        rh = max(hs)
        for j, p in enumerate(row):
            role, rlabel, av, name_, sub, goal, beh, fru, gives = p
            x = pad + j * (pcolw + gap)
            pg.glass_card(x, pg.y, pcolw, rh)
            y = pg.y + 30
            lbl_c = ACCENT_DEEP if role == "hirer" else GREEN
            lw = len(rlabel) * (10.5 * 0.6 + 2.4) + 40
            pg.rect(x + 30, y, lw, 30, lbl_c, "none", 15)
            pg.text(x + 30 + 18, y + 20, rlabel.upper(), 10.5, "#FFFFFF", ls=2.4)
            y += 30 + 22
            pg.circle(x + 30 + 32, y + 26, 32, lbl_c)
            pg.text(x + 30 + 32, y + 37, av, 28, "#FFFFFF", serif=True, anchor="middle")
            ny = y + 22
            pg.text(x + 30 + 80, ny, name_, 26 if desktop else 22, INK, serif=True, weight=500)
            ny += 25
            for ln in wtext(sub.upper(), 10.5, pcolw - 150, False):
                pg.text(x + 30 + 80, ny, ln, 10.5, FAINT, ls=1)
                ny += 15
            y += 74 + max(0, len(wtext(sub.upper(), 10.5, pcolw - 150, False)) - 1) * 15 + 6
            for label, txt in [("Goal", goal), ("Behaviour & workarounds", beh),
                               ("Frustrations", fru), ("What the system gives", gives)]:
                y += 14
                pg.text(x + 30, y, label.upper(), 10.5, ACCENT_DEEP, ls=2.4)
                y += 22
                y = pg.para(x + 30, y, txt, body, pcolw - 60)
                y += 6
        pg.y += rh + gap
    pg.y -= gap

    # ---------- footer ----------
    pg.y += 90
    pg.text(cx, pg.y, "Kaam × RozgaarSetu", 40 if desktop else 28, INK, serif=True, anchor="middle")
    pg.y += (40 if desktop else 28) * 1.5 + 10
    pg.y = pg.cpara(cx, pg.y, "Final research compilation · UI/UX", body, cw, INK_SOFT)
    pg.y += 8
    pg.y = pg.cpara(cx, pg.y, "Sample personas are composites built from research patterns; "
                     "Bhagat Singh is field-based.", body, cw, FAINT)
    pg.y += 8

    pg.save()


if __name__ == "__main__":
    render(1440, "website-desktop.svg")
    render(390, "website-mobile.svg")
