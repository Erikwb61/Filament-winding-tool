"""
Tolerance Analysis Test
Testet die Monte-Carlo Toleranz-Simulation
"""

from fw_core.tolerance_analysis import ToleranceAnalysis, SensitivityAnalysis
import json


def test_tolerance_study():
    """Teste Toleranz-Studie"""
    
    print("=" * 70)
    print("Toleranz-Studie: Quasi-isotrope Lamellen [0/±45/90]s")
    print("=" * 70)
    
    # Definiere nominale Sequenz
    nominal_sequence = [
        ("M40J", 0, 1),
        ("M40J", 45, 1),
        ("M40J", -45, 1),
        ("M40J", 90, 1),
    ]
    
    # Erstelle Toleranz-Analyzer
    analyzer = ToleranceAnalysis(
        nominal_sequence,
        ply_thickness_mm=0.125,
        num_samples=500  # 500 Samples für schnelleren Test
    )
    
    print(f"\nNominale Eigenschaften:")
    print(f"  E_x: {analyzer.nominal_props['E_x']:.3f} GPa")
    print(f"  E_y: {analyzer.nominal_props['E_y']:.3f} GPa")
    print(f"  G_xy: {analyzer.nominal_props['G_xy']:.3f} GPa")
    
    # Führe Toleranz-Studie durch
    print(f"\nFühre Monte-Carlo Studie durch (Winkel ±1°, Dicke ±5%)...")
    results = analyzer.run_tolerance_study(
        angle_tolerance_deg=1.0,
        thickness_tolerance_percent=5.0
    )
    
    print(f"\n--- Ergebnisse für E_x ---")
    print(f"  Mittelwert: {results['E_x']['mean']:.4f} GPa")
    print(f"  Std.Abw.: {results['E_x']['std']:.4f} GPa")
    print(f"  Min-Max: [{results['E_x']['min']:.4f}, {results['E_x']['max']:.4f}] GPa")
    print(f"  5%-95% CI: [{results['E_x']['q05']:.4f}, {results['E_x']['q95']:.4f}] GPa")
    print(f"  Variations-Koeff.: {results['E_x']['cv']:.3f} (=±{results['E_x']['cv']*100:.1f}%)")
    
    print(f"\n--- Ergebnisse für G_xy ---")
    print(f"  Mittelwert: {results['G_xy']['mean']:.4f} GPa")
    print(f"  Std.Abw.: {results['G_xy']['std']:.4f} GPa")
    print(f"  5%-95% CI: [{results['G_xy']['q05']:.4f}, {results['G_xy']['q95']:.4f}] GPa")
    
    # Berechne Konfidenzgrenzen
    print(f"\n--- Konfidenzintervalle (95%) ---")
    ci_Ex = analyzer.get_confidence_bounds("E_x", 0.95, results)
    ci_Ey = analyzer.get_confidence_bounds("E_y", 0.95, results)
    print(f"  E_x: [{ci_Ex[0]:.4f}, {ci_Ex[1]:.4f}] GPa")
    print(f"  E_y: [{ci_Ey[0]:.4f}, {ci_Ey[1]:.4f}] GPa")
    
    print("\n" + "=" * 70)


def test_failure_tolerance_study():
    """Teste Failure-Toleranz-Studie"""
    
    print("\n" + "=" * 70)
    print("Failure Tolerance Study")
    print("=" * 70)
    
    nominal_sequence = [
        ("IM7", 0, 2),
        ("IM7", 45, 1),
        ("IM7", -45, 1),
        ("IM7", 90, 1),
    ]
    
    analyzer = ToleranceAnalysis(
        nominal_sequence,
        num_samples=300
    )
    
    print(f"\nFühre Failure-Toleranz-Studie durch unter Last (1000 N/m @ 0°)...")
    
    # Analysiere unter Zug-Last
    results = analyzer.run_failure_tolerance_study(
        N_x=1000,
        num_samples=300
    )
    
    print(f"\n--- Versagens-Statistiken ---")
    print(f"  Durchschn. Sicherheitsfaktor: {results['safety_factor']['mean']:.2f}")
    print(f"  Std.Abw.: {results['safety_factor']['std']:.2f}")
    print(f"  Min-Max: [{results['safety_factor']['min']:.2f}, {results['safety_factor']['max']:.2f}]")
    print(f"  Ausfallwahrscheinlichkeit: {results['probability_of_failure']*100:.2f}%")
    
    print(f"\n--- Kritische Plies ---")
    dist = results['critical_plies_distribution']
    print(f"  Häufigster kritischer Ply: {dist['most_critical_ply']}")
    print(f"  Durchschnittlicher kritischer Ply: {dist['avg_critical_ply']:.1f}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    try:
        test_tolerance_study()
        test_failure_tolerance_study()
        print("\n✅ Alle Toleranzanalyse-Tests erfolgreich!")
    except Exception as e:
        print(f"\n❌ Test fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()
