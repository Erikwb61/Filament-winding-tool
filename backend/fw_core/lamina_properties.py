"""
Lamina Properties Module
Berechnet die Steifigkeitseigenschaften einzelner Faserschichten (Lamina)
basierend auf Materialdaten und lokalen Koordinatensystemen.

Classical Laminate Theory (CLT) - Teil 1
"""

import numpy as np
from typing import Dict, Tuple


class LaminaProperties:
    """Berechnet Materialeigenschaften für einzelne Lamina (Faserschichten)"""
    
    def __init__(self, E1: float, E2: float, nu12: float, G12: float, 
                 t: float = 0.125):
        """
        Initialisiere Lamina-Eigenschaften
        
        Args:
            E1: Längsmodul (Faserrichtung) in GPa
            E2: Quermodul (Transversal) in GPa
            nu12: Querkontraktionszahl
            G12: Schubmodul in GPa
            t: Schichtdicke in mm
        """
        self.E1 = E1  # GPa
        self.E2 = E2  # GPa
        self.nu12 = nu12
        self.nu21 = (E2 / E1) * nu12  # Symmetrie der Compliance-Matrix
        self.G12 = G12  # GPa
        self.t = t / 1000  # Konvertiere mm -> m
        
        # Berechne Compliance-Matrix S (in 1/GPa)
        self.S = self._calculate_compliance_matrix()
        
        # Berechne Steifigkeitsmatrix Q (in GPa)
        self.Q = self._calculate_stiffness_matrix()
    
    def _calculate_compliance_matrix(self) -> np.ndarray:
        """Berechne 3x3 Compliance-Matrix S in Materialkoordinaten (1-2-3)"""
        S = np.zeros((3, 3))
        
        S[0, 0] = 1 / self.E1
        S[1, 1] = 1 / self.E2
        S[2, 2] = 1 / self.G12
        S[0, 1] = -self.nu12 / self.E1
        S[1, 0] = -self.nu21 / self.E2
        
        return S
    
    def _calculate_stiffness_matrix(self) -> np.ndarray:
        """Berechne 3x3 Steifigkeitsmatrix Q = S^(-1) in Materialkoordinaten"""
        Q = np.linalg.inv(self.S)
        return Q
    
    def get_Q_bar(self, theta_deg: float) -> np.ndarray:
        """
        Berechne transformierte Steifigkeitsmatrix Q̄ für beliebigen Wickelwinkel
        
        Args:
            theta_deg: Wickelwinkel in Grad (0° = Faserrichtung)
            
        Returns:
            3x3 Q̄-Matrix in globalen Koordinaten (x-y-z)
        """
        theta = np.radians(theta_deg)
        c = np.cos(theta)
        s = np.sin(theta)
        
        # Transformationsmatrix für Spannungen
        T = np.array([
            [c**2, s**2, 2*c*s],
            [s**2, c**2, -2*c*s],
            [-c*s, c*s, c**2 - s**2]
        ])
        
        # Transformationsmatrix für Dehnungen (mit Faktor 2 für Schub)
        T_strain = np.array([
            [c**2, s**2, c*s],
            [s**2, c**2, -c*s],
            [-2*c*s, 2*c*s, c**2 - s**2]
        ])
        
        # Q̄ = T^(-1) * Q * T_strain
        Q_bar = np.linalg.inv(T) @ self.Q @ T_strain
        
        return Q_bar
    
    def get_effective_properties(self, theta_deg: float) -> Dict[str, float]:
        """
        Berechne effektive Materialeigenschaften für transformiertes Koordinatensystem
        
        Args:
            theta_deg: Wickelwinkel in Grad
            
        Returns:
            Dict mit E_x, E_y, G_xy, nu_xy
        """
        Q_bar = self.get_Q_bar(theta_deg)
        
        # Aus Q̄-Matrix können wir effektive Eigenschaften extrahieren
        E_x = 1 / (self.S[0, 0] * np.cos(np.radians(theta_deg))**4 + 
                    2 * self.S[0, 1] * np.cos(np.radians(theta_deg))**2 * 
                    np.sin(np.radians(theta_deg))**2 + 
                    self.S[1, 1] * np.sin(np.radians(theta_deg))**4 + 
                    (4 * self.S[2, 2] - 2 * self.S[0, 1]) * 
                    np.cos(np.radians(theta_deg))**2 * np.sin(np.radians(theta_deg))**2)
        
        E_y = 1 / (self.S[0, 0] * np.sin(np.radians(theta_deg))**4 + 
                    2 * self.S[0, 1] * np.cos(np.radians(theta_deg))**2 * 
                    np.sin(np.radians(theta_deg))**2 + 
                    self.S[1, 1] * np.cos(np.radians(theta_deg))**4 + 
                    (4 * self.S[2, 2] - 2 * self.S[0, 1]) * 
                    np.cos(np.radians(theta_deg))**2 * np.sin(np.radians(theta_deg))**2)
        
        G_xy = 1 / (4 * (2 * self.S[0, 0] + 2 * self.S[1, 1] - 4 * self.S[0, 1] + 
                    self.S[2, 2]) * np.cos(np.radians(theta_deg))**2 * 
                    np.sin(np.radians(theta_deg))**2 + 
                    self.S[2, 2] * (np.cos(np.radians(theta_deg))**2 - 
                    np.sin(np.radians(theta_deg))**2)**2)
        
        nu_xy = -(Q_bar[0, 1] / Q_bar[0, 0])
        
        return {
            "E_x": max(E_x, 0.1),  # Mindestens 0.1 GPa
            "E_y": max(E_y, 0.1),
            "G_xy": max(G_xy, 0.1),
            "nu_xy": nu_xy
        }
    
    def get_strength_properties(self) -> Dict[str, float]:
        """
        Gebe Festigkeitseigenschaften des Materials zurück
        (aus Material-Datenbanken, hier Beispielwerte für Carbon/Epoxy)
        
        Returns:
            Dict mit Zug/Druck/Scherfestigkeiten
        """
        # Typische Werte für Carbon-Epoxy (AS4/3501-6)
        return {
            "F_1t": 2250,  # Zug-Festigkeit Faserrichtung in MPa
            "F_1c": 1500,  # Druck-Festigkeit Faserrichtung
            "F_2t": 50,    # Zug-Festigkeit Querrichtung
            "F_2c": 250,   # Druck-Festigkeit Querrichtung
            "F_12s": 100   # Scherfestigkeit
        }


class LaminaDatabase:
    """Vordefinierte Materialdatenbank für gängige Faserverbundstoffe"""
    
    MATERIALS = {
        "M40J": {
            "name": "Torayca M40J 12K / 3900-2B",
            "E1": 231,      # GPa
            "E2": 15.2,     # GPa
            "nu12": 0.20,
            "G12": 7.2,     # GPa
            "density": 1.60 # g/cm³
        },
        "IM7": {
            "name": "Hexcel IM7 / 8552",
            "E1": 171,
            "E2": 10.3,
            "nu12": 0.32,
            "G12": 7.2,
            "density": 1.58
        },
        "MR70": {
            "name": "Mitsubishi MR70 12K",
            "E1": 230,
            "E2": 14.8,
            "nu12": 0.21,
            "G12": 7.0,
            "density": 1.61
        },
        "T700S": {
            "name": "Toray T700S / 2592",
            "E1": 230,
            "E2": 13.4,
            "nu12": 0.20,
            "G12": 6.4,
            "density": 1.59
        }
    }
    
    @classmethod
    def get_lamina(cls, material_name: str, thickness_mm: float = 0.125) -> LaminaProperties:
        """
        Erstelle Lamina-Objekt aus Materialdatenbank
        
        Args:
            material_name: Name des Materials (z.B. "M40J")
            thickness_mm: Schichtdicke in mm
            
        Returns:
            LaminaProperties-Objekt
        """
        if material_name not in cls.MATERIALS:
            raise ValueError(f"Material '{material_name}' nicht in Datenbank. "
                           f"Verfügbar: {list(cls.MATERIALS.keys())}")
        
        mat = cls.MATERIALS[material_name]
        return LaminaProperties(
            E1=mat["E1"],
            E2=mat["E2"],
            nu12=mat["nu12"],
            G12=mat["G12"],
            t=thickness_mm
        )
