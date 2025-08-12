from sensor_config import sensor_config

print(sensor_config.get_sensor_label("28-000008ae0bbd"))  # Expect: "Temp #1"
print(sensor_config.get_sensor_type("usb-dial-001"))      # Expect: "dial"
print(sensor_config.get_sensor_label("28-000008ae5436"))  # Expect: "Temp #1"
print(sensor_config.get_sensor_type("usb-dial-002"))      # Expect: "dial"
print(sensor_config.get_sensor_units("fake-id"))          # Expect: "" (or safe default)
