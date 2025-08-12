# from data_engine import DataEngine
# import time
# 
# if __name__ == '__main__':
# 	engine = DataEngine()
# 	engine.start()
# 
# 	engine.start_logging()
# 	print("Logging started...")
# 
# 	try:
# 		for _ in range(5):
# 			data = engine.get_latest_data()
# 			print("Latest:", data)
# 			time.sleep(1.5)
# 	except KeyboardInterrupt:
# 		pass
# 
# 	engine.stop_logging()
# 	print("Logging stopped.")
# 
# 	engine.export_csv()
# 	engine.stop()

from data_engine import DataEngine
import time

engine = DataEngine(poll_interval=1.0)
engine.start()
engine.start_logging()

print("Polling for 5 seconds...")
time.sleep(5)

engine.stop_logging()
path = engine.export_csv()
print(f"Saved to: {path}")

engine.stop()
