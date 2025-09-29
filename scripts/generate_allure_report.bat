@echo off
REM Allure Report Generation Script for Windows
REM This script generates and optionally opens Allure reports for the pytest API automation project.

setlocal enabledelayedexpansion

REM Default values
set OPEN_REPORT=false
set CLEAN_REPORT=false
set RESULTS_DIR=reports\allure-results
set REPORT_DIR=reports\allure-report

REM Parse command line arguments
:parse_args
if "%1"=="--open" (
    set OPEN_REPORT=true
    shift
    goto parse_args
)
if "%1"=="--clean" (
    set CLEAN_REPORT=true
    shift
    goto parse_args
)
if "%1"=="--results-dir" (
    set RESULTS_DIR=%2
    shift
    shift
    goto parse_args
)
if "%1"=="--report-dir" (
    set REPORT_DIR=%2
    shift
    shift
    goto parse_args
)
if "%1"=="" goto start_script
if "%1"=="--help" goto show_help
echo Unknown option: %1
goto show_help

:show_help
echo Usage: generate_allure_report.bat [--open] [--clean] [--results-dir DIR] [--report-dir DIR]
echo.
echo Options:
echo   --open         Open report in browser after generation
echo   --clean        Clean previous report before generating
echo   --results-dir  Allure results directory (default: reports\allure-results)
echo   --report-dir   Allure report directory (default: reports\allure-report)
echo   --help         Show this help message
goto end

:start_script
echo 🚀 Allure Report Generation Script
echo ==================================================

REM Check if Allure is installed
allure --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Allure command line tool not found.
    echo Please install Allure first:
    echo   - Using Scoop: scoop install allure
    echo   - Using Chocolatey: choco install allure-commandline
    echo   - Using npm: npm install -g allure-commandline
    goto end
)

REM Check if results directory exists
if not exist "%RESULTS_DIR%" (
    echo ❌ Results directory not found: %RESULTS_DIR%
    echo Please run tests first with: pytest --alluredir=reports\allure-results
    goto end
)

REM Clean previous report if requested
if "%CLEAN_REPORT%"=="true" (
    if exist "%REPORT_DIR%" (
        echo 🧹 Cleaning previous report: %REPORT_DIR%
        rmdir /s /q "%REPORT_DIR%"
    )
)

REM Generate report
echo 🔄 Generating Allure report...
allure generate "%RESULTS_DIR%" -o "%REPORT_DIR%" --clean
if errorlevel 1 (
    echo ❌ Failed to generate Allure report
    goto end
)

echo ✅ Report generated successfully: %REPORT_DIR%

REM Open report if requested
if "%OPEN_REPORT%"=="true" (
    echo 🔄 Opening Allure report...
    allure open "%REPORT_DIR%"
    if errorlevel 1 (
        echo ⚠️  Failed to open report automatically. You can open it manually:
        echo    allure open %REPORT_DIR%
    )
)

echo.
echo 🎉 Allure report generation completed!
echo 📁 Report location: %CD%\%REPORT_DIR%
echo 🌐 To view report: allure open %REPORT_DIR%

:end
