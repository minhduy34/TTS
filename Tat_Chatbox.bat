@echo off
chcp 65001 >nul
echo ========================================================
echo   DANG TAT HE THONG TRO LY AI SINH VIEN...
echo ========================================================
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000" ^| findstr "LISTENING"') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8001" ^| findstr "LISTENING"') do taskkill /F /PID %%a >nul 2>&1
echo Da tat thanh cong cac tien trinh tren cong 8000 va 8001!
timeout /t 2 >nul
