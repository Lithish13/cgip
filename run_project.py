#!/usr/bin/env python3
"""
Launcher script for the CGIP Spatial Gesture Calculator.
Starts a local HTTP server on http://localhost:8000 and opens the app in your default browser.
"""

import http.server
import os
import socketserver
import sys
import webbrowser

PORT = 8000

def main():
    # Ensure index.html exists (fallback to index-v2.html if needed)
    if not os.path.exists("index.html") and os.path.exists("index-v2.html"):
        with open("index-v2.html", "rb") as src, open("index.html", "wb") as dst:
            dst.write(src.read())

    handler = http.server.SimpleHTTPRequestHandler
    socketserver.TCPServer.allow_reuse_address = True

    try:
        with socketserver.TCPServer(("", PORT), handler) as httpd:
            url = f"http://localhost:{PORT}/index.html"
            print(f"[*] Starting CGIP Gesture Calculator Web Server at: {url}")
            print("[*] Opening browser automatically... (Press Ctrl+C to stop)")
            webbrowser.open(url)
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Server stopped.")
        sys.exit(0)

if __name__ == "__main__":
    main()
