from flask import Flask, jsonify, render_template, send_file, request
from data_engine import DataEngine
from sensor_config import sensor_config
import os
from datetime import datetime, timezone

app = Flask(__name__)

# Start background polling engine
engine = DataEngine()
engine.start()

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/api/data')
def api_data():
	raw_data = engine.get_latest_data()
	formatted = {}

	for sensor_id, entry in raw_data.items():
		ts = datetime.fromtimestamp(entry['timestamp'], tz=timezone.utc).isoformat()
		formatted[sensor_id] = {
			"sensor_value": entry['sensor_value'],
			"timestamp": ts,
			"sensor_type": sensor_config.get_sensor_type(sensor_id),
			"sensor_label": sensor_config.get_sensor_label(sensor_id),
			"sensor_units": sensor_config.get_sensor_units(sensor_id),
			"sample_name": sensor_config.get_sample_name(sensor_id)
		}

	return jsonify(formatted)

@app.route('/api/start', methods=['POST'])
def api_start():
	engine.start_logging()
	return jsonify({'status': 'logging_started'})

@app.route('/api/stop', methods=['POST'])
def api_stop():
	engine.stop_logging()
	return jsonify({'status': 'logging_stopped'})

@app.route('/api/export')
def api_export():
	filepath = engine.export_csv()
	if filepath:
		return send_file(filepath, as_attachment=True)
	else:
		return jsonify({'error': 'No log file found'}), 404

# @app.route('/api/history')
# def api_history():
# 	log_data = engine.get_full_log()
# 
# 	if not log_data:
# 		return jsonify({'error': 'No history data available'}), 404
# 
# 	return jsonify(log_data)
@app.route('/api/history')
def api_history():
	log_data = engine.get_full_log()
	print(f"[DEBUG] /api/history returned {len(log_data)} records.")
	return jsonify(log_data)
	
@app.route('/api/status')
def api_status():
	return jsonify({"logging": engine.logger.is_logging()})


if __name__ == '__main__':
	port = int(os.environ.get('PORT', 5000))
	app.run(debug=True, host='0.0.0.0', port=port)
