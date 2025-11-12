"""
Filament Winding Tool – verbessertes Flask-Backend
- Robuster Sequenz-Parser (±, +/-, xN, Listenformat)
- Pydantic-Validierung für POST-Bodies
- Einheitliche Fehlerausgaben (keine Tracebacks in Prod)
- CORS enger konfigurierbar
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from pydantic import BaseModel, Field, ValidationError
from typing import List, Tuple, Optional, Any
import os
import re
import uuid
import logging
import traceback

# --- fw_core (dein Projekt) ---
from fw_core.model import Layup, Geometry as CoreGeometry
from fw_core.presets import MATERIALS, PROCESSES
from fw_core import parser as fw_parser
import fw_core.geometry as geom_ops
from fw_core.lamina_properties import LaminaDatabase
from fw_core.laminate_properties import LaminateProperties, SymmetricLaminate
from fw_core.failure_analysis import LaminateFailureAnalysis, ReserveFactorAnalysis
from fw_core.tolerance_analysis import ToleranceAnalysis
from fw_core import autoclave

# -----------------------------------------------------------------------------
# App & CORS
# -----------------------------------------------------------------------------
app = Flask(__name__)

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:8000").split(",")
CORS(app, resources={r"/api/*": {"origins": ALLOWED_ORIGINS}})

# Logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("fw_backend")

PROD = os.getenv("ENV", "dev").lower() == "prod"


# -----------------------------------------------------------------------------
# Pydantic Schemas (Validation)
# -----------------------------------------------------------------------------
class ParsePayload(BaseModel):
    sequence: str = Field(default="[0/±45/90]s")
    ply_thickness_mm: float = Field(default=0.125, gt=0)
    material: str = Field(default="M40J")


class CalculatePayload(ParsePayload):
    diameter_bottom_mm: float = Field(default=200.0, gt=0)
    diameter_top_mm: float = Field(default=200.0, gt=0)
    height_mm: float = Field(default=500.0, gt=0)
    winding_angle_deg: float = Field(default=45.0, ge=0, le=90)
    tow_width_mm: float = Field(default=5.0, gt=0)
    tow_count: int = Field(default=8, ge=1)
    overlap: float = Field(default=0.1, ge=0, lt=1.0)
    process: str = Field(default="Towpreg")


class LaminatePropsPayload(BaseModel):
    # sequence erlaubt: String ODER Liste
    sequence: Any = Field(default="[0/±45/90]s")
    ply_thickness_mm: float = Field(default=0.125, gt=0)
    material: str = Field(default="M40J")


class FailurePayload(LaminatePropsPayload):
    N_x: float = Field(default=1000.0)
    N_y: float = Field(default=0.0)
    N_xy: float = Field(default=0.0)
    load_case: str = Field(default="tension")


class TolerancePayload(LaminatePropsPayload):
    angle_tolerance_deg: float = Field(default=1.0, ge=0)
    thickness_tolerance_pct: float = Field(default=5.0, ge=0)
    num_samples: int = Field(default=500, ge=1, le=5000)
    N_x: Optional[float] = None
    N_y: Optional[float] = 0.0
    N_xy: Optional[float] = 0.0


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def json_body_or_empty() -> dict:
    return request.get_json(silent=True) or {}


def fail_response(e: Exception, code: int = 400):
    err_id = str(uuid.uuid4())[:8]
    # Immer loggen (inkl. Traceback), aber dem Client in PROD keine sensiblen Details senden
    logger.exception("ERR %s: %s", err_id, e)
    if PROD:
        return jsonify({"success": False, "error": f"Internal error ({err_id})"}), code
    return jsonify({"success": False, "error": str(e), "traceback": traceback.format_exc(), "err_id": err_id}), code


def ensure_material(material_key: str, db: dict, db_name: str):
    if material_key not in db:
        raise KeyError(f"Material '{material_key}' nicht in {db_name} vorhanden.")


def parse_sequence_general(payload_sequence: Any, default_material_key: str = "M40J") -> Tuple[List[Tuple[str, float, int]], bool]:
    """
    Vereinheitlichter Parser für CLT/Failure/Tolerance:
      - String:  "[0/±45/90]s", "[-45/0/+45]", "0x8/90x2", "[0/90]"
      - Liste:   [[material, angle_deg, num_plies], ...]
    Rückgabe: (lamina_list, is_symmetric)
    lamina_list: [(material_key, angle_deg, count), ...]
    """
    # Listenformat: direkt übernehmen
    if isinstance(payload_sequence, list):
        lamina_list = []
        for item in payload_sequence:
            if not isinstance(item, (list, tuple)) or len(item) != 3:
                raise ValueError(f"Ungültiger Sequenz-Eintrag (erwartet [mat, angle, count]): {item}")
            mkey, ang, cnt = item
            mkey = default_material_key if (mkey is None or mkey == "") else str(mkey)
            lamina_list.append((mkey, float(ang), int(cnt)))
        return lamina_list, False

    # Stringformat
    seq_str = str(payload_sequence).strip()
    is_symmetric = seq_str.lower().endswith('s')
    core = seq_str[:-1].strip() if is_symmetric else seq_str

    if core.startswith('[') and core.endswith(']'):
        core = core[1:-1].strip()

    if not core:
        return [(default_material_key, 0.0, 8)], is_symmetric

    lamina_list: List[Tuple[str, float, int]] = []
    for token in core.split('/'):
        a_str = token.strip()
        if not a_str:
            continue

        m = re.match(r'^(±|\+|-)?\s*(\d+)', a_str)
        if not m:
            raise ValueError(f"Ungültiger Layer-Eintrag: '{a_str}'")

        sign, ang = m.group(1), int(m.group(2))
        # Multiplikator ...xN
        c = 1
        cm = re.search(r'x\s*(\d+)$', a_str, re.IGNORECASE)
        if cm:
            c = int(cm.group(1))

        if sign == '±':
            lamina_list.append((default_material_key, +float(ang), c))
            lamina_list.append((default_material_key, -float(ang), c))
        else:
            val = -float(ang) if sign == '-' else float(ang)
            lamina_list.append((default_material_key, val, c))

    if not lamina_list:
        lamina_list = [(default_material_key, 0.0, 8)]
    return lamina_list, is_symmetric


# -----------------------------------------------------------------------------
# API: PRESETS-Lookups & Winding-Planung
# -----------------------------------------------------------------------------
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
        data = ParsePayload.model_validate(json_body_or_empty()).model_dump()
        ensure_material(data["material"], MATERIALS, "PRESETS.MATERIALS")

        material = MATERIALS[data["material"]]
        ply_thickness_m = data["ply_thickness_mm"] / 1000.0

        layers = fw_parser.parse_sequence(data["sequence"], ply_thickness_m, material)

        result = {"sequence": data["sequence"], "num_layers": len(layers), "layers": []}
        cum_mm = 0.0
        for idx, layer in enumerate(layers):
            t_mm = getattr(layer, "thickness", 0.0) * 1000.0
            cum_mm += t_mm
            result["layers"].append({
                "index": idx,
                "angle": getattr(layer, "angle", None),
                "thickness_mm": t_mm,
                "material": getattr(getattr(layer, "material", None), "name", data["material"]),
                "cumulative_thickness_mm": cum_mm
            })
        return jsonify(result)

    except ValidationError as ve:
        return fail_response(ve, 400)
    except Exception as e:
        return fail_response(e, 400)


@app.post("/api/calculate")
def api_calculate():
    try:
        data = CalculatePayload.model_validate(json_body_or_empty()).model_dump()
        ensure_material(data["material"], MATERIALS, "PRESETS.MATERIALS")

        material = MATERIALS[data["material"]]
        ply_thickness_m = data["ply_thickness_mm"] / 1000.0
        layers = fw_parser.parse_sequence(data["sequence"], ply_thickness_m, material)

        geo = CoreGeometry(
            d_bottom=data["diameter_bottom_mm"] / 1000.0,
            d_top=data["diameter_top_mm"] / 1000.0,
            height=data["height_mm"] / 1000.0,
            winding_angle=data["winding_angle_deg"],
            tow_width=data["tow_width_mm"] / 1000.0,
            tow_count=data["tow_count"],
            overlap=data["overlap"],
        )

        layup = Layup(name="WebCalculation", layers=layers, geometry=geo)
        if data["process"] in PROCESSES:
            layup.process = PROCESSES[data["process"]]

        summary = geom_ops.layup_summary(layup)
        total_thickness_m = sum(getattr(l, "thickness", 0.0) for l in layers)

        result = {
            "success": True,
            "sequence": data["sequence"],
            "num_layers": len(layers),
            "circumference_m": summary.get("umfang_m"),
            "path_length_m": summary.get("pfadlaenge_m"),
            "passes": summary.get("durchlaeufe"),
            "time_seconds": summary.get("zeit_s"),
            "time_minutes": (summary.get("zeit_s") or 0.0) / 60.0,
            "mass_kg": summary.get("masse_kg"),
            "total_thickness_mm": total_thickness_m * 1000.0,
            "layers": [
                {
                    "index": i,
                    "angle": getattr(l, "angle", None),
                    "thickness_mm": getattr(l, "thickness", 0.0) * 1000.0,
                    "material": getattr(getattr(l, "material", None), "name", data["material"]),
                } for i, l in enumerate(layers)
            ],
        }
        return jsonify(result)

    except ValidationError as ve:
        return fail_response(ve, 400)
    except Exception as e:
        return fail_response(e, 400)


@app.get("/api/autoclave-profile")
def api_autoclave_profile():
    try:
        profile = autoclave.default_autoclave_profile()
        return jsonify({
            "time_min": profile.get("time_min"),
            "temp_C": profile.get("temp_C"),
            "pressure_bar": profile.get("pressure_bar"),
        })
    except Exception as e:
        return fail_response(e, 400)


# -----------------------------------------------------------------------------
# CLT / Failure / Tolerance (LaminaDatabase-basierend)
# -----------------------------------------------------------------------------
@app.post("/api/laminate-properties")
def api_laminate_props():
    try:
        payload = LaminatePropsPayload.model_validate(json_body_or_empty())
        material_key = payload.material
        ensure_material(material_key, LaminaDatabase.MATERIALS, "LaminaDatabase.MATERIALS")

        lamina_list, is_sym = parse_sequence_general(payload.sequence, default_material_key=material_key)
        lam = SymmetricLaminate(lamina_list, ply_thickness_mm=payload.ply_thickness_mm) if is_sym \
              else LaminateProperties(lamina_list, ply_thickness_mm=payload.ply_thickness_mm)

        abd = lam.get_ABD_matrix()
        eff = lam.get_properties()
        try:
            total_thk = sum(getattr(p, "thickness_mm", payload.ply_thickness_mm) for p in lam.plies)
        except Exception:
            total_thk = len(lam.plies) * payload.ply_thickness_mm

        return jsonify({
            "success": True,
            "sequence": str(lamina_list),
            "num_plies": len(lam.plies),
            "total_thickness_mm": round(total_thk, 3),
            "A_matrix": lam.A.tolist(),
            "B_matrix": lam.B.tolist(),
            "D_matrix": lam.D.tolist(),
            "ABD_matrix": abd.tolist(),
            "effective_properties": {
                "E_x_GPa": round(eff["E_x"], 3),
                "E_y_GPa": round(eff["E_y"], 3),
                "G_xy_GPa": round(eff["G_xy"], 3),
                "nu_xy": round(eff["nu_xy"], 4),
            },
        })

    except ValidationError as ve:
        return fail_response(ve, 400)
    except Exception as e:
        return fail_response(e, 400)


@app.post("/api/failure-analysis")
def api_failure():
    try:
        payload = FailurePayload.model_validate(json_body_or_empty())
        material_key = payload.material
        ensure_material(material_key, LaminaDatabase.MATERIALS, "LaminaDatabase.MATERIALS")

        lamina_list, is_sym = parse_sequence_general(payload.sequence, default_material_key=material_key)
        lam = SymmetricLaminate(lamina_list, ply_thickness_mm=payload.ply_thickness_mm) if is_sym \
              else LaminateProperties(lamina_list, ply_thickness_mm=payload.ply_thickness_mm)

        analyzer = LaminateFailureAnalysis(lam)
        res = analyzer.analyze(payload.N_x, payload.N_y, payload.N_xy, payload.load_case)

        reserve_rating = ReserveFactorAnalysis.get_rf_rating(res["min_safety_factor"])

        plies_fmt = []
        for p in res["plies"]:
            plies_fmt.append({
                "ply_id": p["ply_id"],
                "angle_deg": round(p["angle"], 1),
                "sigma_1_MPa": round(p["sigma_1_MPa"], 2),
                "sigma_2_MPa": round(p["sigma_2_MPa"], 2),
                "tau_12_MPa": round(p["tau_12_MPa"], 2),
                "tsai_wu_index": round(p["tsai_wu_index"], 4),
                "safety_factor": round(p["safety_factor"], 2),
                "status": p["status"],
            })

        critical_idx = res.get("critical_ply")
        critical_angle = res["plies"][critical_idx]["angle"] if critical_idx is not None else None

        return jsonify({
            "success": True,
            "load_case": payload.load_case,
            "loads": {"N_x": payload.N_x, "N_y": payload.N_y, "N_xy": payload.N_xy},
            "ply_analysis": plies_fmt,
            "global_analysis": {
                "min_safety_factor": round(res["min_safety_factor"], 2),
                "max_failure_index": round(res["max_failure_index"], 4),
                "critical_ply_id": critical_idx,
                "critical_angle_deg": round(critical_angle, 1) if critical_angle is not None else None,
                "overall_status": res["overall_status"],
                "reserve_strength_percent": round(res["reserve_strength_percent"], 2),
                "design_status": "safe" if res["min_safety_factor"] > 1.5 else ("warning" if res["min_safety_factor"] > 1.0 else "critical"),
                "reserve_class": reserve_rating,
            },
        })

    except ValidationError as ve:
        return fail_response(ve, 400)
    except Exception as e:
        return fail_response(e, 400)


@app.post("/api/tolerance-study")
def api_tolerance():
    try:
        payload = TolerancePayload.model_validate(json_body_or_empty())
        material_key = payload.material
        ensure_material(material_key, LaminaDatabase.MATERIALS, "LaminaDatabase.MATERIALS")

        lamina_list, is_sym = parse_sequence_general(payload.sequence, default_material_key=material_key)
        lam = SymmetricLaminate(lamina_list, ply_thickness_mm=payload.ply_thickness_mm) if is_sym \
              else LaminateProperties(lamina_list, ply_thickness_mm=payload.ply_thickness_mm)

        tol = ToleranceAnalysis(lamina_list, ply_thickness_mm=payload.ply_thickness_mm, num_samples=payload.num_samples)

        prop_results = tol.run_tolerance_study(
            angle_tolerance_deg=payload.angle_tolerance_deg,
            thickness_tolerance_percent=payload.thickness_tolerance_pct,
        )

        conf = {}
        for k in ("E_x", "E_y", "G_xy"):
            if k in prop_results:
                lo, hi = tol.get_confidence_bounds(k, 0.95, prop_results)
                conf[k] = [round(lo, 4), round(hi, 4)]

        failure_stats = None
        if payload.N_x is not None:
            fail = tol.run_failure_tolerance_study(
                N_x=float(payload.N_x),
                N_y=float(payload.N_y or 0.0),
                N_xy=float(payload.N_xy or 0.0),
                num_samples=min(300, payload.num_samples),
            )
            sf_stats = fail.get("safety_factor", {})
            failure_stats = {
                "mean_safety_factor": round(sf_stats.get("mean", 0), 2),
                "std_safety_factor": round(sf_stats.get("std", 0), 2),
                "min_max_sf": [round(sf_stats.get("min", 0), 2), round(sf_stats.get("max", 0), 2)],
                "probability_of_failure": round(fail.get("probability_of_failure", 0), 4),
                "critical_ply_distribution": fail.get("critical_plies_distribution", {}),
            }

        def fmt_stats(stats: dict):
            return {
                "mean": round(stats["mean"], 4),
                "median": round(stats["median"], 4),
                "std": round(stats["std"], 4),
                "min": round(stats["min"], 4),
                "max": round(stats["max"], 4),
                "q05": round(stats["q05"], 4),
                "q25": round(stats["q25"], 4),
                "q75": round(stats["q75"], 4),
                "q95": round(stats["q95"], 4),
                "cv_percent": round(stats["cv"] * 100.0, 2),
            }

        prop_stats = {}
        for k in ("E_x", "E_y", "G_xy", "nu_xy"):
            if k in prop_results:
                prop_stats[k] = fmt_stats(prop_results[k])

        return jsonify({
            "success": True,
            "num_samples": payload.num_samples,
            "tolerances": {
                "angle_deg": payload.angle_tolerance_deg,
                "thickness_pct": payload.thickness_tolerance_pct,
            },
            "property_statistics": prop_stats,
            "confidence_intervals_95": conf,
            "failure_analysis": failure_stats,
        })

    except ValidationError as ve:
        return fail_response(ve, 400)
    except Exception as e:
        return fail_response(e, 400)


# -----------------------------------------------------------------------------
# Health & Errors
# -----------------------------------------------------------------------------
@app.get("/health")
def health():
    return jsonify({"status": "ok", "message": "Filament Winding Tool Backend läuft"})


@app.errorhandler(404)
def not_found(_):
    return jsonify({"error": "Endpoint nicht gefunden"}), 404


@app.errorhandler(500)
def internal_error(err):
    return fail_response(Exception(str(err)), 500)


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    print("[START] Backend auf http://localhost:5000  |  CORS:", ALLOWED_ORIGINS)
    app.run(debug=not PROD, host="0.0.0.0", port=5000, use_reloader=False)

