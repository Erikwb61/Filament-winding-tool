#!/usr/bin/env python3
"""
Frontend HTTP Server für Filament Winding Tool
Serves HTML, CSS, JavaScript, and static assets
"""

import http.server
import socketserver
import os
import sys
from pathlib import Path

PORT = 8000
FRONTEND_DIR = Path(__file__).parent

class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()
    
    def log_message(self, format, *args):
        print(f"[{self.client_address[0]}] {format % args}")


if __name__ == "__main__":
    os.chdir(FRONTEND_DIR)
    
    with socketserver.TCPServer(("", PORT), CORSRequestHandler) as httpd:
        print(f"[START] Frontend Server auf http://localhost:{PORT}")
        print(f"[INFO] Serving files from: {FRONTEND_DIR}")
        print("[INFO] Drücke Ctrl+C zum Beenden")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[STOP] Server beendet")
            sys.exit(0)
