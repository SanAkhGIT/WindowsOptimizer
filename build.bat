@echo off
setlocal
py -m pip install -r requirements.txt
pyinstaller --noconfirm --clean --onefile --windowed --add-data "extensions;extensions" --name WindowsOptimizer main.py
echo.
echo Build complete:
echo dist\WindowsOptimizer.exe
pause
