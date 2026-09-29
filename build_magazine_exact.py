#!/usr/bin/env python3
"""Exact-detail Figma transfer of the GATHER NO MOSS Rolling Stones magazine.

Renders magazine/magazine.html (self-contained: data-URI images, fonts in
magazine/fonts/) in headless Chromium, captures each of the 10 .page sections
(8x8in = 768x768px artboards) with the REAL rendered layout -- per-line text
runs with exact position, font, size, weight, color, letter-spacing, alignment,
plus image rects -- and emits 10 SVGs with editable <text> and <image> layers
over a raster backdrop layer (hide the raster group in Figma for clean editing).

Usage:
    python3 build_magazine_exact.py [--html magazine/magazine.html]
                                    [--out magazine_svg] [--only 01]

Requires: playwright + Chromium (headless). Anton/Archivo must be installed
as system fonts on the machine running this (fc-cache) for faithful metrics.
"""
import argparse
import base64
import json
import os
import sys
import time
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent

PAGE_W, PAGE_H, N_PAGES = 768, 768, 10

BASE_CSS = """
*,*::before,*::after{animation:none!important;transition:none!important;scroll-behavior:auto!important}
"""

EXTRACT_JS = r"""
() => {
  const IDX = window.__PAGE_IDX__;
  const secs = document.querySelectorAll('section.page');
  const root = secs[IDX];
  const out = {texts: [], images: [], bgs: [], W: 0, H: 0, pageBg: '#f3e9d2'};

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

  const sr = root.getBoundingClientRect();
  out.W = Math.round(sr.width); out.H = Math.round(sr.height);
  out.pageBg = rgb2hex(csOf(root).backgroundColor).hex;

  // ---- canvas probe for exact alphabetic baselines ----
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
      // keep coords relative to the page section
      if(r.width > 0 && r.height > 0)
        chars.push({ch: text[i], x: r.left - sr.left, y: r.top - sr.top, w: r.width, h: r.height});
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

  // ---- images ----
  root.querySelectorAll('img').forEach(img => {
    if(!isVis(img)) return;
    if(!img.complete || img.naturalWidth === 0) return;
    const r = img.getBoundingClientRect();
    if(r.width < 2 || r.height < 2) return;
    const src = img.currentSrc || img.src || '';
    if(!src.startsWith('data:image')){ out.skipped = (out.skipped || 0) + 1; return; }
    out.images.push({x: r.left - sr.left, y: r.top - sr.top, w: r.width, h: r.height,
                     src, fit: csOf(img).objectFit || 'fill'});
  });

  // ---- opaque flat backgrounds ----
  const seen = [];
  root.querySelectorAll('*').forEach(el => {
    if(!isVis(el)) return;
    const c = rgb2hex(csOf(el).backgroundColor);
    if(c.alpha < 1) return;
    const r = el.getBoundingClientRect();
    if(r.width * r.height < 60000) return;
    seen.push({x: r.left - sr.left, y: r.top - sr.top, w: r.width, h: r.height,
               fill: c.hex, area: r.width * r.height});
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
    print("[magazine]", *a, flush=True)


def fit_to_par(fit):
    if fit == "cover":
        return "xMidYMid slice"
    if fit == "contain":
        return "xMidYMid meet"
    return "none"


def build_svg(name, W, H, page_bg, bgs, raster_b64, images, texts):
    p = []
    A = p.append
    A('<?xml version="1.0" encoding="UTF-8"?>')
    A(f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
      f'width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
    A(f'<title>{escape(name)}</title>')
    A('<g id="flat-backgrounds">')
    A(f'<rect x="0" y="0" width="{W}" height="{H}" fill="{page_bg}"/>')
    for b in bgs:
        A(f'<rect x="{b["x"]:.1f}" y="{b["y"]:.1f}" width="{b["w"]:.1f}" height="{b["h"]:.1f}" '
          f'fill="{b["fill"]}"/>')
    A('</g>')
    A('<g id="raster-backdrop">')
    A(f'<image x="0" y="0" width="{W}" height="{H}" preserveAspectRatio="none" '
      f'xlink:href="data:image/jpeg;base64,{raster_b64}"/>')
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
        A(f'<text {" ".join(attrs)}>{escape(t["str"])}</text>')
    A('</g>')
    A('</svg>')
    return "".join(p)


def capture_page(page, idx, out_dir):
    name = f"{idx+1:02d}-page-{idx+1:02d}"
    page.evaluate(f"window.scrollTo(0, {idx * PAGE_H})")
    page.wait_for_timeout(400)
    page.evaluate(f"window.__PAGE_IDX__ = {idx}")
    data = page.evaluate(EXTRACT_JS)
    W, H = int(round(data["W"])), int(round(data["H"]))
    log(f"{name}: W={W} H={H} texts={len(data['texts'])} "
        f"images={len(data['images'])} bgs={len(data['bgs'])} "
        f"skipped_imgs={data.get('skipped', 0)}")
    shot = page.screenshot(clip={"x": 0, "y": 0, "width": PAGE_W, "height": PAGE_H},
                           type="jpeg", quality=72)
    raster_b64 = base64.b64encode(shot).decode("ascii")
    svg = build_svg(name, W, H, data["pageBg"], data["bgs"],
                    raster_b64, data["images"], data["texts"])
    dest = out_dir / f"{name}.svg"
    dest.write_text(svg, encoding="utf-8")
    log(f"{name}: wrote {len(svg)//1024}KB -> {dest.name}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", default="magazine/magazine.html")
    ap.add_argument("--out", default="magazine_svg")
    ap.add_argument("--only", default=None,
                    help="only capture pages whose 1-based number contains this string")
    args = ap.parse_args()
    src = Path(args.html) if os.path.isabs(args.html) else HERE / args.html
    if not src.exists():
        log(f"FATAL: source not found: {src}")
        sys.exit(2)
    out_dir = Path(args.out) if os.path.isabs(args.out) else HERE / args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    pages = [i for i in range(N_PAGES)
             if not args.only or args.only in f"{i+1:02d}"]
    log(f"{len(pages)} pages -> {out_dir}")

    from playwright.sync_api import sync_playwright
    t0 = time.time()
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True,
                                     args=["--no-sandbox", "--disable-dev-shm-usage"])
        try:
            pg = browser.new_page(viewport={"width": PAGE_W, "height": PAGE_H},
                                  device_scale_factor=1)
            pg.goto(src.as_uri(), wait_until="domcontentloaded", timeout=60000)
            pg.wait_for_timeout(1200)
            pg.add_style_tag(content=BASE_CSS)
            pg.evaluate("document.fonts.ready.then(()=>1)")
            try:
                pg.wait_for_function(
                    "() => Array.from(document.images).every(i => i.complete)",
                    timeout=60000)
            except Exception:
                log("WARNING: some images not complete")
            pg.wait_for_timeout(500)
            n = pg.evaluate("document.querySelectorAll('section.page').length")
            log(f"found {n} .page sections")
            for idx in pages:
                try:
                    capture_page(pg, idx, out_dir)
                except Exception as e:
                    log(f"page {idx+1}: FAILED: {e}")
        finally:
            browser.close()
    log(f"done in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
