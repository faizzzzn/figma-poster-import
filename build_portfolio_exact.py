#!/usr/bin/env python3
"""Exact-detail Figma transfer of Faizan's portfolio website.

Renders portfolio.html (committed next to this script) in headless Chromium,
extracts the REAL rendered layout -- per-line text runs with exact position,
font, size, weight, color, letter-spacing, alignment, plus image rects with
their data-URI sources -- and emits 12 SVGs (main page + 5 case studies x
desktop 1440 / mobile 390) with editable <text> and <image> layers over
flat opaque background rects. NO raster backdrop layer (dropped per
Faizan's request -- it caused a visual glitch in Figma).

Usage:
    python3 build_portfolio_exact.py [--out website_svg_portfolio] [--only 01]

Requires: playwright + Chromium (headless), Pillow (only for QA).
"""
import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
SRC_HTML = HERE / "portfolio.html"

VIEWS = [
    ("01-main-desktop", 1440, 900, None),
    ("02-main-mobile", 390, 844, None),
    ("03-case-silver-gaunt-desktop", 1440, 900, "silver-gaunt"),
    ("04-case-silver-gaunt-mobile", 390, 844, "silver-gaunt"),
    ("05-case-rifle-desktop", 1440, 900, "rifle"),
    ("06-case-rifle-mobile", 390, 844, "rifle"),
    ("07-case-enav-desktop", 1440, 900, "enav"),
    ("08-case-enav-mobile", 390, 844, "enav"),
    ("09-case-underroot-desktop", 1440, 900, "underroot"),
    ("10-case-underroot-mobile", 390, 844, "underroot"),
    ("11-case-hearing-aid-desktop", 1440, 900, "hearing-aid"),
    ("12-case-hearing-aid-mobile", 390, 844, "hearing-aid"),
]

BASE_CSS = """
*,*::before,*::after{animation:none!important;transition:none!important;scroll-behavior:auto!important}
.cursor,.cursor-dot{display:none!important}
.reveal{opacity:1!important;transform:none!important}
canvas{display:none!important}
"""

CASE_CSS = """
.case-window{position:absolute!important;inset:auto!important;top:0!important;left:0!important;
  width:100%!important;height:auto!important;max-height:none!important;overflow:visible!important;
  visibility:visible!important;opacity:1!important;z-index:1!important}
.case-top{position:static!important}
body>*:not(.case-window){display:none!important}
"""

EXTRACT_JS = r"""
() => {
  const CASE = window.__CASE_SLUG__;
  const root = CASE ? document.getElementById('caseWindow') : document.body;
  const out = {texts: [], images: [], bgs: [], W: 0, H: 0, pageBg: '#080808'};

  function rgb2hex(c){
    const m = /rgba?\(([^)]+)\)/.exec(c || '');
    if(!m) return '#000000';
    const p = m[1].split(',').map(s => parseFloat(s));
    const a = p.length > 3 ? p[3] : 1;
    const hex = '#' + p.slice(0,3).map(v =>
      Math.round(Math.min(255, Math.max(0, v))).toString(16).padStart(2,'0')).join('');
    return {hex, alpha: a};
  }
  function csOf(el){ return getComputedStyle(el); }
  function isVis(el){
    const r = el.getBoundingClientRect();
    if(r.width < 0.5 || r.height < 0.5) return false;
    const cs = csOf(el);
    if(cs.display === 'none' || cs.visibility === 'hidden' || cs.visibility === 'collapse') return false;
    if(parseFloat(cs.opacity) === 0) return false;
    return true;
  }

  // ---- page background ----
  let bgc = rgb2hex(csOf(document.body).backgroundColor);
  if(bgc.alpha === 0) bgc = rgb2hex(csOf(document.documentElement).backgroundColor);
  out.pageBg = bgc.hex;
  out.W = CASE ? root.scrollWidth : Math.max(document.documentElement.scrollWidth, window.innerWidth);
  out.H = CASE ? root.scrollHeight : document.documentElement.scrollHeight;

  // ---- canvas probe for exact alphabetic baselines ----
  const probe = document.createElement('canvas').getContext('2d');
  const ascCache = {};
  function ascentFor(ch, font){
    const k = font + '|' + ch;
    if(ascCache[k] !== undefined) return ascCache[k];
    probe.font = font;
    const m = probe.measureText(ch);
    // require real ink: some glyphs (space) report zero boxes
    const ink = (m.actualBoundingBoxLeft || 0) + (m.actualBoundingBoxRight || 0);
    const v = ink > 0.01 ? m.actualBoundingBoxAscent : -1;
    ascCache[k] = v;
    return v;
  }

  function xform(t, tr){
    if(tr === 'uppercase') return t.toUpperCase();
    if(tr === 'lowercase') return t.toLowerCase();
    if(tr === 'capitalize') return t.replace(/(^|\s)\S/g, s => s.toUpperCase());
    return t;
  }

  // ---- text: per text node -> per rendered line ----
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
    acceptNode(n){
      const p = n.parentElement;
      if(!p) return NodeFilter.FILTER_REJECT;
      const tag = p.tagName;
      if(tag === 'SCRIPT' || tag === 'STYLE' || tag === 'NOSCRIPT' || tag === 'TEMPLATE')
        return NodeFilter.FILTER_REJECT;
      if(p.closest('svg')) return NodeFilter.FILTER_REJECT;
      if(!n.textContent || !n.textContent.trim()) return NodeFilter.FILTER_REJECT;
      // skip anything inside a hidden subtree
      let el = p;
      while(el && el !== root){
        const c = csOf(el);
        if(c.display === 'none' || c.visibility === 'hidden' || parseFloat(c.opacity) === 0)
          return NodeFilter.FILTER_REJECT;
        el = el.parentElement;
      }
      return NodeFilter.FILTER_ACCEPT;
    }
  });

  const nodes = [];
  while(walker.nextNode()) nodes.push(walker.currentNode);
  const range = document.createRange();

  for(const node of nodes){
    const pel = node.parentElement;
    const cs = csOf(pel);
    const text = xform(node.textContent, cs.textTransform);
    const fs = parseFloat(cs.fontSize);
    if(!(fs > 0)) continue;
    const font = `${cs.fontStyle} ${cs.fontWeight} ${fs}px ${cs.fontFamily}`;
    // measure per-char rects
    const chars = [];
    for(let i = 0; i < text.length; i++){
      range.setStart(node, i); range.setEnd(node, i + 1);
      const r = range.getBoundingClientRect();
      if(r.width > 0 && r.height > 0)
        chars.push({ch: text[i], x: r.left, y: r.top, w: r.width, h: r.height});
    }
    if(!chars.length) continue;
    // group into lines by y
    chars.sort((a,b) => a.y - b.y);
    const lines = [];
    let cur = [], acc = 0;
    for(const c of chars){
      const mean = cur.length ? acc / cur.length : c.y;
      if(!cur.length || Math.abs(c.y - mean) <= Math.max(2, fs * 0.12)){
        cur.push(c); acc += c.y;
      } else { lines.push(cur); cur = [c]; acc = c.y; }
    }
    if(cur.length) lines.push(cur);

    const col = rgb2hex(cs.color);
    const ls = cs.letterSpacing === 'normal' ? '' : cs.letterSpacing;
    const td = cs.textDecorationLine && cs.textDecorationLine !== 'none'
      ? cs.textDecorationLine.split(' ')[0] : '';
    const style = {
      fontFamily: cs.fontFamily, fontSize: fs, fontWeight: cs.fontWeight,
      fontStyle: cs.fontStyle, fill: col.hex, fillOpacity: col.alpha,
      letterSpacing: ls, textDecoration: td,
      textAlign: cs.textAlign,
    };
    for(const ln of lines){
      ln.sort((a,b) => a.x - b.x);
      const str = ln.map(c => c.ch).join('');
      if(!str.trim()) continue;
      const top = Math.min(...ln.map(c => c.y));
      const left = Math.min(...ln.map(c => c.x));
      const right = Math.max(...ln.map(c => c.x + c.w));
      // exact baseline: median of (charTop + canvas-measured ascent)
      const bases = [];
      for(const c of ln){
        const a = ascentFor(c.ch, font);
        if(a > 0) bases.push(c.y + a);
      }
      bases.sort((a,b) => a - b);
      const baseline = bases.length
        ? bases[Math.floor(bases.length / 2)]
        : top + fs * 0.8;
      let ax = left, anchor = 'start';
      if(style.textAlign === 'center'){ ax = (left + right) / 2; anchor = 'middle'; }
      else if(style.textAlign === 'right' || style.textAlign === 'end'){ ax = right; anchor = 'end'; }
      out.texts.push({x: ax, y: baseline, str, anchor, ...style});
    }
  }

  // ---- images ----
  root.querySelectorAll('img').forEach(img => {
    if(!isVis(img)) return;
    if(!img.complete || img.naturalWidth === 0) return;
    const r = img.getBoundingClientRect();
    if(r.width < 2 || r.height < 2) return;
    const src = img.currentSrc || img.src || '';
    if(!src.startsWith('data:image')){ out.skipped = (out.skipped || 0) + 1; return; }
    out.images.push({x: r.left, y: r.top, w: r.width, h: r.height,
                     src, fit: csOf(img).objectFit || 'fill'});
  });

  // ---- opaque flat backgrounds (clean-edit layer; no raster backdrop) ----
  const seen = [];
  root.querySelectorAll('*').forEach(el => {
    if(!isVis(el)) return;
    const c = rgb2hex(csOf(el).backgroundColor);
    if(c.alpha < 1) return;
    const r = el.getBoundingClientRect();
    if(r.width * r.height < 60000) return;
    seen.push({x: r.left, y: r.top, w: r.width, h: r.height, fill: c.hex,
               area: r.width * r.height});
  });
  seen.sort((a,b) => b.area - a.area);
  const kept = [];
  for(const s of seen){
    const dup = kept.some(k => k.fill === s.fill &&
      s.x >= k.x - 1 && s.y >= k.y - 1 &&
      s.x + s.w <= k.x + k.w + 1 && s.y + s.h <= k.y + k.h + 1);
    if(!dup) kept.push(s);
  }
  out.bgs = kept;
  out.textCount = out.texts.length;
  return out;
}
"""


def log(*a):
    print("[exact]", *a, flush=True)


def fit_to_par(fit):
    if fit == "cover":
        return "xMidYMid slice"
    if fit == "contain":
        return "xMidYMid meet"
    return "none"


def build_svg(name, W, H, page_bg, bgs, images, texts):
    p = []
    A = p.append
    A('<?xml version="1.0" encoding="UTF-8"?>')
    A(f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
      f'width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
    A(f'<title>{escape(name)}</title>')
    # 1. flat backgrounds (clean-edit layer; full-artboard rect guarantees
    #    nothing transparent shows through)
    A('<g id="flat-backgrounds">')
    A(f'<rect x="0" y="0" width="{W}" height="{H}" fill="{page_bg}"/>')
    for b in bgs:
        A(f'<rect x="{b["x"]:.1f}" y="{b["y"]:.1f}" width="{b["w"]:.1f}" height="{b["h"]:.1f}" '
          f'fill="{b["fill"]}"/>')
    A('</g>')
    # 2. images (editable, unaltered sources at exact rects)
    A('<g id="images">')
    for im in images:
        par = fit_to_par(im["fit"])
        A(f'<image x="{im["x"]:.1f}" y="{im["y"]:.1f}" width="{im["w"]:.1f}" height="{im["h"]:.1f}" '
          f'preserveAspectRatio="{par}" xlink:href="{im["src"]}"/>')
    A('</g>')
    # 4. text (editable)
    A('<g id="text">')
    for t in texts:
        attrs = [f'x="{t["x"]:.1f}"', f'y="{t["y"]:.1f}"',
                 f'font-family="{escape(t["fontFamily"], {"\"": "&quot;"})}"',
                 f'font-size="{t["fontSize"]:.1f}"',
                 f'font-weight="{escape(str(t["fontWeight"]))}"',
                 f'fill="{t["fill"]}"']
        if t["fontStyle"] and t["fontStyle"] != "normal":
            attrs.append(f'font-style="{t["fontStyle"]}"')
        if t.get("letterSpacing"):
            attrs.append(f'letter-spacing="{escape(t["letterSpacing"])}"')
        if t["anchor"] != "start":
            attrs.append(f'text-anchor="{t["anchor"]}"')
        if t.get("textDecoration"):
            attrs.append(f'text-decoration="{t["textDecoration"]}"')
        if t.get("fillOpacity") is not None and abs(t["fillOpacity"] - 1.0) > 0.01:
            attrs.append(f'fill-opacity="{t["fillOpacity"]:.2f}"')
        A(f'<text {" ".join(attrs)}>{escape(t["str"])}</text>')
    A('</g>')
    A('</svg>')
    return "".join(p)


def _launch_kwargs():
    """Prefer a local Chromium binary when present (sandbox), else Playwright's."""
    import os as _os
    for cand in (_os.environ.get("PLAYWRIGHT_CHROMIUM_PATH", ""),
                 "/opt/meta-chromium/chrome"):
        if cand and Path(cand).exists():
            return {"executable_path": cand,
                    "args": ["--no-sandbox", "--disable-dev-shm-usage"]}
    return {}


def capture_view(pw, name, vw, vh, slug, out_dir):
    browser = pw.chromium.launch(headless=True, **_launch_kwargs())
    try:
        page = browser.new_page(viewport={"width": vw, "height": vh},
                                device_scale_factor=1)
        url = SRC_HTML.as_uri() + (f"#case-{slug}" if slug else "")
        log(f"{name}: loading {url[:80]}...")
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(1200)
        # kill motion, hide cursor dot, force reveals visible
        page.add_style_tag(content=BASE_CSS + (CASE_CSS if slug else ""))
        page.evaluate("document.querySelectorAll('.reveal').forEach(e=>e.classList.add('in'))")
        if slug:
            page.evaluate("window.__CASE_SLUG__ = " + json.dumps(slug))
            # ensure case window opened via hash
            page.wait_for_selector("#caseWindow.open", timeout=15000)
        else:
            page.evaluate("window.__CASE_SLUG__ = null")
        # scroll through to trigger lazy images (sweep + per-image pin)
        page.evaluate("""async () => {
          const h = document.documentElement.scrollHeight;
          const vh = window.innerHeight;
          for(let y = 0; y < h; y += Math.floor(vh * 0.8)){
            window.scrollTo(0, y);
            await new Promise(r => setTimeout(r, 90));
          }
          const imgs = Array.from(document.images);
          for(const im of imgs){
            try{ im.loading = 'eager'; }catch(e){}
            if(im.complete && im.naturalWidth > 0) continue;
            im.scrollIntoView({block: 'center'});
            await new Promise(r => setTimeout(r, 140));
          }
          window.scrollTo(0, 0);
        }""")
        page.wait_for_timeout(800)
        # wait for images + fonts
        page.evaluate("document.fonts.ready.then(()=>1)")
        try:
            page.wait_for_function(
                "() => Array.from(document.images).every(i => i.complete)",
                timeout=30000)
        except Exception:
            log(f"{name}: WARNING some images not complete")
        page.wait_for_timeout(500)
        page.evaluate("window.scrollTo(0,0)")
        page.wait_for_timeout(300)

        data = page.evaluate(EXTRACT_JS)
        W, H = int(round(data["W"])), int(round(data["H"]))
        log(f"{name}: W={W} H={H} texts={len(data['texts'])} "
            f"images={len(data['images'])} bgs={len(data['bgs'])} "
            f"skipped_imgs={data.get('skipped', 0)}")

        # no raster backdrop: flat backgrounds + images + text only
        svg = build_svg(name, W, H, data["pageBg"], data["bgs"],
                        data["images"], data["texts"])
        dest = out_dir / f"{name}.svg"
        dest.write_text(svg, encoding="utf-8")
        log(f"{name}: wrote {len(svg)//1024}KB -> {dest.name}")
        return len(svg)
    finally:
        browser.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="website_svg_portfolio")
    ap.add_argument("--only", default=None,
                    help="only capture views whose name contains this string")
    args = ap.parse_args()
    if not SRC_HTML.exists():
        log(f"FATAL: source not found: {SRC_HTML}")
        sys.exit(2)
    out_dir = Path(args.out) if os.path.isabs(args.out) else HERE / args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    views = [v for v in VIEWS if not args.only or args.only in v[0]]
    log(f"{len(views)} views -> {out_dir}")

    from playwright.sync_api import sync_playwright
    t0 = time.time()
    with sync_playwright() as pw:
        for name, vw, vh, slug in views:
            try:
                capture_view(pw, name, vw, vh, slug, out_dir)
            except Exception as e:
                log(f"{name}: FAILED: {e}")
    log(f"done in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
