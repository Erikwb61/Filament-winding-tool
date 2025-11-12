// Backend URL
const API_URL = 'http://localhost:5000/api';

// Material-Datenbank (wird vom Backend geladen)
let MATERIALS = {};

// Prozess-Presets (wird vom Backend geladen)
let PROCESSES = {};

// Globale Variablen
let layers = [];
let autoclaveChart = null;

// Chart initialisieren und Daten vom Backend laden
async function initAutoclaveChart() {
    try {
        // Autoklav-Profil vom Backend laden
        const response = await fetch(`${API_URL}/autoclave-profile`);
        const data = await response.json();
        
        const autoclaveData = {
            time_min: data.time_min,
            temp_C: data.temp_C,
            pressure_bar: data.pressure_bar
        };

        const ctx = document.getElementById('autoclaveChart').getContext('2d');

        if (autoclaveChart) {
            autoclaveChart.destroy();
        }

        autoclaveChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: autoclaveData.time_min,
                datasets: [
                    {
                        label: 'Temperatur (°C)',
                        data: autoclaveData.temp_C,
                        borderColor: '#ff6b6b',
                        backgroundColor: 'rgba(255, 107, 107, 0.1)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4,
                        pointRadius: 6,
                        pointBackgroundColor: '#ff6b6b',
                        pointBorderColor: 'white',
                        pointBorderWidth: 2,
                        yAxisID: 'y',
                        pointHoverRadius: 8
                    },
                    {
                        label: 'Druck (bar)',
                        data: autoclaveData.pressure_bar,
                        borderColor: '#4ecdc4',
                        backgroundColor: 'rgba(78, 205, 196, 0.1)',
                        borderWidth: 3,
                        borderDash: [5, 5],
                        fill: true,
                        tension: 0.4,
                        pointRadius: 6,
                        pointBackgroundColor: '#4ecdc4',
                        pointBorderColor: 'white',
                        pointBorderWidth: 2,
                        yAxisID: 'y1',
                        pointHoverRadius: 8
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            font: { size: 12, weight: 'bold' },
                            padding: 15,
                            usePointStyle: true
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleFont: { size: 13, weight: 'bold' },
                        bodyFont: { size: 12 },
                        padding: 12,
                        boxPadding: 6,
                        borderColor: 'rgba(255, 255, 255, 0.3)',
                        borderWidth: 1
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Zeit [min]',
                            font: { size: 13, weight: 'bold' }
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Temperatur [°C]',
                            color: '#ff6b6b',
                            font: { size: 13, weight: 'bold' }
                        },
                        position: 'left',
                        ticks: {
                            color: '#ff6b6b'
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    },
                    y1: {
                        title: {
                            display: true,
                            text: 'Druck [bar]',
                            color: '#4ecdc4',
                            font: { size: 13, weight: 'bold' }
                        },
                        position: 'right',
                        ticks: {
                            color: '#4ecdc4'
                        },
                        grid: {
                            drawOnChartArea: false
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Fehler beim Laden des Autoklav-Profils:', error);
        showError('Fehler beim Laden des Autoklav-Profils');
    }
}

// Sequenz parsen
async function parseLayers() {
    hideMessages();
    try {
        const sequenceStr = document.getElementById('sequence').value;
        const plyThickness = parseFloat(document.getElementById('plyThickness').value);
        const material = document.getElementById('material').value;

        if (!sequenceStr || plyThickness <= 0) {
            showError('Bitte gültige Eingaben machen!');
            return;
        }

        // API aufrufen
        const response = await fetch(`${API_URL}/parse`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                sequence: sequenceStr,
                ply_thickness_mm: plyThickness,
                material: material
            })
        });

        const result = await response.json();

        if (!response.ok) {
            showError('Fehler beim Parsen: ' + result.error);
            return;
        }

        layers = result.layers;
        updateLayersTable();
        showSuccess(`${result.num_layers} Schichten erfolgreich geparst`);
    } catch (e) {
        showError('Fehler beim Parsen: ' + e.message);
        console.error(e);
    }
}

// Tabelle aktualisieren
function updateLayersTable() {
    const tbody = document.getElementById('layersBody');
    tbody.innerHTML = '';

    layers.forEach((layer, idx) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${layer.index + 1}</td>
            <td>${layer.angle.toFixed(1)}</td>
            <td>${layer.thickness_mm.toFixed(3)}</td>
            <td>${layer.material}</td>
            <td>${layer.cumulative_thickness_mm.toFixed(3)}</td>
        `;
        tbody.appendChild(row);
    });
}

// Berechnung durchführen
async function calculate() {
    hideMessages();
    try {
        if (layers.length === 0) {
            showError('Bitte parsen Sie zuerst die Sequenz!');
            return;
        }

        const sequenceStr = document.getElementById('sequence').value;
        const plyThickness = parseFloat(document.getElementById('plyThickness').value);
        const material = document.getElementById('material').value;
        const diameterBottom = parseFloat(document.getElementById('diameterBottom').value);
        const diameterTop = parseFloat(document.getElementById('diameterTop').value);
        const height = parseFloat(document.getElementById('height').value);
        const process = document.getElementById('process').value;

        // API aufrufen
        const response = await fetch(`${API_URL}/calculate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                sequence: sequenceStr,
                ply_thickness_mm: plyThickness,
                material: material,
                diameter_bottom_mm: diameterBottom,
                diameter_top_mm: diameterTop,
                height_mm: height,
                winding_angle_deg: 45,
                tow_width_mm: 5,
                tow_count: 8,
                overlap: 0.1,
                process: process
            })
        });

        const result = await response.json();

        if (!result.success) {
            showError('Fehler bei Berechnung: ' + result.error);
            console.error(result.traceback);
            return;
        }

        // UI aktualisieren
        document.getElementById('circumference').textContent = result.circumference_m.toFixed(3);
        document.getElementById('pathLength').textContent = result.path_length_m.toFixed(3);
        document.getElementById('passes').textContent = result.passes.toFixed(1);
        document.getElementById('time').textContent = result.time_minutes.toFixed(1);
        document.getElementById('mass').textContent = result.mass_kg.toFixed(3);
        document.getElementById('totalThickness').textContent = result.total_thickness_mm.toFixed(3);

        // Summary anzeigen
        const summaryText = `
            <strong>Umfang:</strong> ${result.circumference_m.toFixed(3)} m | 
            <strong>Pfadlänge:</strong> ${result.path_length_m.toFixed(3)} m | 
            <strong>Durchläufe:</strong> ${result.passes.toFixed(1)} | 
            <strong>Verarbeitungszeit:</strong> ${result.time_minutes.toFixed(1)} min | 
            <strong>Gesamtmasse:</strong> ${result.mass_kg.toFixed(3)} kg | 
            <strong>Schichtdicke:</strong> ${result.total_thickness_mm.toFixed(3)} mm
        `;
        document.getElementById('summaryText').innerHTML = summaryText;
        document.getElementById('summary').style.display = 'block';

        showSuccess('✓ Berechnung erfolgreich durchgeführt!');
    } catch (e) {
        showError('Fehler bei Berechnung: ' + e.message);
        console.error(e);
    }
}

// Zurücksetzen
function reset() {
    layers = [];
    document.getElementById('sequence').value = '[0/±45/90]s';
    document.getElementById('plyThickness').value = '0.125';
    document.getElementById('diameterBottom').value = '200';
    document.getElementById('diameterTop').value = '200';
    document.getElementById('height').value = '500';
    document.getElementById('layersBody').innerHTML = '';
    document.getElementById('summary').style.display = 'none';
    document.getElementById('circumference').textContent = '–';
    document.getElementById('pathLength').textContent = '–';
    document.getElementById('passes').textContent = '–';
    document.getElementById('time').textContent = '–';
    document.getElementById('mass').textContent = '–';
    document.getElementById('totalThickness').textContent = '–';
    hideMessages();
}

// Nachrichtenfunktionen
function showError(msg) {
    const el = document.getElementById('errorMsg');
    document.getElementById('errorText').textContent = msg;
    el.classList.add('show');
}

function showSuccess(msg) {
    const el = document.getElementById('successMsg');
    document.getElementById('successText').textContent = msg;
    el.classList.add('show');
}

function hideMessages() {
    document.getElementById('errorMsg').classList.remove('show');
    document.getElementById('successMsg').classList.remove('show');
}

// Materialien und Prozesse vom Backend laden
async function loadDataFromBackend() {
    try {
        // Materialien laden
        const materialsResponse = await fetch(`${API_URL}/materials`);
        MATERIALS = await materialsResponse.json();

        // Material Dropdown füllen
        const materialSelect = document.getElementById('material');
        materialSelect.innerHTML = '';
        Object.keys(MATERIALS).forEach(key => {
            const option = document.createElement('option');
            option.value = key;
            option.textContent = MATERIALS[key].name;
            materialSelect.appendChild(option);
        });

        // Prozesse laden
        const processesResponse = await fetch(`${API_URL}/processes`);
        PROCESSES = await processesResponse.json();

        // Prozess Dropdown füllen
        const processSelect = document.getElementById('process');
        processSelect.innerHTML = '';
        Object.keys(PROCESSES).forEach(key => {
            const option = document.createElement('option');
            option.value = key;
            option.textContent = PROCESSES[key].name;
            processSelect.appendChild(option);
        });

        // Autoklav-Chart initialisieren
        await initAutoclaveChart();

    } catch (error) {
        console.error('Fehler beim Laden der Backend-Daten:', error);
        showError('Fehler beim Verbinden zum Backend. Läuft der Server auf Port 5000?');
    }
}

// Bei Seitenladezeiten starten
document.addEventListener('DOMContentLoaded', function() {
    loadDataFromBackend();
});
