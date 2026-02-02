@echo off
setlocal EnableDelayedExpansion

title Cellpose Stem Cell Counting - Installer
color 0B

echo ========================================
echo   Cellpose Stem Cell Counting Installer
echo ========================================
echo.

:: =====================================================
:: STEP 0: Admin Rights Check and Auto-Elevation
:: =====================================================
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ADMIN CHECK] This script requires Administrator privileges.
    echo               Restarting with elevated permissions...
    timeout /t 2 >nul
    
    :: Create VBScript to elevate
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\elevate.vbs"
    echo UAC.ShellExecute "%~s0", "", "", "runas", 1 >> "%temp%\elevate.vbs"
    
    "%temp%\elevate.vbs"
    del "%temp%\elevate.vbs"
    exit /b
)
echo [ADMIN CHECK] Running with Administrator privileges.
echo.

:: =====================================================
:: STEP 0.5: Enable Long Path Support
:: =====================================================
echo [PRE-FLIGHT] Checking Long Path Support...
reg query "HKLM\SYSTEM\CurrentControlSet\Control\FileSystem" /v LongPathsEnabled | find "0x1" >nul
if %errorlevel% neq 0 (
    echo              Enabling long path support...
    reg add "HKLM\SYSTEM\CurrentControlSet\Control\FileSystem" /v LongPathsEnabled /t REG_DWORD /d 1 /f >nul
    echo              Long paths enabled. Note: A reboot may be required for full effect.
) else (
    echo              Long path support already enabled.
)
echo.

:: =====================================================
:: STEP 0.6: Check Winget Availability
:: =====================================================
echo [PRE-FLIGHT] Checking Winget Package Manager...
where winget >nul 2>&1
if %errorlevel% neq 0 (
    echo              Winget not found. Installing App Installer from Microsoft Store...
    
    :: Check if Microsoft Store is available (some enterprise Windows 11 may not have it)
    if not exist "C:\Program Files\WindowsApps\Microsoft.WindowsStore*" (
        echo              WARNING: Microsoft Store not available.
        echo              Attempting to install winget via alternative method...
        
        :: Download and install winget manually
        curl -L -o "%TEMP%\Microsoft.DesktopAppInstaller_8wekyb3d8bbwe.msixbundle" "https://aka.ms/getwinget" --silent --show-error
        if exist "%TEMP%\Microsoft.DesktopAppInstaller_8wekyb3d8bbwe.msixbundle" (
            powershell -Command "Add-AppxPackage -Path '%TEMP%\Microsoft.DesktopAppInstaller_8wekyb3d8bbwe.msixbundle' -ErrorAction Stop"
            if %errorlevel% neq 0 (
                echo              ERROR: Failed to install winget. Please install manually:
                echo              https://aka.ms/winget
                pause
                exit /b 1
            )
            del "%TEMP%\Microsoft.DesktopAppInstaller_8wekyb3d8bbwe.msixbundle" >nul 2>&1
            echo              Winget installed! You may need to restart this script.
            timeout /t 3 >nul
        ) else (
            echo              ERROR: Failed to download winget installer.
            echo              Please download and install manually from: https://aka.ms/winget
            pause
            exit /b 1
        )
    ) else (
        :: Try installing via MS Store
        start ms-windows-store://pdp/?ProductId=9NBLGGH4NNS1
        echo              Microsoft Store opened. Please install "App Installer" manually.
        echo              After installation, close the Store and press any key to continue...
        pause >nul
        
        :: Check again
        where winget >nul 2>&1
        if %errorlevel% neq 0 (
            echo              Winget still not found. Installation may have failed.
            echo              Please install App Installer manually and restart this script.
            pause
            exit /b 1
        )
    )
) else (
    echo              Winget found!
)
echo.

:: =====================================================
:: STEP 0.7: Check Disk Space (Need ~10GB total)
:: =====================================================
echo [PRE-FLIGHT] Checking Available Disk Space...
for /f "tokens=3" %%a in ('dir /-c "C:" ^| find "bytes free"') do set FREESPACE=%%a
set FREESPACE=%FREESPACE:,=%
if %FREESPACE% lss 10737418240 (
    echo              WARNING: Low disk space detected!
    echo              Required: ~10 GB
    echo              Available: %FREESPACE% bytes
    echo              Installation may fail. Please free up space and try again.
    set /p CONTINUE="Continue anyway? (y/n): "
    if /i not "!CONTINUE!"=="y" exit /b 1
) else (
    set /a FREESPACE_GB=%FREESPACE% / 1073741824
    echo              Sufficient space: ~!FREESPACE_GB! GB available
)
echo.

:: =====================================================
:: STEP 1: Visual Studio C++ Build Tools
:: =====================================================
echo [1/6] Checking Visual Studio C++ Build Tools...

:: Check for existing installation
reg query "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\VisualStudio\Setup\SharedInstallPath" >nul 2>&1
if %errorlevel% equ 0 (
    echo       VS installation found!
    goto :VS_DONE
)

reg query "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\VisualStudio\14.0\Setup\VC" >nul 2>&1
if %errorlevel% equ 0 (
    echo       VS 2015 found!
    goto :VS_DONE
)

:: Check for Build Tools specifically
if exist "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools" (
    echo       VS 2022 Build Tools found!
    goto :VS_DONE
)
if exist "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools" (
    echo       VS 2019 Build Tools found!
    goto :VS_DONE
)

echo       VS Build Tools not found. Installing...

:: Download VS Build Tools
echo       Downloading Visual Studio Build Tools (~2MB installer)...
set "VS_INSTALLER=%TEMP%\vs_buildtools.exe"

:: Remove old installer if exists
if exist "%VS_INSTALLER%" del "%VS_INSTALLER%"

:: Download with curl (Windows 11 has it built-in)
where curl >nul 2>&1
if %errorlevel% neq 0 (
    echo       ERROR: curl not found. This is unusual for Windows 11.
    echo       Please download manually: https://aka.ms/vs/17/release/vs_buildtools.exe
    echo       Run it with: --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended
    pause
    exit /b 1
)

curl -L -o "%VS_INSTALLER%" "https://aka.ms/vs/17/release/vs_buildtools.exe" --silent --show-error --retry 3 --connect-timeout 30
if %errorlevel% neq 0 (
    echo       ERROR: Failed to download VS Build Tools.
    echo       Please install manually from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
    pause
    exit /b 1
)

:: Verify download
if not exist "%VS_INSTALLER%" (
    echo       ERROR: Download file not found.
    pause
    exit /b 1
)

:: Add Windows Defender exclusion for this file (temporarily)
echo       Adding temporary antivirus exclusion for installer...
powershell -Command "try { Add-MpPreference -ExclusionPath '%VS_INSTALLER%' -ErrorAction Stop } catch { }" >nul 2>&1

:: Install VS Build Tools with C++ workload
echo       Installing VS Build Tools (this takes 10-20 minutes)...
echo       Installing C++ build tools, Windows SDK, and CMake...
"%VS_INSTALLER%" --quiet --wait --norestart --nocache --add Microsoft.VisualStudio.Workload.VCTools --add Microsoft.VisualStudio.Component.Windows11SDK.22621 --add Microsoft.VisualStudio.Component.CMake.Tools --includeRecommended

set VS_INSTALL_RESULT=%errorlevel%

:: Remove exclusion
powershell -Command "try { Remove-MpPreference -ExclusionPath '%VS_INSTALLER%' -ErrorAction Stop } catch { }" >nul 2>&1

:: Check result
if %VS_INSTALL_RESULT% equ 0 (
    echo       VS Build Tools installed successfully!
) else if %VS_INSTALL_RESULT% equ 3010 (
    echo       VS Build Tools installed! A system restart is required.
    echo       Please restart your computer and run this script again.
    set /p REBOOT="Restart now? (y/n): "
    if /i "!REBOOT!"=="y" (
        shutdown /r /t 10 /c "Restarting to complete VS Build Tools installation"
        echo Restarting in 10 seconds...
        timeout /t 10
    ) else (
        pause
        exit /b 0
    )
) else (
    echo       WARNING: VS Build Tools installation may have failed (code: %VS_INSTALL_RESULT%).
    echo       Some Python packages with C++ extensions may not install correctly.
    echo       You can continue and see if pip can use pre-built wheels,
    echo       or install manually from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
    set /p CONTINUE="Continue anyway? (y/n): "
    if /i not "!CONTINUE!"=="y" (
        if exist "%VS_INSTALLER%" del "%VS_INSTALLER%"
        pause
        exit /b 1
    )
)

:: Cleanup
if exist "%VS_INSTALLER%" del "%VS_INSTALLER%"

:VS_DONE
echo.

:: =====================================================
:: STEP 2: Python
:: =====================================================
echo [2/6] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo       Python not found. Installing Python 3.12 via winget...
    winget install -e --id Python.Python.3.12 --source winget --accept-package-agreements --accept-source-agreements
    if %errorlevel% neq 0 (
        echo       ERROR: Failed to install Python via winget.
        echo       Please install Python 3.12 manually from: https://www.python.org/downloads/
        pause
        exit /b 1
    )
    
    :: Refresh environment to pick up new Python
    echo       Refreshing environment variables...
    for /f "delims=" %%a in ('"C:\Windows\System32\wbem\wmic.exe" path Win32_VideoController get PNPDeviceID /value 2^>nul ^| find "PCI"') do set "DUMMY=%%a"
    call :RefreshEnv
    
    :: Verify Python is now available
    python --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo       Python installed but not in PATH.
        echo       Please restart this script to continue.
        pause
        exit /b 0
    )
    echo       Python installed successfully!
) else (
    for /f "delims=" %%a in ('python --version 2^>^&1') do echo       %%a found!
)
echo.

:: =====================================================
:: STEP 3: Git
:: =====================================================
echo [3/6] Checking Git installation...
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo       Git not found. Installing via winget...
    winget install -e --id Git.Git --source winget --accept-package-agreements --accept-source-agreements
    if %errorlevel% neq 0 (
        echo       ERROR: Failed to install Git via winget.
        echo       Please install Git manually from: https://git-scm.com/download/win
        pause
        exit /b 1
    )
    
    :: Refresh environment
    echo       Refreshing environment variables...
    call :RefreshEnv
    
    :: Verify Git is now available
    git --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo       Git installed but not in PATH.
        echo       Please restart this script to continue.
        pause
        exit /b 0
    )
    echo       Git installed successfully!
) else (
    for /f "delims=" %%a in ('git --version 2^>^&1') do echo       %%a found!
)
echo.

:: =====================================================
:: STEP 4: Repository Setup
:: =====================================================
set "INSTALL_DIR=%USERPROFILE%\cellpose-stemcell-counting"

echo [4/6] Setting up repository...
if exist "%INSTALL_DIR%" (
    echo       Directory exists. Checking for updates...
    cd /d "%INSTALL_DIR%"
    
    :: Check if it's a valid git repo
    if exist ".git" (
        git remote update >nul 2>&1
        git status -uno | find "Your branch is up to date" >nul
        if %errorlevel% equ 0 (
            echo       Repository is up to date.
        ) else (
            echo       Updates available. Pulling latest changes...
            git pull
            if %errorlevel% neq 0 (
                echo       WARNING: Failed to pull updates. Continuing with local version...
            )
        )
    ) else (
        echo       WARNING: Directory exists but is not a git repository.
        echo       Removing and re-cloning...
        cd /d "%USERPROFILE%"
        rmdir /s /q "%INSTALL_DIR%"
        git clone https://github.com/rif42/cellpose-stemcell-counting.git "%INSTALL_DIR%"
        cd /d "%INSTALL_DIR%"
    )
) else (
    echo       Cloning repository...
    git clone https://github.com/rif42/cellpose-stemcell-counting.git "%INSTALL_DIR%"
    if %errorlevel% neq 0 (
        echo       ERROR: Failed to clone repository.
        echo       Please check your internet connection and try again.
        pause
        exit /b 1
    )
    cd /d "%INSTALL_DIR%"
)
echo       Repository ready at: %INSTALL_DIR%
echo.

:: =====================================================
:: STEP 5: Virtual Environment & Dependencies
:: =====================================================
echo [5/6] Setting up Python environment...
set "VENV_PATH=%INSTALL_DIR%\venv"

if not exist "%VENV_PATH%" (
    echo       Creating virtual environment...
    python -m venv "%VENV_PATH%"
    if %errorlevel% neq 0 (
        echo       ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo       Virtual environment created.
) else (
    echo       Virtual environment already exists.
)

:: Activate venv
echo       Activating virtual environment...
call "%VENV_PATH%\Scripts\activate.bat"
if %errorlevel% neq 0 (
    echo       ERROR: Failed to activate virtual environment.
    pause
    exit /b 1
)

:: Upgrade pip
echo       Upgrading pip...
python -m pip install --upgrade pip --quiet

:: Install dependencies
echo [6/6] Installing Python dependencies...
echo       This may take 5-15 minutes depending on your connection...
echo       Installing packages from requirements.txt...

:: Set environment variables to help compilation
set "CMAKE_GENERATOR=Visual Studio 17 2022"
set "DISTUTILS_USE_SDK=1"

python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo       WARNING: Some packages failed to install.
    echo       This might be due to missing C++ compiler or incompatible packages.
    echo       Please check the error messages above.
    set /p CONTINUE="Continue anyway? (y/n): "
    if /i not "!CONTINUE!"=="y" (
        pause
        exit /b 1
    )
) else (
    echo       All dependencies installed successfully!
)

:: =====================================================
:: Installation Complete
:: =====================================================
echo.
echo ========================================
echo   Installation Complete!
echo ========================================
echo.
echo To run Cellpose GUI later, use:
echo   cd %INSTALL_DIR%
echo   venv\Scripts\activate.bat
echo   python -m cellpose
echo.

:: Create shortcut on desktop (optional)
echo Would you like to create a desktop shortcut for easy launching?
set /p CREATE_SHORTCUT="Create desktop shortcut? (y/n): "
if /i "!CREATE_SHORTCUT!"=="y" (
    (
        echo @echo off
        echo cd /d "%INSTALL_DIR%"
        echo call venv\Scripts\activate.bat
        echo python -m cellpose
        echo pause
    ) > "%INSTALL_DIR%\launch_cellpose.bat"
    
    powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\Cellpose.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\launch_cellpose.bat'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.IconLocation = '%WINDIR%\System32\shell32.dll,14'; $Shortcut.Save()"
    echo Desktop shortcut created!
)

:: Ask if user wants to run cellpose now
set /p RUNNOW="Do you want to launch Cellpose now? (y/n): "
if /i "!RUNNOW!"=="y" (
    echo.
    echo Launching Cellpose...
    python -m cellpose
)

pause
exit /b 0

:: =====================================================
:: Helper Functions
:: =====================================================
:RefreshEnv
:: Refresh environment variables without restarting
for /f "delims=" %%a in ('path') do (
    set "PATH=%%a"
)

:: Also update system PATH
for /f "skip=2 tokens=1,2*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path 2^>nul') do (
    if "%%a"=="Path" (
        set "SYSPATH=%%c"
    )
)
for /f "skip=2 tokens=1,2*" %%a in ('reg query "HKCU\Environment" /v Path 2^>nul') do (
    if "%%a"=="Path" (
        set "USERPATH=%%c"
    )
)

if defined SYSPATH (
    if defined USERPATH (
        set "PATH=!SYSPATH!;!USERPATH!"
    ) else (
        set "PATH=!SYSPATH!"
    )
) else (
    if defined USERPATH (
        set "PATH=!USERPATH!"
    )
)

goto :eof
