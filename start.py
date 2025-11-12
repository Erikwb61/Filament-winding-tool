#!/usr/bin/env python3
"""
Start script für Filament Winding Tool
Startet Backend (Port 5000) und Frontend (Port 8000)
"""

import subprocess
import time
import sys
import os
from pathlib import Path

def start_server(name, path, port):
    """Start a Python server in a separate process"""
    server_script = path / "server.py"
    if not server_script.exists():
        print(f"ERROR: {server_script} not found")
        return None
    
    print(f"\n[START] Starte {name} auf Port {port}")
    print(f"        Pfad: {path}")
    
    try:
        process = subprocess.Popen(
            [sys.executable, str(server_script)],
            cwd=str(path),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print(f"[OK] {name} PID: {process.pid}")
        return process
    except Exception as e:
        print(f"[ERROR] Konnte {name} nicht starten: {e}")
        return None


def main():
    root = Path(__file__).parent
    backend_dir = root / "backend"
    frontend_dir = root / "frontend"
    
    print("=" * 60)
    print("Filament Winding Tool - Multi-Server Start")
    print("=" * 60)
    
    # Start backend
    backend_proc = start_server("Backend API", backend_dir, 5000)
    time.sleep(2)
    
    # Start frontend
    frontend_proc = start_server("Frontend Server", frontend_dir, 8000)
    time.sleep(2)
    
    print("\n" + "=" * 60)
    print("ALLE SERVER GESTARTET!")
    print("=" * 60)
    print("\nWEB-ANWENDUNG:")
    print("  → Öffne: http://localhost:8000/index.html")
    print("\nAPI ENDPOINTS:")
    print("  → http://localhost:5000/api/materials")
    print("  → http://localhost:5000/api/laminate-properties")
    print("  → http://localhost:5000/api/failure-analysis")
    print("  → http://localhost:5000/api/tolerance-study")
    print("\n[INFO] Drücke Ctrl+C zum Beenden aller Server")
    print("=" * 60 + "\n")
    
    try:
        if backend_proc:
            backend_proc.wait()
        if frontend_proc:
            frontend_proc.wait()
    except KeyboardInterrupt:
        print("\n\n[STOP] Beende alle Server...")
        if backend_proc and backend_proc.poll() is None:
            backend_proc.terminate()
            backend_proc.wait(timeout=5)
        if frontend_proc and frontend_proc.poll() is None:
            frontend_proc.terminate()
            frontend_proc.wait(timeout=5)
        print("[OK] Alle Server beendet")
        sys.exit(0)


if __name__ == "__main__":
    main()
