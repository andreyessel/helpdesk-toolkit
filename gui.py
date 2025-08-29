
#!/usr/bin/env python3
"""
gui.py - Simple Tkinter GUI to run helpdesk.py and show output.
Click "Run Diagnostics" to execute helpdesk.py and view summary in the text box.
"""
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
import subprocess
import threading
import os
import sys

SCRIPT = "helpdesk.py"  # script to run; ensure you're in the project folder

def run_command(cmd, output_widget):
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in proc.stdout:
            output_widget.insert(tk.END, line)
            output_widget.see(tk.END)
        proc.wait()
    except Exception as e:
        output_widget.insert(tk.END, f"Error running command: {e}\\n")

def on_run(output_widget):
    output_widget.delete("1.0", tk.END)
    output_widget.insert(tk.END, "Running diagnostics...\\n")
    # run in new thread to avoid blocking GUI
    def target():
        cmd = [sys.executable, SCRIPT, "--report", "gui_report.json"]
        run_command(cmd, output_widget)
        output_widget.insert(tk.END, "\\nDone. Saved gui_report.json\\n")
    threading.Thread(target=target, daemon=True).start()

def build_gui():
    root = tk.Tk()
    root.title("Help-desk Toolkit (GUI)")
    root.geometry("800x600")
    frame = tk.Frame(root)
    frame.pack(fill=tk.BOTH, expand=True)
    btn = tk.Button(frame, text="Run Diagnostics", command=lambda: on_run(text))
    btn.pack(padx=10, pady=10)
    text = ScrolledText(frame)
    text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    root.mainloop()

if __name__ == "__main__":
    build_gui()
