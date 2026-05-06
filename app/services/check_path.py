import os
from pathlib import Path

csv_path = os.path.join(Path(__file__).parent.parent.parent, "data", "carriers.csv")
print("csv_path (before normpath):", csv_path)
csv_path = os.path.normpath(csv_path)
print("csv_path (after normpath):", csv_path)
