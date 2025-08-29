
# Help-desk Toolkit (starter)

A simple Python CLI that collects basic system diagnostics and saves a JSON report. Designed as a beginner-friendly starter project for a help-desk / desktop support portfolio.

## What it does (short)
- Collects OS, hostname, Python version
- Lists network interfaces and DNS lookup
- Reports CPU, memory, disk usage
- Lists top processes by memory usage
- Pings one or more hosts and records results
- Saves a JSON report for triage

## Quick start (Windows)

1. Install Python 3.10+ from https://www.python.org and make sure "Add Python to PATH" is checked.
2. Open PowerShell or CMD.
3. Create a folder and enter it:
   ```powershell
   mkdir helpdesk_toolkit
   cd helpdesk_toolkit
   ```
4. (Optional) Create a virtual environment and activate it:
   ```powershell
   python -m venv venv
   .\\venv\\Scripts\\activate
   ```
5. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
6. Run the tool:
   ```powershell
   python helpdesk.py --report my_report.json --ping 8.8.8.8 1.1.1.1
   ```

## Notes
- Some parts (like service restart or clearing system temp) require administrator privileges; this starter focuses on safe read-only diagnostics.
- Add features gradually: GUI, remote agent, one-click fixes as stretch goals.

## How to use for job applications
Put the repo link on your resume and include a one-line bullet like:
> Built a Python-based help-desk diagnostics CLI that collects system info, pings endpoints, and outputs a triage-ready JSON report.
