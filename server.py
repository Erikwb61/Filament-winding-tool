"""
Flask Backend für Filament Winding Tool
Integriert die echten fw_core Module
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import traceback
import json
import numpy as np

from fw_core.model import Layup, Geometry, Layer
from fw_core.presets import MATERIALS, PROCESSES
from fw_core import parser, geometry, autoclave
from fw_core.lamina_properties import LaminaDatabase
from fw_core.laminate_properties import LaminateProperties, SymmetricLaminate
from fw_core.failure_analysis import LaminateFailureAnalysis, ReserveFactorAnalysis
from fw_core.tolerance_analysis import ToleranceAnalysis

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


# ============================================================================
# CLT (Classical Laminate Theory) Endpoints
# ============================================================================

@app.route('/api/laminate-properties', methods=['POST'])
def laminate_properties():
    """Berechnet Laminateigenschaften (ABD-Matrix)
    
    Request JSON:
    {
        "sequence": [[material, angle, num_plies], ...],  oder String "[0/±45/90]s"
        "ply_thickness_mm": 0.125,
        "material": "M40J"
    }
    
    Response:
    {
        "A_matrix": [[...], [...], [...]],  3x3 Membransteifigkeitsmatrix
        "B_matrix": [[...], [...], [...]],  3x3 Kopplungsmatrix
        "D_matrix": [[...], [...], [...]],  3x3 Biegesteifigkeitsmatrix
        "ABD_matrix": [[6x6 kombiniert]],
        "effective_properties": {E_x, E_y, G_xy, nu_xy},
        "num_plies": int,
        "total_thickness_mm": float,
        "laminate_type": "symmetric|asymmetric"
    }
    """
    try:
        data = request.json
        material_key = data.get('material', 'M40J')
        ply_thickness_mm = float(data.get('ply_thickness_mm', 0.125))
        ply_thickness_m = ply_thickness_mm / 1000.0
        
        if material_key not in LaminaDatabase.materials:
            return jsonify({'error': f'Material {material_key} nicht in Datenbank'}), 400
        
        # Parse sequence - akzeptiert JSON-Array oder String
        sequence_input = data.get('sequence')
        
        if isinstance(sequence_input, str):
            # String-Format: "[0/±45/90]s" → SymmetricLaminate verwenden
            laminate = SymmetricLaminate(
                base_sequence=sequence_input,
                material=material_key,
                ply_thickness=ply_thickness_m
            )
            sequence_list = laminate.get_sequence()
        else:
            # Array-Format: [[material, angle, count], ...]
            sequence_list = sequence_input if sequence_input else [['M40J', 0, 8]]
        
        # LaminateProperties erstellen
        lam = LaminateProperties(
            sequence=sequence_list,
            material_name=material_key,
            ply_thickness=ply_thickness_m
        )
        
        # ABD-Matrix berechnen
        abd_matrix = lam.get_ABD_matrix()
        
        # Effektive Eigenschaften
        eff_props = lam.get_effective_properties()
        
        # Total thickness
        total_thickness = sum(s[2] for s in sequence_list) * ply_thickness_mm
        
        result = {
            'success': True,
            'sequence': str(sequence_list),
            'num_plies': sum(s[2] for s in sequence_list),
            'total_thickness_mm': round(total_thickness, 4),
            'A_matrix': lam._A_matrix.tolist() if hasattr(lam, '_A_matrix') else [],
            'B_matrix': lam._B_matrix.tolist() if hasattr(lam, '_B_matrix') else [],
            'D_matrix': lam._D_matrix.tolist() if hasattr(lam, '_D_matrix') else [],
            'ABD_matrix': abd_matrix.tolist(),
            'effective_properties': {
                'E_x_GPa': round(eff_props['E_x'], 3),
                'E_y_GPa': round(eff_props['E_y'], 3),
                'G_xy_GPa': round(eff_props['G_xy'], 3),
                'nu_xy': round(eff_props['nu_xy'], 4),
                'laminate_type': 'symmetric' if lam.is_symmetric else 'asymmetric'
            }
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 400


@app.route('/api/failure-analysis', methods=['POST'])
def failure_analysis():
    """Versagensanalyse mit Tsai-Wu Kriterium
    
    Request JSON:
    {
        "sequence": [[material, angle, num_plies], ...],
        "ply_thickness_mm": 0.125,
        "material": "M40J",
        "N_x": 1000,      // N/m (Normalkraft in x-Richtung)
        "N_y": 0,
        "N_xy": 0,
        "load_case": "tension"
    }
    
    Response:
    {
        "ply_analysis": [
            {ply_id, angle, sigma_1, sigma_2, tau_12, tsai_wu_index, safety_factor, status}
        ],
        "global_analysis": {
            "min_safety_factor": float,
            "max_failure_index": float,
            "critical_ply_id": int,
            "critical_angle": float,
            "probability_of_failure": float,
            "design_status": "safe|warning|critical"
        }
    }
    """
    try:
        data = request.json
        material_key = data.get('material', 'M40J')
        ply_thickness_mm = float(data.get('ply_thickness_mm', 0.125))
        ply_thickness_m = ply_thickness_mm / 1000.0
        
        # Loads
        N_x = float(data.get('N_x', 1000))
        N_y = float(data.get('N_y', 0))
        N_xy = float(data.get('N_xy', 0))
        load_case = data.get('load_case', 'tension')
        
        if material_key not in LaminaDatabase.materials:
            return jsonify({'error': f'Material {material_key} nicht in Datenbank'}), 400
        
        # Parse sequence
        sequence_input = data.get('sequence')
        
        if isinstance(sequence_input, str):
            laminate = SymmetricLaminate(
                base_sequence=sequence_input,
                material=material_key,
                ply_thickness=ply_thickness_m
            )
            sequence_list = laminate.get_sequence()
        else:
            sequence_list = sequence_input if sequence_input else [['M40J', 0, 8]]
        
        # LaminateProperties
        lam = LaminateProperties(
            sequence=sequence_list,
            material_name=material_key,
            ply_thickness=ply_thickness_m
        )
        
        # Failure Analysis
        failure_analyzer = LaminateFailureAnalysis(lam, material_key)
        analysis_result = failure_analyzer.analyze(N_x, N_y, N_xy, load_case)
        
        # Reserve Factor Rating
        reserve_analyzer = ReserveFactorAnalysis()
        min_sf = analysis_result['min_safety_factor']
        reserve_rating = reserve_analyzer.classify_reserve_factor(min_sf)
        
        # Format response
        ply_data = []
        for ply_id, ply_info in enumerate(analysis_result['ply_data']):
            ply_data.append({
                'ply_id': ply_id,
                'angle_deg': round(ply_info['angle'], 1),
                'sigma_1_MPa': round(ply_info['sigma_1'], 2),
                'sigma_2_MPa': round(ply_info['sigma_2'], 2),
                'tau_12_MPa': round(ply_info['tau_12'], 2),
                'tsai_wu_index': round(ply_info['tsai_wu_index'], 4),
                'safety_factor': round(ply_info['safety_factor'], 2),
                'status': 'safe' if ply_info['safety_factor'] > 1.0 else 'failed'
            })
        
        result = {
            'success': True,
            'load_case': load_case,
            'loads': {'N_x': N_x, 'N_y': N_y, 'N_xy': N_xy},
            'ply_analysis': ply_data,
            'global_analysis': {
                'min_safety_factor': round(min_sf, 2),
                'max_failure_index': round(analysis_result['max_failure_index'], 4),
                'critical_ply_id': analysis_result['critical_ply_id'],
                'critical_angle_deg': round(analysis_result['critical_angle'], 1),
                'probability_of_failure': round(analysis_result['probability_of_failure'], 4),
                'design_status': 'safe' if min_sf > 1.5 else ('warning' if min_sf > 1.0 else 'critical'),
                'reserve_rating': reserve_rating
            }
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 400


@app.route('/api/tolerance-study', methods=['POST'])
def tolerance_study():
    """Monte-Carlo Toleranzanalyse
    
    Request JSON:
    {
        "sequence": [[material, angle, num_plies], ...],
        "ply_thickness_mm": 0.125,
        "material": "M40J",
        "angle_tolerance_deg": 1.0,
        "thickness_tolerance_pct": 5.0,
        "num_samples": 500,
        "N_x": 1000,  // Optional: Für Failure-Studie
        "N_y": 0,
        "N_xy": 0
    }
    
    Response:
    {
        "property_statistics": {
            "E_x": {mean, std, q05, q25, q75, q95, cv},
            "E_y": {...},
            "G_xy": {...},
            "nu_xy": {...}
        },
        "confidence_intervals_95": {
            "E_x": [lower, upper],
            "E_y": [lower, upper],
            "G_xy": [lower, upper]
        },
        "failure_statistics": {
            "mean_sf": float,
            "std_sf": float,
            "probability_of_failure": float,
            "critical_ply_distribution": {ply_id: count}
        },
        "num_samples": int
    }
    """
    try:
        data = request.json
        material_key = data.get('material', 'M40J')
        ply_thickness_mm = float(data.get('ply_thickness_mm', 0.125))
        ply_thickness_m = ply_thickness_mm / 1000.0
        num_samples = int(data.get('num_samples', 500))
        angle_tol = float(data.get('angle_tolerance_deg', 1.0))
        thickness_tol = float(data.get('thickness_tolerance_pct', 5.0))
        
        if material_key not in LaminaDatabase.materials:
            return jsonify({'error': f'Material {material_key} nicht in Datenbank'}), 400
        
        # Parse sequence
        sequence_input = data.get('sequence')
        
        if isinstance(sequence_input, str):
            laminate = SymmetricLaminate(
                base_sequence=sequence_input,
                material=material_key,
                ply_thickness=ply_thickness_m
            )
            sequence_list = laminate.get_sequence()
        else:
            sequence_list = sequence_input if sequence_input else [['M40J', 0, 8]]
        
        # LaminateProperties
        lam = LaminateProperties(
            sequence=sequence_list,
            material_name=material_key,
            ply_thickness=ply_thickness_m
        )
        
        # ToleranceAnalysis
        tol_analyzer = ToleranceAnalysis(lam, num_samples=num_samples)
        
        # Property tolerance study
        prop_results = tol_analyzer.run_tolerance_study(
            angle_tol_deg=angle_tol,
            thickness_tol_pct=thickness_tol
        )
        
        # Confidence intervals
        conf_intervals = {}
        for prop in ['E_x', 'E_y', 'G_xy']:
            if prop in prop_results:
                ci = tol_analyzer.get_confidence_bounds(prop, 0.95, prop_results)
                conf_intervals[prop] = [round(ci[0], 4), round(ci[1], 4)]
        
        # Optional: Failure tolerance study
        failure_stats = None
        N_x = data.get('N_x')
        if N_x is not None:
            N_x = float(N_x)
            N_y = float(data.get('N_y', 0))
            N_xy = float(data.get('N_xy', 0))
            
            fail_results = tol_analyzer.run_failure_tolerance_study(
                N_x=N_x, N_y=N_y, N_xy=N_xy,
                num_samples=min(300, num_samples)
            )
            
            failure_stats = {
                'mean_safety_factor': round(fail_results['mean_sf'], 2),
                'std_safety_factor': round(fail_results['std_sf'], 2),
                'min_max_sf': [round(fail_results['min_sf'], 2), round(fail_results['max_sf'], 2)],
                'probability_of_failure': round(fail_results['prob_failure'], 4),
                'critical_ply_distribution': {str(k): v for k, v in fail_results['critical_ply_dist'].items()}
            }
        
        # Format property statistics
        prop_stats = {}
        for prop in ['E_x', 'E_y', 'G_xy', 'nu_xy']:
            if prop in prop_results:
                stats = prop_results[prop]
                prop_stats[prop] = {
                    'mean': round(stats['mean'], 4),
                    'median': round(stats['median'], 4),
                    'std': round(stats['std'], 4),
                    'min': round(stats['min'], 4),
                    'max': round(stats['max'], 4),
                    'q05': round(stats['q05'], 4),
                    'q25': round(stats['q25'], 4),
                    'q75': round(stats['q75'], 4),
                    'q95': round(stats['q95'], 4),
                    'cv_percent': round(stats['cv'] * 100, 2)
                }
        
        result = {
            'success': True,
            'num_samples': num_samples,
            'tolerances': {
                'angle_deg': angle_tol,
                'thickness_pct': thickness_tol
            },
            'property_statistics': prop_stats,
            'confidence_intervals_95': conf_intervals,
            'failure_analysis': failure_stats
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 400


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
