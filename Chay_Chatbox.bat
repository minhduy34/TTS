@echo off
chcp 65001 >nul
title KHOI DONG HE THONG TRO LY AI SINH VIEN
echo ========================================================
echo   DANG KHOI DONG TRO LY AI SINH VIEN (MULTI-AGENT NL-TO-SQL)
echo ========================================================
echo.

cd /d "%~dp0"

echo [1/3] Dang khoi dong AI Service (Port 8001)...
start "AI Service (Port 8001)" cmd /k "cd /d "%~dp0ai\src" && uv run python.exe main.py"

echo [2/3] Dang khoi dong Web Backend (Port 8000)...
start "Web Backend (Port 8000)" cmd /k "cd /d "%~dp0fe_be" && uv run python.exe main.py"

echo [3/3] Dang chuan bi mo trinh duyet...
timeout /t 3 /nobreak >nul
start http://localhost:8000

echo.
echo ========================================================
echo   HE THONG DA KHOI DONG HOAN TAT!
echo   Dia chi truy cap: http://localhost:8000
echo   (Khi muon tat he thong, ban chi can chay Tat_Chatbox.bat)
echo ========================================================
timeout /t 5
