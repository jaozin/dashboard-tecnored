@echo off

echo ======================================
echo GERANDO CONTROLE STATUS DOCUMENTO
echo ======================================

cd /d "%~dp0"

python scripts\script_comp_atualizado.py

pause