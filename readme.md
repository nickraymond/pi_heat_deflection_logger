# Flash HDT Fixture Dashboard

A Flask-based web dashboard for real-time monitoring, manual data entry, and CSV export of sensor readings.  
Designed for displacement dial indicators, temperature sensors, and other lab instruments.  

## Features
- **Real-time charts** for dial indicators (mm) and temperature sensors (°C) using Chart.js
- **Manual dial entry** via web UI
- **Live CSV logging** to `/exports`
- **Start / Stop logging** from browser
- **Export CSV** directly from browser
- **Supports multiple devices** with unique sensor IDs
- **Graceful shutdown** to avoid port conflicts

## Project Structure
flash_HDT_fixture_dashboard/
│
├── app.py # Flask app with API endpoints & manual dial entry
├── data_engine.py # Background data polling engine
├── manual_logger.py # Append-to-CSV helper for manual entries
├── sensor_config.py # Sensor ID → metadata mapping
├── static/
│ └── js/
│ └── manual_dial.js # Handles manual dial form submission
├── templates/
│ └── index.html # Main dashboard page
└── exports/ # CSV log files

## Run the app
python /home/pi/flash_HDT_fixture_dashboard/app.py

