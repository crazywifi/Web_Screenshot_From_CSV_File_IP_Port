@echo off
setlocal enabledelayedexpansion

:: Ask user for the input file
set /p inputFile="Enter the input file name (e.g., a.txt): "

if not exist "%inputFile%" (
    echo [ERROR] File "%inputFile%" not found!
    exit /b
)

:: Clear previous results
echo. > accessible.txt
echo. > inaccessible.txt
echo. > redirected.txt

echo =============================================
echo       Checking URLs from "%inputFile%"
echo =============================================

:: Process each URL
for /f "delims=" %%i in (%inputFile%) do (
    echo Checking: %%i...
    
    :: Use curl to follow redirects (-L) and capture headers (-I)
    curl --head --location --silent --max-time 5 %%i > temp_headers.txt 2>nul
    
    :: Extract final redirected URL
    set "finalURL="
    for /f "tokens=2 delims= " %%j in ('findstr /I "Location:" temp_headers.txt') do set "finalURL=%%j"

    :: Check if request was successful
    findstr /I "HTTP/1.1 200 HTTP/2 200" temp_headers.txt >nul
    if !errorlevel! == 0 (
        if defined finalURL (
            echo [REDIRECTED] %%i → !finalURL!
            echo %%i redirected to !finalURL! >> redirected.txt
        ) else (
            echo [OK] %%i is ACCESSIBLE
            echo %%i >> accessible.txt
        )
    ) else (
        echo [FAIL] %%i is NOT accessible
        echo %%i >> inaccessible.txt
    )
)

del temp_headers.txt 2>nul

echo =============================================
echo   Check Completed! 
echo   - Accessible URLs   → accessible.txt
echo   - Inaccessible URLs → inaccessible.txt
echo   - Redirected URLs   → redirected.txt
echo =============================================

pause
