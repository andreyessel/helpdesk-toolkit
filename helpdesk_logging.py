
#!/usr/bin/env python3
"""
helpdesk_logging.py - Same diagnostics as helpdesk.py but with logging to file.
Logs are written to logs/helpdesk.log and also printed to console.
"""

import logging
import argparse
import json
import datetime
import tempfile
import os
import sys
try:
    import psutil
except ImportError:
    psutil = None

# Configure logging
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
log_file = os.path.join(LOG_DIR, "helpdesk.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger("helpdesk")

def now_iso():
    return datetime.datetime.utcnow().isoformat() + "Z"

def bytes_to_mb(b):
    try:
        return round(b / 1024 / 1024, 1)
    except Exception:
        return None

def collect_basic_report():
    report = {"timestamp": now_iso()}
    if psutil is None:
        logger.error("psutil not installed. Install with pip install -r requirements.txt")
        return report
    try:
        report["memory"] = {"percent": psutil.virtual_memory().percent}
        report["cpu"] = {"logical_processors": psutil.cpu_count(logical=True), "cpu_percent_overall": psutil.cpu_percent(interval=0.5)}
        report["disks"] = []
        for p in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(p.mountpoint)
                report["disks"].append({"mountpoint": p.mountpoint, "percent": usage.percent})
            except Exception:
                pass
        # top 3 processes
        procs = []
        for p in psutil.process_iter(attrs=['pid','name','memory_info']):
            info = p.info
            mem = info.get('memory_info')
            mem_rss = mem.rss if mem else 0
            procs.append((mem_rss, info.get('pid'), info.get('name')))
        procs.sort(reverse=True)
        report["top_processes"] = [{"pid": pid, "name": name, "memory_mb": bytes_to_mb(mem)} for mem,pid,name in procs[:3]]
    except Exception as e:
        logger.exception("Error collecting report: %s", e)
    return report

def save_report(report, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    logger.info("Saved report to %s", path)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", "-r", default="report.json")
    parser.add_argument("--ping", "-p", nargs="*", default=["8.8.8.8"])
    args = parser.parse_args()
    logger.info("Starting helpdesk_logging run")
    report = collect_basic_report()
    # Add ping placeholders; full ping functionality can be copied from helpdesk.py if desired
    report["pings"] = {h: {"status": "unknown"} for h in args.ping}
    save_report(report, args.report)
    logger.info("Done. Log file: %s", log_file)

if __name__ == "__main__":
    main()
