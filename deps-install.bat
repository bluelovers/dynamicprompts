@echo off
setlocal enabledelayedexpansion

rem ===========================================================================
rem  deps-install.bat - initialise project dependencies
rem
rem  Usage:
rem    deps-install              install core + yaml + dev (default)
rem    deps-install --all        install every extra (magicprompt, feelinglucky)
rem    deps-install --no-dev     runtime deps only, no dev tools
rem    deps-install [any uv sync args...]
rem
rem  Creates .venv and pins versions from uv.lock.
rem
rem  NOTE: keep this file ASCII-only. Non-ASCII bytes are read in the
rem  console codepage and will corrupt command parsing.
rem ===========================================================================

cd /d "%~dp0"

rem -- collect all arguments --------------------------------------------------
set "ARGS="
:collect
if "%~1"=="" goto :dispatch
set ARGS=!ARGS! %1
shift
goto :collect

:dispatch
rem -- default to the extras this project expects ----------------------------
if "!ARGS!"=="" set ARGS=--extra yaml --extra dev

echo [deps] running: uv sync!ARGS!
uv sync!ARGS!
if errorlevel 1 (
    echo [deps] dependency install failed, see the output above.
    exit /b 1
)

echo [deps] done.
exit /b 0
