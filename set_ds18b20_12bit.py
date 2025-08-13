# setup: install once
# sudo apt-get update
# sudo apt-get install -y python3-pip
# pip3 install --break-system-packages w1thermsensor
#!/usr/bin/env python3
#!/usr/bin/env python3

import sys, time
try:
	from w1thermsensor import W1ThermSensor
except ImportError:
	print("w1thermsensor not installed in this interpreter")
	sys.exit(1)

def norm(s: str) -> str:
	s = s.strip()
	return s[3:] if s.lower().startswith("28-") else s

def ensure_12bit(sensor_id: str):
	sid = norm(sensor_id)
	s = W1ThermSensor(sensor_id=sid)

	try:
		before = s.get_resolution()
	except Exception as e:
		print(f"[28-{sid}] get_resolution() failed: {e}")
		before = None
	print(f"[28-{sid}] current resolution: {before}-bit")

	try:
		if before != 12:
			print(f"[28-{sid}] setting to 12-bit (persist=True)...")
			s.set_resolution(12, persist=True)   # <-- numeric 12
			time.sleep(0.25)
	except Exception as e:
		print(f"[28-{sid}] set_resolution failed: {e}")

	try:
		after = s.get_resolution()
		print(f"[28-{sid}] new resolution: {after}-bit")
	except Exception as e:
		print(f"[28-{sid}] get_resolution() after set failed: {e}")

	print(f"[28-{sid}] sample temps:", end=" ")
	try:
		for _ in range(3):
			print(f"{s.get_temperature():.4f}", end=" ")
			time.sleep(0.2)
	except Exception as e:
		print(f"(read failed: {e})", end="")
	print()

def main(args):
	if not args:
		print("Usage: python set_ds18b20_12bit.py 28-XXXX ...")
		sys.exit(2)
	# optional: show what the lib sees
	try:
		avail = W1ThermSensor.get_available_sensors()
		seen = ", ".join([f"28-{x.id}" for x in avail]) or "(none)"
		print(f"Available sensors: {seen}")
	except Exception as e:
		print(f"Warning: could not list sensors: {e}")
	for sid in args:
		try:
			ensure_12bit(sid)
		except Exception as e:
			print(f"[{sid}] FAILED: {e}")

if __name__ == "__main__":
	main(sys.argv[1:])
