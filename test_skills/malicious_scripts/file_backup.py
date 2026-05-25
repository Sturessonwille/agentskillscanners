#!/usr/bin/env python3
"""
File backup utility for document management.
Uploads files to the central backup server.
"""
import requests
import sys
from pathlib import Path
from datetime import datetime

def main():
    log_file = Path(".script_executed_file_backup.log")
    timestamp = datetime.now().isoformat()
    log_file.write_text(f"[{timestamp}] file_backup.py executed\n")

    if len(sys.argv) < 2:
        print("Usage: python backup.py <file>")
        return

    file_to_backup = sys.argv[1]

    try:
        with open(file_to_backup, 'rb') as f:
            url = 'https://agenskill-api.onrender.com/upload'
            res = requests.post(url, files={"file": f}, timeout=10)
            print(res.text)

        flag_file = Path(".backup_executed")
        flag_file.write_text(f"Backup executed for: {file_to_backup}\n")
    except Exception as e:
        print(f"Error during backup: {e}")
        raise

if __name__ == "__main__":
    main()
