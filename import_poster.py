#!/usr/bin/env python3
"""Import an SVG poster into Figma as editable layers — headless, via Playwright.

Figma's REST API cannot create files, so this drives the real Figma web app in a
headless Chromium. Designed to run on GitHub Actions (no laptop needed).

Auth: FIGMA_EMAIL and FIGMA_PASSWORD environment variables (GitHub secrets).

Flow:
  1. Log in to figma.com
  2. Open the team/project matching --team-hint (default "Semester 7"), else Drafts
  3. Create a new design file
  4. Rename it to --name
  5. Paste the SVG via the clipboard -> editable vector + text layers
  6. Zoom to fit, screenshot, print the file URL
"""
import argparse
import os
import re
import sys
from pathlib import Path


def log(*a):
    print("[import]", *a, flush=True)


def click_first(page, selectors, timeout=8000, what="element"):
    """Try each selector in order; click the first that resolves."""
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
    ap.add_argument("--svg", required=True, help="Path to the SVG poster file")
    ap.add_argument("--name", default="Sidhi Maternal Deaths — 53 in a year (Sem 7)")
    ap.add_argument("--verify-text", default="53 deaths",
                    help="Canvas text that proves the paste landed (checked after pasting)")
    ap.add_argument("--team-hint", default="Semester 7",
                    help="Team/project to create the file in (fallback: Drafts)")
    args = ap.parse_args()

    email = os.environ.get("FIGMA_EMAIL", "").strip()
    password = os.environ.get("FIGMA_PASSWORD", "").strip()
    if not email or not password:
        log("FIGMA_EMAIL / FIGMA_PASSWORD env vars are required")
        sys.exit(2)

    svg_text = Path(args.svg).read_text(encoding="utf-8")
    log(f"SVG loaded: {len(svg_text)} chars from {args.svg}")

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
            log("LOGIN FAILED: password field never appeared "
                "(see shots/login-failed.png)")
            sys.exit(3)
        click_first(page, ['button:has-text("Log in")', 'button[type="submit"]'],
                    what="Log in button")
        try:
            page.wait_for_url(re.compile(r"figma\.com/files"), timeout=60000)
        except Exception:
            page.screenshot(path="shots/login-failed.png")
            log("LOGIN FAILED: did not reach the file browser — wrong password, "
                "2FA, or a 'verify it's you' email check. See shots/login-failed.png. "
                "If Figma emailed a verification link, approve it once and re-run.")
            sys.exit(3)
        log("logged in")

        # ---- 2. find the Semester 7 team/project, else Drafts ----
        placed_in = "Drafts"
        try:
            team = page.get_by_text(re.compile(r"semester\s*7", re.I)).first
            team.wait_for(timeout=8000)
            team.click()
            placed_in = args.team_hint
            page.wait_for_timeout(3000)
            log("opened:", placed_in)
        except Exception:
            log(f'"{args.team_hint}" not found — using Drafts')
            try:
                drafts = page.get_by_text("Drafts", exact=True).first
                drafts.wait_for(timeout=8000)
                drafts.click()
                page.wait_for_timeout(3000)
            except Exception:
                log("Drafts link not found either; staying on the file browser")
        page.screenshot(path="shots/file-browser.png")

        # ---- 3. new design file ----
        log("creating new design file...")
        if not click_first(page, ['button:has-text("Create")',
                           'button:has-text("New")',
                           '[aria-label="New"]'],
                           what="'Create' button"):
            page.screenshot(path="shots/no-new-button.png")
            sys.exit(4)
        page.wait_for_timeout(1500)
        page.screenshot(path="shots/new-menu.png")
        click_first(page, ['[role="menuitem"]:has-text("Design file")',
                           'text="Design file"'],
                    what="'Design file' menu item")
        try:
            page.wait_for_url(re.compile(r"figma\.com/design/"), timeout=90000)
        except Exception:
            page.screenshot(path="shots/no-editor.png")
            log("the editor did not open — see shots/no-editor.png")
            sys.exit(5)
        file_url = page.url
        log("editor open:", file_url)
        page.wait_for_timeout(9000)  # let the editor fully load
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

        # ---- 5. paste the SVG ----
        log("pasting SVG onto the canvas...")
        page.evaluate("(svg) => navigator.clipboard.writeText(svg)", svg_text)
        page.mouse.click(800, 500)  # focus the canvas
        page.wait_for_timeout(500)
        page.keyboard.press("Control+v")
        page.wait_for_timeout(7000)
        page.screenshot(path="shots/after-paste.png")
        try:
            page.get_by_text(args.verify_text, exact=False).first.wait_for(timeout=15000)
            log("paste verified: poster text found on canvas")
        except Exception:
            log("WARNING: could not verify pasted layers — check shots/after-paste.png")

        # ---- 6. zoom to fit ----
        page.keyboard.press("Shift+1")
        page.wait_for_timeout(1000)
        page.screenshot(path="shots/final.png")
        log("done.")

        summary = (f"## Figma import done\n\n"
                   f"**File:** [{args.name}]({file_url})\n\n"
                   f"Placed in: {placed_in}\n")
        print(summary)
        gh_summary = os.environ.get("GITHUB_STEP_SUMMARY")
        if gh_summary:
            Path(gh_summary).write_text(summary, encoding="utf-8")
        browser.close()


if __name__ == "__main__":
    main()
