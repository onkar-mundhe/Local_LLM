@echo off
title Qwen Server
cd /d "%~dp0"
python start_server.py
if not "%1"=="silent" pause
