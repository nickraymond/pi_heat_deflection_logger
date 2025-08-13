import csv
import os
import threading
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Tuple, Optional

# New, richer schema (matches /api/export order)
NEW_FIELDNAMES: List[str] = [
	"ts_epoch",
	"ts_utc",
	"ts_local",
	"sensor_id",
	"sensor_type",
	"sensor_label",
	"sensor_units",
	"sample_name",
	"value",
]

_csv_lock = threading.Lock()


def ensure_parent_dir(path: str) -> None:
	parent = os.path.dirname(os.path.abspath(path))
	if parent and not os.path.exists(parent):
		os.makedirs(parent, exist_ok=True)


def _read_existing_header(path: str) -> Optional[List[str]]:
	try:
		with open(path, "r", encoding="utf-8", newline="") as f:
			first = f.readline().strip()
			if not first:
				return None
			# naive split (header has no commas in names)
			return [h.strip() for h in first.split(",")]
	except FileNotFoundError:
		return None
	except Exception:
		return None


def _rotate_old_file(path: str, header: List[str]) -> None:
	"""Rename an existing file to a timestamped backup before creating a new one."""
	ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
	base, ext = os.path.splitext(path)
	bak = f"{base}.v1_{ts}{ext or '.csv'}"
	try:
		os.replace(path, bak)
	except Exception:
		# If replace fails for any reason, we leave the old file in place;
		# new file will still be created/overwritten by caller.
		pass


def _to_epoch_utc_local(ts_input) -> Tuple[float, str, str]:
	"""
	Accepts either:
	  - epoch (float/int) or
	  - ISO string (e.g., '2025-08-12T18:22:33Z' or with offset)
	Returns (epoch_float, iso_utc, human_local_no_tz)
	"""
	# Detect epoch-like
	epoch: Optional[float] = None
	if isinstance(ts_input, (int, float)):
		epoch = float(ts_input)
	elif isinstance(ts_input, str) and ts_input:
		s = ts_input.strip()
		try:
			# Normalize trailing Z to +00:00 for fromisoformat
			if s.endswith("Z"):
				s = s[:-1] + "+00:00"
			dt = datetime.fromisoformat(s)
			if dt.tzinfo is None:
				# Treat naive as local, convert to UTC
				dt = dt.astimezone()
			epoch = dt.timestamp()
		except Exception:
			epoch = None

	if epoch is None:
		# Fallback: "now"
		dt_utc = datetime.now(timezone.utc)
	else:
		dt_utc = datetime.fromtimestamp(epoch, tz=timezone.utc)

	ts_epoch = dt_utc.timestamp()
	ts_utc = dt_utc.isoformat()                       # e.g., 2025-08-12T18:22:33+00:00
	ts_local = dt_utc.astimezone().strftime("%Y-%m-%d %H:%M:%S")  # human local, no tz
	return ts_epoch, ts_utc, ts_local


def _normalize_row(row: Dict[str, object]) -> Dict[str, object]:
	"""
	Map flexible input rows to NEW_FIELDNAMES.
	Accepts legacy keys like:
	  - 'timestamp' (epoch or ISO)  OR the new 'ts_epoch'/'ts_utc'/'ts_local'
	  - 'sensor_value' OR 'value'
	"""
	# Prefer explicit new fields if present
	ts_epoch = row.get("ts_epoch")
	ts_utc = row.get("ts_utc")
	ts_local = row.get("ts_local")

	if ts_epoch is None or ts_utc is None or ts_local is None:
		# Derive from 'timestamp' (epoch or ISO)
		ts_epoch, ts_utc, ts_local = _to_epoch_utc_local(row.get("timestamp"))

	value = row.get("value")
	if value is None and "sensor_value" in row:
		value = row.get("sensor_value")

	return {
		"ts_epoch": f"{float(ts_epoch):.6f}" if isinstance(ts_epoch, (int, float, str)) else "",
		"ts_utc": ts_utc or "",
		"ts_local": ts_local or "",
		"sensor_id": row.get("sensor_id", ""),
		"sensor_type": row.get("sensor_type", ""),
		"sensor_label": row.get("sensor_label", ""),
		"sensor_units": row.get("sensor_units", ""),
		"sample_name": row.get("sample_name", ""),
		"value": value if value is not None else "",
	}


def append_rows(csv_path: str, rows: Iterable[Dict[str, object]]) -> int:
	"""
	Append rows to CSV at csv_path using the NEW_FIELDNAMES schema.
	- If the file doesn't exist or is empty, write the NEW_FIELDNAMES header.
	- If the file exists with an older/different header, rotate it to a timestamped
	  backup and start a new file with the NEW_FIELDNAMES header.
	- Input rows can be legacy (timestamp + sensor_value) or new format; they will
	  be normalized automatically.
	Returns number of rows written.
	"""
	ensure_parent_dir(csv_path)

	wrote = 0
	with _csv_lock:
		# Check header situation first
		existing_header = _read_existing_header(csv_path)
		if existing_header:
			# If header differs, rotate
			if existing_header != NEW_FIELDNAMES:
				_rotate_old_file(csv_path, existing_header)

		file_exists = os.path.exists(csv_path) and os.path.getsize(csv_path) > 0

		with open(csv_path, mode="a", newline="", encoding="utf-8") as f:
			writer = csv.DictWriter(f, fieldnames=NEW_FIELDNAMES)
			if not file_exists or (existing_header and existing_header != NEW_FIELDNAMES):
				writer.writeheader()

			for r in rows:
				norm = _normalize_row(r)
				writer.writerow(norm)
				wrote += 1

	return wrote
