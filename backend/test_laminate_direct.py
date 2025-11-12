from fw_core.laminate_properties import LaminateProperties, SymmetricLaminate

# Test: Create a simple laminate
lamina_list = [("M40J", 0, 2), ("M40J", 45, 2)]
print("Lamina list:", lamina_list)

lam = LaminateProperties(lamina_list, ply_thickness_mm=0.125)
print(f"\nLaminat: {len(lam.plies)} plies")

props = lam.get_properties()
print(f"\nProperties:")
print(f"  E_x: {props['E_x']} GPa")
print(f"  E_y: {props['E_y']} GPa")
print(f"  G_xy: {props['G_xy']} GPa")
print(f"  nu_xy: {props['nu_xy']}")
print(f"  thickness_mm: {props['thickness_mm']}")
print(f"  num_plies: {props['num_plies']}")

# Check A matrix
abd = lam.get_ABD_matrix()
print(f"\nA-Matrix shape: {lam.A.shape}")
print(f"A-Matrix:\n{lam.A}")

print(f"\nB-Matrix:\n{lam.B}")
print(f"\nD-Matrix shape: {lam.D.shape}")
print(f"D-Matrix:\n{lam.D}")
