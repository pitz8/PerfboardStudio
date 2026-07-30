#!/usr/bin/env python3
"""Run the browser test suites headlessly.

The app has no build step and no Node dependency, so its tests are plain HTML
pages that import the real ES modules and write their results into the DOM. This
script serves the repo, drives a headless Chromium-family browser over each page
and reports the summary line.

    python tools/run_browser_tests.py
    python tools/run_browser_tests.py --browser "C:\\path\\to\\msedge.exe"
    python tools/run_browser_tests.py --keep-going

Exit status is non-zero if any suite fails or cannot be run.
"""

from __future__ import annotations

import argparse
import http.server
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SUITES = [
    ("unit", "tools/selftest.html"),
    ("integration", "tools/integration.html"),
]

# Places a Chromium-family browser usually lives, per platform.
CANDIDATES = {
    "win32": [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ],
    "darwin": [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ],
    "linux": [
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
        "/usr/bin/microsoft-edge",
    ],
}

SUMMARY_RE = re.compile(
    r'id="summary"[^>]*>\s*(\d+)\s+passed,\s+(\d+)\s+failed', re.IGNORECASE)
FAIL_RE = re.compile(r'<div class="fail">([\s\S]*?)</div>')


def find_browser(explicit: str | None) -> str | None:
    if explicit:
        return explicit if Path(explicit).exists() else None
    for name in ("chrome", "chromium", "google-chrome", "msedge", "microsoft-edge"):
        found = shutil.which(name)
        if found:
            return found
    for path in CANDIDATES.get(sys.platform, []):
        if Path(path).exists():
            return path
    return None


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):  # noqa: D102 - silence the request log
        pass


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def serve(port: int):
    os.chdir(ROOT)
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), QuietHandler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd


def run_suite(browser: str, url: str, budget_ms: int) -> tuple[str, str]:
    """Load `url` headlessly and return (dumped html, stderr)."""
    with tempfile.TemporaryDirectory(prefix="pbs-prof-") as profile:
        cmd = [
            browser,
            "--headless=new",
            "--disable-gpu",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-extensions",
            "--window-size=1600,1200",
            f"--user-data-dir={profile}",
            f"--virtual-time-budget={budget_ms}",
            "--dump-dom",
            url,
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=300)
        return proc.stdout or "", proc.stderr or ""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--browser", help="path to a Chromium-family browser executable")
    ap.add_argument("--budget", type=int, default=45000,
                    help="virtual time budget per suite, in ms (default 45000)")
    ap.add_argument("--keep-going", action="store_true",
                    help="run every suite even after one fails")
    ap.add_argument("--verbose", action="store_true", help="print browser stderr")
    args = ap.parse_args()

    browser = find_browser(args.browser)
    if not browser:
        print("No Chromium-family browser found. Install Chrome/Edge/Chromium, or "
              "pass --browser <path>.", file=sys.stderr)
        print("You can also just open tools/selftest.html and tools/integration.html "
              "in any browser via 'npm run dev'.", file=sys.stderr)
        return 2
    print(f"browser: {browser}")

    port = free_port()
    httpd = serve(port)
    base = f"http://127.0.0.1:{port}"
    print(f"serving {ROOT} at {base}\n")

    failed = 0
    try:
        for name, page in SUITES:
            url = f"{base}/{page}"
            html, err = run_suite(browser, url, args.budget)
            if args.verbose and err.strip():
                print(err.strip(), file=sys.stderr)

            m = SUMMARY_RE.search(html)
            if not m:
                print(f"FAIL {name:<12} the page did not report a summary "
                      f"(a module probably failed to load)")
                # Surface whatever the page managed to say.
                for snippet in FAIL_RE.findall(html)[:5]:
                    print(f"       {snippet.strip()}")
                if not html.strip():
                    print("       the browser produced no output at all")
                failed += 1
                if not args.keep_going:
                    return 1
                continue

            passed, fails = int(m.group(1)), int(m.group(2))
            status = "ok  " if fails == 0 else "FAIL"
            print(f"{status} {name:<12} {passed} passed, {fails} failed")
            if fails:
                for snippet in FAIL_RE.findall(html):
                    print(f"       {snippet.strip()}")
                failed += 1
                if not args.keep_going:
                    return 1
    finally:
        httpd.shutdown()

    print()
    if failed:
        print(f"{failed} suite(s) failed")
        return 1
    print("all suites passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
