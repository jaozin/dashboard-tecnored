@echo off

echo ======================================
echo PROCESSAMENTO DE SPRINT DO CRONOGRAMA
echo ======================================

cd /d "%~dp0"

python scripts\processar_sprint_comparativo.py

pause