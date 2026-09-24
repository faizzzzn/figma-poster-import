# figma-poster-import

Puts an SVG poster into Figma as **editable vector + text layers** — headless, on GitHub Actions. No laptop needed, no copy-pasting.

Why a browser and not the Figma API? Figma's REST API has no file-creation endpoint (writes are limited to variables, comments, and webhooks), so this drives the real Figma web app in headless Chromium: log in → open the Semester 7 team → new design file → paste SVG via clipboard → zoom to fit → report the file URL.

## One-time setup

Add two secrets to this repo (Settings → Secrets and variables → Actions → New repository secret), or from a terminal with `gh`:

```
gh secret set FIGMA_EMAIL
gh secret set FIGMA_PASSWORD
```

(`gh secret set NAME` with no value prompts securely — nothing lands in shell history.)

Notes:
- The first run from a new IP may trigger Figma's "verify it's you" email. Approve it once from your inbox, then re-run the workflow.
- If Figma ever forces 2FA on the account, password login will fail and the run will stop with a screenshot showing where.

## Run it

Actions tab → **import-poster-to-figma** → **Run workflow** (file name and team are editable per run),

or from a terminal:

```
gh workflow run import.yml
```

When it finishes, the file URL is printed in the run summary. Screenshots of every step are kept as the `figma-import-shots` artifact for 90 days.

## Files

- `import_poster.py` — the Playwright import script (also runnable locally: `pip install playwright && python -m playwright install chromium`)
- `sidhi_maternal_deaths.svg` — the poster (2400×5700, dark editorial)
- `.github/workflows/import.yml` — the scheduled-runnable workflow
