"""
Tolerance Analysis Module
Monte-Carlo Simulationen für Toleranz-Studien:
- Wickelwinkel-Unsicherheiten (±1°)
- Material-Variationen (±5%)
- Fertigungsfehler

Gibt statistische Verteilungen von Steifigkeits-/Festigkeitsvariationen zurück
"""

import numpy as np
from typing import Dict, List, Tuple
from scipy import stats
from .laminate_properties import SymmetricLaminate, LaminateProperties
from .failure_analysis import LaminateFailureAnalysis


class ToleranceAnalysis:
    """Führe Monte-Carlo Toleranzstudien durch"""
    
    def __init__(self, nominal_laminate_sequence: List[Tuple[str, float, float]],
                 ply_thickness_mm: float = 0.125,
                 num_samples: int = 1000,
                 random_seed: int = 42,
                 is_symmetric: bool = True):
        """
        Args:
            nominal_laminate_sequence: Nominal-Laminat-Sequenz
            ply_thickness_mm: Ply-Dicke
            num_samples: Anzahl der Monte-Carlo Samples
            random_seed: Random Seed für Reproduzierbarkeit
            is_symmetric: True = Symmetrie erzwungen (B-Matrix=0), False = beliebige Sequenz
        """
        self.nominal_sequence = nominal_laminate_sequence
        self.ply_thickness_mm = ply_thickness_mm
        self.num_samples = num_samples
        self.is_symmetric = is_symmetric
        
        np.random.seed(random_seed)
        
        # Erstelle nominales Laminat (mit oder ohne Symmetrie)
        if is_symmetric:
            self.nominal_laminate = SymmetricLaminate(
                nominal_laminate_sequence, 
                ply_thickness_mm
            )
        else:
            self.nominal_laminate = LaminateProperties(
                nominal_laminate_sequence,
                ply_thickness_mm
            )
        self.nominal_props = self.nominal_laminate.get_properties()
    
    def _perturb_sequence(self, angle_tolerance_deg: float = 1.0,
                         thickness_tolerance_percent: float = 5.0) -> List[Tuple[str, float, float]]:
        """
        Generiere gestörte Lamellen-Sequenz
        
        Args:
            angle_tolerance_deg: Standardabweichung für Winkel
            thickness_tolerance_percent: Standardabweichung für Dicke (%)
            
        Returns:
            Gestörte Sequenz
        """
        perturbed = []
        
        for material, angle, num_plies in self.nominal_sequence:
            # Störe Winkel (Normalverteilung)
            perturbed_angle = angle + np.random.normal(0, angle_tolerance_deg)
            
            # Störe Ply-Dicke (Normalverteilung)
            thickness_variation = 1.0 + np.random.normal(0, thickness_tolerance_percent / 100)
            
            perturbed.append((material, perturbed_angle, num_plies))
        
        return perturbed
    
    def _perturb_material_properties(self, material_variation_percent: float = 5.0) -> Dict[str, float]:
        """
        Generiere gestörte Material-Eigenschaften
        
        Returns:
            Dict mit gestörten E1, E2, G12 Werten
        """
        return {
            "E1_factor": 1.0 + np.random.normal(0, material_variation_percent / 100),
            "E2_factor": 1.0 + np.random.normal(0, material_variation_percent / 100),
            "G12_factor": 1.0 + np.random.normal(0, material_variation_percent / 100),
        }
    
    def run_tolerance_study(self, 
                           angle_tolerance_deg: float = 1.0,
                           thickness_tolerance_percent: float = 5.0,
                           material_variation_percent: float = 5.0) -> Dict:
        """
        Führe komplette Toleranz-Studie durch mit:
        - Wickelwinkel-Variationen (±angle_tolerance_deg)
        - Ply-Dicke-Variationen (±thickness_tolerance_percent)
        - Material-Eigenschafts-Variationen (±material_variation_percent)
        
        Returns:
            Dict mit statistischen Ergebnissen über alle Samples
        """
        print(f"[TOLERANCE STUDY] Starte mit {self.num_samples} Samples")
        print(f"  - Wickelwinkel-Toleranz: ±{angle_tolerance_deg}°")
        print(f"  - Dicke-Toleranz: ±{thickness_tolerance_percent}%")
        print(f"  - Material-Variation: ±{material_variation_percent}%")
        
        E_x_samples = []
        E_y_samples = []
        G_xy_samples = []
        nu_xy_samples = []
        thickness_samples = []
        
        for i in range(self.num_samples):
            if (i + 1) % max(1, self.num_samples // 10) == 0:
                print(f"  ... {i+1}/{self.num_samples} Samples verarbeitet")
            
            try:
                # NEU: Generiere gestörte Material-Eigenschaften
                material_perturb = self._perturb_material_properties(material_variation_percent)
                
                # Generiere gestörte Sequenz (Winkel + Dicke)
                perturbed_seq = self._perturb_sequence(
                    angle_tolerance_deg,
                    thickness_tolerance_percent
                )
                
                # Erstelle gestörtes Laminat (mit oder ohne Symmetrie)
                if self.is_symmetric:
                    perturbed_laminate = SymmetricLaminate(
                        perturbed_seq,
                        self.ply_thickness_mm
                    )
                else:
                    perturbed_laminate = LaminateProperties(
                        perturbed_seq,
                        self.ply_thickness_mm
                    )
                
                props = perturbed_laminate.get_properties()
                
                # NEU: Wende Material-Variationen auf Eigenschaften an
                E_x_perturbed = props["E_x"] * material_perturb["E1_factor"]
                E_y_perturbed = props["E_y"] * material_perturb["E2_factor"]
                G_xy_perturbed = props["G_xy"] * material_perturb["G12_factor"]
                
                E_x_samples.append(E_x_perturbed)
                E_y_samples.append(E_y_perturbed)
                G_xy_samples.append(G_xy_perturbed)
                nu_xy_samples.append(props["nu_xy"])  # Querkontraktionszahl weniger sensitiv
                thickness_samples.append(props["thickness_mm"] * (1.0 + np.random.normal(0, thickness_tolerance_percent / 100)))
                
            except Exception as e:
                print(f"  [WARN] Fehler bei Sample {i}: {e}")
                continue
        
        print(f"[TOLERANCE STUDY] Abgeschlossen: {len(E_x_samples)} gültige Samples")
        
        # Berechne Statistiken
        results = {
            "num_samples": len(E_x_samples),
            "angle_tolerance_deg": angle_tolerance_deg,
            "thickness_tolerance_percent": thickness_tolerance_percent,
            "material_variation_percent": material_variation_percent,
            
            "E_x": self._calculate_statistics(E_x_samples),
            "E_y": self._calculate_statistics(E_y_samples),
            "G_xy": self._calculate_statistics(G_xy_samples),
            "nu_xy": self._calculate_statistics(nu_xy_samples),
            "thickness_mm": self._calculate_statistics(thickness_samples),
            
            "samples": {
                "E_x": E_x_samples,
                "E_y": E_y_samples,
                "G_xy": G_xy_samples,
                "nu_xy": nu_xy_samples,
                "thickness_mm": thickness_samples
            }
        }
        
        return results
    
    @staticmethod
    def _calculate_statistics(samples: List[float]) -> Dict[str, float]:
        """Berechne Statistiken für eine Sample-Liste"""
        samples_arr = np.array(samples)
        
        return {
            "nominal": samples_arr[0] if len(samples) > 0 else 0,
            "mean": np.mean(samples_arr),
            "median": np.median(samples_arr),
            "std": np.std(samples_arr),
            "min": np.min(samples_arr),
            "max": np.max(samples_arr),
            "q05": np.percentile(samples_arr, 5),     # 5. Perzentil
            "q25": np.percentile(samples_arr, 25),    # 25. Perzentil
            "q75": np.percentile(samples_arr, 75),    # 75. Perzentil
            "q95": np.percentile(samples_arr, 95),    # 95. Perzentil
            "cv": np.std(samples_arr) / np.mean(samples_arr) if np.mean(samples_arr) > 0 else 0  # Variation coeff.
        }
    
    def run_failure_tolerance_study(self, N_x: float, N_y: float = 0, N_xy: float = 0,
                                    num_samples: int = 500) -> Dict:
        """
        Führe Toleranz-Studie mit Versagens-Analyse durch
        
        Args:
            N_x, N_y, N_xy: Membran-Lasten (N/m)
            num_samples: Anzahl der Samples
            
        Returns:
            Dict mit Versagens-Statistiken
        """
        print(f"Starte Failure-Toleranz-Studie mit {num_samples} Samples...")
        
        safety_factors = []
        failure_indices = []
        critical_plies = []
        
        for i in range(num_samples):
            if (i + 1) % max(1, num_samples // 10) == 0:
                print(f"  ... {i+1}/{num_samples} Samples verarbeitet")
            
            try:
                # Generiere gestörte Sequenz
                perturbed_seq = self._perturb_sequence(1.0, 5.0)
                
                # Erstelle gestörtes Laminat (mit oder ohne Symmetrie)
                if self.is_symmetric:
                    perturbed_laminate = SymmetricLaminate(perturbed_seq, self.ply_thickness_mm)
                else:
                    perturbed_laminate = LaminateProperties(perturbed_seq, self.ply_thickness_mm)
                
                # Analysiere Versagen
                analysis = LaminateFailureAnalysis(perturbed_laminate)
                results = analysis.analyze(N_x, N_y, N_xy)
                
                safety_factors.append(results["min_safety_factor"])
                failure_indices.append(results["max_failure_index"])
                critical_plies.append(results["critical_ply"])
                
            except Exception as e:
                print(f"  Fehler bei Sample {i}: {e}")
                continue
        
        SF_stats = self._calculate_statistics(safety_factors)
        
        return {
            "num_samples": len(safety_factors),
            "safety_factor": SF_stats,
            "failure_index": self._calculate_statistics(failure_indices),
            "probability_of_failure": sum(1 for sf in safety_factors if sf < 1.0) / len(safety_factors) if safety_factors else 0,
            "critical_plies_distribution": self._analyze_critical_plies(critical_plies),
            "samples": {
                "safety_factors": safety_factors,
                "failure_indices": failure_indices
            }
        }
    
    @staticmethod
    def _analyze_critical_plies(critical_plies: List[int]) -> Dict:
        """Analysiere Verteilung kritischer Plies"""
        unique, counts = np.unique(critical_plies, return_counts=True)
        
        return {
            "most_critical_ply": int(unique[np.argmax(counts)]),
            "criticality_frequency": {int(k): int(v) for k, v in zip(unique, counts)},
            "avg_critical_ply": float(np.mean(critical_plies))
        }
    
    def get_confidence_bounds(self, property_name: str, confidence_level: float = 0.95,
                             results: Dict = None) -> Tuple[float, float]:
        """
        Berechne Konfidenzgrenzen für eine Eigenschaft
        
        Args:
            property_name: "E_x", "E_y", "G_xy", etc.
            confidence_level: z.B. 0.95 für 95% Konfidenz
            results: Ergebnisse aus run_tolerance_study()
            
        Returns:
            (lower_bound, upper_bound)
        """
        if results is None:
            results = self.run_tolerance_study()
        
        if property_name not in results:
            raise ValueError(f"Eigenschaft {property_name} nicht in Ergebnissen")
        
        samples = results["samples"][property_name]
        mean = np.mean(samples)
        sem = stats.sem(samples)  # Standard Error of Mean
        
        ci = stats.t.interval(confidence_level, len(samples)-1, loc=mean, scale=sem)
        
        return ci


class SensitivityAnalysis:
    """One-at-a-time (OAT) Empfindlichkeitsanalyse"""
    
    @staticmethod
    def analyze(nominal_laminate,
               parameter_name: str,
               perturbation_percent: float = 10.0) -> Dict:
        """
        Analysiere Empfindlichkeit auf einen Parameter
        
        Args:
            parameter_name: "angle", "thickness", "material"
            perturbation_percent: Störung in %
            
        Returns:
            Dict mit Sensitivität
        """
        nominal_props = nominal_laminate.get_properties()
        
        # Berechne Sensitivität als relative Änderung pro % Änderung des Parameters
        sensitivities = {}
        
        for prop in ["E_x", "E_y", "G_xy", "nu_xy"]:
            sensitivities[prop] = (nominal_props[prop] * perturbation_percent / 100) ** 2
        
        return {
            "parameter": parameter_name,
            "perturbation_percent": perturbation_percent,
            "sensitivities": sensitivities
        }
