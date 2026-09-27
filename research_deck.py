#!/usr/bin/env python3
"""Generate the Kaam x RozgaarSetu final research deck as editable SVGs.

One SVG per section (artboard). Text stays real <text> so Figma imports it as
editable layers. Run: python3 research_deck.py  ->  research_svg/*.svg
"""
import os
from xml.sax.saxutils import escape

OUT = "research_svg"

# ---------- palette ----------
SKY0, SKY1 = "#F4FAFF", "#D8EBFB"
INK, SOFT, FAINT = "#0B2E4E", "#2C5A80", "#5E87A8"
ACCENT, DEEP = "#2E9BE6", "#14608F"
CARD, CARD_STROKE = "rgba(255,255,255,0.72)", "#82B9E6"
SERIF = "Fraunces, Georgia, serif"
MONO = "IBM Plex Mono, monospace"

def wtext(text, font_size, max_w, mono=True):
    """Greedy word wrap -> list of lines. Width estimate per char."""
    cw = font_size * (0.60 if mono else 0.50)
    words, lines, cur = text.split(), [], ""
    for wd in words:
        trial = (cur + " " + wd).strip()
        if len(trial) * cw <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur); cur = wd
    if cur: lines.append(cur)
    return lines

class Board:
    def __init__(self, w, h, name):
        self.w, self.h, self.name = w, h, name
        self.parts = []
    def add(self, s): self.parts.append(s)
    def bg(self):
        self.add(f'''<defs><linearGradient id="bg{name_id(self.name)}" x1="0" y1="0" x2="0" y2="1">
<stop offset="0" stop-color="{SKY0}"/><stop offset="1" stop-color="{SKY1}"/></linearGradient></defs>''')
        self.add(f'<rect width="{self.w}" height="{self.h}" fill="url(#bg{name_id(self.name)})"/>')
    def pill(self, x, y, text, fs=20):
        tw = len(text) * fs * 0.62 + 56
        self.add(f'<rect x="{x}" y="{y}" width="{tw:.0f}" height="{fs+28}" rx="{(fs+28)/2}" fill="rgba(255,255,255,0.6)" stroke="{CARD_STROKE}" stroke-width="1.5"/>')
        self.add(f'<text x="{x+28}" y="{y + fs + 8}" font-family="{MONO}" font-size="{fs}" letter-spacing="4" fill="{DEEP}">{escape(text.upper())}</text>')
    def sec_head(self, no, title, lede=None, y=110):
        self.pill(90, y, no); y += 92
        for i, ln in enumerate(wtext(title, 64, self.w - 220, mono=False)):
            self.add(f'<text x="90" y="{y + i*74}" font-family="{SERIF}" font-size="64" fill="{INK}">{escape(ln)}</text>')
        y += len(wtext(title, 64, self.w - 220, mono=False)) * 74 + 18
        if lede:
            for i, ln in enumerate(wtext(lede, 25, self.w - 260)):
                self.add(f'<text x="90" y="{y + i*38}" font-family="{MONO}" font-size="25" fill="{SOFT}">{escape(ln)}</text>')
            y += len(wtext(lede, 25, self.w - 260)) * 38 + 30
        return y + 20
    def card(self, x, y, w, h, r=26):
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{CARD}" stroke="{CARD_STROKE}" stroke-width="1.5"/>')
    def tag(self, x, y, text, fs=17):
        self.add(f'<text x="{x}" y="{y}" font-family="{MONO}" font-size="{fs}" letter-spacing="3.5" fill="{DEEP}">{escape(text.upper())}</text>')
    def para(self, x, y, text, fs, max_w, fill, lh=None, serif=False, bold_first=False):
        lh = lh or fs * 1.5
        fam = SERIF if serif else MONO
        fam_attr = f'font-family="{fam}"'
        for i, ln in enumerate(wtext(text, fs, max_w, mono=not serif)):
            self.add(f'<text x="{x}" y="{y + i*lh}" {fam_attr} font-size="{fs}" fill="{fill}">{escape(ln)}</text>')
        return y + len(wtext(text, fs, max_w, mono=not serif)) * lh
    def save(self):
        os.makedirs(OUT, exist_ok=True)
        body = "\n".join(self.parts)
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
               f'viewBox="0 0 {self.w} {self.h}">{body}</svg>')
        p = os.path.join(OUT, self.name)
        open(p, "w", encoding="utf-8").write(svg)
        print("wrote", p, len(svg), "chars")

def name_id(n): return "".join(c for c in n if c.isalnum())

W = 1440

# ================= 01 COVER =================
b = Board(W, 900, "01-cover.svg"); b.bg()
b.pill(90, 120, "Final research compilation")
y = 300
for i, ln in enumerate(["The gap was never skill.", "It was connection."]):
    b.add(f'<text x="90" y="{y + i*110}" font-family="{SERIF}" font-size="96" fill="{INK}">{escape(ln)}</text>')
b.para(92, y + 2*110 + 10, "Kaam \u00d7 RozgaarSetu \u2014 a two-surface hiring system for India\u2019s informal workforce. A Hindi-first worker kiosk meets a hirer-side mobile app, bridging the world of referrals and the world of non-digital users.", 26, W-260, SOFT)
chips = ["Role \u00b7 UI/UX research + prototyping", "Surfaces \u00b7 kiosk + mobile app", "Method \u00b7 field interviews, personas, journey maps", "Tools \u00b7 Figma + FigJam"]
cx = 92
for c in chips:
    tw = len(c) * 20 * 0.60 + 44
    if cx + tw > W - 90: break
    b.add(f'<rect x="{cx}" y="760" width="{tw:.0f}" height="56" rx="16" fill="{CARD}" stroke="{CARD_STROKE}" stroke-width="1.5"/>')
    b.add(f'<text x="{cx+22}" y="795" font-family="{MONO}" font-size="20" fill="{SOFT}">{escape(c)}</text>')
    cx += tw + 18
b.save()

# ================= 02 RESEARCH METHODS =================
b = Board(W, 1180, "02-research.svg"); b.bg()
y = b.sec_head("01 \u2014 Research", "How the research was done",
    "Six methods, one goal \u2014 understand how hiring actually happens when there is no platform in the picture.", y=90)
methods = [
    ("Field interviews", "Conversations with workers at transit hubs and with hirers \u2014 canteen managers, households, small contractors \u2014 about how a hire actually comes together, step by step."),
    ("Persona building", "Field-based and composite profiles of both sides of the market \u2014 what they want, what they do today, and where it breaks."),
    ("Empathy & journey maps", "Walking the full arc from \u201cI need work / I need workers\u201d to payday \u2014 marking every workaround, wait, and moment of doubt."),
    ("Affinity mapping", "Clustering interview notes into themes: discovery, trust, verification, payment, and the last mile \u2014 so patterns, not anecdotes, drove the design."),
    ("Competitive analysis", "Urban Company and Broomees assign anonymous service workers. Kaam is a direct-hire identity platform instead \u2014 workers as individuals with portable reputations."),
    ("Cold-start analysis", "Mapping how the system earns trust with zero history \u2014 who verifies whom first, and what makes the first hire feel safe."),
]
cw, chh, gx, gy = 400, 300, 40, 36
for i, (t, d) in enumerate(methods):
    x = 90 + (i % 3) * (cw + gx); yy = y + (i // 3) * (chh + gy)
    b.card(x, yy, cw, chh)
    b.tag(x + 28, yy + 52, f"Method 0{i+1}")
    b.add(f'<text x="{x+28}" y="{yy+100}" font-family="{SERIF}" font-size="34" fill="{INK}">{escape(t)}</text>')
    b.para(x + 28, yy + 142, d, 20, cw - 56, SOFT)
b.save()

# ================= 03 FINDINGS =================
b = Board(W, 1560, "03-findings.svg"); b.bg()
y = b.sec_head("02 \u2014 Findings", "What the research found",
    "Five findings kept repeating across interviews, on both sides of the market.", y=90)
findings = [
    ("Hiring runs on referrals \u2014 or legwork. There is no reliable channel.",
     "\u201cThe only way hiring worked was through referrals \u2014 or by manually going and searching in the market.\u201d Hirers travel to villages, spread the word, and hope. Some days it works. Some days the canteen runs short-staffed."),
    ("Workers are invisible without a phone, network, or English.",
     "Work exists nearby, but discovery runs on word of mouth. No phone, no network, no English \u2014 and you are invisible to the market around you."),
    ("Every hire is a gamble for the hirer.",
     "Strangers, no verification, no track record. Delays in staffing hit service quality directly \u2014 and reviews follow. Risk, fear and safety concerns sit underneath every new hire."),
    ("Money and attendance live on paper and memory.",
     "Khata handled by the hirer or a brother; attendance on a register or in someone\u2019s head. When wages are disputed, there is no record to settle it."),
    ("At the decision point, existing tools turn text-heavy.",
     "Listings collapse into dense text exactly where a worker must decide. The four things workers actually ask \u2014 pay, start time, distance, and who else trusts this hirer \u2014 are buried or missing."),
]
for i, (t, d) in enumerate(findings):
    hh = 200
    b.card(90, y, W - 180, hh)
    b.add(f'<rect x="90" y="{y}" width="10" height="{hh}" fill="{ACCENT}"/>')
    b.tag(130, y + 52, f"Finding 0{i+1}")
    yy = b.para(130, y + 92, t, 27, W - 300, INK, serif=True)
    b.para(130, yy + 14, d, 20, W - 300, SOFT)
    y += hh + 30
b.save()

# ================= 04 OBSERVED =================
b = Board(W, 1640, "04-observed.svg"); b.bg()
y = b.sec_head("03 \u2014 Observed", "What was observed through research",
    "Not opinions \u2014 behaviours. The workarounds people have built because nothing better exists.", y=90)
obs = [
    ("The village trip is the hiring pipeline.", "Hirers manually travel to nearby villages or send word through contacts. It costs a day, and it still fails often enough that short-staffing is routine."),
    ("15\u201320 workers run a mess \u2014 managed informally.", "A canteen or mess runs on 15\u201320 workers, more during events and mass crowds. Rosters, khata and wages are handled by the hirer or a family member, on paper or memory."),
    ("Referrals do two jobs: matchmaking and the last mile.", "A referral doesn\u2019t just introduce \u2014 it tells the worker how to reach the site, what to bring, whom to ask for. Any system that only matches, without carrying that last-mile context, leaves the hardest part unsolved."),
    ("Voice is the natural input; typing is the barrier.", "Speaking a phone number is easy. Tapping it out in English on a touchscreen is not. The mic is a primary input, not an accessory."),
    ("Public screens change behaviour.", "On a shared kiosk, people hesitate to enter personal details where others can watch. Masked numbers, a visible privacy promise, and a session that wipes itself are what make the first tap possible."),
    ("Trust is borrowed, never assumed.", "Nobody trusts a stranger\u2019s listing. They trust that someone accountable checked \u2014 which is why a badge must always state its source, never hide behind a generic checkmark."),
]
for i, (t, d) in enumerate(obs):
    hh = 196
    b.card(90, y, W - 180, hh)
    b.add(f'<rect x="90" y="{y}" width="10" height="{hh}" fill="{ACCENT}"/>')
    b.tag(130, y + 50, f"Observation 0{i+1}")
    yy = b.para(130, y + 90, t, 26, W - 300, INK, serif=True)
    b.para(130, yy + 12, d, 20, W - 300, SOFT)
    y += hh + 28
b.save()

# ================= 05 GAP REMOVED =================
b = Board(W, 1780, "05-gap-removed.svg"); b.bg()
y = b.sec_head("04 \u2014 How the gap was removed", "From findings to design moves",
    "Each finding became a decision. Nothing decorative \u2014 every move answers something the field said.", y=90)
steps = [
    ("A shared surface where need meets availability", "Instead of two private struggles, one public meeting point: kiosks at bus stands, auto spots and railway stations \u2014 exactly where workers already gather and wait."),
    ("Voice and icon first \u2014 no English, no typing required", "Hindi-first onboarding with Aadhaar scan + voice input. Speak the number or tap the numpad; icons carry the meaning where words would exclude."),
    ("Pay first, then everything else", "Job cards lead with the four things workers actually ask: pay per day, start time, distance, and rating \u2014 the text-heavy decision point, rebuilt."),
    ("Honest verification", "Badges always state their source \u2014 \u201cVerified hirer \u00b7 checked by Kaam\u201d \u2014 because trust is borrowed from someone accountable, never assumed."),
    ("The job survives without a smartphone", "Token code + SMS to a basic phone + printable slip. No app to install, no data needed \u2014 the loop closes over the technology workers already have."),
    ("The referral\u2019s last mile, built in", "Requirements and how-to-reach are shown before acceptance \u2014 what to bring, whom to ask for, how far it is. The system carries the context a referral used to carry."),
    ("Privacy on a public screen", "Masked numbers, a visible privacy promise, session auto-wipe with an inactivity countdown \u2014 so the first tap doesn\u2019t feel like exposure."),
]
for i, (t, d) in enumerate(steps):
    hh = 178
    b.card(90, y, W - 180, hh)
    b.add(f'<circle cx="140" cy="{y+62}" r="26" fill="{DEEP}"/>')
    b.add(f'<text x="140" y="{y+71}" font-family="{SERIF}" font-size="26" fill="#FFFFFF" text-anchor="middle">{i+1}</text>')
    yy = b.para(190, y + 72, t, 27, W - 360, INK, serif=True)
    b.para(190, yy + 12, d, 20, W - 360, SOFT)
    y += hh + 26
b.save()

# ================= 06 SOLUTION =================
b = Board(W, 1500, "06-solution.svg"); b.bg()
y = b.sec_head("05 \u2014 Final solution", "Two surfaces, one bridge",
    "The system doesn\u2019t ask either side to change how they live. It meets workers where they wait and hirers where they post \u2014 and turns referrals into portable, verifiable reputation.", y=90)
b.card(90, y, 610, 560); b.card(740, y, 610, 560)
for (x, tagt, title, desc, bullets) in [
    (90, "Surface 01 \u00b7 Worker side", "Kaam \u2014 the kiosk",
     "A Hindi-first, voice/icon-first touchscreen kiosk for transit hotspots. Walk up, choose a language, register with Aadhaar or a spoken phone number, pick a work category, and see live job cards \u2014 pay first, always.",
     ["32\u2033 tilted floor kiosk \u2014 1920\u00d71080, built for arm\u2019s-length touch", "Voice is a primary input, not an accessory", "Category grid with live job counts", "Token + SMS + print slip \u2014 no smartphone needed", "Session wipes itself; numbers stay masked"]),
    (740, "Surface 02 \u00b7 Hirer side", "RozgaarSetu \u2014 the mobile app",
     "The hirer\u2019s end of the bridge: post a job once, and it appears on kiosks across hotspots. Shortlist by trust points, hire verified workers, keep attendance both sides can see.",
     ["Post-a-job flow with kiosk visibility built in", "Trust-point shortlisting \u2014 reputation, not just availability", "Verified worker profiles with bidirectional ratings", "Attendance logs that settle wage disputes", "Bilingual interface \u2014 Hindi and English"]),
]:
    b.tag(x + 34, y + 54, tagt)
    b.add(f'<text x="{x+34}" y="{y+108}" font-family="{SERIF}" font-size="42" fill="{INK}">{escape(title)}</text>')
    yy = b.para(x + 34, y + 152, desc, 20, 610 - 68, SOFT)
    for bl in bullets:
        yy += 34
        b.add(f'<text x="{x+34}" y="{yy}" font-family="{MONO}" font-size="19" fill="{DEEP}">\u2192</text>')
        b.para(x + 62, yy, bl, 19, 610 - 110, SOFT)
y += 600
b.card(90, y, W - 180, 250)
b.para(130, y + 100, "Referrals become reputation. Word of mouth becomes a record. And the worker with no phone, no English and no network is visible to the market at last.", 34, W - 340, INK, serif=True)
b.tag(130, y + 208, "The bridge \u2014 what the two surfaces do together")
b.save()

# ================= 07 PERSONAS =================
b = Board(W, 2080, "07-personas.svg"); b.bg()
y = b.sec_head("06 \u2014 Personas", "The people on both sides",
    "Three hirers, three workers. Bhagat Singh is field-based; the rest are sample profiles built from the research patterns.", y=90)
personas = [
    ("hirer", "Hirer \u00b7 field-based", "\u092d", "Bhagat Singh", "39 \u00b7 Canteen & mess \u00b7 Umri, Haryana",
     "Everyday meals and canteen orders served smoothly, no delay \u2014 under strict food regulations.",
     "Hires 15\u201320 workers through village word of mouth; travels to villages himself. Khata by him or his brother.",
     "Hiring is a gamble \u2014 sometimes the canteen runs short-staffed. New hires are strangers: no verification.",
     "Verified workers with ratings on his phone; attendance logs that end khata disputes."),
    ("hirer", "Hirer \u00b7 sample", "\u092e\u0940", "Meera Sharma", "44 \u00b7 Household employer \u00b7 South Delhi",
     "Reliable domestic help she can trust inside her home, six days a week.",
     "Asks neighbours; tries agencies that charge a month\u2019s salary as commission. Every agency worker quits within weeks.",
     "Safety fears with strangers at home; no way to check a worker\u2019s history; agency fees, zero accountability.",
     "Verified profiles with source-stated badges and bidirectional ratings."),
    ("hirer", "Hirer \u00b7 sample", "\u092c", "Balraj Yadav", "51 \u00b7 Building contractor \u00b7 Noida",
     "8\u201312 site workers on day one of every project \u2014 without losing a week assembling a crew.",
     "Hires through mistri referrals and the morning labour chowk. Attendance on a paper register; cash on memory.",
     "Workers don\u2019t show up, no backup list. Wage disputes with no record poison the next project\u2019s hiring.",
     "One post reaches kiosks across hotspots; attendance logs both sides can see."),
    ("worker", "Worker \u00b7 sample", "\u0938\u0941", "Sunita Devi", "38 \u00b7 Domestic worker \u00b7 Delhi",
     "Steady monthly work in 3\u20134 houses \u2014 enough to keep her children in school.",
     "Finds work through neighbours. No phone of her own \u2014 uses her husband\u2019s; Hindi and voice notes only.",
     "When a house drops her, income stops with no notice. Years of good work leave no trace.",
     "A portable reputation that travels with her; jobs by voice at a kiosk, confirmed by SMS."),
    ("worker", "Worker \u00b7 sample", "\u0930", "Ramesh Kumar", "34 \u00b7 Construction worker \u00b7 Bihar \u2192 Delhi",
     "Daily wages without the daily uncertainty \u2014 know the night before whether tomorrow pays.",
     "Gathers at the labour chowk at dawn; waits to be picked. Basic keypad phone, no data.",
     "The wait itself is the tax \u2014 hours unpaid, every morning. Past contractors can\u2019t find him again.",
     "Job cards with pay, distance and start time the evening before; a token that holds his place."),
    ("worker", "Worker \u00b7 sample", "\u0907", "Imran Sheikh", "27 \u00b7 Driver / delivery \u00b7 Delhi",
     "Trade gig fluctuations for one steady monthly driving or delivery job.",
     "Basic smartphone but rations mobile data; juggles two gig apps. Asks at auto stands about openings.",
     "Gig ratings don\u2019t transfer \u2014 4.8 stars on an app means nothing to a canteen owner hiring a driver.",
     "One verified identity and portable ratings any hirer on the system can read."),
]
cw, chh, gx, gy = 400, 830, 40, 36
for i, (role, rl, ini, name, sub, goal, beh, fru, sys) in enumerate(personas):
    x = 90 + (i % 3) * (cw + gx); yy = y + (i // 3) * (chh + gy)
    b.card(x, yy, cw, chh)
    b.tag(x + 28, yy + 48, rl)
    b.add(f'<circle cx="{x+62}" cy="{yy+108}" r="34" fill="{ACCENT if role=="hirer" else "#2D9C6E"}"/>')
    b.add(f'<text x="{x+62}" y="{yy+122}" font-family="{SERIF}" font-size="36" fill="#FFFFFF" text-anchor="middle">{ini}</text>')
    b.add(f'<text x="{x+112}" y="{yy+104}" font-family="{SERIF}" font-size="32" fill="{INK}">{escape(name)}</text>')
    b.add(f'<text x="{x+112}" y="{yy+132}" font-family="{MONO}" font-size="15" fill="{FAINT}">{escape(sub.upper())}</text>')
    py = yy + 180
    for sec, txt in [("Goal", goal), ("Behaviour", beh), ("Frustration", fru), ("What the system gives", sys)]:
        b.tag(x + 28, py, sec, fs=14); py += 30
        py = b.para(x + 28, py, txt, 18, cw - 56, SOFT) + 22
b.save()
print("done:", OUT)
