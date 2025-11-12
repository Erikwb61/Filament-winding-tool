#!/usr/bin/env python3
"""
Setup script für Filament Winding Tool
Installiert Dependencies und konfiguriert die Umgebung
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a shell command"""
    print(f"\n[{description}]")
    print(f"  $ {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"  ✓ Success")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Error: {e.stderr}")
        return False


def main():
    root = Path(__file__).parent
    
    print("=" * 70)
    print("Filament Winding Tool - Setup")
    print("=" * 70)
    
    # Check Python version
    print(f"\nPython Version: {sys.version}")
    if sys.version_info < (3, 8):
        print("ERROR: Python 3.8+ is required")
        sys.exit(1)
    
    # Create virtual environment if needed
    venv_dir = root / ".venv"
    if not venv_dir.exists():
        print("\n[VENV] Virtual environment not found, creating...")
        run_command([sys.executable, "-m", "venv", str(venv_dir)], "Create venv")
    
    # Get Python executable in venv
    if sys.platform == "win32":
        python_exe = venv_dir / "Scripts" / "python.exe"
    else:
        python_exe = venv_dir / "bin" / "python"
    
    if not python_exe.exists():
        print(f"ERROR: Python executable not found at {python_exe}")
        sys.exit(1)
    
    # Install requirements
    print("\n[PIP] Installing dependencies...")
    
    requirements = [
        "flask==3.1.2",
        "flask-cors==6.0.1",
        "pydantic==2.5.0",
        "requests==2.31.0",
        "scipy==1.11.4",
        "numpy==1.24.3",
    ]
    
    for package in requirements:
        run_command([str(python_exe), "-m", "pip", "install", package], f"Install {package}")
    
    # Copy .env if not exists
    env_file = root / ".env"
    env_example = root / ".env.example"
    if not env_file.exists() and env_example.exists():
        print("\n[CONFIG] Copying .env.example to .env")
        import shutil
        shutil.copy(env_example, env_file)
        print("  ✓ Created .env (please configure if needed)")
    
    print("\n" + "=" * 70)
    print("Setup complete!")
    print("=" * 70)
    
    print("\nNächste Schritte:")
    print("1. Backend starten:")
    print("   cd backend && python server.py")
    print("\n2. Frontend starten (in separatem Terminal):")
    print("   cd frontend && python server.py")
    print("\n3. Öffne: http://localhost:8000/index.html")
    print("\nODER beide Server mit einem Command starten:")
    print("   python start.py")
    print()


if __name__ == "__main__":
    main()
