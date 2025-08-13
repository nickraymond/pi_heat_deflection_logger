from flask import Flask, jsonify, render_template, send_file, request, Response
from data_engine import DataEngine
from sensor_config import sensor_config
from manual_logger import append_rows
import os
import io
import csv
import json
from datetime import datetime, timezone

# ===== Config =====
CSV_LOG_PATH = os.getenv("CSV_LOG_PATH", os.path.join("exports", "data_log.csv"))

TEMP1_ID = "28-000008ae0bbd"
TEMP2_ID = "28-000008ae5436"
DIAL1_MANUAL_ID = "dial_1_manual_entry"
DIAL2_MANUAL_ID = "dial_2_manual_entry"

ACTIVE_SAMPLES = {"sample1": "", "sample2": ""}

THEME_PATH = os.path.join("config", "theme.json")
DEFAULT_THEME = {
	"colorA": "#0A4A8A",  # Sofar dark blue
	"colorB": "#2E86FF"   # Sofar light blue
}

app = Flask(__name__)
engine = DataEngine()
engine.start()


def _ensure_dir(p):
	os.makedirs(os.path.dirname(os.path.abspath(p)), exist_ok=True)


def _load_theme():
	try:
		with open(THEME_PATH, "r", encoding="utf-8") as f:
			data = json.load(f)
			return {
				"colorA": data.get("colorA") or DEFAULT_THEME["colorA"],
				"colorB": data.get("colorB") or DEFAULT_THEME["colorB"],
			}
	except Exception:
		# create default on first use
		_ensure_dir(THEME_PATH)
		with open(THEME_PATH, "w", encoding="utf-8") as f:
			json.dump(DEFAULT_THEME, f, indent=2)
		return DEFAULT_THEME.copy()


@app.route("/")
def index():
	return render_template("index.html")


@app.get("/logo.png")
def logo_png():
	# Serve Sofar_logo.png from the project root if present
	path = os.path.join(os.getcwd(), "Sofar_logo.png")
	if os.path.exists(path):
		return send_file(path, mimetype="image/png")
	return jsonify({"error": "Sofar_logo.png not found in working directory"}), 404


# ---------- Theme API ----------
@app.get("/api/theme")
def api_theme_get():
	return jsonify(_load_theme())


@app.post("/api/theme")
def api_theme_post():
	data = request.get_json(silent=True) or {}
	theme = {
		"colorA": (data.get("colorA") or DEFAULT_THEME["colorA"]).strip(),
		"colorB": (data.get("colorB") or DEFAULT_THEME["colorB"]).strip(),
	}
	_ensure_dir(THEME_PATH)
	with open(THEME_PATH, "w", encoding="utf-8") as f:
		json.dump(theme, f, indent=2)
	return jsonify({"ok": True, **theme})


# ---------- Live data ----------
# --- helper: normalize timestamp to epoch float ---
def _to_epoch(ts):
	"""Return epoch seconds as float from mixed timestamp formats, or None."""
	if isinstance(ts, (int, float)):
		return float(ts)
	if isinstance(ts, str):
		s = ts.strip()
		# numeric string?
		try:
			return float(s)
		except ValueError:
			pass
		# ISO string?
		try:
			if s.endswith("Z"):
				s = s[:-1] + "+00:00"
			dt = datetime.fromisoformat(s)
			if dt.tzinfo is None:
				dt = dt.astimezone()
			return dt.timestamp()
		except Exception:
			return None
	return None


@app.get("/api/data")
def api_data():
	# Start with the engine's view
	latest = engine.get_latest_data()  # {sensor_id: {"timestamp": epoch(float), "sensor_value": x}}
	# Merge in newest values from the in-memory log (manual entries, etc.)
	seen = set()
	for row in reversed(engine.logger.data):
		sid = row.get("sensor_id")
		if not sid or sid in seen:
			continue
		ts_epoch = _to_epoch(row.get("timestamp"))
		val = row.get("sensor_value")
		# Accept either 'sensor_value' or legacy 'value'
		if val is None:
			val = row.get("value")
		if ts_epoch is not None and val is not None:
			latest[sid] = {"timestamp": ts_epoch, "sensor_value": val}
			seen.add(sid)

	# Format response expected by the frontend
	formatted = {}
	for sensor_id, entry in latest.items():
		ts_epoch = _to_epoch(entry.get("timestamp"))
		if ts_epoch is None:
			# skip malformed
			continue
		ts_iso = datetime.fromtimestamp(ts_epoch, tz=timezone.utc).isoformat()
		formatted[sensor_id] = {
			"sensor_value": entry.get("sensor_value"),
			"timestamp": ts_iso,
			"sensor_type": sensor_config.get_sensor_type(sensor_id),
			"sensor_label": sensor_config.get_sensor_label(sensor_id),
			"sensor_units": sensor_config.get_sensor_units(sensor_id),
			"sample_name": sensor_config.get_sample_name(sensor_id),
		}
	return jsonify(formatted)


@app.post("/api/start")
def api_start():
	data = request.get_json(silent=True) or {}
	s1 = (data.get("sample1") or "").strip()
	s2 = (data.get("sample2") or "").strip()
	if not s1 or not s2:
		return jsonify({"ok": False, "error": "Both Sample 1 and Sample 2 IDs are required"}), 400

	ACTIVE_SAMPLES["sample1"] = s1
	ACTIVE_SAMPLES["sample2"] = s2

	if TEMP1_ID in sensor_config.mapping:
		sensor_config.mapping[TEMP1_ID]["sample_name"] = s1
	if TEMP2_ID in sensor_config.mapping:
		sensor_config.mapping[TEMP2_ID]["sample_name"] = s2
	if DIAL1_MANUAL_ID in sensor_config.mapping:
		sensor_config.mapping[DIAL1_MANUAL_ID]["sample_name"] = s1
	if DIAL2_MANUAL_ID in sensor_config.mapping:
		sensor_config.mapping[DIAL2_MANUAL_ID]["sample_name"] = s2

	engine.start_logging()
	return jsonify({"ok": True, "logging": True, "sample1": s1, "sample2": s2})


@app.post("/api/stop")
def api_stop():
	engine.stop_logging()
	ACTIVE_SAMPLES["sample1"] = ""
	ACTIVE_SAMPLES["sample2"] = ""
	if TEMP1_ID in sensor_config.mapping:
		sensor_config.mapping[TEMP1_ID]["sample_name"] = ""
	if TEMP2_ID in sensor_config.mapping:
		sensor_config.mapping[TEMP2_ID]["sample_name"] = ""
	if DIAL1_MANUAL_ID in sensor_config.mapping:
		sensor_config.mapping[DIAL1_MANUAL_ID]["sample_name"] = ""
	if DIAL2_MANUAL_ID in sensor_config.mapping:
		sensor_config.mapping[DIAL2_MANUAL_ID]["sample_name"] = ""
	return jsonify({"ok": True, "logging": False})


@app.get("/api/history")
def api_history():
	return jsonify(engine.get_full_log())


@app.get("/api/status")
def api_status():
	return jsonify(
		{"logging": engine.logger.is_logging(),
		 "sample1": ACTIVE_SAMPLES["sample1"],
		 "sample2": ACTIVE_SAMPLES["sample2"]}
	)


@app.post("/manual_dial_input")
def manual_dial_input():
	data = request.get_json(silent=True) or {}

	def is_number(x):
		try:
			float(x)
			return True
		except (TypeError, ValueError):
			return False

	provided = []
	if "dial_1" in data:
		if not is_number(data["dial_1"]):
			return ("dial_1 must be numeric", 400)
		provided.append(("dial_1", float(data["dial_1"])))
	if "dial_2" in data:
		if not is_number(data["dial_2"]):
			return ("dial_2 must be numeric", 400)
		provided.append(("dial_2", float(data["dial_2"])))

	if not provided:
		return ("Provide at least one numeric value", 400)

	now = datetime.now(timezone.utc)
	ts_iso = now.isoformat().replace("+00:00", "Z")
	ts_epoch = now.timestamp()

	rows = []
	for name, val in provided:
		if name == "dial_1":
			sensor_id = DIAL1_MANUAL_ID
			sensor_label = "Manual Dial 1"
			sample_name = ACTIVE_SAMPLES["sample1"]
		else:
			sensor_id = DIAL2_MANUAL_ID
			sensor_label = "Manual Dial 2"
			sample_name = ACTIVE_SAMPLES["sample2"]

		rows.append(
			{
				"timestamp": ts_iso,   # manual_logger will derive epoch/utc/local
				"sensor_id": sensor_id,
				"sensor_type": "dial_indicator",
				"sensor_label": sensor_label,
				"sensor_units": "mm",
				"sample_name": sample_name or "",
				"value": val,
			}
		)

		engine.logger.data.append(
			{
				"timestamp": ts_epoch,  # epoch (for live plots/export)
				"sensor_id": sensor_id,
				"sensor_type": "dial_indicator",
				"sensor_label": sensor_label,
				"sensor_units": "mm",
				"sample_name": sample_name or "",
				"sensor_value": val,
			}
		)

	append_rows(CSV_LOG_PATH, rows)
	return jsonify({"ok": True, "timestamp": ts_iso, "saved_rows": len(provided)})


# ---------- Export CSV: save to disk AND download ----------
@app.get("/api/export")
def api_export():
	history = engine.get_full_log() or []
	if not history:
		return jsonify({"error": "No history data available"}), 404

	output = io.StringIO()
	writer = csv.writer(output)
	writer.writerow([
		"ts_epoch", "ts_utc", "ts_local",
		"sensor_id", "sensor_type", "sensor_label", "sensor_units",
		"sample_name", "value"
	])

	rows_written = 0
	for row in history:
		ts_epoch = _to_epoch(row.get("timestamp"))
		if ts_epoch is None:
			# skip malformed timestamps
			continue

		dt_utc = datetime.fromtimestamp(ts_epoch, tz=timezone.utc)
		ts_utc = dt_utc.isoformat()
		ts_local = dt_utc.astimezone().strftime("%Y-%m-%d %H:%M:%S")

		value = row.get("sensor_value", row.get("value", ""))

		writer.writerow([
			f"{ts_epoch:.6f}", ts_utc, ts_local,
			row.get("sensor_id", ""),
			row.get("sensor_type", ""),
			row.get("sensor_label", ""),
			row.get("sensor_units", ""),
			row.get("sample_name", ""),
			value
		])
		rows_written += 1

	if rows_written == 0:
		return jsonify({"error": "No valid rows to export"}), 400

	csv_text = output.getvalue()
	output.close()

	# Save a copy to exports/ with a UTC timestamped filename
	os.makedirs("exports", exist_ok=True)
	fname = "log_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + ".csv"
	disk_path = os.path.join("exports", fname)
	with open(disk_path, "w", encoding="utf-8", newline="") as f:
		f.write(csv_text)

	# Return the same file to the browser
	return Response(
		csv_text.encode("utf-8"),
		mimetype="text/csv",
		headers={"Content-Disposition": f"attachment; filename={fname}"},
	)



if __name__ == "__main__":
	try:
		app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True, use_reloader=False)
	except KeyboardInterrupt:
		print("Shutting down...")
	finally:
		try:
			engine.stop()
		except Exception:
			pass
