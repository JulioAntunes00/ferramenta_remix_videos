@echo off
title Remix Videos - Inicializador Local
echo ====================================================
echo      INICIANDO SISTEMA REMIX VIDEOS ANTI-BAN
echo ====================================================
echo.

echo 1. Iniciando Backend FastAPI (Porta 8000)...
start "Backend - Remix Videos" cmd /k "cd backend && uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

echo 2. Iniciando Frontend Vite React (Porta 5173)...
start "Frontend - Remix Videos" cmd /k "cd frontend && npm run dev"

echo.
echo Tudo pronto! O sistema estara acessivel em:
echo http://localhost:5173
echo.
timeout /t 5
start http://localhost:5173
