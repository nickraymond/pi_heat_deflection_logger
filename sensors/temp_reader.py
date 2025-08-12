import os
import glob
import threading
import time

class TemperatureSensorPoller:
	def __init__(self):
		self.base_dir = '/sys/bus/w1/devices/'
		self.sensors = self._discover_sensors()
		self.data = {}
		self.lock = threading.Lock()
		self._stop_event = threading.Event()
		self.thread = threading.Thread(target=self._poll_loop)

	def _discover_sensors(self):
		return glob.glob(self.base_dir + '28-*')

	def _read_raw(self, device_file):
		with open(device_file, 'r') as f:
			return f.readlines()

	def _read_temp(self, sensor_path):
		lines = self._read_raw(sensor_path + '/w1_slave')
		if lines[0].strip()[-3:] != 'YES':
			return None
		equals_pos = lines[1].find('t=')
		if equals_pos != -1:
			temp_string = lines[1][equals_pos+2:]
			try:
				temp_c = float(temp_string) / 1000.0
				return temp_c
			except ValueError:
				return None
		return None

	def _poll_loop(self):
		while not self._stop_event.is_set():
			with self.lock:
				for sensor_path in self.sensors:
					sensor_id = os.path.basename(sensor_path)
					temp_c = self._read_temp(sensor_path)
					if temp_c is not None:
						self.data[sensor_id] = {
							'sensor_value': temp_c,              # ✅ updated key
							'timestamp': time.time()
						}
			time.sleep(1)  # polling rate

	def start(self):
		self.thread.start()

	def stop(self):
		self._stop_event.set()
		self.thread.join()

	def get_data(self):
		with self.lock:
			return self.data.copy()
