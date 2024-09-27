from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
import requests
from datetime import datetime
import os
import logging

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_secret_key_here')
socketio = SocketIO(app)

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
    for field, sensor in FIELDS.items():
        url = f'https://api.thingspeak.com/channels/{CHANNEL_ID}/fields/{field}.json?api_key={READ_API_KEY}&results=1'
        try:
            response = requests.get(url)
            response.raise_for_status()
            channel_data = response.json()
            logging.debug(f"Raw data for {sensor}: {channel_data}")
            if 'feeds' in channel_data and len(channel_data['feeds']) > 0:
                value = channel_data['feeds'][0].get(f'field{field}')
                if value is not None:
                    data[sensor] = float(value)
                    logging.debug(f"Processed data for {sensor}: {data[sensor]}")
                else:
                    logging.warning(f"No value found for {sensor}")
            else:
                logging.warning(f"No feeds found for {sensor}")
        except Exception as e:
            logging.error(f"Error fetching data for {sensor}: {str(e)}")
    logging.debug(f"Final processed data: {data}")
    return data

@socketio.on('request_data')
def handle_request_data():
    data = fetch_thingspeak_data()
    for sensor, value in data.items():
        data[sensor] = {
            'value': value,
            'status': 'normal' if thresholds[sensor]['min'] <= value <= thresholds[sensor]['max'] else 'alert'
        }
    result = {'timestamp': datetime.now().isoformat(), 'sensors': data}
    logging.debug(f"Emitting data: {result}")
    socketio.emit('sensor_update', result)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
