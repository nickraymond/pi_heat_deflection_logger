from temp_reader import TemperatureSensorPoller
import time

if __name__ == '__main__':
	poller = TemperatureSensorPoller()
	poller.start()

	try:
		while True:
			data = poller.get_data()
			print(data)
			time.sleep(2)
	except KeyboardInterrupt:
		poller.stop()
