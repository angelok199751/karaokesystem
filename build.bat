@echo off
echo === KaraokeForge Build ===

echo [1/4] Creating virtual environment...
python -m venv .venv
call .venv\Scripts\activate.bat

echo [2/4] Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

echo [3/4] Downloading ML models...
python -c "from src.utils.models import download_all; download_all()"

echo [4/4] Building executable...
pyinstaller karaoke_forge.spec

echo === Build complete! ===
echo Executable: dist\KaraokeForge\KaraokeForge.exe
pause
