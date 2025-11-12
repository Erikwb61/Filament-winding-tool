# Filament Winding Tool

Professionelles Web-basiertes Tool zur Faserwickeltechnik-Analyse mit klassischer Laminattheorie (CLT).

## Projektstruktur

```
fw_tool/
├── frontend/              # Frontend (HTML, CSS, JS, Assets)
│   ├── server.py         # HTTP Server für Frontend (Port 8000)
│   ├── index.html        # Hauptanwendung
│   ├── app.js            # Frontend Logik & API Communication
│   ├── Carbongewebe.jpg  # Carbon-Faser Hintergrund
│   └── ...
│
├── backend/               # Backend (Flask API, fw_core)
│   ├── server.py         # Flask REST API (Port 5000)
│   ├── fw_core/          # Core Calculation Libraries
│   │   ├── lamina_properties.py       # Single-Ply Eigenschaften
│   │   ├── laminate_properties.py     # ABD-Matrizen
│   │   ├── failure_analysis.py        # Tsai-Wu Versagensanalyse
│   │   ├── tolerance_analysis.py      # Monte-Carlo Studien
│   │   └── ...
│   └── test_*.py         # Backend Tests
│
└── README.md
```

## Schnellstart

### 1. Backend starten (Port 5000)

```bash
cd backend
python server.py
```

### 2. Frontend starten (Port 8000)

```bash
cd frontend
python server.py
```

Öffne: `http://localhost:8000/index.html`

## Hauptfeatures

- **Material Library**: Support for multiple carbon fiber materials (M40J, IM7, MR70)
- **Sequence Parsing**: Standard notation support (e.g., [0/±45/90]s)
- **Geometry Configuration**: Support for cylindrical and conical geometries
- **Process Profiles**: Predefined winding processes (Towpreg, Nasswickeln, AFP)
- **Autoclave Simulation**: Temperature and pressure profiles
- **Real-time Calculations**: Path length, mass, processing time, and pass count

## Project Structure

```
fw_tool/
├── app.js                    # Frontend JavaScript logic
├── index.html                # Main web interface
├── server.py                 # Flask REST API backend
├── carbon-bg.png             # Carbon fiber texture background
├── Filament-Winding-4.jpg    # Process illustration
├── fw_core/                  # Core calculation modules
│   ├── parser.py             # Sequence parsing
│   ├── geometry.py           # Geometric calculations
│   ├── autoclave.py          # Autoclave profiles
│   ├── model.py              # Data models
│   ├── layup_io.py           # Layer I/O operations
│   └── presets.py            # Material/Process presets
├── generate_background.py    # Carbon texture generator
└── README.md                 # This file
```

## Technology Stack

- **Frontend**: HTML5, CSS3, JavaScript, Chart.js
- **Backend**: Python 3.11, Flask, Flask-CORS
- **Libraries**: Pillow (image generation), NumPy, Matplotlib

## Setup & Installation

### Prerequisites

- Python 3.11+
- pip or conda package manager

### Installation Steps

1. Clone the repository:
```bash
git clone https://github.com/yourusername/fw_tool.git
cd fw_tool
```

2. Create and activate virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate      # On Windows
source .venv/bin/activate   # On macOS/Linux
```

3. Install dependencies:
```bash
pip install flask flask-cors pillow matplotlib numpy
```

## Running the Application

### Start Backend (Flask API)

```bash
python server.py
```

The API will be available at `http://localhost:5000/api`

### Start Frontend (HTTP Server)

In another terminal:

```bash
python -m http.server 8000
```

Open browser at `http://localhost:8000`

## API Endpoints

- `GET /api/materials` - Get available materials
- `GET /api/processes` - Get process presets
- `POST /api/parse` - Parse layup sequence
- `POST /api/calculate` - Calculate properties
- `GET /api/autoclave-profile` - Get autoclave profile

## Usage

1. Enter layup sequence in standard notation (e.g., [0/±45/90]s)
2. Configure geometry (diameter, height)
3. Select material and process
4. Click "Parse" to analyze sequence
5. Click "Calculate" to run simulations

Results include:
- Circumference and path length
- Number of passes required
- Processing time
- Total mass
- Stack thickness
- Autoclave temperature/pressure profile

## Configuration

### Materials

Add or modify materials in `fw_core/presets.py`:

```python
MATERIALS = {
    'M40J': {'name': 'M40J Carbon', 'density': 1.60, ...},
    ...
}
```

### Processes

Edit process parameters in `fw_core/presets.py`:

```python
PROCESSES = {
    'Towpreg': {'name': 'Towpreg', 'speed': ...},
    ...
}
```

## Design

- **Color Scheme**: Professional gray-black palette with carbon fiber texture
- **Responsive**: Works on desktop and tablet devices
- **Modern UI**: Glasmorphism effects, smooth animations

## License

MIT License - feel free to use and modify

## Contributing

Contributions are welcome! Please create a pull request with your changes.

## Support

For issues or questions, open an issue on GitHub.

---

**Last Updated**: November 12, 2025
