"""
Quick test of materials and processes endpoints
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import sys
sys.path.insert(0, r'c:\fw_tool')

from backend.fw_core.presets import MATERIALS, PROCESSES
from backend.fw_core.lamina_properties import LaminaDatabase
from backend.fw_core import parser as fw_parser

app = Flask(__name__)
CORS(app)

# Initialize lamina database
lamina_db = LaminaDatabase()

@app.get("/api/materials")
def api_materials():
    result = {}
    for key, mat in MATERIALS.items():
        result[key] = {
            "name": getattr(mat, "name", key),
            "density": getattr(mat, "density", None),
            "fiber_areal_weight": getattr(mat, "fiber_areal_weight", None),
        }
    return jsonify(result)

@app.get("/api/processes")
def api_processes():
    result = {}
    for key, proc in PROCESSES.items():
        result[key] = {
            "name": getattr(proc, "name", key),
            "type": getattr(proc, "type", None),
            "line_speed": getattr(proc, "line_speed", None),
            "efficiency": getattr(proc, "efficiency", None),
        }
    return jsonify(result)

@app.post("/api/parse")
def api_parse():
    try:
        data = request.get_json()
        sequence = data.get("sequence", "[0/±45/90]s")
        ply_thickness_mm = data.get("ply_thickness_mm", 0.125)
        material_key = data.get("material", "M40J")
        
        if material_key not in MATERIALS:
            return jsonify({"error": f"Material {material_key} not found"}), 400
        
        material = MATERIALS[material_key]
        ply_thickness_m = ply_thickness_mm / 1000.0
        
        layers = fw_parser.parse_sequence(sequence, ply_thickness_m, material)
        
        result = {"sequence": sequence, "num_layers": len(layers), "layers": []}
        cum_mm = 0.0
        for idx, layer in enumerate(layers):
            t_mm = getattr(layer, "thickness", 0.0) * 1000.0
            cum_mm += t_mm
            result["layers"].append({
                "index": idx,
                "angle": getattr(layer, "angle", None),
                "thickness_mm": round(t_mm, 4),
                "material": getattr(getattr(layer, "material", None), "name", material_key),
                "cumulative_thickness_mm": round(cum_mm, 4)
            })
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.get("/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    print("[TEST] Quick test server on http://localhost:5001")
    print("[INFO] Endpoints: /api/materials, /api/processes, /api/parse, /health")
    app.run(debug=False, host="0.0.0.0", port=5001, use_reloader=False)
