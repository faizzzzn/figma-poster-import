#!/usr/bin/env python3
"""Faizan Haidri portfolio -> Figma SVG artboards (EXACT edition).

The previous approximation generator is preserved untouched as
build_portfolio_figma_approx.py. This entry point now delegates to
build_portfolio_exact.py, which renders the real portfolio.html in
headless Chromium and extracts exact text positions, fonts, colors,
image rectangles, and a pixel-faithful raster backdrop into
website_svg_portfolio/.

Usage: python build_portfolio_figma.py [--out website_svg_portfolio] [--only NAME]
"""
import runpy
import sys
from pathlib import Path

if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    # default output dir matches the import workflow's paste glob
    sys.argv = [sys.argv[0]] + (sys.argv[1:] or ["--out", "website_svg_portfolio"])
    runpy.run_path(str(here / "build_portfolio_exact.py"), run_name="__main__")
