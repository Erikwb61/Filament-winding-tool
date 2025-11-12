"""
Flask Backend für Filament Winding Tool
Integriert die echten fw_core Module
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import traceback

from fw_core.model import Layup, Geometry, Layer
from fw_core.presets import MATERIALS, PROCESSES
from fw_core import parser, geometry, autoclave

app = Flask(__name__)
CORS(app)  # Cross-Origin Resource Sharing aktivieren

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/materials', methods=['GET'])
def get_materials():
    """Liefert alle verfügbaren Materialien"""
    result = {}
    for key, mat in MATERIALS.items():
        result[key] = {
            'name': mat.name,
            'density': mat.density,
            'fiber_areal_weight': mat.fiber_areal_weight
        }
    return jsonify(result)


@app.route('/api/processes', methods=['GET'])
def get_processes():
    """Liefert alle verfügbaren Prozesse"""
    result = {}
    for key, proc in PROCESSES.items():
        result[key] = {
            'name': proc.name,
            'type': proc.type,
            'line_speed': proc.line_speed,
            'efficiency': proc.efficiency
        }
    return jsonify(result)


@app.route('/api/parse', methods=['POST'])
def parse_sequence():
    """Parst eine Layup-Sequenz
    
    Request JSON:
    {
        "sequence": "[0/±45/90]s",
        "ply_thickness_mm": 0.125,
        "material": "M40J"
    }
    """
    try:
        data = request.json
        sequence = data.get('sequence', '')
        ply_thickness_mm = float(data.get('ply_thickness_mm', 0.125))
        material_key = data.get('material', 'M40J')

        if material_key not in MATERIALS:
            return jsonify({'error': f'Material {material_key} nicht gefunden'}), 400

        material = MATERIALS[material_key]
        ply_thickness_m = ply_thickness_mm / 1000.0

        # Parser aufrufen
        layers = parser.parse_sequence(sequence, ply_thickness_m, material)

        # Ergebnis formatieren
        result = {
            'sequence': sequence,
            'num_layers': len(layers),
            'layers': []
        }

        cumulative_thickness = 0
        for idx, layer in enumerate(layers):
            cumulative_thickness += layer.thickness * 1000  # → mm
            result['layers'].append({
                'index': idx,
                'angle': layer.angle,
                'thickness_mm': layer.thickness * 1000,
                'material': layer.material.name,
                'cumulative_thickness_mm': cumulative_thickness
            })

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 400


@app.route('/api/calculate', methods=['POST'])
def calculate():
    """Führt Berechnung durch
    
    Request JSON:
    {
        "sequence": "[0/±45/90]s",
        "ply_thickness_mm": 0.125,
        "material": "M40J",
        "diameter_bottom_mm": 200,
        "diameter_top_mm": 200,
        "height_mm": 500,
        "winding_angle_deg": 45,
        "tow_width_mm": 5,
        "tow_count": 8,
        "overlap": 0.1,
        "process": "Towpreg"
    }
    """
    try:
        data = request.json

        # Parse Sequenz
        sequence = data.get('sequence', '')
        ply_thickness_mm = float(data.get('ply_thickness_mm', 0.125))
        material_key = data.get('material', 'M40J')

        if material_key not in MATERIALS:
            return jsonify({'error': f'Material {material_key} nicht gefunden'}), 400

        material = MATERIALS[material_key]
        ply_thickness_m = ply_thickness_mm / 1000.0

        layers = parser.parse_sequence(sequence, ply_thickness_m, material)

        # Geometrie
        geo = Geometry(
            d_bottom=float(data.get('diameter_bottom_mm', 200)) / 1000,
            d_top=float(data.get('diameter_top_mm', 200)) / 1000,
            height=float(data.get('height_mm', 500)) / 1000,
            winding_angle=float(data.get('winding_angle_deg', 45)),
            tow_width=float(data.get('tow_width_mm', 5)) / 1000,
            tow_count=int(data.get('tow_count', 8)),
            overlap=float(data.get('overlap', 0.1))
        )

        # Layup zusammenstellen
        layup = Layup(name="WebCalculation", layers=layers, geometry=geo)

        # Prozess
        process_key = data.get('process', 'Towpreg')
        if process_key in PROCESSES:
            layup.process = PROCESSES[process_key]

        # Berechnung
        summary = geometry.layup_summary(layup)

        # Total thickness
        total_thickness_m = sum(l.thickness for l in layers)

        result = {
            'success': True,
            'sequence': sequence,
            'num_layers': len(layers),
            'circumference_m': summary['umfang_m'],
            'path_length_m': summary['pfadlaenge_m'],
            'passes': summary['durchlaeufe'],
            'time_seconds': summary['zeit_s'],
            'time_minutes': summary['zeit_s'] / 60,
            'mass_kg': summary['masse_kg'],
            'total_thickness_mm': total_thickness_m * 1000,
            'layers': [
                {
                    'index': idx,
                    'angle': layer.angle,
                    'thickness_mm': layer.thickness * 1000,
                    'material': layer.material.name
                }
                for idx, layer in enumerate(layers)
            ]
        }

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 400


@app.route('/api/autoclave-profile', methods=['GET'])
def get_autoclave_profile():
    """Liefert das Standard-Autoklav-Profil"""
    profile = autoclave.default_autoclave_profile()
    return jsonify({
        'time_min': profile['time_min'],
        'temp_C': profile['temp_C'],
        'pressure_bar': profile['pressure_bar']
    })


@app.route('/health', methods=['GET'])
def health_check():
    """Health-Check Endpoint"""
    return jsonify({'status': 'ok', 'message': 'Filament Winding Tool Backend läuft'})


# ============================================================================
# Error Handler
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint nicht gefunden'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Interner Fehler'}), 500


# ============================================================================
# Main
# ============================================================================

if __name__ == '__main__':
    print("🚀 Filament Winding Tool Backend startet auf http://localhost:5000")
    print("📡 API verfügbar unter /api/*")
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
