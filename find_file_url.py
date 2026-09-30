#!/usr/bin/env python3
"""Find an existing Figma file by name and print its real editor URL.

Logs in headless, opens the team file browser, clicks the file tile with
the given name, waits for the URL to resolve to a real file key
(/design/new is the pre-navigation template and is NOT accepted),
then prints FILE_URL: <url>.

Auth: FIGMA_EMAIL and FIGMA_PASSWORD env vars (GitHub secrets).
Usage: python find_file_url.py --name "Faizan Haidri — Project Pages"
"""
import argparse
import os
import re
import sys
from pathlib import Path


def log(*a):
    print("[find-file-url]", *a, flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True, help="Exact Figma file name")
    ap.add_argument("--team-hint", default="Semester 7")
    args = ap.parse_args()

    email = os.environ.get("FIGMA_EMAIL", "").strip()
    password = os.environ.get("FIGMA_PASSWORD", "").strip()
    if not email or not password:
        log("FIGMA_EMAIL / FIGMA_PASSWORD env vars are required")
        sys.exit(2)

    from playwright.sync_api import sync_playwright

    shots = Path("shots")
    shots.mkdir(exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1600, "height": 1000})
        ctx.set_default_timeout(20000)
        page = ctx.new_page()

        # ---- 1. log in ----
        page.goto("https://www.figma.com/login", wait_until="domcontentloaded")
        page.locator('input[type="email"], input[name="email"]').first.fill(email)
        page.locator('button:has-text("Continue"), button[type="submit"]').first.click()
        page.wait_for_timeout(2500)
        try:
            pw = page.locator('input[type="password"]').first
            pw.wait_for(timeout=15000)
            pw.fill(password)
        except Exception:
            page.screenshot(path="shots/login-failed.png")
            log("LOGIN FAILED: password field never appeared")
            sys.exit(3)
        page.locator('button:has-text("Log in"), button[type="submit"]').first.click()
        try:
            page.wait_for_url(re.compile(r"figma\.com/files"), timeout=60000)
        except Exception:
            page.screenshot(path="shots/login-failed.png")
            log("LOGIN FAILED: did not reach the file browser")
            sys.exit(3)
        log("logged in")

        # ---- 2. open the team ----
        try:
            team = page.get_by_text(re.compile(r"semester\s*7", re.I)).first
            team.wait_for(timeout=8000)
            team.click()
            page.wait_for_timeout(4000)
            log("opened team:", args.team_hint)
        except Exception:
            log(f'team "{args.team_hint}" not found — staying on file browser')
        page.screenshot(path="shots/find-file-browser.png")

        # ---- 3. click the file tile ----
        tile = page.get_by_text(args.name, exact=True).first
        try:
            tile.wait_for(timeout=20000)
        except Exception:
            page.screenshot(path="shots/find-not-found.png")
            log(f'file "{args.name}" not found in this view')
            sys.exit(4)
        # the name text may sit inside the tile; click its closest tile link
        try:
            tile.click(timeout=10000)
        except Exception:
            page.screenshot(path="shots/find-click-failed.png")
            log("could not click the file tile")
            sys.exit(4)

        # ---- 4. wait for the real file-key URL ----
        try:
            page.wait_for_url(re.compile(r"figma\.com/design/(?!new\b)[A-Za-z0-9]"),
                              timeout=90000)
        except Exception:
            page.screenshot(path="shots/find-no-url.png")
            log("editor URL never resolved to a file key; current:", page.url)
            sys.exit(5)
        page.wait_for_timeout(2000)
        page.screenshot(path="shots/find-opened.png")
        print(f"FILE_URL: {page.url}", flush=True)
        browser.close()


if __name__ == "__main__":
    main()
