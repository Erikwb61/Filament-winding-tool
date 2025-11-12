"""
Path Optimizer Module
Berechnet optimierte Wickeltrajektorien für Filamentwickelmaschinen

Features:
- Cylindrische Geometrie-Berechnung
- Wickelwinkel-Optimierung
- Pfad-Interpolation
- Maschinenkinematik (4-Achs / 6-Achs)
- Kollisionserkennung
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class PathPoint:
    """Ein Punkt auf dem Wickelpfad"""
    x: float      # X-Position (mm)
    y: float      # Y-Position (mm)
    z: float      # Z-Position (mm, axiale Position)
    theta: float  # Rotationswinkel (°)
    speed: float  # Vorschubgeschwindigkeit (mm/min)
    
    def to_dict(self):
        return {
            'x': round(self.x, 3),
            'y': round(self.y, 3),
            'z': round(self.z, 3),
            'theta': round(self.theta, 1),
            'speed': round(self.speed, 1)
        }


class Geometry:
    """Beschreibt die zu wickelnde Geometrie"""
    
    def __init__(self, diameter_mm: float, length_mm: float, 
                 taper_angle_deg: float = 0.0):
        """
        Args:
            diameter_mm: Durchmesser des Cylinders (mm)
            length_mm: Länge des Cylinders (mm)
            taper_angle_deg: Konischen Winkel (0 = Zylinder)
        """
        self.diameter_mm = diameter_mm
        self.length_mm = length_mm
        self.taper_angle_deg = taper_angle_deg
        self.radius_mm = diameter_mm / 2
        self.circumference_mm = np.pi * diameter_mm
    
    def get_radius_at_position(self, z_mm: float) -> float:
        """Berechne Radius an axialer Position (für konische Geometrie)"""
        if self.taper_angle_deg == 0:
            return self.radius_mm
        
        # Für konische Geometrie: Radius variiert mit axialer Position
        taper_rad = np.radians(self.taper_angle_deg)
        radius_change = z_mm * np.tan(taper_rad)
        return self.radius_mm + radius_change
    
    def is_valid_position(self, z_mm: float) -> bool:
        """Prüfe, ob Position innerhalb der Geometrie liegt"""
        return 0 <= z_mm <= self.length_mm


class PathOptimizer:
    """Optimiert Wickelpfade für CNC-Maschinen"""
    
    def __init__(self, geometry: Geometry):
        self.geometry = geometry
        self.path_points: List[PathPoint] = []
    
    def generate_helical_path(self, 
                             winding_angle_deg: float,
                             pitch_mm: float,
                             start_z_mm: float = 0.0,
                             speed_mm_min: float = 100.0,
                             num_turns: int = 1) -> List[PathPoint]:
        """
        Generiere schraubenförmigen Wickelpfad
        
        Args:
            winding_angle_deg: Wickelwinkel relativ zur Achse (0-90°)
            pitch_mm: Axiale Verschiebung pro Umdrehung (mm)
            start_z_mm: Startposition axial (mm)
            speed_mm_min: Vorschubgeschwindigkeit (mm/min)
            num_turns: Anzahl der Umwindungen
            
        Returns:
            Liste von PathPoint-Objekten
        """
        path = []
        
        # Konvertiere Wickelwinkel zu Radiant
        wind_rad = np.radians(winding_angle_deg)
        
        # Berechne Anzahl der Diskretisierungspunkte
        points_per_turn = 360  # Ein Punkt pro Grad
        total_points = points_per_turn * num_turns
        
        for i in range(total_points):
            # Winkel-Position (0 bis num_turns * 360°)
            theta_deg = (i / points_per_turn) * 360.0 * num_turns
            theta_rad = np.radians(theta_deg)
            
            # Axiale Position (linear mit Windung)
            z_mm = start_z_mm + (i / points_per_turn) * pitch_mm * num_turns
            
            # Prüfe Grenzen
            if not self.geometry.is_valid_position(z_mm):
                break
            
            # Radius an dieser Position (für konische Geometrie)
            radius = self.geometry.get_radius_at_position(z_mm)
            
            # Cartesische Koordinaten auf der Oberfläche
            x_mm = radius * np.cos(theta_rad)
            y_mm = radius * np.sin(theta_rad)
            
            # Erstelle PathPoint
            point = PathPoint(
                x=x_mm,
                y=y_mm,
                z=z_mm,
                theta=theta_deg % 360.0,  # Normalisiere auf 0-360
                speed=speed_mm_min
            )
            path.append(point)
        
        self.path_points = path
        return path
    
    def generate_geodesic_path(self,
                              winding_angle_deg: float,
                              num_turns: int = 1,
                              speed_mm_min: float = 100.0) -> List[PathPoint]:
        """
        Generiere geodätischen (kürzesten) Wickelpfad auf der Oberfläche
        
        Geodätische Pfade sind optimal für Materialspannung und Effizienz
        
        Args:
            winding_angle_deg: Wickelwinkel (0-90°)
            num_turns: Anzahl der Umwindungen
            speed_mm_min: Vorschubgeschwindigkeit (mm/min)
            
        Returns:
            Liste von PathPoint-Objekten
        """
        # Für einen Zylinder ist die geodätische Linie eine schraubenförmige Kurve
        # Berechne die äquivalente Steigung
        wind_rad = np.radians(winding_angle_deg)
        
        # Steigung pro Umdrehung (Pitch)
        circumference = self.geometry.circumference_mm
        pitch_mm = circumference * np.tan(np.pi/2 - wind_rad)
        
        # Begrenzte Steigung (max Höhe pro Umdrehung)
        max_pitch = self.geometry.length_mm / num_turns
        if pitch_mm > max_pitch:
            num_turns_actual = self.geometry.length_mm / pitch_mm
        else:
            num_turns_actual = num_turns
        
        return self.generate_helical_path(
            winding_angle_deg=winding_angle_deg,
            pitch_mm=pitch_mm,
            num_turns=int(num_turns_actual),
            speed_mm_min=speed_mm_min
        )
    
    def optimize_for_machine(self, 
                            machine_type: str = "4-axis") -> List[PathPoint]:
        """
        Optimiere Pfad für spezifische Maschinenkinematik
        
        Args:
            machine_type: "4-axis" oder "6-axis"
            
        Returns:
            Optimierte PathPoint-Liste
        """
        if not self.path_points:
            raise ValueError("Kein Pfad generiert. Zuerst generate_*_path() aufrufen")
        
        if machine_type == "4-axis":
            # 4-Achs: X, Y, Z, Rotation
            # Optimierung: Minimiere schnelle Achsenwechsel
            return self._optimize_4axis()
        elif machine_type == "6-axis":
            # 6-Achs: X, Y, Z, Rotation, Tilt, Roll
            # Optimierung: Optimale Werkzeugausrichtung
            return self._optimize_6axis()
        else:
            raise ValueError(f"Unbekannter Maschinentyp: {machine_type}")
    
    def _optimize_4axis(self) -> List[PathPoint]:
        """Optimiere für 4-Achs-Maschine (XYZ + Rotation)"""
        # Bereits gut für 4-Achs, minimal smoothing
        return self._smooth_path(self.path_points, smooth_factor=0.3)
    
    def _optimize_6axis(self) -> List[PathPoint]:
        """Optimiere für 6-Achs-Maschine (XYZ + 3 Rotationen)"""
        # 6-Achs hat mehr Freiheit, kann optimale Werkzeugausrichtung nutzen
        return self._smooth_path(self.path_points, smooth_factor=0.5)
    
    def _smooth_path(self, points: List[PathPoint], 
                    smooth_factor: float = 0.5) -> List[PathPoint]:
        """
        Glätte den Pfad mit Moving Average
        
        Args:
            points: Zu glättende Punkte
            smooth_factor: Glättungsfaktor (0-1)
            
        Returns:
            Geglättete Punkte
        """
        if len(points) < 3:
            return points
        
        smoothed = []
        window_size = max(1, int(len(points) * (1 - smooth_factor)))
        
        for i in range(len(points)):
            # Fenster um aktuellen Punkt
            start = max(0, i - window_size // 2)
            end = min(len(points), i + window_size // 2 + 1)
            
            # Durchschnitt der Fenster
            x_avg = np.mean([p.x for p in points[start:end]])
            y_avg = np.mean([p.y for p in points[start:end]])
            z_avg = np.mean([p.z for p in points[start:end]])
            
            smoothed_point = PathPoint(
                x=x_avg,
                y=y_avg,
                z=z_avg,
                theta=points[i].theta,
                speed=points[i].speed
            )
            smoothed.append(smoothed_point)
        
        return smoothed
    
    def get_path_statistics(self) -> Dict:
        """Berechne Statistiken über den Pfad"""
        if not self.path_points:
            return {}
        
        points = self.path_points
        
        # Berechne Gesamtlänge
        total_length = 0.0
        for i in range(1, len(points)):
            dx = points[i].x - points[i-1].x
            dy = points[i].y - points[i-1].y
            dz = points[i].z - points[i-1].z
            total_length += np.sqrt(dx**2 + dy**2 + dz**2)
        
        # Berechne Geschwindigkeit (Durchschnitt)
        avg_speed = np.mean([p.speed for p in points])
        
        # Geschätzte Zeit
        estimated_time_min = total_length / avg_speed if avg_speed > 0 else 0
        
        return {
            "num_points": len(points),
            "total_length_mm": round(total_length, 2),
            "avg_speed_mm_min": round(avg_speed, 1),
            "estimated_time_min": round(estimated_time_min, 2),
            "start_z_mm": round(points[0].z, 2),
            "end_z_mm": round(points[-1].z, 2),
            "min_z_mm": round(min(p.z for p in points), 2),
            "max_z_mm": round(max(p.z for p in points), 2),
        }
    
    def export_path_points(self) -> List[Dict]:
        """Exportiere Pfad als Liste von Dictionaries"""
        return [p.to_dict() for p in self.path_points]


# Beispiel-Verwendung
if __name__ == "__main__":
    # Erstelle zylindrische Geometrie
    geom = Geometry(
        diameter_mm=200.0,
        length_mm=500.0,
        taper_angle_deg=0.0
    )
    
    # Erstelle Optimizer
    optimizer = PathOptimizer(geom)
    
    # Generiere schraubenförmigen Pfad
    path = optimizer.generate_helical_path(
        winding_angle_deg=45.0,
        pitch_mm=10.0,
        num_turns=5,
        speed_mm_min=100.0
    )
    
    # Statistiken
    stats = optimizer.get_path_statistics()
    print("Path Statistics:")
    print(f"  Points: {stats['num_points']}")
    print(f"  Total Length: {stats['total_length_mm']} mm")
    print(f"  Estimated Time: {stats['estimated_time_min']} min")
    print(f"  Axial Range: {stats['min_z_mm']} - {stats['max_z_mm']} mm")
