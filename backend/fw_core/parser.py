import re
from typing import List
from .model import Layer, Material

ANGLE_RE = re.compile(r"(?P<sign>±|\+|-)?(?P<angle>\d+)")
MULT_RE  = re.compile(r"(?P<count>\d+)x")

def parse_sequence(seq: str, default_thickness: float, default_material: Material) -> List[Layer]:
    seq = seq.replace(" ", "")
    # Symmetrie mit "s"
    if seq.endswith("s"):
        core = seq[:-1]
        layers = _parse_block(core, default_thickness, default_material)
        mirrored = [
            Layer(angle=-l.angle, thickness=l.thickness, material=l.material)
            for l in reversed(layers)
        ]
        return layers + mirrored
    else:
        return _parse_block(seq, default_thickness, default_material)

def _parse_block(block: str, default_thickness: float, default_material: Material) -> List[Layer]:
    # äußere [] entfernen
    if block.startswith("[") and block.endswith("]"):
        block = block[1:-1]

    parts = _split_top_level(block, "/")
    layers: List[Layer] = []

    for part in parts:
        m = MULT_RE.match(part)  # z.B. 2x[...]
        if m:
            count = int(m.group("count"))
            rest = part[m.end():]
            sub_layers = _parse_block(rest, default_thickness, default_material)
            layers.extend(sub_layers * count)
        else:
            angles = _angles_from_token(part)
            for a in angles:
                layers.append(Layer(angle=a, thickness=default_thickness, material=default_material))

    return layers

def _split_top_level(s: str, sep: str) -> List[str]:
    parts = []
    current = []
    depth = 0
    for ch in s:
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
        if ch == sep and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
    if current:
        parts.append("".join(current))
    return parts

def _angles_from_token(token: str) -> List[float]:
    m = ANGLE_RE.fullmatch(token)
    if not m:
        raise ValueError(f"Ungültiger Winkel-Token: {token}")
    angle = float(m.group("angle"))
    sign = m.group("sign")
    if sign == "±":
        return [+angle, -angle]
    elif sign == "-":
        return [-angle]
    else:
        return [angle]
