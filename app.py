from flask import Flask, jsonify, render_template, send_file, request
from data_engine import DataEngine
from sensor_config import sensor_config
from manual_logger import append_rows
import os
from datetime import datetime, timezone

# CSV destination
CSV_LOG_PATH = os.getenv("CSV_LOG_PATH", os.path.join("exports", "data_log.csv"))

app = Flask(__name__)

# Start background polling engine
engine = DataEngine()
engine.start()

@app.route('/')
def index():
	return render_template('index.html')

# ---------- UPDATED: /api/data merges in latest manual rows ----------
@app.route('/api/data')
def api_data():
	# Start with the engine’s latest snapshot (what you had originally)
	latest = engine.get_latest_data()  # expected: {sensor_id: {'timestamp': epoch, 'sensor_value': ...}, ...}

	# Overlay most recent manual entries from logger.data (history list)
	# We scan from the tail until we’ve found the latest per sensor_id.
	seen = set()
	for row in reversed(engine.logger.data):
		sid = row.get('sensor_id')
		if not sid or sid in seen:
			continue
		# Manual rows we wrote have epoch seconds in row['timestamp'] and 'sensor_value'
		ts_epoch = row.get('timestamp')
		val = row.get('sensor_value')
		if ts_epoch is not None and val is not None:
			latest[sid] = {'timestamp': ts_epoch, 'sensor_value': val}
			seen.add(sid)

	# Now format for the frontend (same fields you already use)
	formatted = {}
	for sensor_id, entry in latest.items():
		ts_epoch = entry['timestamp']
		# Convert epoch -> ISO for the client
		ts_iso = datetime.fromtimestamp(ts_epoch, tz=timezone.utc).isoformat()
		formatted[sensor_id] = {
			"sensor_value": entry['sensor_value'],
			"timestamp": ts_iso,
			"sensor_type": sensor_config.get_sensor_type(sensor_id),
			"sensor_label": sensor_config.get_sensor_label(sensor_id),
			"sensor_units": sensor_config.get_sensor_units(sensor_id),
			"sample_name": sensor_config.get_sample_name(sensor_id)
		}
	return jsonify(formatted)

@app.post('/api/start')
def api_start():
	engine.start_logging()
	return jsonify({'status': 'logging_started'})

@app.post('/api/stop')
def api_stop():
	engine.stop_logging()
	return jsonify({'status': 'logging_stopped'})

@app.get('/api/export')
def api_export():
	filepath = engine.export_csv()
	if filepath:
		return send_file(filepath, as_attachment=True)
	else:
		return jsonify({'error': 'No log file found'}), 404

@app.get('/api/history')
def api_history():
	log_data = engine.get_full_log()
	return jsonify(log_data)

@app.get('/api/status')
def api_status():
	return jsonify({"logging": engine.logger.is_logging()})

# ---------- UPDATED: manual save writes CSV (ISO) + history (epoch) ----------
@app.post('/manual_dial_input')
def manual_dial_input():
	data = request.get_json(silent=True) or {}

	def is_number(x):
		try:
			float(x)
			return True
		except (TypeError, ValueError):
			return False

	provided = []
	if 'dial_1' in data:
		if not is_number(data['dial_1']):
			return ("dial_1 must be numeric", 400)
		provided.append(('dial_1', float(data['dial_1'])))
	if 'dial_2' in data:
		if not is_number(data['dial_2']):
			return ("dial_2 must be numeric", 400)
		provided.append(('dial_2', float(data['dial_2'])))

	if not provided:
		return ("Provide at least one numeric value", 400)

	now = datetime.now(timezone.utc)
	ts_iso = now.isoformat().replace('+00:00', 'Z')  # CSV
	ts_epoch = now.timestamp()                       # history/API

	rows = []
	for name, val in provided:
		if name == 'dial_1':
			sensor_id = 'dial_1_manual_entry'
			sensor_label = 'Manual Dial 1'
		else:
			sensor_id = 'dial_2_manual_entry'
			sensor_label = 'Manual Dial 2'

		# CSV row
		rows.append({
			'timestamp': ts_iso,
			'sensor_id': sensor_id,
			'sensor_type': 'dial_indicator',
			'sensor_label': sensor_label,
			'sensor_units': 'mm',
			'value': val,
		})

		# In-memory history row (what /api/data merge will see)
		engine.logger.data.append({
			'timestamp': ts_epoch,       # epoch float
			'sensor_id': sensor_id,
			'sensor_type': 'dial_indicator',
			'sensor_label': sensor_label,
			'sensor_units': 'mm',
			'sample_name': '',
			'sensor_value': val
		})

	append_rows(CSV_LOG_PATH, rows)

	return jsonify({'ok': True, 'timestamp': ts_iso, 'saved_rows': len(provided)})

if __name__ == '__main__':
	try:
		app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True, use_reloader=False)
	except KeyboardInterrupt:
		print("Shutting down...")
	finally:
		try:
			engine.stop()
		except Exception:
			pass
