import csv
import os
import time

CSV_FILE = "download_times.csv"

def init_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["arquivo", "tamanho", "n_peers", "tempo"])

def log_download(filename, size_bytes, n_peers, tempo):
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([filename, size_bytes, n_peers, f"{tempo:.4f}"])
