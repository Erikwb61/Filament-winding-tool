"""
Failure Analysis Module
Implementiert verschiedene Versagenskriterien für Faserverbundstoffe
(Tsai-Wu, Maximum Stress, Maximum Strain)

Classical Laminate Theory (CLT) - Teil 3
"""

import numpy as np
from typing import List, Dict, Tuple
from .lamina_properties import LaminaDatabase


class FailureAnalysis:
    """Berechnet Versagenskriterien für Laminaten"""
    
    @staticmethod
    def tsai_wu_criterion(sigma_1: float, sigma_2: float, tau_12: float,
                         material: str) -> float:
        """
        Berechne Tsai-Wu Versagenskriterium
        
        F = (σ₁/F₁ᵗ)(σ₁/F₁ᶜ) + (σ₂/F₂ᵗ)(σ₂/F₂ᶜ) + (τ₁₂/F₁₂ˢ)² 
            + σ₁(1/F₁ᵗ - 1/F₁ᶜ) + σ₂(1/F₂ᵗ - 1/F₂ᶜ) - 2f₁₂(σ₁σ₂/(F₁ᵗF₁ᶜF₂ᵗF₂ᶜ))
        
        Versagen wenn F ≥ 1
        
        Args:
            sigma_1, sigma_2, tau_12: Spannungen in Faserkoordinaten (MPa)
            material: Materialname
            
        Returns:
            Failure Index (0 = sicher, 1 = Versagen, >1 = Versagen)
        """
        lamina = LaminaDatabase.get_lamina(material)
        props = lamina.get_strength_properties()
        
        F1t = props["F_1t"]  # Zug-Festigkeit Faserrichtung
        F1c = props["F_1c"]  # Druck-Festigkeit Faserrichtung
        F2t = props["F_2t"]  # Zug-Festigkeit Querrichtung
        F2c = props["F_2c"]  # Druck-Festigkeit Querrichtung
        F12s = props["F_12s"] # Scherfestigkeit
        
        # Interaktionsparameter (typisch f12 = 0 für erste Näherung)
        f12 = 0.0
        
        # Berechne die einzelnen Terme
        term1 = (sigma_1 / (F1t * F1c)) * sigma_1
        term2 = (sigma_2 / (F2t * F2c)) * sigma_2
        term3 = (tau_12 / F12s)**2
        term4 = sigma_1 * (1/F1t - 1/F1c)
        term5 = sigma_2 * (1/F2t - 1/F2c)
        term6 = -2 * f12 * (sigma_1 * sigma_2 / (F1t * F1c * F2t * F2c))
        
        F = term1 + term2 + term3 + term4 + term5 + term6
        
        return F
    
    @staticmethod
    def maximum_stress_criterion(sigma_1: float, sigma_2: float, tau_12: float,
                                 material: str) -> Tuple[float, float]:
        """
        Maximum Stress Criterion
        Einfaches Versagenskriterium: Vergleich mit Festigkeitswerten
        
        Returns:
            (failure_index, limiting_stress)
        """
        lamina = LaminaDatabase.get_lamina(material)
        props = lamina.get_strength_properties()
        
        F1t = props["F_1t"]
        F1c = props["F_1c"]
        F2t = props["F_2t"]
        F2c = props["F_2c"]
        F12s = props["F_12s"]
        
        # Normalisiere jede Spannung
        ratios = []
        
        if sigma_1 > 0:
            ratios.append(sigma_1 / F1t)
        elif sigma_1 < 0:
            ratios.append(-sigma_1 / F1c)
        
        if sigma_2 > 0:
            ratios.append(sigma_2 / F2t)
        elif sigma_2 < 0:
            ratios.append(-sigma_2 / F2c)
        
        ratios.append(abs(tau_12) / F12s)
        
        failure_index = max(ratios) if ratios else 0
        return failure_index, max(ratios)
    
    @staticmethod
    def calculate_safety_factor(failure_index: float) -> float:
        """
        Berechne Sicherheitsfaktor aus Failure Index
        
        Args:
            failure_index: Failure Index (0-1 = sicher, >1 = Versagen)
            
        Returns:
            Sicherheitsfaktor (>1 = sicher)
        """
        if failure_index < 1e-6:
            return 999.0  # Praktisch unendlich
        return 1.0 / failure_index


class LaminateFailureAnalysis:
    """Analysiere Versagensrisiko für komplettes Laminat"""
    
    def __init__(self, laminate_props):
        """
        Args:
            laminate_props: LaminateProperties-Objekt
        """
        self.laminate = laminate_props
    
    def analyze(self, N_x: float, N_y: float, N_xy: float, 
                load_case: str = "tension") -> Dict:
        """
        Analysiere das komplette Laminat unter Last
        
        Args:
            N_x, N_y, N_xy: Membran-Kräfte (N/m)
            load_case: "tension", "compression", "shear"
            
        Returns:
            Dict mit Failure Analysis für jeden Ply
        """
        # Berechne Spannungen in jedem Ply
        ply_stresses = self.laminate.get_ply_stresses(N_x, N_y, N_xy)
        
        results = {
            "load_case": load_case,
            "plies": [],
            "critical_ply": None,
            "min_safety_factor": 999.0,
            "max_failure_index": 0.0
        }
        
        for i, ply_stress in enumerate(ply_stresses):
            sigma_1 = ply_stress["sigma_1"]
            sigma_2 = ply_stress["sigma_2"]
            tau_12 = ply_stress["tau_12"]
            
            # Berechne Failure Indices
            F_TW = FailureAnalysis.tsai_wu_criterion(
                sigma_1, sigma_2, tau_12, ply_stress["material"]
            )
            F_MS, _ = FailureAnalysis.maximum_stress_criterion(
                sigma_1, sigma_2, tau_12, ply_stress["material"]
            )
            
            SF = FailureAnalysis.calculate_safety_factor(F_TW)
            
            ply_result = {
                "ply_id": i,
                "angle": ply_stress["angle"],
                "material": ply_stress["material"],
                "sigma_1_MPa": sigma_1,
                "sigma_2_MPa": sigma_2,
                "tau_12_MPa": tau_12,
                "tsai_wu_index": F_TW,
                "max_stress_index": F_MS,
                "safety_factor": SF,
                "status": "Safe" if F_TW < 1.0 else "Failed"
            }
            
            results["plies"].append(ply_result)
            
            # Tracke kritischen Ply
            if F_TW > results["max_failure_index"]:
                results["max_failure_index"] = F_TW
                results["critical_ply"] = i
            
            if SF < results["min_safety_factor"]:
                results["min_safety_factor"] = SF
        
        # Gesamt-Beurteilung
        results["overall_status"] = "Safe" if results["max_failure_index"] < 1.0 else "Failed"
        results["reserve_strength_percent"] = max(0, (1 - results["max_failure_index"]) * 100)
        
        return results
    
    def find_allowable_load(self, N_x_ref: float, N_y_ref: float = 0, N_xy_ref: float = 0,
                           target_SF: float = 1.5) -> float:
        """
        Finde zulässige Last bei gegebenem Sicherheitsfaktor
        
        Args:
            N_x_ref, N_y_ref, N_xy_ref: Referenz-Kräfte (N/m)
            target_SF: Ziel-Sicherheitsfaktor
            
        Returns:
            Skalierungsfaktor für zulässige Last
        """
        # Binäre Suche nach zulässiger Last
        scale_low = 0.0
        scale_high = 10.0
        tolerance = 0.001
        
        while scale_high - scale_low > tolerance:
            scale_mid = (scale_low + scale_high) / 2
            
            analysis = self.analyze(
                N_x_ref * scale_mid,
                N_y_ref * scale_mid,
                N_xy_ref * scale_mid
            )
            
            if analysis["min_safety_factor"] < target_SF:
                scale_high = scale_mid
            else:
                scale_low = scale_mid
        
        return scale_high


class ReserveFactorAnalysis:
    """Berechne Reserve Factors nach MIL-HDBK-17"""
    
    @staticmethod
    def calculate_rf(failure_index: float) -> float:
        """
        Reserve Factor = 1 / Failure Index
        """
        if failure_index < 1e-6:
            return 999.0
        return 1.0 / failure_index
    
    @staticmethod
    def get_rf_rating(rf: float) -> str:
        """Klassifiziere Reserve Factor"""
        if rf < 1.0:
            return "Critical"
        elif rf < 1.5:
            return "Poor"
        elif rf < 2.0:
            return "Acceptable"
        elif rf < 3.0:
            return "Good"
        else:
            return "Excellent"
