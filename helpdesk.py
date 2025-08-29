#!/usr/bin/env python3
"""
helpdesk.py - Help-desk Toolkit CLI (enhanced + safe --fix mode)

This script does read-only checks (CPU, memory, disks, network, top processes)
and can optionally offer safe, interactive fixes (terminate a process,
clean user temp files, stop OneDrive). The fixes always ask for confirmation.

How to use:
  python helpdesk.py --report my_report.json --ping 8.8.8.8 1.1.1.1
  python helpdesk.py --report my_report.json --ping 8.8.8.8 --fix

Notes:
- The script mostly *reads* system information. It will only perform actions
  when you explicitly run with --fix and confirm each action.
- Deleting files or terminating processes can cause data loss if a program
  has unsaved work. The script asks for confirmation before doing anything.
"""

# Standard library imports
import argparse    # for parsing command line arguments like --report or --fix
import platform    # to find OS details (Windows, Linux, macOS)
import socket      # to get hostname and DNS info
import json        # to save the report as JSON
import datetime    # to timestamp the report
import subprocess  # to run ping command
import sys         # for general system functions
import os          # for file operations
import tempfile    # to find the user's temp folder
import time        # for time calculations when cleaning temp
import shutil      # could be used for safe file operations (not heavily used here)

# Third-party import (psutil gives access to CPU/memory/process info).
# If it's not installed, psutil will be None and we tell the user to install it.
try:
    import psutil
except ImportError:
    psutil = None

# Simple helper: return current time in ISO format (human + machine-friendly)
def now_iso():
    return datetime.datetime.utcnow().isoformat() + "Z"

# Collect basic system info: OS, architecture, hostname, Python version
def collect_system_info():
    info = {
        "timestamp": now_iso(),
        "platform": platform.system(),
        "platform_release": platform.release(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "hostname": socket.gethostname(),
        "python_version": platform.python_version(),
    }
    return info

# Get network interface addresses (IP, MAC), and do a simple DNS lookup
def get_network_info():
    nets = {}
    try:
        # psutil.net_if_addrs returns addresses for each network interface
        addrs = psutil.net_if_addrs()
        for iface, addr_list in addrs.items():
            nets[iface] = []
            for a in addr_list:
                # We convert address family to string so JSON will be readable
                nets[iface].append({
                    "family": str(a.family),
                    "address": a.address,
                    "netmask": a.netmask,
                    "broadcast": a.broadcast
                })
    except Exception as e:
        # If something goes wrong, record the error instead of crashing
        nets["error"] = str(e)

    # Add a simple DNS lookup for the hostname (helps show primary IP)
    try:
        host = socket.gethostname()
        nets["dns_lookup"] = socket.gethostbyname_ex(host)
    except Exception as e:
        nets["dns_error"] = str(e)

    return nets

# CPU details: core counts and basic CPU percent usage
def cpu_info():
    try:
        cpu = {
            "physical_cores": psutil.cpu_count(logical=False),
            "logical_processors": psutil.cpu_count(logical=True),
            # percent per CPU core (this will sleep 1 second for measurement)
            "cpu_percent_per_cpu": psutil.cpu_percent(interval=1, percpu=True),
            # overall CPU percent (brief measurement)
            "cpu_percent_overall": psutil.cpu_percent(interval=0.5),
        }
    except Exception as e:
        cpu = {"error": str(e)}
    return cpu

# Memory snapshot: total, available, used, percent used
def memory_info():
    try:
        vm = psutil.virtual_memory()
        return {"total": vm.total, "available": vm.available, "used": vm.used, "percent": vm.percent}
    except Exception as e:
        return {"error": str(e)}

# Disk usage: iterate partitions and record used/free/percent
def disk_info():
    parts = []
    try:
        for p in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(p.mountpoint)
                parts.append({
                    "device": p.device,
                    "mountpoint": p.mountpoint,
                    "fstype": p.fstype,
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free,
                    "percent": usage.percent
                })
            except Exception as e:
                # if a partition cannot be read, record the error for that device
                parts.append({"device": p.device, "error": str(e)})
    except Exception as e:
        parts = [{"error": str(e)}]
    return parts

# List top processes by memory usage (we return n results)
def top_processes(n=5):
    procs = []
    try:
        # iterate processes and collect pid, name, username, memory, cpu%
        for p in psutil.process_iter(attrs=['pid','name','username','memory_info','cpu_percent']):
            info = p.info
            mem = info.get('memory_info')
            mem_rss = mem.rss if mem else None
            procs.append({
                "pid": info.get('pid'),
                "name": info.get('name'),
                "user": info.get('username'),
                "memory_rss": mem_rss,
                "cpu_percent": info.get('cpu_percent')
            })
        # sort by memory (largest first)
        procs_sorted = sorted(procs, key=lambda x: x.get('memory_rss') or 0, reverse=True)
        return procs_sorted[:n]
    except Exception as e:
        return [{"error": str(e)}]

# Cross-platform ping wrapper that runs the OS ping command and captures output
def ping_host(host, count=1, timeout=1000):
    param = "-n" if platform.system().lower()=="windows" else "-c"
    cmd = ["ping", param, str(count), host]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return {"returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}
    except Exception as e:
        return {"error": str(e)}

# Run all checks and assemble the report dictionary
def run_checks(args):
    # If psutil missing, return an error dict - the main will print this
    if psutil is None:
        return {"error": "psutil not installed. run `pip install -r requirements.txt`"}

    report = {}
    report["system"] = collect_system_info()
    report["network"] = get_network_info()
    report["cpu"] = cpu_info()
    report["memory"] = memory_info()
    report["disks"] = disk_info()
    report["top_processes"] = top_processes(n=args.top_processes)

    report["pings"] = {}
    # ping every host provided on the command line
    for h in args.ping:
        report["pings"][h] = ping_host(h)

    return report

# Small helper to convert bytes into megabytes (MB) with one decimal
def bytes_to_mb(b):
    try:
        return round(b / 1024 / 1024, 1)
    except Exception:
        return None

# Print a readable summary to the console (short, human-friendly)
def pretty_print_summary(report):
    sys_info = report.get("system", {})
    print("=== Help-desk Toolkit Summary ===")
    print(f"Host: {sys_info.get('hostname')} - Platform: {sys_info.get('platform')} {sys_info.get('platform_release')}")
    print(f"Python: {sys_info.get('python_version')}")
    print("CPU logical:", report.get("cpu", {}).get("logical_processors"))
    print("CPU overall %:", report.get("cpu", {}).get("cpu_percent_overall"))

    mem = report.get("memory", {})
    print("Memory % used:", mem.get("percent"))

    # show top processes with memory in MB so numbers are easier to read
    print("Top processes by memory:")
    for p in report.get("top_processes", [])[:5]:
        name = p.get("name") or "<unknown>"
        pid = p.get("pid")
        mem_bytes = p.get("memory_rss")
        mem_mb = bytes_to_mb(mem_bytes) if mem_bytes else "?"
        print(f"  {name} (pid {pid}) memory={mem_mb} MB")

    # ping summary (reachable or not)
    if report.get("pings"):
        print("Ping results:")
        for host, res in report["pings"].items():
            if isinstance(res, dict) and res.get("returncode") == 0:
                print(f"  {host} reachable")
            else:
                print(f"  {host} NOT reachable (see report)")

# Based on the report data, produce a list of suggestions and print advice
# Each suggestion is a tuple: (action_code, readable_text, data)
# - action_code: internal code used by interactive_fix to decide what to do
# - readable_text: shown to the user in the menu
# - data: optional extra (e.g., PID to kill)
def suggest_actions(report):
    suggestions = []
    print("\n=== Suggestions ===")

    # Memory check: if memory usage > 80% we recommend action
    mem = report.get("memory", {})
    mem_pct = mem.get("percent")
    if isinstance(mem_pct, (int, float)) and mem_pct > 80:
        print(f"- Memory is high ({mem_pct}%). Consider closing heavy programs or restarting apps.")
        top = report.get("top_processes", [])[:3]
        print("  Top memory users:")
        for p in top:
            name = p.get("name") or "<unknown>"
            pid = p.get("pid")
            mb = bytes_to_mb(p.get("memory_rss")) or "?"
            print(f"    • {name} (pid {pid}) ~ {mb} MB")
        print("  Suggested quick actions: close extra Chrome tabs, pause OneDrive sync, reboot if needed.")
        # Offer to terminate the top processes (we add kill tasks to suggestions)
        for p in top:
            suggestions.append(("kill_process", f"Terminate process {p.get('name')} (pid {p.get('pid')})", p.get('pid')))
    else:
        print("- Memory looks okay.")

    # CPU check: if overall CPU is very high, surface suggestion
    cpu_overall = report.get("cpu", {}).get("cpu_percent_overall")
    if isinstance(cpu_overall, (int, float)) and cpu_overall > 85:
        print(f"- CPU usage is high ({cpu_overall}%). Check processes or consider rebooting.")
    else:
        print("- CPU usage looks okay.")

    # Disk check: warn if any partition is over 90% used
    disks = report.get("disks", [])
    high_disks = [d for d in disks if isinstance(d, dict) and d.get("percent") and d.get("percent") > 90]
    if high_disks:
        print("- Disk usage is high on:")
        for d in high_disks:
            print(f"  • {d.get('mountpoint')} {d.get('percent')}% used")
        print("  Consider cleaning temp files or freeing space.")
        # Suggest cleaning the user temp folder (safer than touching system folders)
        suggestions.append(("clean_temp", "Clean user temporary files older than X days", None))
    else:
        print("- Disk usage looks okay.")

    # Detect OneDrive (common source of high memory/disk activity)
    onedrive_present = any((p.get("name") or "").lower().startswith("onedrive") for p in report.get("top_processes", []))
    if onedrive_present:
        print("- OneDrive appears to be running and using memory. You can pause syncing or exit OneDrive if desired.")
        suggestions.append(("stop_onedrive", "Stop OneDrive process (pause syncing)", None))

    # Ping/network check: if any tested host is unreachable, suggest network checks
    pings = report.get("pings", {})
    unreachable = [h for h, r in pings.items() if not (isinstance(r, dict) and r.get("returncode") == 0)]
    if unreachable:
        print(f"- Some hosts are unreachable: {', '.join(unreachable)}. Check network cable, Wi-Fi, or router.")
    else:
        print("- Network connectivity to tested hosts looks OK.")

    # Return the action suggestions so interactive_fix can show them
    return suggestions

# -----------------------------
# Safe action helper functions
# -----------------------------

# Simple yes/no prompt that returns True only for 'y'
def confirm(prompt):
    while True:
        ans = input(f"{prompt} [y/N]: ").strip().lower()
        if ans == "y":
            return True
        if ans == "n" or ans == "":
            return False

# Attempt to gracefully terminate a process by PID, escalate to kill if needed
def kill_process(pid):
    try:
        p = psutil.Process(int(pid))
        name = p.name()
        print(f"Attempting to terminate {name} (pid {pid}) ...")
        p.terminate()  # send terminate signal
        try:
            p.wait(timeout=5)  # wait up to 5 seconds for it to cleanly exit
            print("Process terminated.")
            return True, f"Terminated {name} (pid {pid})"
        except psutil.TimeoutExpired:
            # If it doesn't exit, force kill
            p.kill()
            p.wait(timeout=3)
            print("Process killed.")
            return True, f"Killed {name} (pid {pid})"
    except (psutil.NoSuchProcess, ValueError) as e:
        return False, f"Process {pid} not found: {e}"
    except psutil.AccessDenied:
        # Windows may block termination of some system processes
        return False, "Access denied. Try running PowerShell as Administrator."
    except Exception as e:
        return False, str(e)

# Clean files from the user's temporary folder that are older than `older_than_days`
# This only touches the user's temp directory (safe-ish) and does not modify system folders
def clean_user_temp(older_than_days=3):
    temp_dir = tempfile.gettempdir()  # user's temp path, e.g., C:\Users\andre\AppData\Local\Temp
    deleted_files = 0
    deleted_bytes = 0
    now_ts = time.time()
    cutoff = now_ts - (older_than_days * 86400)  # convert days to seconds

    # Walk the temp folder and remove old files. We ignore errors to avoid crashes.
    for root, dirs, files in os.walk(temp_dir):
        for name in files:
            try:
                full = os.path.join(root, name)
                mtime = os.path.getmtime(full)
                if mtime < cutoff:
                    size = os.path.getsize(full)
                    os.remove(full)
                    deleted_files += 1
                    deleted_bytes += size
            except Exception:
                # ignore permission errors and busy files
                pass
    return deleted_files, deleted_bytes, temp_dir

# Attempt to stop OneDrive processes by name (simple, works for common OneDrive executables)
def stop_onedrive_processes():
    stopped = []
    failed = []
    for p in psutil.process_iter(attrs=['pid','name']):
        n = (p.info.get('name') or '').lower()
        if n.startswith("onedrive"):
            try:
                p.terminate()
                p.wait(timeout=5)
                stopped.append((p.info.get('pid'), p.info.get('name')))
            except Exception as e:
                failed.append((p.info.get('pid'), str(e)))
    return stopped, failed

# Interactive menu for running safe fixes suggested earlier
def interactive_fix(suggestions):
    if not suggestions:
        print("\nNo automated suggestions available to fix.")
        return

    print("\n=== Fix Mode: Safe actions you can run ===")
    # Show each suggestion with a number so user can pick one
    for i, s in enumerate(suggestions, start=1):
        code, text, data = s
        print(f" {i}. {text}")
    print(" 0. Exit without doing anything")

    # Ask the user to pick an action number
    try:
        choice = int(input("Choose an action number to run (0 to exit): ").strip() or "0")
    except Exception:
        print("Invalid choice. Exiting.")
        return

    if choice == 0:
        print("Exiting fix mode.")
        return
    if not (1 <= choice <= len(suggestions)):
        print("Choice out of range. Exiting.")
        return

    action = suggestions[choice - 1]
    code, text, data = action

    # If the action is to kill a process, we may already have a PID included.
    if code == "kill_process":
        pid = data
        if pid is None:
            pid = input("Enter PID to terminate: ").strip()
        else:
            print(f"Selected to terminate PID {pid}")
        # Warn the user about unsaved work being lost and confirm
        print("WARNING: this will close the program immediately and could cause unsaved work to be lost.")
        if confirm(f"Proceed to terminate PID {pid}?"):
            ok, msg = kill_process(pid)
            print(msg)
        else:
            print("Aborted by user.")

    # Clean user temp files older than a user-chosen number of days
    elif code == "clean_temp":
        days_str = input("Delete files older than how many days? (default 3): ").strip() or "3"
        try:
            days = int(days_str)
        except:
            days = 3
        print(f"This will permanently delete files from your user temp folder older than {days} days: {tempfile.gettempdir()}")
        if confirm("Proceed with cleaning temp files?"):
            files_deleted, bytes_deleted, temp_dir = clean_user_temp(days)
            print(f"Deleted {files_deleted} files (~{round(bytes_deleted/1024/1024,1)} MB) from {temp_dir}")
        else:
            print("Aborted by user.")

    # Stop OneDrive: attempt to terminate OneDrive processes
    elif code == "stop_onedrive":
        print("This will attempt to stop OneDrive processes (pause syncing).")
        if confirm("Proceed to stop OneDrive processes?"):
            stopped, failed = stop_onedrive_processes()
            if stopped:
                print("Stopped processes:", stopped)
            if failed:
                print("Failed to stop:", failed)
            if not stopped and not failed:
                print("No OneDrive processes found.")
        else:
            print("Aborted by user.")

    else:
        print("Unknown action code. Exiting.")

# Save the full JSON report to a file for later inspection or to attach to a ticket
def save_report(report, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"Saved report to {path}")

# Main entrypoint: parse args, run checks, print summary, optionally run fixes
def main():
    parser = argparse.ArgumentParser(description="Help-desk Toolkit CLI (enhanced + fix)")
    parser.add_argument("--report", "-r", default="report.json", help="Path to write JSON report")
    parser.add_argument("--ping", "-p", nargs="*", default=["8.8.8.8"], help="Host(s) to ping")
    parser.add_argument("--top-processes", "-t", type=int, default=5, help="Number of top processes to include")
    # --fix triggers the interactive fix menu (we still ask before doing anything)
    parser.add_argument("--fix", action="store_true", help="Interactive safe fix mode (prompts before actions)")
    args = parser.parse_args()

    # Run the checks and build a dictionary called `report`
    report = run_checks(args)

    # Print a small human-friendly summary
    pretty_print_summary(report)

    # Derive suggestions (list of safe actions) and show them
    suggestions = suggest_actions(report)

    # Save the full report to disk as JSON
    save_report(report, args.report)

    # If user passed --fix, show the interactive menu to run a chosen safe action
    if args.fix:
        interactive_fix(suggestions)

# Only run main if this file is executed as the main program
if __name__ == "__main__":
    main()
