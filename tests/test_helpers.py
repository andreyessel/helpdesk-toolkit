
import os
from ticket_export import summarize_report

def test_summarize_report_minimal():
    rep = {
        "system": {"timestamp": "2025-08-29T00:00:00Z", "hostname": "testhost", "python_version": "3.10"},
        "memory": {"percent": 50},
        "cpu": {"cpu_percent_overall": 10},
        "disks": [{"percent": 20}],
        "top_processes": [{"pid": 1, "name": "proc1"}]
    }
    s = summarize_report(rep)
    assert s["host"] == "testhost"
    assert s["memory_percent"] == 50
    assert "proc1" in s["top_processes"]
