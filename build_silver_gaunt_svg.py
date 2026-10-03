#!/usr/bin/env python3
"""Exact-detail Figma transfer of Faizan's Silver Gaunt compilation.

Renders silver-gaunt-compilation.html (committed next to this script,
images in silver-gaunt-images/) in headless Chromium, extracts the REAL
rendered layout -- per-line text runs with exact position, font, size,
weight, color, letter-spacing, alignment, plus image rects with data-URI
sources -- and emits 6 SVGs (cover + 5 chapters) at 1440px wide with
editable <text> and <image> layers over flat opaque background rects.
NO raster backdrop layer (per Faizan's standing request).

Artboard isolation: the page is reloaded once per artboard with CSS that
hides everything except the target (section.hero, or one
article.case-chapter). The fixed topbar is hidden on all artboards; the
footer rides along on the last artboard only. Scroll-reveal elements are
forced visible for capture.

Images are inlined as data URIs into a temp copy of the HTML before
rendering, because the extractor only accepts data:image sources.

Usage:
    python3 build_silver_gaunt_svg.py [--out website_svg_silver_gaunt] [--only 03]

Requires: playwright + Chromium (headless).
"""
import argparse
import base64
import mimetypes
import os
import re
import time
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
SRC_HTML = HERE / "silver-gaunt-compilation.html"
IMG_DIR = HERE / "silver-gaunt-images"

# (svg name, kind, chapter index for :nth-of-type; kind 'cover' = hero)
VIEWS = [
    ("00-silver-gaunt-cover", "cover", None),
    ("01-chapter-01-inspiration", "chapter", 1),
    ("02-chapter-02-joints", "chapter", 2),
    ("03-chapter-03-finger-set", "chapter", 3),
    ("04-chapter-04-glove", "chapter", 4),
    ("05-chapter-05-final", "chapter", 5),
]

BASE_CSS = """
*,*::before,*::after{animation:none!important;transition:none!important;scroll-behavior:auto!important}
header.topbar{display:none!important}
.reveal{opacity:1!important;transform:none!important}
"""

COVER_CSS = """
.case-shell{display:none!important}
footer.site-foot{display:none!important}
"""


def chapter_css(k, last):
    css = f"""
section.hero{{display:none!important}}
.case-shell{{display:block!important}}
aside.case-rail{{display:none!important}}
main.case-main>article.case-chapter{{display:none!important}}
main.case-main>article.case-chapter:nth-of-type({k}){{display:block!important}}
"""
    if not last:
        css += "footer.site-foot{display:none!important}\n"
    return css


EXTRACT_JS = r"""
() => {
  const root = document.body;
  const out = {texts: [], images: [], bgs: [], W: 0, H: 0, pageBg: '#ffffff'};

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

  let bgc = rgb2hex(csOf(document.body).backgroundColor);
  if(bgc.alpha === 0) bgc = rgb2hex(csOf(document.documentElement).backgroundColor);
  out.pageBg = bgc.hex;
  out.W = Math.max(root.scrollWidth, window.innerWidth);
  out.H = root.scrollHeight;

  const probe = document.createElement('canvas').getContext('2d');
  const ascCache = {};
  function ascentFor(ch, font){
    const k = font + '|' + ch;
    if(ascCache[k] !== undefined) return ascCache[k];
    probe.font = font;
    const m = probe.measureText(ch);
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

  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
    acceptNode(n){
      const p = n.parentElement;
      if(!p) return NodeFilter.FILTER_REJECT;
      const tag = p.tagName;
      if(tag === 'SCRIPT' || tag === 'STYLE' || tag === 'NOSCRIPT' || tag === 'TEMPLATE')
        return NodeFilter.FILTER_REJECT;
      if(p.closest('svg')) return NodeFilter.FILTER_REJECT;
      if(p.closest('canvas')) return NodeFilter.FILTER_REJECT;
      if(!n.textContent || !n.textContent.trim()) return NodeFilter.FILTER_REJECT;
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
    const chars = [];
    for(let i = 0; i < text.length; i++){
      range.setStart(node, i); range.setEnd(node, i + 1);
      const r = range.getBoundingClientRect();
      if(r.width > 0 && r.height > 0)
        chars.push({ch: text[i], x: r.left, y: r.top, w: r.width, h: r.height});
    }
    if(!chars.length) continue;
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

  root.querySelectorAll('img').forEach(img => {
    if(!isVis(img)) return;
    if(!img.complete || img.naturalWidth === 0) return;
    const r = img.getBoundingClientRect();
    if(r.width < 2 || r.height < 2) return;
    const src = img.currentSrc || img.src || '';
    if(!src.startsWith('data:image')){ out.skipped = (out.skipped || 0) + 1; return; }
    out.images.push({x: r.left, y: r.top, w: r.width, h: r.height,
                     nw: img.naturalWidth, nh: img.naturalHeight,
                     src, fit: csOf(img).objectFit || 'fill'});
  });

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
  return out;
}
"""


def log(*a):
    print("[gaunt-exact]", *a, flush=True)


def inline_images(html, img_dir):
    """Replace src="assets/..." with data URIs. Returns (html, count)."""
    count = 0

    def repl(m):
        nonlocal count
        rel = m.group(1)
        p = img_dir / rel
        if not p.exists():
            log(f"WARNING: image not found: {p}")
            return m.group(0)
        mime = mimetypes.guess_type(str(p))[0] or "image/jpeg"
        data = base64.b64encode(p.read_bytes()).decode("ascii")
        count += 1
        return f'src="data:{mime};base64,{data}"'

    html = re.sub(r'src="assets/([^"]+)"', repl, html)
    return html, count


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
      f'xml:space="preserve" '
      f'width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
    A(f'<title>{escape(name)}</title>')
    A('<g id="flat-backgrounds">')
    A(f'<rect x="0" y="0" width="{W}" height="{H}" fill="{page_bg}"/>')
    for b in bgs:
        A(f'<rect x="{b["x"]:.1f}" y="{b["y"]:.1f}" width="{b["w"]:.1f}" height="{b["h"]:.1f}" '
          f'fill="{b["fill"]}"/>')
    A('</g>')
    A('<g id="images">')
    for im in images:
        par = fit_to_par(im["fit"])
        A(f'<image x="{im["x"]:.1f}" y="{im["y"]:.1f}" width="{im["w"]:.1f}" height="{im["h"]:.1f}" '
          f'preserveAspectRatio="{par}" xlink:href="{im["src"]}"/>')
    A('</g>')
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
        attrs.append('xml:space="preserve"')
        A(f'<text {" ".join(attrs)}>{escape(t["str"])}</text>')
    A('</g>')
    A('</svg>')
    return "".join(p)


def capture_view(pw, src_uri, name, kind, k, out_dir, last):
    from playwright.sync_api import sync_playwright  # noqa: F401 (kept for parity)
    browser = pw.chromium.launch(headless=True,
                                 args=["--no-sandbox", "--disable-dev-shm-usage"])
    try:
        page = browser.new_page(viewport={"width": 1440, "height": 900},
                                device_scale_factor=1)
        log(f"{name}: loading ...")
        page.goto(src_uri, wait_until="domcontentloaded", timeout=60000)
        page.evaluate("document.querySelectorAll('img').forEach(i=>{i.loading='eager'})")
        css = BASE_CSS + (COVER_CSS if kind == "cover" else chapter_css(k, last))
        page.add_style_tag(content=css)
        page.wait_for_timeout(1200)

        page.evaluate("""async () => {
          const h = document.documentElement.scrollHeight;
          const vh = window.innerHeight;
          for(let y = 0; y < h; y += Math.floor(vh * 0.8)){
            window.scrollTo(0, y);
            await new Promise(r => setTimeout(r, 60));
          }
          window.scrollTo(0, 0);
        }""")
        try:
            page.wait_for_function(
                "() => Array.from(document.images).every(i => i.complete)",
                timeout=45000)
        except Exception:
            log(f"{name}: WARNING some images not complete")
        page.wait_for_timeout(500)
        page.evaluate("window.scrollTo(0,0)")
        page.wait_for_timeout(300)

        data = page.evaluate(EXTRACT_JS)
        W, H = int(round(data["W"])), int(round(data["H"]))
        # Faizan's rule: NEVER upscale. Fit each image's native pixels
        # inside its layout frame, centered; shrink-only.
        clamped = 0
        for im in data["images"]:
            nw, nh = im.get("nw") or 0, im.get("nh") or 0
            if nw > 0 and nh > 0:
                s = min(1.0, im["w"] / nw, im["h"] / nh)
                if s < 1.0 - 1e-9:
                    clamped += 1
                dw, dh = nw * s, nh * s
                im["x"] += (im["w"] - dw) / 2
                im["y"] += (im["h"] - dh) / 2
                im["w"], im["h"] = dw, dh
        log(f"{name}: W={W} H={H} texts={len(data['texts'])} "
            f"images={len(data['images'])} bgs={len(data['bgs'])} "
            f"skipped_imgs={data.get('skipped', 0)} native_clamped={clamped}")
        if H > 12000:
            log(f"{name}: WARNING height {H} exceeds 12000px paste budget")

        svg = build_svg(name, W, H, data["pageBg"], data["bgs"],
                        data["images"], data["texts"])
        dest = out_dir / f"{name}.svg"
        dest.write_text(svg, encoding="utf-8")
        log(f"{name}: wrote {len(svg)//1024}KB -> {dest.name}")
        return {"name": name, "H": H, "texts": len(data["texts"]),
                "images": len(data["images"]),
                "skipped": data.get("skipped", 0)}
    finally:
        browser.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(SRC_HTML))
    ap.add_argument("--imgdir", default=str(IMG_DIR))
    ap.add_argument("--out", default="website_svg_silver_gaunt")
    ap.add_argument("--only", default=None,
                    help="only capture views whose name contains this string")
    args = ap.parse_args()

    src = Path(args.src)
    if not src.exists():
        log(f"FATAL: source not found: {src}")
        sys.exit(2)
    imgdir = Path(args.imgdir)

    html = src.read_text(encoding="utf-8")
    html, n_img = inline_images(html, imgdir)
    log(f"inlined {n_img} images")
    if n_img == 0:
        log("FATAL: no images inlined -- check --imgdir")
        sys.exit(2)
    tmp = Path(os.environ.get("TMPDIR", "/tmp")) / "silver_gaunt_inline.html"
    tmp.write_text(html, encoding="utf-8")
    src_uri = tmp.as_uri()

    out_dir = Path(args.out) if os.path.isabs(args.out) else HERE / args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    views = [v for v in VIEWS if not args.only or args.only in v[0]]
    log(f"{len(views)} views -> {out_dir}")

    from playwright.sync_api import sync_playwright
    t0 = time.time()
    results = []
    with sync_playwright() as pw:
        for i, (name, kind, k) in enumerate(views):
            try:
                results.append(capture_view(pw, src_uri, name, kind, k,
                                            out_dir, last=(i == len(views) - 1)))
            except Exception as e:
                log(f"{name}: FAILED: {e}")
    tot_t = sum(r["texts"] for r in results)
    tot_i = sum(r["images"] for r in results)
    tot_s = sum(r["skipped"] for r in results)
    log(f"done in {time.time()-t0:.0f}s: {len(results)} SVGs, "
        f"{tot_t} text runs, {tot_i} images, {tot_s} skipped")
    if tot_s:
        log("WARNING: skipped images will be MISSING in Figma")
        sys.exit(1)


if __name__ == "__main__":
    main()
