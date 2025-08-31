# AIS System - Quick Start Guide

## 🚀 Fastest Way to Start

**Double-click: `quick_start.bat`**

This will automatically:
1. Check if Python is installed
2. Create virtual environment if needed
3. Install dependencies
4. Launch the AIS system

## 📋 Alternative Methods

### Method 1: Manual Setup
1. Double-click `setup_environment.bat`
2. Double-click `run_direct.bat`

### Method 2: Step by Step
1. Open Command Prompt in this folder
2. Run: `python -m venv ais_env`
3. Run: `ais_env\Scripts\activate`
4. Run: `pip install -r requirements.txt`
5. Run: `python run_ais_system.py`

## 🧪 Testing

- **Quick Test**: `test_all_simple.bat`
- **Synthetic Data**: `test_synthetic_data.bat`
- **GUI Test**: `test_gui.bat`

## 📦 Requirements

- **Python 3.8+** (Download from python.org)
- **Windows** (batch files are for Windows)
- **Internet connection** (for installing dependencies)

## 🔧 Troubleshooting

### "Python not found"
- Install Python from https://python.org/downloads/
- Make sure to check "Add Python to PATH"

### "Virtual environment not found"
- Run `setup_environment.bat` first
- Or manually create: `python -m venv ais_env`

### "Dependencies failed"
- Check internet connection
- Try: `ais_env\Scripts\python.exe -m pip install --upgrade pip`
- Then: `ais_env\Scripts\python.exe -m pip install -r requirements.txt`

## 🎯 What Each File Does

- `quick_start.bat` - One-click setup and launch
- `setup_environment.bat` - Create virtual environment and install dependencies
- `run_direct.bat` - Launch AIS system (after setup)
- `run_launcher.bat` - Alternative launcher
- `test_all_simple.bat` - Run comprehensive tests

## 🌟 Features Available

1. **Complete AIS System** - All components running
2. **Web API Server** - REST API on http://localhost:8000
3. **GUI Interface** - Desktop application (requires PyQt6)
4. **System Tests** - Verify everything works
5. **Health Check** - System diagnostics
6. **Synthetic Data Generator** - Generate test data
7. **Setup Tools** - Install dependencies

Choose your option from the menu after launching!