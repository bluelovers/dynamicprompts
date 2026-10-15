@echo off
setlocal enabledelayedexpansion

rem ===========================================================================
rem  dev.bat - launcher for tests and ruff
rem
rem  Usage:
rem    dev test  [args]   run pytest
rem    dev cov   [args]   run pytest with coverage
rem    dev lint  [args]   ruff check
rem    dev fmt   [args]   ruff format
rem    dev check          ruff check + ruff format --check
rem    dev fix   [args]   ruff check --fix
rem    dev                show this help
rem
rem  Arguments are passed through unchanged, e.g.:
rem    dev test -k diagnostics -x
rem
rem  NOTE: keep this file ASCII-only. Non-ASCII bytes are read in the
rem  console codepage and will corrupt command parsing.
rem ===========================================================================

cd /d "%~dp0"

set "CMD=%~1"
if "%CMD%"=="" goto :help

rem -- collect every argument after the command, preserving quotes ------------
shift
set "ARGS="
:collect
if "%~1"=="" goto :dispatch
set ARGS=!ARGS! %1
shift
goto :collect

rem -- dispatch ---------------------------------------------------------------
:dispatch
if /i "%CMD%"=="test"  goto :do_test
if /i "%CMD%"=="cov"   goto :do_cov
if /i "%CMD%"=="lint"  goto :do_lint
if /i "%CMD%"=="fmt"   goto :do_fmt
if /i "%CMD%"=="check" goto :do_check
if /i "%CMD%"=="fix"   goto :do_fix
echo [dev] unknown command: %CMD%
goto :help

:do_test
uv run pytest!ARGS!
exit /b %ERRORLEVEL%

:do_cov
uv run pytest --cov=dynamicprompts --cov-report=term-missing!ARGS!
exit /b %ERRORLEVEL%

:do_lint
uv run ruff check .!ARGS!
exit /b %ERRORLEVEL%

:do_fmt
uv run ruff format .!ARGS!
exit /b %ERRORLEVEL%

:do_check
uv run ruff check .
if errorlevel 1 exit /b 1
uv run ruff format --check .
exit /b %ERRORLEVEL%

:do_fix
uv run ruff check --fix .!ARGS!
exit /b %ERRORLEVEL%

:help
echo.
echo Usage: dev ^<command^> [args...]
echo.
echo   test  [args]   run pytest
echo   cov   [args]   run pytest with coverage
echo   lint  [args]   ruff check
echo   fmt   [args]   ruff format
echo   check          ruff check + ruff format --check
echo   fix   [args]   ruff check --fix
echo.
exit /b 0
