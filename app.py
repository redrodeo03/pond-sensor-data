from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
import requests
from datetime import datetime
import time
import threading
import logging

app = Flask(__name__)
socketio = SocketIO(app)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ThingSpeak channel details
CHANNEL_ID = '2617252'
READ_API_KEY = 'S7MH5E4KBNVDFCHY'

# Sensor fields
FIELDS = {
    '1': 'turbidity',
    '3': 'tds',
    '4': 'ph'
}

# Thresholds
thresholds = {
    'turbidity': {'min': 720, 'max': 740},
    'tds': {'min': 114, 'max': 120},
    'ph': {'min': 7.4, 'max': 7.6}
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/set_thresholds', methods=['POST'])
def set_thresholds():
    global thresholds
    new_thresholds = request.json
    for sensor, values in new_thresholds.items():
        if sensor in thresholds:
            thresholds[sensor]['min'] = float(values['min'])
            thresholds[sensor]['max'] = float(values['max'])
    return jsonify({"status": "success", "thresholds": thresholds})

def fetch_thingspeak_data():
    data = {}
    latest_timestamp = None
    for field, sensor in FIELDS.items():
        url = f'https://api.thingspeak.com/channels/{CHANNEL_ID}/fields/{field}.json?api_key={READ_API_KEY}&results=2'
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raises an HTTPError for bad responses
            channel_data = response.json()
            if 'feeds' in channel_data and len(channel_data['feeds']) > 0:
                latest_feed = channel_data['feeds'][-1]
                value = latest_feed.get(f'field{field}')
                if value is not None:
                    data[sensor] = float(value)
                    timestamp = latest_feed.get('created_at')
                    if timestamp:
                        if latest_timestamp is None or timestamp > latest_timestamp:
                            latest_timestamp = timestamp
                else:
                    logger.warning(f"No data for field {field} in the latest feed")
            else:
                logger.warning(f"No feeds found for field {field}")
        except requests.RequestException as e:
            logger.error(f"Error fetching data for field {field}: {str(e)}")
        except ValueError as e:
            logger.error(f"Error parsing data for field {field}: {str(e)}")
        except KeyError as e:
            logger.error(f"Unexpected data structure for field {field}: {str(e)}")
    
    if latest_timestamp:
        data['timestamp'] = latest_timestamp
    return data

def get_data_with_status(data):
    sensors_data = {}
    for sensor, value in data.items():
        if sensor != 'timestamp':
            sensors_data[sensor] = {
                'value': value,
                'status': 'normal' if thresholds[sensor]['min'] <= value <= thresholds[sensor]['max'] else 'alert'
            }
    return {
        'timestamp': data.get('timestamp', datetime.now().isoformat()),
        'sensors': sensors_data
    }

def send_sensor_data():
    while True:
        data = fetch_thingspeak_data()
        if data:
            data_with_status = get_data_with_status(data)
            socketio.emit('sensor_update', data_with_status)
        time.sleep(15)  # ThingSpeak's free plan allows 15 seconds between API calls

@socketio.on('connect')
def handle_connect():
    logger.info('Client connected')

if __name__ == '__main__':
    threading.Thread(target=send_sensor_data, daemon=True).start()
    socketio.run(app, debug=True)
