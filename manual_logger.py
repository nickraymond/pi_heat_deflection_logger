import csv
import os
import threading
from typing import Dict, Iterable

# CSV schema is fixed to keep downstream tooling consistent
FIELDNAMES = [
	"timestamp",
	"sensor_id",
	"sensor_type",
	"sensor_label",
	"sensor_units",
	"value",
]

# Simple process-local lock to prevent concurrent writes from interleaving
_csv_lock = threading.Lock()


def ensure_parent_dir(path: str) -> None:
	parent = os.path.dirname(os.path.abspath(path))
	if parent and not os.path.exists(parent):
		os.makedirs(parent, exist_ok=True)


def append_rows(csv_path: str, rows: Iterable[Dict[str, object]]) -> int:
	"""Append rows to CSV at csv_path. Ensures header exists.

	Each row must contain keys in FIELDNAMES. Returns number of rows written.
	"""
	ensure_parent_dir(csv_path)
	wrote = 0
	with _csv_lock:
		file_exists = os.path.exists(csv_path) and os.path.getsize(csv_path) > 0
		with open(csv_path, mode="a", newline="", encoding="utf-8") as f:
			writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
			if not file_exists:
				writer.writeheader()
			for r in rows:
				# Only keep defined schema keys
				writer.writerow({k: r.get(k, "") for k in FIELDNAMES})
				wrote += 1
	return wrote