
# Help-desk Toolkit — Full Project (Enhanced)

This repository is a beginner-friendly Python toolkit for basic help-desk diagnostics and safe, interactive fixes.
It includes:
- `helpdesk.py` — main, commented diagnostics CLI (existing).
- `helpdesk_logging.py` — same functionality plus logging to `logs/helpdesk.log`.
- `ticket_export.py` — convert a JSON report into a CSV "ticket" summary for attachments.
- `gui.py` — small Tkinter GUI wrapper to run diagnostics and show results.
- `tests/` — pytest tests for helper functions.
- GitHub Actions workflow for CI (tests + lint).

## Quick Start (Windows)

1. Create and activate a virtual environment:
```powershell
python -m venv venv
.env\Scripts\Activate.ps1
```

2. Install dependencies:
```powershell
pip install -r requirements.txt
```

3. Run diagnostics (console):
```powershell
python helpdesk.py --report my_report.json --ping 8.8.8.8 1.1.1.1
```

4. Run diagnostics with safe interactive fixes:
```powershell
python helpdesk.py --report my_report.json --ping 8.8.8.8 --fix
```

5. Run the GUI (Windows):
```powershell
python gui.py
```

6. Export a CSV ticket from a JSON report:
```powershell
python ticket_export.py my_report.json ticket.csv
```

## Logging
Use `helpdesk_logging.py` to record operations and suggestions to `logs/helpdesk.log`:
```powershell
python helpdesk_logging.py --report my_report.json --ping 8.8.8.8 --fix
```

## Tests and CI
Run tests locally:
```powershell
pip install pytest
pytest -q
```

The repository includes a GitHub Actions workflow at `.github/workflows/ci.yml` that installs deps and runs tests on push/PR.

## Resume / GitHub suggestions
- Add a 10-20 second demo GIF (run the script and record terminal output).
- Add screenshots and a short demo in README.
- Keep commit history tidy and write a one-line resume bullet:
  > Built a Python help-desk diagnostics CLI that collects system info, performs network checks, saves triage-ready JSON reports, and offers safe interactive fixes and CSV ticket export.

