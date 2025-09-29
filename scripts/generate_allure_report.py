#!/usr/bin/env python3
"""
Allure Report Generation Script

This script generates and optionally opens Allure reports for the pytest API automation project.
It supports both generating reports and serving them locally.

Usage:
    python scripts/generate_allure_report.py [--open] [--clean]
    
Options:
    --open    Open the report in browser after generation
    --clean   Clean previous report before generating new one
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def run_command(command: str, description: str) -> bool:
    """Run a command and return success status."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Error: {e.stderr}")
        return False


def check_allure_installed() -> bool:
    """Check if Allure command line tool is installed."""
    try:
        subprocess.run("allure --version", shell=True, check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def install_allure() -> bool:
    """Install Allure command line tool."""
    print("📦 Allure command line tool not found. Installing...")
    
    # Try different installation methods based on OS
    install_commands = [
        "npm install -g allure-commandline",
        "scoop install allure",
        "choco install allure-commandline"
    ]
    
    for cmd in install_commands:
        print(f"🔄 Trying: {cmd}")
        try:
            subprocess.run(cmd, shell=True, check=True, capture_output=True)
            print("✅ Allure installed successfully")
            return True
        except subprocess.CalledProcessError:
            continue
    
    print("❌ Failed to install Allure. Please install manually:")
    print("   - Windows: scoop install allure or choco install allure-commandline")
    print("   - macOS: brew install allure")
    print("   - Linux: npm install -g allure-commandline")
    return False


def main():
    parser = argparse.ArgumentParser(description="Generate Allure reports for pytest API automation")
    parser.add_argument("--open", action="store_true", help="Open report in browser after generation")
    parser.add_argument("--clean", action="store_true", help="Clean previous report before generating")
    parser.add_argument("--results-dir", default="reports/allure-results", help="Allure results directory")
    parser.add_argument("--report-dir", default="reports/allure-report", help="Allure report directory")
    
    args = parser.parse_args()
    
    # Get project root directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    print("🚀 Allure Report Generation Script")
    print("=" * 50)
    
    # Check if Allure is installed
    if not check_allure_installed():
        if not install_allure():
            sys.exit(1)
    
    # Check if results directory exists
    results_dir = Path(args.results_dir)
    if not results_dir.exists():
        print(f"❌ Results directory not found: {results_dir}")
        print("   Please run tests first with: pytest --alluredir=reports/allure-results")
        sys.exit(1)
    
    # Clean previous report if requested
    if args.clean:
        report_dir = Path(args.report_dir)
        if report_dir.exists():
            print(f"🧹 Cleaning previous report: {report_dir}")
            import shutil
            shutil.rmtree(report_dir)
    
    # Generate report
    generate_cmd = f"allure generate {args.results_dir} -o {args.report_dir} --clean"
    if not run_command(generate_cmd, "Generating Allure report"):
        sys.exit(1)
    
    print(f"📊 Report generated successfully: {args.report_dir}")
    
    # Open report if requested
    if args.open:
        open_cmd = f"allure open {args.report_dir}"
        if not run_command(open_cmd, "Opening Allure report"):
            print("⚠️  Failed to open report automatically. You can open it manually:")
            print(f"   allure open {args.report_dir}")
    
    print("\n🎉 Allure report generation completed!")
    print(f"📁 Report location: {Path(args.report_dir).absolute()}")
    print(f"🌐 To view report: allure open {args.report_dir}")


if __name__ == "__main__":
    main()
