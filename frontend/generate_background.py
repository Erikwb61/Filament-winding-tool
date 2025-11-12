"""
Generiert ein Carbon-Fiber Hintergrund-Bild
"""

from PIL import Image, ImageDraw, ImageFilter
import random

# Bildgröße
width, height = 1920, 1440

# Basis-Bild (dunkles Grau-Schwarz)
img = Image.new('RGB', (width, height), color=(20, 20, 20))

# Faser-Muster hinzufügen
draw = ImageDraw.Draw(img, 'RGBA')

# Horizontale und vertikale "Faser"-Linien
for i in range(0, width, 50):
    alpha = random.randint(15, 45)
    draw.line([(i, 0), (i + random.randint(-200, 200), height)], fill=(100, 100, 100, alpha), width=random.randint(1, 2))

for i in range(0, height, 50):
    alpha = random.randint(15, 45)
    draw.line([(0, i), (width, i + random.randint(-200, 200))], fill=(100, 100, 100, alpha), width=random.randint(1, 2))

# Zufällige dunkle und helle Punkte für Tiefenwirkung
for _ in range(3000):
    x = random.randint(0, width)
    y = random.randint(0, height)
    size = random.randint(1, 4)
    alpha = random.randint(8, 40)
    color = random.choice([
        (60, 60, 60, alpha),    # Dunkelgrau
        (100, 100, 100, alpha),  # Hellgrau
        (40, 40, 40, alpha)      # Sehr dunkel
    ])
    draw.ellipse(
        [(x - size, y - size), (x + size, y + size)],
        fill=color
    )

# Filter anwenden für Glätte und Realismus
img = img.filter(ImageFilter.GaussianBlur(radius=1))

# Speichern
img.save('c:\\fw_tool\\carbon-bg.png')
print("✅ Carbon-Fiber Hintergrund gespeichert: c:\\fw_tool\\carbon-bg.png")
