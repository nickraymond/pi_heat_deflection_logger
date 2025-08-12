# import threading
# import time
# 
# from sensors.temp_reader import TemperatureSensorPoller
# from logger import DataLogger
# from sensor_config import SENSOR_CONFIG
# 
# class DataEngine:
# 	def __init__(self, poll_interval=1.0):
# 		self.poller = TemperatureSensorPoller()
# 		self.logger = DataLogger(SENSOR_CONFIG)
# 		self.poll_interval = poll_interval
# 		self._stop_event = threading.Event()
# 		self._thread = threading.Thread(target=self._poll_loop)
# 		self._thread.daemon = True  # exit with main program
# 
# 	def start(self):
# 		self.poller.start()
# 		self._thread.start()
# 		print("[DataEngine] Started.")
# 
# 	def stop(self):
# 		self._stop_event.set()
# 		self.poller.stop()
# 		print("[DataEngine] Stopped.")
# 
# 	def _poll_loop(self):
# 		while not self._stop_event.is_set():
# 			sensor_data = self.poller.get_data()
# 			self.logger.log(sensor_data)
# 			time.sleep(self.poll_interval)
# 
# 	def start_logging(self):
# 		self.logger.start()
# 
# 	def stop_logging(self):
# 		self.logger.stop()
# 
# 	def export_csv(self):
# 		return self.logger.export_csv()
# 
# 	def get_latest_data(self):
# 		return self.poller.get_data()  # for live view


import threading
import time
from typing import Optional, Dict

from sensors.temp_reader import TemperatureSensorPoller
from logger import DataLogger
from sensor_config import sensor_config


class DataEngine:
	def __init__(self, poll_interval: float = 1.0):
		"""
		Core engine that handles polling sensor data and logging.

		:param poll_interval: Time in seconds between each poll
		"""
		self.poller = TemperatureSensorPoller()
		self.logger = DataLogger(sensor_config)
		self.poll_interval = poll_interval
		self._stop_event = threading.Event()
		self._thread: Optional[threading.Thread] = None

	def start(self):
		"""Start the polling thread and sensor hardware."""
		self.poller.start()
		self._thread = threading.Thread(target=self._poll_loop, daemon=True)
		self._thread.start()
		print("[DataEngine] Started.")

	def stop(self):
		"""Stop polling and sensor hardware."""
		self._stop_event.set()
		self.poller.stop()
		if self._thread and self._thread.is_alive():
			self._thread.join()
		print("[DataEngine] Stopped.")

	def _poll_loop(self):
		"""Background loop to continuously poll and log data."""
		while not self._stop_event.is_set():
			sensor_data = self.poller.get_data()
			self.logger.log(sensor_data)
			time.sleep(self.poll_interval)

	def start_logging(self):
		"""Begin saving data to memory."""
		self.logger.start()

	def stop_logging(self):
		"""Stop saving data to memory."""
		self.logger.stop()

	def export_csv(self) -> Optional[str]:
		"""Export the collected log to CSV file."""
		return self.logger.export_csv()

	def get_latest_data(self) -> Dict[str, Dict[str, float]]:
		"""Return the most recent sensor data."""
		return self.poller.get_data()

	def get_full_log(self):
		return self.logger.get_full_log()

