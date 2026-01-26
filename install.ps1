# Cellpose Stem Cell Counting - Installation Script
# Run this script with PowerShell

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Cellpose Stem Cell Counting Installer" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed, if not install via winget
Write-Host "[1/5] Checking Python installation..." -ForegroundColor Yellow
$pythonInstalled = $false
try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match "Python") {
        Write-Host "      Found: $pythonVersion" -ForegroundColor Green
        $pythonInstalled = $true
    }
} catch {}

if (-not $pythonInstalled) {
    Write-Host "      Python not found. Installing via winget..." -ForegroundColor Yellow
    winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -eq 0) {
        Write-Host "      Python installed successfully!" -ForegroundColor Green
        Write-Host "      Please restart this script after installation completes." -ForegroundColor Yellow
        Read-Host "Press Enter to exit"
        exit 0
    } else {
        Write-Host "      ERROR: Failed to install Python." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Check if Git is installed, if not install via winget
Write-Host "[2/5] Checking Git installation..." -ForegroundColor Yellow
$gitInstalled = $false
try {
    $gitVersion = git --version 2>&1
    if ($gitVersion -match "git version") {
        Write-Host "      Found: $gitVersion" -ForegroundColor Green
        $gitInstalled = $true
    }
} catch {}

if (-not $gitInstalled) {
    Write-Host "      Git not found. Installing via winget..." -ForegroundColor Yellow
    winget install -e --id Git.Git --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -eq 0) {
        Write-Host "      Git installed successfully!" -ForegroundColor Green
        Write-Host "      Please restart this script after installation completes." -ForegroundColor Yellow
        Read-Host "Press Enter to exit"
        exit 0
    } else {
        Write-Host "      ERROR: Failed to install Git." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Set the installation directory
$installDir = "$env:USERPROFILE\cellpose-stemcell-counting"

# Clone the repository
Write-Host "[3/5] Cloning repository..." -ForegroundColor Yellow
if (Test-Path $installDir) {
    Write-Host "      Directory already exists. Pulling latest changes..." -ForegroundColor Yellow
    Set-Location $installDir
    git pull
} else {
    git clone https://github.com/rif42/cellpose-stemcell-counting.git $installDir
    Set-Location $installDir
}
Write-Host "      Repository ready at: $installDir" -ForegroundColor Green

# Create virtual environment
Write-Host "[4/5] Setting up Python virtual environment..." -ForegroundColor Yellow
$venvPath = "$installDir\venv"
if (-not (Test-Path $venvPath)) {
    python -m venv $venvPath
    Write-Host "      Virtual environment created." -ForegroundColor Green
} else {
    Write-Host "      Virtual environment already exists." -ForegroundColor Green
}

# Activate virtual environment and install dependencies
Write-Host "[5/5] Installing dependencies (this may take several minutes)..." -ForegroundColor Yellow
& "$venvPath\Scripts\Activate.ps1"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Installation Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "To run Cellpose GUI, use these commands:" -ForegroundColor Cyan
Write-Host "  cd $installDir" -ForegroundColor White
Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "  python -m cellpose" -ForegroundColor White
Write-Host ""

# Ask if user wants to run cellpose now
$runNow = Read-Host "Do you want to launch Cellpose now? (y/n)"
if ($runNow -eq "y" -or $runNow -eq "Y") {
    Write-Host "Launching Cellpose..." -ForegroundColor Cyan
    python -m cellpose
}
