#!/usr/bin/env python3
"""Local preview server for william-yates.dev.

Builds the site into ./out (NOT the live /var/www/html) and serves it at
http://localhost:8000 so you can preview changes before publishing.

Usage:  python3 serve.py   (or: make serve)
"""

import os, http.server, socketserver, functools

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
PORT = int(os.environ.get("PORT", "8000"))

# Build into ./out by pointing the builder's SITE_ROOT there before importing it.
os.environ["SITE_ROOT"] = OUT
import build  # noqa: E402

build.main()

handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=OUT)
print(f"\nServing {OUT} at http://localhost:{PORT}  (Ctrl-C to stop)")
with socketserver.TCPServer(("", PORT), handler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
