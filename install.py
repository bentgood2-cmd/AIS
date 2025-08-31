#!/usr/bin/env python3
"""
Minimal AIS v3.2.1 Installer
Creates environment, installs dependencies, and launches the system.
"""

import os
import sys
import subprocess
import venv
from pathlib import Path

def run_command(cmd, check=True):
    """Run command and return result."""
    try:
        result = subprocess.run(cmd, shell=True, check=check, capture_output=True, text=True)
        return result.returncode == 0
    except subprocess.CalledProcessError:
        return False

def create_environment():
    """Create virtual environment."""
    venv_path = Path("ais_env")
    if venv_path.exists():
        print("Environment exists, skipping creation...")
        return venv_path
    
    print("Creating virtual environment...")
    venv.create(venv_path, with_pip=True)
    return venv_path

def install_dependencies(venv_path):
    """Install required packages."""
    pip_path = venv_path / ("Scripts/pip.exe" if os.name == 'nt' else "bin/pip")
    
    packages = [
        "fastapi", "uvicorn", "torch", "numpy", "pandas", 
        "scikit-learn", "transformers", "pytest"
    ]
    
    print("Installing dependencies...")
    for package in packages:
        print(f"Installing {package}...")
        if not run_command(f'"{pip_path}" install {package}'):
            print(f"Warning: Failed to install {package}")

def create_directories():
    """Create essential directories."""
    dirs = ["ais/core", "ais/api", "ais/utils", "config", "tests"]
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    print("Created directory structure")

def activate_and_run():
    """Activate environment and run the system."""
    if os.name == 'nt':
        activate_script = "ais_env\\Scripts\\activate.bat"
        python_exe = "ais_env\\Scripts\\python.exe"
    else:
        activate_script = "source ais_env/bin/activate"
        python_exe = "ais_env/bin/python"
    
    print("\nEnvironment ready!")
    print(f"To activate manually: {activate_script}")
    
    # Try to run the main system if it exists
    if Path("ais/main.py").exists():
        print("Starting AIS system...")
        run_command(f'"{python_exe}" -m ais.main', check=False)
    else:
        print("AIS main module not found. Environment is ready for development.")

def main():
    """Main installer function."""
    print("AIS v3.2.1 Installer")
    print("===================")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("Error: Python 3.8+ required")
        sys.exit(1)
    
    try:
        venv_path = create_environment()
        install_dependencies(venv_path)
        create_directories()
        activate_and_run()
        
        print("\nInstallation complete!")
        
    except Exception as e:
        print(f"Installation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()