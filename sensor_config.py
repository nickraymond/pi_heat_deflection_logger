class SensorConfig:
	def __init__(self):
		self.mapping = {
			"28-000008ae0bbd": {
				"sensor_label": "Temp #1",
				"sensor_type": "temperature",
				"sensor_units": "°C",
				"sample_name": "HDPE-testtest"
			},
			"28-000008ae5436": {
				"sensor_label": "Temp #2",
				"sensor_type": "temperature",
				"sensor_units": "°C",
				"sample_name": "PHA-testtest"
			},
			"usb-dial-001": {
				"sensor_label": "Dial #1",
				"sensor_type": "dial",
				"sensor_units": "mm",
				"sample_name": "HDPE"
			},
			"usb-dial-002": {
				"sensor_label": "Dial #2",
				"sensor_type": "dial",
				"sensor_units": "mm",
				"sample_name": "PHA"
			},
			# ✅ Manual entry IDs
			"dial_1_manual_entry": {
				"sensor_label": "Manual Dial 1",
				"sensor_type": "dial_indicator",
				"sensor_units": "mm",
				"sample_name": ""
			},
			"dial_2_manual_entry": {
				"sensor_label": "Manual Dial 2",
				"sensor_type": "dial_indicator",
				"sensor_units": "mm",
				"sample_name": ""
			}
		}

	def get_sensor_type(self, sensor_id):
		return self.mapping.get(sensor_id, {}).get("sensor_type", "unknown")

	def get_sensor_label(self, sensor_id):
		return self.mapping.get(sensor_id, {}).get("sensor_label", "")

	def get_sensor_units(self, sensor_id):
		return self.mapping.get(sensor_id, {}).get("sensor_units", "")

	def get_sample_name(self, sensor_id):
		return self.mapping.get(sensor_id, {}).get("sample_name", "")

# ✅ create an instance
sensor_config = SensorConfig()
