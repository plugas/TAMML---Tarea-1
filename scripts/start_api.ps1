# Arranca la API del agente (Módulo 3) — PowerShell
Set-Location $PSScriptRoot\..
Write-Host "API Riopaila en http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "Health: http://127.0.0.1:8000/health" -ForegroundColor Cyan
uvicorn riopaila_rag.api.main:app --host 0.0.0.0 --port 8000
