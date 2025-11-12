"""
Laminate Properties Module
Berechnet die Steifigkeitsmatrizen (A, B, D) für einen kompletten Lamellen-Stack
basierend auf individuellen Lamina-Eigenschaften und deren Anordnung.

Classical Laminate Theory (CLT) - Teil 2
"""

import numpy as np
from typing import List, Dict, Tuple
from .lamina_properties import LaminaProperties, LaminaDatabase


class LaminateProperties:
    """Berechnet ABD-Matrizen und effektive Lamellen-Eigenschaften"""
    
    def __init__(self, lamina_list: List[Tuple[str, float, float]], 
                 ply_thickness_mm: float = 0.125):
        """
        Initialisiere Lamellen-Laminate aus einer Liste von Lagen
        
        Args:
            lamina_list: Liste von (Material, Winkel_deg, Anzahl_Lagen)
                        z.B. [("M40J", 0, 2), ("M40J", 45, 2), ("M40J", -45, 2), ("M40J", 90, 2)]
            ply_thickness_mm: Dicke pro Ply in mm
        """
        self.ply_thickness_mm = ply_thickness_mm
        self.lamina_list = lamina_list
        self.plies = []  # Liste aller Plies mit ihre z-Koordinaten
        self.build_ply_sequence()
        
        # Berechne ABD-Matrizen
        self.A, self.B, self.D = self._calculate_ABD()
        
        # Berechne effektive Eigenschaften
        self.effective_props = self._calculate_effective_properties()
    
    def build_ply_sequence(self):
        """Baue die komplette Ply-Sequenz aus der Eingabeliste"""
        self.plies = []
        z_coord = -sum([n * self.ply_thickness_mm for _, _, n in self.lamina_list]) / 2000  # m
        
        for material, angle_deg, num_plies in self.lamina_list:
            for _ in range(int(num_plies)):
                lamina = LaminaDatabase.get_lamina(material, self.ply_thickness_mm)
                self.plies.append({
                    "material": material,
                    "angle": angle_deg,
                    "lamina": lamina,
                    "z_mid": z_coord + self.ply_thickness_mm / 2000  # m
                })
                z_coord += self.ply_thickness_mm / 1000  # m
    
    def _calculate_ABD(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Berechne die ABD-Steifigkeitsmatrizen
        
        A: Membran-Steifigkeitsmatrix (in-plane)
        B: Kopplungs-Steifigkeitsmatrix
        D: Biege-Steifigkeitsmatrix
        
        Returns:
            (A_matrix, B_matrix, D_matrix) je 3x3 in N/m bzw. N
        """
        A = np.zeros((3, 3))
        B = np.zeros((3, 3))
        D = np.zeros((3, 3))
        
        # Iteriere über alle Plies
        for i, ply in enumerate(self.plies):
            Q_bar = ply["lamina"].get_Q_bar(ply["angle"])
            t_ply = self.ply_thickness_mm / 1000  # Konvertiere zu m
            
            # z-Koordinate (m) mit Bezug zur Mittelebene
            if i == 0:
                z_bottom = -sum([p["lamina"].t for p in self.plies]) / 2
                z_top = z_bottom + ply["lamina"].t
            else:
                z_bottom = self.plies[i-1]["z_mid"] + ply["lamina"].t / 2
                z_top = z_bottom + ply["lamina"].t
            
            z_mid = (z_bottom + z_top) / 2
            
            # A-Matrix: Membran-Steifigkeit
            A += Q_bar * t_ply
            
            # B-Matrix: Kopplungs-Term
            B += Q_bar * z_mid * t_ply
            
            # D-Matrix: Biege-Steifigkeit
            D += Q_bar * (z_mid**2 + t_ply**2 / 12) * t_ply
        
        return A, B, D
    
    def get_ABD_matrix(self) -> np.ndarray:
        """
        Gebe die komplette 6x6 ABD-Matrix zurück
        
        Returns:
            6x6 Gesamt-Steifigkeitsmatrix [A B; B D]
        """
        ABD = np.zeros((6, 6))
        ABD[0:3, 0:3] = self.A
        ABD[0:3, 3:6] = self.B
        ABD[3:6, 0:3] = self.B
        ABD[3:6, 3:6] = self.D
        
        return ABD
    
    def _calculate_effective_properties(self) -> Dict[str, float]:
        """
        Berechne effektive Laminat-Eigenschaften aus der ABD-Matrix
        
        Returns:
            Dict mit E_x, E_y, G_xy, nu_xy für das komplette Laminat
        """
        # Aus Membran-Steifigkeit A berechnen
        # E_x = A_11 * t_total / t_ref
        
        total_thickness = len(self.plies) * self.ply_thickness_mm / 1000  # m
        
        # Aus A-Matrix
        a11_inv = np.linalg.inv(self.A[0:2, 0:2])
        
        E_x = 1 / (total_thickness * a11_inv[0, 0])
        E_y = 1 / (total_thickness * a11_inv[1, 1])
        G_xy = 1 / (total_thickness * self.A[2, 2]**(-1))
        nu_xy = -a11_inv[0, 1] / a11_inv[0, 0]
        
        return {
            "E_x": E_x / 1e9,  # Konvertiere zu GPa
            "E_y": E_y / 1e9,
            "G_xy": G_xy / 1e9,
            "nu_xy": nu_xy,
            "thickness_mm": total_thickness * 1000,
            "num_plies": len(self.plies)
        }
    
    def get_properties(self) -> Dict[str, float]:
        """Gebe effektive Laminat-Eigenschaften zurück"""
        return self.effective_props
    
    def get_ply_stresses(self, N_x: float, N_y: float, N_xy: float) -> List[Dict]:
        """
        Berechne Spannungen in jedem Ply unter gegebenen Membran-Kräften
        
        Args:
            N_x, N_y, N_xy: Membran-Kräfte in N/m
            
        Returns:
            Liste von Ply-Spannungen (σ_1, σ_2, τ_12 in MPa)
        """
        # Berechne Dehnungen aus N = A * ε
        epsilon = np.linalg.solve(self.A[:3, :3], np.array([N_x, N_y, N_xy]))
        
        ply_stresses = []
        for ply in self.plies:
            # In Faserkoordinaten transformieren
            sigma_xy = ply["lamina"].get_Q_bar(ply["angle"]) @ epsilon
            
            # In Material-Koordinaten transformieren
            theta = np.radians(ply["angle"])
            c, s = np.cos(theta), np.sin(theta)
            
            sigma_1 = c**2 * sigma_xy[0] + s**2 * sigma_xy[1] + 2*c*s*sigma_xy[2]
            sigma_2 = s**2 * sigma_xy[0] + c**2 * sigma_xy[1] - 2*c*s*sigma_xy[2]
            tau_12 = -c*s * sigma_xy[0] + c*s * sigma_xy[1] + (c**2 - s**2) * sigma_xy[2]
            
            ply_stresses.append({
                "material": ply["material"],
                "angle": ply["angle"],
                "sigma_1": sigma_1 / 1e6,  # Konvertiere zu MPa
                "sigma_2": sigma_2 / 1e6,
                "tau_12": tau_12 / 1e6
            })
        
        return ply_stresses
    
    def get_sequence_string(self) -> str:
        """Gebe die Lamellen-Sequenz als String zurück (z.B. [0/±45/90]s)"""
        sequences = {}
        for material, angle, num_plies in self.lamina_list:
            key = f"{angle}°"
            sequences[key] = int(num_plies)
        
        seq_str = "[" + "/".join([f"{k}" for k in sequences.keys()]) + "]"
        return seq_str


class SymmetricLaminate(LaminateProperties):
    """Spezialfall: Symmetrische Laminaten (B-Matrix = 0)"""
    
    def __init__(self, lamina_list: List[Tuple[str, float, float]], 
                 ply_thickness_mm: float = 0.125):
        """
        Erstelle symmetrisches Laminat (das ist die Standardannahme für Wickelstrukturen)
        
        Args:
            lamina_list: Nur die obere Hälfte angeben, wird automatisch gespiegelt
            ply_thickness_mm: Dicke pro Ply in mm
        """
        # Verdopple die Sequenz für Symmetrie
        symmetric_list = lamina_list + [(mat, -ang, n) for mat, ang, n in reversed(lamina_list)]
        super().__init__(symmetric_list, ply_thickness_mm)
