import csv
import os
from flask import request
from datetime import datetime

CSV_PATH = os.path.join('persistent_storage', 'upload_logs.csv')

def init_csv_log():
    """Initialize the CSV log file with headers if it doesn't exist."""
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp', 'filename', 'file_size_mb',
                'processing_duration_sec', 'ip', 'user_agent'
            ])
        print("📄 CSV log initialized.")

def log_upload_csv(filename, file_size_mb, processing_duration_sec):
    """Append an upload log entry to the CSV."""
    with open(CSV_PATH, mode='a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.utcnow().isoformat(),
            filename,
            round(file_size_mb, 2),
            round(processing_duration_sec, 2),
            request.remote_addr,
            request.headers.get('User-Agent')
        ])
    print(f"📝 Logged upload to CSV: {filename} ({file_size_mb:.2f} MB)")