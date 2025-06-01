#!/usr/bin/env python3
import os
import signal
import psutil

print("🔍 Ricerca processi Python duplicati...")

current_pid = os.getpid()
python_processes = []

for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        if proc.info['name'] and 'python' in proc.info['name'].lower():
            if proc.info['cmdline'] and any('main.py' in arg for arg in proc.info['cmdline']):
                if proc.info['pid'] != current_pid:
                    python_processes.append(proc.info['pid'])
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass

if python_processes:
    print(f"⚠️ Trovati {len(python_processes)} processi bot duplicati")
    for pid in python_processes:
        try:
            os.kill(pid, signal.SIGTERM)
            print(f"✅ Terminato processo {pid}")
        except:
            print(f"❌ Non posso terminare {pid}")
else:
    print("✅ Nessun processo duplicato trovato")
