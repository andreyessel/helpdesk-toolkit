
#!/usr/bin/env python3
"""
ticket_export.py - Create a small CSV ticket summary from a JSON report.
Usage:
  python ticket_export.py my_report.json ticket.csv
The CSV contains: timestamp, host, python_version, memory_percent, cpu_percent, disk_percent, top_processes
"""
import sys, json, csv, os

def read_report(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def summarize_report(rep):
    sys_info = rep.get("system", {})
    mem = rep.get("memory", {})
    cpu = rep.get("cpu", {})
    disks = rep.get("disks", [])
    top = rep.get("top_processes", [])
    disk_percent = disks[0].get("percent") if disks else ""
    top_names = "; ".join([f"{p.get('name')} (pid {p.get('pid')})" for p in top])
    return {
        "timestamp": sys_info.get("timestamp"),
        "host": sys_info.get("hostname"),
        "python_version": sys_info.get("python_version"),
        "memory_percent": mem.get("percent"),
        "cpu_percent_overall": cpu.get("cpu_percent_overall"),
        "disk_percent": disk_percent,
        "top_processes": top_names
    }

def write_csv(summary, out_path):
    keys = ["timestamp","host","python_version","memory_percent","cpu_percent_overall","disk_percent","top_processes"]
    with open(out_path, "w", newline='', encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=keys)
        writer.writeheader()
        writer.writerow(summary)

def main():
    if len(sys.argv) < 3:
        print("Usage: python ticket_export.py my_report.json ticket.csv")
        sys.exit(1)
    in_path = sys.argv[1]
    out_path = sys.argv[2]
    rep = read_report(in_path)
    summary = summarize_report(rep)
    write_csv(summary, out_path)
    print(f"Wrote ticket summary to {out_path}")

if __name__ == "__main__":
    main()
