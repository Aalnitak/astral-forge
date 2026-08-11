@echo off
setlocal enabledelayedexpansion

set CADDY_SERVICE=caddy
set CERT_DEST=caddy-root.crt

echo Finding Caddy local root certificate...

for /f "usebackq delims=" %%i in (`docker compose exec -T %CADDY_SERVICE% find ../data -name root.crt`) do (
    set CERT_PATH=%%i
    goto found
)

:found
if "%CERT_PATH%"=="" (
    echo Could not find root.crt inside the Caddy container.
    echo Make sure Caddy is running.
    exit /b 1
)

echo Found certificate at:
echo   %CERT_PATH%

echo Copying certificate to:
echo   %CERT_DEST%

docker compose cp %CADDY_SERVICE%:%CERT_PATH% %CERT_DEST%

if errorlevel 1 (
    echo Failed to copy certificate.
    exit /b 1
)

echo Adding certificate to Windows Trusted Root Certification Authorities...
echo You may need to run this file as Administrator.

certutil -addstore -f Root %CERT_DEST% || (
    echo Failed to trust certificate.
    echo run this file in Administrator CMD shell .
    exit /b 1
)

echo Done.
echo Restart your browser.

endlocal