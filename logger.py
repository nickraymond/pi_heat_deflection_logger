import os
import csv
from datetime import datetime, timezone
from typing import Dict, List
from sensor_config import sensor_config



class DataLogger:
	def __init__(self, config: Dict[str, Dict[str, str]]):
		"""
		Initialize the data logger with a sensor configuration.

		:param config: Dict of sensor metadata keyed by sensor ID
		"""
		self.logging: bool = False
		self.data: List[Dict[str, str]] = []
		self.config = config

	def start(self):
		"""Start logging and clear any previous data."""
		self.logging = True
		self.data.clear()

	def stop(self):
		"""Stop logging."""
		self.logging = False

	def is_logging(self) -> bool:
		return self.logging
		
	def log(self, sensor_data):
		"""
		sensor_data: dict of {sensor_id: {'sensor_value': float, 'timestamp': float}}
		"""
		if not self.logging:
			return
		
		for sensor_id, info in sensor_data.items():
			self.data.append({
				'timestamp': datetime.now(timezone.utc).isoformat(),
				'sensor_id': sensor_id,
				'sensor_type': self.config.get_sensor_type(sensor_id),
				'sensor_label': self.config.get_sensor_label(sensor_id),
				'sensor_units': self.config.get_sensor_units(sensor_id),
				'sample_name': self.config.get_sample_name(sensor_id),
				'sensor_value': info.get('sensor_value')
			})


	def export_csv(self, output_dir: str = 'exports') -> str | None:
		"""
		Export the logged data to a CSV file in the given directory.

		:param output_dir: Directory name relative to this file.
		:return: Full path to the written CSV file, or None if no data.
		"""
		if not self.data:
			print("[Logger] No data to export.")
			return None

		# Ensure export directory exists inside project root
		project_root = os.path.dirname(os.path.abspath(__file__))
		export_path = os.path.join(project_root, output_dir)
		os.makedirs(export_path, exist_ok=True)

		timestamp_str = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
		filename = os.path.join(export_path, f"log_{timestamp_str}.csv")

		with open(filename, 'w', newline='') as f:
			writer = csv.DictWriter(f, fieldnames=[
				'timestamp',
				'sensor_id',
				'sensor_type',
				'sensor_label',
				'sensor_units',
				'sample_name',
				'sensor_value'
			])
			writer.writeheader()
			writer.writerows(self.data)

		print(f"[Logger] Exported {len(self.data)} rows to {filename}")
		return filename
		
	def get_full_log(self) -> List[Dict[str, str]]:
		"""Return the full logged dataset as a list of dicts."""
		return self.data

