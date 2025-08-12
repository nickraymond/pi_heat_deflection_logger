from logger import DataLogger
from sensor_config import sensor_config
from datetime import datetime, timezone

logger = DataLogger(sensor_config)

logger.start()
logger.log({
	"28-000008ae0bbd": {
		"sensor_value": 22.5,
		"timestamp": datetime.now(timezone.utc).timestamp()
	},
	"usb-dial-001": {
		"sensor_value": 0.12,
		"timestamp": datetime.now(timezone.utc).timestamp()
	}
})
logger.stop()

filename = logger.export_csv()
print(f"CSV written: {filename}")
