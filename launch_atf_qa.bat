@echo off
echo ========================================
echo  ATF Local Q^&A Server
echo  RobotRoss Compliance Wiki
echo ========================================
echo.

cd /d "%~dp0"
git checkout task/8dvp6ma64g1co2w >nul 2>&1

echo Starting server... (browser will open in 3 seconds)
echo.

:: Start server in its own window so logs are visible there
start "ATF Q&A Server" cmd /k "python ATF\tools\atf_local_server.py"

:: Give the server time to load the corpus
timeout /t 3 /nobreak >nul

:: Open the browser
start "" "http://localhost:8771/index_local.html"

echo Server is running at http://localhost:8771
echo.
echo Close the "ATF Q^&A Server" window to stop the server.
echo You can close this window now.
echo.
pause
