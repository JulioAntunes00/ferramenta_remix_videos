@echo off
title Multiplicador de Videos TikTok - Inicializador Local
echo ====================================================
echo   INICIANDO MULTIPLICADOR DE VIDEOS TIKTOK
echo ====================================================
echo.

echo 1. Iniciando Backend FastAPI (Porta 8000)...
start "Backend - Multiplicador TikTok" cmd /k "cd backend && uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

echo 2. Iniciando Frontend Vite React (Porta 5173)...
start "Frontend - Multiplicador TikTok" cmd /k "cd frontend && npm run dev"

echo.
echo Tudo pronto! O sistema estara acessivel em:
echo http://localhost:5173
echo.
timeout /t 5
start http://localhost:5173
