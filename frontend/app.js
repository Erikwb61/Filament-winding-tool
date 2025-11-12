// Backend URL
const API_URL = 'http://localhost:5000/api';

// Für Debugging: Falls Port 5000 nicht antwortet, verwende 5001
const API_FALLBACK = 'http://localhost:5001/api';

// Helper: Mache API-Anfrage mit Fallback-Unterstützung
async function apiCall(endpoint, options = {}) {
    const urls = [API_URL, API_FALLBACK];
    
    for (const url of urls) {
        try {
            const fullUrl = `${url}${endpoint}`;
            console.log(`Trying ${fullUrl}...`);
            
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 3000);
            
            const response = await fetch(fullUrl, {
                ...options,
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            if (response.ok) {
                console.log(`Success with ${url}`);
                return response;
            }
        } catch (error) {
            console.warn(`Failed with ${url}: ${error.message}`);
            // Try next URL
        }
    }
    
    // Alle URLs fehlgeschlagen
    throw new Error('Keine API verfügbar (versucht 5000 und 5001)');
}

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

        // API aufrufen mit Fallback
        const response = await apiCall('/parse', {
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
            showError('Fehler beim Parsen: ' + (result.error || 'Unbekannter Fehler'));
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
        let apiUrl = API_URL;
        
        // Versuche auf API_FALLBACK zu fallen, wenn primary nicht antwortet
        try {
            const testResponse = await fetch(`${API_URL}/materials`, { signal: AbortSignal.timeout(2000) });
            if (!testResponse.ok) throw new Error('Primary API not responding');
        } catch (e) {
            console.warn('Primary API unreachable, trying fallback...', e);
            apiUrl = API_FALLBACK;
        }
        
        // Materialien laden
        const materialsResponse = await fetch(`${apiUrl}/materials`);
        if (!materialsResponse.ok) throw new Error('Failed to load materials');
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
        const processesResponse = await fetch(`${apiUrl}/processes`);
        if (!processesResponse.ok) throw new Error('Failed to load processes');
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
        
        console.log('Backend data loaded successfully from:', apiUrl);

    } catch (error) {
        console.error('Fehler beim Laden der Backend-Daten:', error);
        showError('Fehler beim Verbinden zum Backend. Läuft der Server auf Port 5000 oder 5001?');
    }
}

// ============================================================================
// NEW CLT (Classical Laminate Theory) Functions
// ============================================================================

// Laminate Properties (ABD Matrix) berechnen
async function calculateLaminateProperties() {
    hideMessages();
    try {
        const sequence = document.getElementById('sequence').value;
        const plyThickness = parseFloat(document.getElementById('plyThickness').value);
        const material = document.getElementById('material').value;

        if (!sequence || plyThickness <= 0) {
            showError('Bitte gültige Eingaben machen!');
            return;
        }

        const response = await fetch(`${API_URL}/laminate-properties`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                sequence: sequence,
                material: material,
                ply_thickness_mm: plyThickness
            })
        });

        const result = await response.json();

        if (!result.success) {
            showError('CLT Fehler: ' + result.error);
            console.error(result.traceback);
            return;
        }

        // Ergebnisse anzeigen
        console.log('✓ Laminate Properties (ABD Matrix):', result);
        const effProps = result.effective_properties;
        
        document.getElementById('clt-ex').textContent = effProps.E_x_GPa.toFixed(3);
        document.getElementById('clt-gxy').textContent = effProps.G_xy_GPa.toFixed(3);
        document.getElementById('cltResults').style.display = 'block';
        
        showSuccess(
            `✓ CLT berechnet: E_x=${effProps.E_x_GPa.toFixed(2)} GPa, E_y=${effProps.E_y_GPa.toFixed(2)} GPa, G_xy=${effProps.G_xy_GPa.toFixed(2)} GPa`
        );

        return result;
    } catch (error) {
        showError('Fehler: ' + error.message);
        console.error(error);
    }
}

// Failure Analysis (Tsai-Wu Kriterium)
async function calculateFailureAnalysis() {
    hideMessages();
    try {
        const sequence = document.getElementById('sequence').value;
        const plyThickness = parseFloat(document.getElementById('plyThickness').value);
        const material = document.getElementById('material').value;
        const nx = parseFloat(document.getElementById('diameterBottom').value) || 1000;

        const response = await fetch(`${API_URL}/failure-analysis`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                sequence: sequence,
                material: material,
                ply_thickness_mm: plyThickness,
                N_x: nx,
                N_y: 0,
                N_xy: 0,
                load_case: 'tension'
            })
        });

        const result = await response.json();

        if (!result.success) {
            showError('Failure Analysis Fehler: ' + result.error);
            console.error(result.traceback);
            return;
        }

        // Ergebnisse anzeigen
        console.log('✓ Failure Analysis (Tsai-Wu):', result);
        const global = result.global_analysis;
        
        document.getElementById('clt-sf').textContent = global.min_safety_factor.toFixed(2);
        document.getElementById('clt-ply').textContent = global.critical_ply_id;
        document.getElementById('clt-status').textContent = global.design_status.toUpperCase();
        document.getElementById('clt-prob').textContent = (global.probability_of_failure * 100).toFixed(2);
        document.getElementById('cltResults').style.display = 'block';
        
        showSuccess(
            `✓ Failure Analysis: Min SF=${global.min_safety_factor.toFixed(2)}, Critical Ply=${global.critical_ply_id}, Status=${global.design_status.toUpperCase()}`
        );

        return result;
    } catch (error) {
        showError('Fehler: ' + error.message);
        console.error(error);
    }
}

// Tolerance Study (Monte-Carlo)
async function runToleranceStudy() {
    hideMessages();
    try {
        const sequence = document.getElementById('sequence').value;
        const plyThickness = parseFloat(document.getElementById('plyThickness').value);
        const material = document.getElementById('material').value;
        const numSamples = 500;

        const response = await fetch(`${API_URL}/tolerance-study`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                sequence: sequence,
                material: material,
                ply_thickness_mm: plyThickness,
                angle_tolerance_deg: 1.0,
                thickness_tolerance_pct: 5.0,
                num_samples: numSamples,
                N_x: 1000,
                N_y: 0,
                N_xy: 0
            })
        });

        const result = await response.json();

        if (!result.success) {
            showError('Tolerance Study Fehler: ' + result.error);
            console.error(result.traceback);
            return;
        }

        // Ergebnisse anzeigen
        console.log('✓ Tolerance Study (Monte-Carlo):', result);
        const props = result.property_statistics;
        
        // Chart anzeigen
        document.getElementById('toleranceChartContainer').style.display = 'block';
        document.getElementById('cltResults').style.display = 'block';
        
        // Update result cards
        if (props.E_x) {
            document.getElementById('clt-ex').textContent = props.E_x.mean.toFixed(3);
        }
        if (props.G_xy) {
            document.getElementById('clt-gxy').textContent = props.G_xy.mean.toFixed(3);
        }

        // Tolerance Chart erstellen
        const chartData = {
            labels: ['E_x', 'E_y', 'G_xy', 'ν_xy'],
            mean: [
                props.E_x ? props.E_x.mean : 0,
                props.E_y ? props.E_y.mean : 0,
                props.G_xy ? props.G_xy.mean : 0,
                props.nu_xy ? props.nu_xy.mean : 0
            ],
            std: [
                props.E_x ? props.E_x.std : 0,
                props.E_y ? props.E_y.std : 0,
                props.G_xy ? props.G_xy.std : 0,
                props.nu_xy ? props.nu_xy.std : 0
            ]
        };

        const ctx = document.getElementById('toleranceChart');
        if (ctx) {
            if (window.toleranceChartInstance) {
                window.toleranceChartInstance.destroy();
            }

            window.toleranceChartInstance = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: chartData.labels,
                    datasets: [
                        {
                            label: 'Mean Value',
                            data: chartData.mean,
                            backgroundColor: 'rgba(16, 185, 129, 0.5)',
                            borderColor: 'rgba(16, 185, 129, 1)',
                            borderWidth: 2
                        },
                        {
                            label: 'Std Deviation',
                            data: chartData.std,
                            backgroundColor: 'rgba(59, 130, 246, 0.5)',
                            borderColor: 'rgba(59, 130, 246, 1)',
                            borderWidth: 2
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: true,
                            labels: {
                                font: { size: 12, weight: 'bold' },
                                padding: 15
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Value [GPa]'
                            }
                        }
                    }
                }
            });
        }

        showSuccess(
            `✓ Tolerance Study: ${numSamples} samples berechnet, E_x CV=${props.E_x ? props.E_x.cv_percent.toFixed(2) : 'N/A'}%`
        );

        return result;
    } catch (error) {
        showError('Fehler: ' + error.message);
        console.error(error);
    }
}

// ============================================================================
// G-CODE EXPORT FUNKTIONEN
// ============================================================================

let lastGCodeData = null;  // Speichere den letzten G-Code für Download

async function exportGCode() {
    try {
        // Zeige Modal mit Loading
        document.getElementById('gcodeModal').style.display = 'flex';
        document.getElementById('gcodeLoading').style.display = 'block';
        document.getElementById('gcodeContent').style.display = 'none';
        document.getElementById('gcodeError').style.display = 'none';

        // Hole Eingabewerte
        const sequence = document.getElementById('sequence').value || '[0/±45/90]s';
        const material = document.getElementById('material').value || 'M40J';
        const plyThickness = parseFloat(document.getElementById('plyThickness').value) || 0.125;
        
        const diameterBottom = parseFloat(document.getElementById('diameterBottom').value) || 200;
        const diameterTop = parseFloat(document.getElementById('diameterTop').value) || 200;
        const height = parseFloat(document.getElementById('height').value) || 500;

        // Gebung für geometrische Parameter
        const diameter = (diameterBottom + diameterTop) / 2;
        const windingAngle = 45.0;  // Default
        const pitchMm = 10.0;  // Default
        const numTurns = Math.floor(height / pitchMm / 2) || 5;

        // API Anfrage
        const payload = {
            sequence: sequence,
            material: material,
            ply_thickness_mm: plyThickness,
            diameter_mm: diameter,
            length_mm: height,
            taper_angle_deg: 0.0,
            winding_angle_deg: windingAngle,
            pitch_mm: pitchMm,
            num_turns: numTurns,
            machine_type: "4-axis",
            controller_type: "fanuc",
            feed_rate_mm_min: 100.0
        };

        console.log('G-Code Export Payload:', payload);

        const response = await fetch(`${API_URL}/export-gcode`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Server Error ${response.status}: ${errorText}`);
        }

        const result = await response.json();

        // Speichere für Download
        lastGCodeData = {
            gcode: result.gcode,
            filename: result.filename,
            timestamp: new Date().toISOString()
        };

        // Zeige Results
        document.getElementById('gcodeLoading').style.display = 'none';
        document.getElementById('gcodeContent').style.display = 'block';

        // Populate Results
        document.getElementById('gcodeText').textContent = result.gcode;
        document.getElementById('gcodeFilename').textContent = result.filename;
        document.getElementById('gcodeLines').textContent = result.gcode.split('\n').length;
        document.getElementById('gcodeMachine').textContent = result.machine_config.type.toUpperCase();
        document.getElementById('gcodeTime').textContent = result.path_statistics.estimated_time_min.toFixed(1);

        showSuccess('✓ G-Code erfolgreich generiert!');

    } catch (error) {
        console.error('G-Code Export Error:', error);
        document.getElementById('gcodeLoading').style.display = 'none';
        document.getElementById('gcodeError').style.display = 'block';
        document.getElementById('gcodeErrorText').textContent = error.message;
        showError('G-Code Export fehlgeschlagen: ' + error.message);
    }
}

function closeGCodeModal() {
    document.getElementById('gcodeModal').style.display = 'none';
    lastGCodeData = null;
}

function downloadGCode() {
    if (!lastGCodeData) {
        showError('Keine G-Code Daten verfügbar');
        return;
    }

    const element = document.createElement('a');
    element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(lastGCodeData.gcode));
    element.setAttribute('download', lastGCodeData.filename);
    element.style.display = 'none';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);

    showSuccess('✓ G-Code heruntergeladen: ' + lastGCodeData.filename);
}

function copyGCodeToClipboard() {
    if (!lastGCodeData) {
        showError('Keine G-Code Daten verfügbar');
        return;
    }

    navigator.clipboard.writeText(lastGCodeData.gcode).then(() => {
        showSuccess('✓ G-Code in die Zwischenablage kopiert!');
    }).catch(err => {
        showError('Fehler beim Kopieren: ' + err.message);
    });
}

// Bei Seitenladezeiten starten
document.addEventListener('DOMContentLoaded', function() {
    loadDataFromBackend();
});
