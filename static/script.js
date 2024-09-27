const socket = io();

const sensors = ['turbidity', 'tds', 'ph'];

function updateSensorValue(sensor, data) {
    const card = document.getElementById(sensor);
    const valueElement = document.getElementById(`${sensor}-value`);
    const indicatorElement = document.getElementById(`${sensor}-indicator`);
    const statusElement = document.getElementById(`${sensor}-status`);

    if (data && typeof data.value === 'number') {
        valueElement.textContent = data.value.toFixed(2);
        
        card.className = `sensor-card ${data.status}`;
        valueElement.className = `value ${data.status}`;
        indicatorElement.className = `status-indicator ${data.status}`;
        statusElement.textContent = data.status.charAt(0).toUpperCase() + data.status.slice(1);
    } else {
        valueElement.textContent = 'N/A';
        card.className = 'sensor-card no-data';
        valueElement.className = 'value no-data';
        indicatorElement.className = 'status-indicator no-data';
        statusElement.textContent = 'No data';
    }
}

function updateTimestamp(timestamp) {
    const date = new Date(timestamp);
    if (!isNaN(date.getTime())) {
        const formattedDate = date.toLocaleString('en-US', { 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric', 
            hour: '2-digit', 
            minute: '2-digit', 
            second: '2-digit' 
        });
        document.getElementById('timestamp').textContent = `Last updated: ${formattedDate}`;
    } else {
        document.getElementById('timestamp').textContent = 'Last updated: Unknown';
    }
}

socket.on('sensor_update', function(data) {
    if (data && data.sensors) {
        sensors.forEach(sensor => {
            updateSensorValue(sensor, data.sensors[sensor]);
        });
        updateTimestamp(data.timestamp);
    } else {
        console.error('Received invalid data structure:', data);
    }
});
