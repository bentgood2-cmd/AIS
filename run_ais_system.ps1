# AIS System Launcher for Windows PowerShell
# This script runs the AIS system launcher with proper error handling

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    AIS System Launcher Starting..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is available
$pythonCmd = $null

# Try to find Python
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCmd = "python"
    Write-Host "✓ Python found in PATH" -ForegroundColor Green
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonCmd = "py"
    Write-Host "✓ Python found via py launcher" -ForegroundColor Green
} else {
    # Try to find Python in common locations
    $pythonPaths = @(
        "C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python*\python.exe",
        "C:\Python*\python.exe",
        "C:\Program Files\Python*\python.exe",
        "C:\Program Files (x86)\Python*\python.exe"
    )
    
    foreach ($path in $pythonPaths) {
        $found = Get-ChildItem -Path $path -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($found) {
            $pythonCmd = $found.FullName
            Write-Host "✓ Python found at: $pythonCmd" -ForegroundColor Green
            break
        }
    }
}

if (-not $pythonCmd) {
    Write-Host "❌ Python not found. Please install Python 3.8+ and try again." -ForegroundColor Red
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

# Check Python version
try {
    $version = & $pythonCmd --version 2>&1
    Write-Host "✓ Python version: $version" -ForegroundColor Green
} catch {
    Write-Host "❌ Error checking Python version: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Starting AIS System Launcher..." -ForegroundColor Yellow
Write-Host ""

# Check if the launcher script exists
if (-not (Test-Path "run_ais_system.py")) {
    Write-Host "❌ run_ais_system.py not found in current directory" -ForegroundColor Red
    Write-Host "Please run this script from the AIS project directory" -ForegroundColor Red
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

# Run the AIS system launcher
try {
    & $pythonCmd run_ais_system.py
} catch {
    Write-Host "❌ Error running AIS System Launcher: $_" -ForegroundColor Red
} finally {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "    AIS System Launcher Exited" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}
