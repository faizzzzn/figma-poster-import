#!/usr/bin/env python3
"""Import the Kaam x RozgaarSetu final research deck into Figma — headless.

Pastes each SVG in research_svg/ as its own artboard, arranged left-to-right
in a row on the canvas of a newly created design file. Text stays editable.

Auth: FIGMA_EMAIL and FIGMA_PASSWORD env vars (GitHub secrets).
"""
import argparse
import glob
import os
import re
import sys
from pathlib import Path

STEP_PX = 1600  # artboard width 1440 + 160 gap; Shift+Right = 10px per press


def log(*a):
    print("[research-import]", *a, flush=True)


def click_first(page, selectors, timeout=8000, what="element"):
    for sel in selectors:
        try:
            page.locator(sel).first.click(timeout=timeout)
            return True
        except Exception:
            continue
    log(f"WARNING: could not click {what}")
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--svgs", default="research_svg",
                    help="Directory of SVGs, pasted in sorted order")
    ap.add_argument("--name", default="Kaam x RozgaarSetu \u2014 Final Research")
    ap.add_argument("--team-hint", default="Semester 7")
    args = ap.parse_args()

    email = os.environ.get("FIGMA_EMAIL", "").strip()
    password = os.environ.get("FIGMA_PASSWORD", "").strip()
    if not email or not password:
        log("FIGMA_EMAIL / FIGMA_PASSWORD env vars are required")
        sys.exit(2)

    svg_files = sorted(glob.glob(os.path.join(args.svgs, "*.svg")))
    if not svg_files:
        log("no SVGs found in", args.svgs)
        sys.exit(2)
    log(f"{len(svg_files)} artboards:", ", ".join(Path(f).name for f in svg_files))

    from playwright.sync_api import sync_playwright

    shots = Path("shots")
    shots.mkdir(exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1600, "height": 1000})
        ctx.set_default_timeout(20000)
        ctx.grant_permissions(["clipboard-read", "clipboard-write"])
        page = ctx.new_page()

        # ---- 1. log in ----
        log("logging in as", email)
        page.goto("https://www.figma.com/login", wait_until="domcontentloaded")
        page.locator('input[type="email"], input[name="email"]').first.fill(email)
        click_first(page, ['button:has-text("Continue")', 'button[type="submit"]'],
                    what="Continue button")
        page.wait_for_timeout(2500)
        try:
            pw = page.locator('input[type="password"]').first
            pw.wait_for(timeout=15000)
            pw.fill(password)
        except Exception:
            page.screenshot(path="shots/login-failed.png")
            log("LOGIN FAILED: password field never appeared")
            sys.exit(3)
        click_first(page, ['button:has-text("Log in")', 'button[type="submit"]'],
                    what="Log in button")
        try:
            page.wait_for_url(re.compile(r"figma\.com/files"), timeout=60000)
        except Exception:
            page.screenshot(path="shots/login-failed.png")
            log("LOGIN FAILED: did not reach the file browser — wrong password, "
                "2FA, or a 'verify it's you' email check. See shots/login-failed.png.")
            sys.exit(3)
        log("logged in")

        # ---- 2. team / drafts ----
        placed_in = "Drafts"
        try:
            team = page.get_by_text(re.compile(r"semester\s*7", re.I)).first
            team.wait_for(timeout=8000)
            team.click()
            placed_in = args.team_hint
            page.wait_for_timeout(3000)
            log("opened:", placed_in)
        except Exception:
            log(f'"{args.team_hint}" not found \u2014 using Drafts')
            try:
                page.get_by_text("Drafts", exact=True).first.click(timeout=8000)
                page.wait_for_timeout(3000)
            except Exception:
                log("Drafts link not found either; staying on the file browser")

        # ---- 3. new design file ----
        log("creating new design file...")
        page.screenshot(path="shots/file-browser.png")
        if not click_first(page, ['button:has-text("Create")', '[aria-label="Create"]'],
                           timeout=15000, what="'Create' button"):
            page.screenshot(path="shots/no-create-button.png")
            sys.exit(4)
        page.wait_for_timeout(1500)
        page.screenshot(path="shots/create-menu.png")
        if not click_first(page, ['[role="menuitem"]:has-text("Design")',
                                  'text="Design"'],
                           timeout=15000, what="'Design' menu item"):
            page.screenshot(path="shots/no-design-item.png")
            log("WARNING: 'Design' menu item not clickable; trying Enter on open menu")
            page.keyboard.press("Enter")
            page.wait_for_timeout(1500)
        try:
            page.wait_for_url(re.compile(r"figma\.com/design/"), timeout=90000)
        except Exception:
            page.screenshot(path="shots/no-editor.png")
            log("the editor did not open \u2014 see shots/no-editor.png")
            sys.exit(5)
        file_url = page.url
        log("editor open:", file_url)
        page.wait_for_timeout(9000)
        page.keyboard.press("Escape")
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)

        # ---- 4. rename ----
        try:
            title = page.get_by_text("Untitled", exact=True).first
            title.wait_for(timeout=15000)
            title.click()
            page.wait_for_timeout(800)
            page.keyboard.press("ControlOrMeta+a")
            page.keyboard.type(args.name, delay=15)
            page.keyboard.press("Enter")
            page.wait_for_timeout(1000)
            log("renamed to:", args.name)
        except Exception as e:
            log("rename skipped (non-fatal):", str(e)[:120])

        # ---- 5. paste each artboard, nudging into a row ----
        # PASTE_STRIDE_PX: when > 0, use the fast "pan the viewport" strategy
        # instead of nudging each layer: after each paste (except the last),
        # deselect and pan the canvas right by STRIDE px, so the next paste
        # lands one stride to the right. Cost is ~stride/10 presses per gap
        # instead of the cumulative i*STEP_PX of the nudge strategy.
        # Default 0 keeps the original nudge behavior for existing workflows.
        stride = int(os.environ.get("PASTE_STRIDE_PX", "0"))
        for i, svg_path in enumerate(svg_files):
            name = Path(svg_path).name
            svg_text = Path(svg_path).read_text(encoding="utf-8")
            log(f"pasting artboard {i+1}/{len(svg_files)}: {name}")
            page.evaluate("(svg) => navigator.clipboard.writeText(svg)", svg_text)
            page.mouse.click(800, 500)  # focus the canvas
            page.wait_for_timeout(500)
            page.keyboard.press("Control+v")
            page.wait_for_timeout(6000)
            if stride > 0:
                if i < len(svg_files) - 1:
                    page.keyboard.press("Escape")
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(400)
                    for _ in range(stride // 10):
                        page.keyboard.press("Shift+ArrowRight")
                    page.wait_for_timeout(400)
                    log(f"  panned viewport right {stride}px")
            else:
                presses = (i * STEP_PX) // 10
                for _ in range(presses):
                    page.keyboard.press("Shift+ArrowRight")
                page.wait_for_timeout(800)
                log(f"  nudged right {i * STEP_PX}px ({presses} presses)")
            page.screenshot(path=f"shots/after-paste-{i+1}.png")

        # ---- 6. zoom to fit + final shot ----
        page.keyboard.press("Shift+1")
        page.wait_for_timeout(1200)
        page.screenshot(path="shots/final.png")
        log("done.")

        summary = (f"## Figma import done\n\n"
                   f"**File:** [{args.name}]({file_url})\n\n"
                   f"Placed in: {placed_in}\n"
                   f"Artboards: {len(svg_files)}\n")
        print(summary)
        gh_summary = os.environ.get("GITHUB_STEP_SUMMARY")
        if gh_summary:
            Path(gh_summary).write_text(summary, encoding="utf-8")
        browser.close()


if __name__ == "__main__":
    main()
