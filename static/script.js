const socket = io();

const sensors = ['turbidity', 'tds', 'ph'];

function updateSensorValue(sensor, data) {
    const valueElement = document.getElementById(`${sensor}-value`);
    const indicatorElement = document.getElementById(`${sensor}-indicator`);
    const statusElement = document.getElementById(`${sensor}-status`);

    if (data && typeof data.value === 'number') {
        valueElement.textContent = data.value.toFixed(2);
        
        valueElement.classList.remove('normal', 'alert');
        valueElement.classList.add(data.status);

        indicatorElement.style.backgroundColor = data.status === 'normal' ? '#27ae60' : '#e74c3c';
        statusElement.textContent = data.status;
    } else {
        valueElement.textContent = 'N/A';
        valueElement.classList.remove('normal', 'alert');
        indicatorElement.style.backgroundColor = '#7f8c8d';
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

// Add smooth transitions for value changes
sensors.forEach(sensor => {
    const valueElement = document.getElementById(`${sensor}-value`);
    valueElement.style.transition = 'color 0.3s ease';
});