@echo off
REM EchoGuard v2.0 MIGRATION SCRIPT FOR WINDOWS
REM Run this to setup everything properly

echo.
echo ====================================
echo 🚨  EchoGuard v2.0 Setup Script
echo ====================================
echo.

REM Check Python
python --version
echo.

REM Create virtual environment
echo 📦 Setting up virtual environment...
python -m venv venv
call venv\Scripts\activate.bat
echo ✅ Virtual environment created
echo.

REM Install dependencies
echo 📥 Installing dependencies...
python -m pip install --upgrade pip
pip install streamlit
pip install qdrant-client  
pip install open-clip-torch
pip install torch torchvision
pip install Pillow
pip install python-dotenv
pip install numpy

echo ✅ Dependencies installed
echo.

REM Create .env if not exists
if not exist .env (
    echo 📝 Creating .env file...
    (
        echo QDRANT_URL=http://localhost:6333
        echo QDRANT_API_KEY=
        echo DEVICE=cpu
        echo OPENAI_API_KEY=
    ) > .env
    echo ✅ .env created (update with your keys if needed)
) else (
    echo ✅ .env already exists
)

echo.
echo ====================================
echo ✅  Setup Complete!
echo ====================================
echo.
echo Next steps:
echo 1. Start Qdrant: docker run -p 6333:6333 qdrant/qdrant:latest
echo 2. Run app: streamlit run app_fixed.py
echo.
pause
