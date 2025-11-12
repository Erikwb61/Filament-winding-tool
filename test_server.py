"""
Quick test of materials and processes endpoints
"""

from flask import Flask, jsonify
from flask_cors import CORS
import sys
sys.path.insert(0, r'c:\fw_tool')

from backend.fw_core.presets import MATERIALS, PROCESSES

app = Flask(__name__)
CORS(app)

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

@app.get("/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    print("[TEST] Quick test server on http://localhost:5001")
    app.run(debug=False, host="0.0.0.0", port=5001, use_reloader=False)
