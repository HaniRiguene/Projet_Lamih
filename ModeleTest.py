import csv
from pathlib import Path
import sys
import time

dataset_path=Path(str(sys.argv[1]))
with open(dataset_path, newline='', encoding="utf-8") as f:
    csv_reader = list(csv.reader(f))
    header, rows = csv_reader[0], csv_reader[1:]

for i in range(0, len(rows), 1000):
    print(str(i) + ":"+ str(rows[i][0]))
    time.sleep(1)



