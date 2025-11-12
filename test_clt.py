"""
CLT Integration Test
Testet die klassische Laminattheorie mit einem realistischen Beispiel
"""

from fw_core.lamina_properties import LaminaDatabase
from fw_core.laminate_properties import SymmetricLaminate
from fw_core.failure_analysis import LaminateFailureAnalysis


def test_quasi_isotropic_laminate():
    """Teste quasi-isotrope Lamellen-Sequenz [0/±45/90]s"""
    
    print("=" * 70)
    print("CLT Test: Quasi-isotrope Lamellen [0/±45/90]s")
    print("=" * 70)
    
    # Definiere Laminat-Sequenz (nur obere Hälfte für Symmetrie)
    lamina_sequence = [
        ("M40J", 0, 1),      # 1 Ply @ 0°
        ("M40J", 45, 1),     # 1 Ply @ +45°
        ("M40J", -45, 1),    # 1 Ply @ -45°
        ("M40J", 90, 1),     # 1 Ply @ 90°
    ]
    
    # Erstelle symmetrisches Laminat
    laminate = SymmetricLaminate(lamina_sequence, ply_thickness_mm=0.125)
    
    print(f"\nSequenz: {laminate.get_sequence_string()}")
    print(f"Gesamtdicke: {laminate.effective_props['thickness_mm']:.3f} mm")
    print(f"Anzahl Plies: {laminate.effective_props['num_plies']}")
    
    # Effektive Eigenschaften
    props = laminate.get_properties()
    print("\n--- Effektive Laminat-Eigenschaften ---")
    print(f"E_x: {props['E_x']:.2f} GPa")
    print(f"E_y: {props['E_y']:.2f} GPa")
    print(f"G_xy: {props['G_xy']:.2f} GPa")
    print(f"ν_xy: {props['nu_xy']:.3f}")
    
    # ABD-Matrizen (nur Diagonale zeigen)
    print("\n--- ABD-Matrizen (Diagonale) ---")
    print(f"A₁₁: {laminate.A[0, 0]:.2e} N/m")
    print(f"A₂₂: {laminate.A[1, 1]:.2e} N/m")
    print(f"D₁₁: {laminate.D[0, 0]:.2e} N·m")
    print(f"D₂₂: {laminate.D[1, 1]:.2e} N·m")
    
    # Simuliere Last-Fall: Zug in x-Richtung
    print("\n--- Last-Fall: Zug 1000 N/m in x-Richtung ---")
    N_x = 1000  # N/m
    N_y = 0
    N_xy = 0
    
    analysis = LaminateFailureAnalysis(laminate)
    results = analysis.analyze(N_x, N_y, N_xy, load_case="tension")
    
    print(f"Gesamtstatus: {results['overall_status']}")
    print(f"Min. Sicherheitsfaktor: {results['min_safety_factor']:.2f}")
    print(f"Max. Failure Index: {results['max_failure_index']:.3f}")
    print(f"Reservekapazität: {results['reserve_strength_percent']:.1f}%")
    
    print("\n--- Spannungen und Versagen pro Ply ---")
    print("Ply | Angle | σ₁ [MPa] | σ₂ [MPa] | τ₁₂ [MPa] | Tsai-Wu | SF   | Status")
    print("-" * 75)
    for ply in results["plies"]:
        print(f"{ply['ply_id']:3d} | {ply['angle']:5.0f}° | {ply['sigma_1_MPa']:7.1f} | "
              f"{ply['sigma_2_MPa']:7.1f} | {ply['tau_12_MPa']:8.1f} | {ply['tsai_wu_index']:7.3f} | "
              f"{ply['safety_factor']:4.2f} | {ply['status']}")
    
    # Finde zulässige Last bei SF=1.5
    print("\n--- Zulässige Last-Berechnung ---")
    allowable_scale = analysis.find_allowable_load(N_x, target_SF=1.5)
    allowable_load = N_x * allowable_scale
    print(f"Zulässige Last bei SF=1.5: {allowable_load:.0f} N/m (Skalierung: {allowable_scale:.2f}x)")
    
    print("\n" + "=" * 70)
    return True


def test_unidirectional_laminate():
    """Teste unidirektionale Lamellen [0]8"""
    
    print("\n" + "=" * 70)
    print("CLT Test: Unidirektionale Lamellen [0]8")
    print("=" * 70)
    
    lamina_sequence = [
        ("IM7", 0, 4),  # 4 Plies @ 0°
    ]
    
    laminate = SymmetricLaminate(lamina_sequence, ply_thickness_mm=0.125)
    
    print(f"\nSequenz: {laminate.get_sequence_string()}")
    print(f"Gesamtdicke: {laminate.effective_props['thickness_mm']:.3f} mm")
    
    props = laminate.get_properties()
    print("\n--- Effektive Laminat-Eigenschaften ---")
    print(f"E_x: {props['E_x']:.2f} GPa")
    print(f"E_y: {props['E_y']:.2f} GPa")
    print(f"G_xy: {props['G_xy']:.2f} GPa")
    
    # Zug in Faserrichtung (sollte hohe Steifigkeit haben)
    N_x = 5000  # N/m
    analysis = LaminateFailureAnalysis(laminate)
    results = analysis.analyze(N_x, 0, 0, load_case="tension")
    
    print(f"\nUnter {N_x} N/m Zug:")
    print(f"  Status: {results['overall_status']}")
    print(f"  Sicherheitsfaktor: {results['min_safety_factor']:.2f}")
    
    print("\n" + "=" * 70)
    return True


if __name__ == "__main__":
    try:
        test_quasi_isotropic_laminate()
        test_unidirectional_laminate()
        print("\n✅ Alle CLT-Tests erfolgreich!")
    except Exception as e:
        print(f"\n❌ Test fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()
