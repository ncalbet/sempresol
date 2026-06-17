"""
generate_image.py
Genera imatges quadrades 1080x1080 per a Instagram amb l'estètica de sempresol.cat
6 plantilles que roten determinísticament per data.
"""

import hashlib
import math
import os
from PIL import Image, ImageDraw, ImageFont


# ── Colors ───────────────────────────────────────────────────────────────────
COLOR_GOLD   = (255, 215,   0)   # #FFD700 — groc daurat
COLOR_CREAM  = (255, 248, 220)   # #FFF8DC — crema suau
COLOR_ORANGE = (255, 184,   0)   # #FFB800 — taronja sol / separadors
COLOR_DARK   = ( 51,  51,  51)   # #333333 — text principal

# Paletes plantilles noves
COLOR_CORAL   = (228,  95,  30)   # terracota mediterrani (Llevant, dalt)
COLOR_WARMGLD = (255, 195,  80)   # or càlid (Llevant, baix)
COLOR_CREAM_W = (255, 252, 230)   # crema quasi blanc (sol i text Llevant)
COLOR_NIGHT1  = ( 38,  18,   4)   # ambre fosc profund (Nit, dalt)
COLOR_NIGHT2  = ( 12,   5,   1)   # quasi negre càlid (Nit, baix)
COLOR_IVORY   = (255, 245, 215)   # ivori càlid (text Nit)

W = H = 1080
MARGIN = 75


# ── Fons ─────────────────────────────────────────────────────────────────────

def _bg_vertical(top_col, bottom_col):
    img  = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        r = int(top_col[0] + (bottom_col[0] - top_col[0]) * t)
        g = int(top_col[1] + (bottom_col[1] - top_col[1]) * t)
        b = int(top_col[2] + (bottom_col[2] - top_col[2]) * t)
        draw.line([(0, y), (W - 1, y)], fill=(r, g, b))
    return img


def _bg_horizontal(left_col, right_col):
    img  = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    for x in range(W):
        t = x / W
        r = int(left_col[0] + (right_col[0] - left_col[0]) * t)
        g = int(left_col[1] + (right_col[1] - left_col[1]) * t)
        b = int(left_col[2] + (right_col[2] - left_col[2]) * t)
        draw.line([(x, 0), (x, H - 1)], fill=(r, g, b))
    return img


def _bg_radial(center_col, edge_col, steps=120):
    """Gradient radial amb el·lipses concèntriques."""
    img  = Image.new("RGB", (W, H), color=edge_col)
    draw = ImageDraw.Draw(img)
    cx, cy = W // 2, H // 2
    max_r  = int(math.sqrt(cx**2 + cy**2)) + 1
    for i in range(steps, -1, -1):
        t = i / steps
        col = (
            int(center_col[0] * t + edge_col[0] * (1 - t)),
            int(center_col[1] * t + edge_col[1] * (1 - t)),
            int(center_col[2] * t + edge_col[2] * (1 - t)),
        )
        r = int(max_r * t)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)
    return img


# ── Sol ──────────────────────────────────────────────────────────────────────

def draw_sun(draw, cx, cy, radius, color=COLOR_ORANGE):
    """Sol geomètric: cercle + 12 raigs."""
    draw.ellipse(
        [(cx - radius, cy - radius), (cx + radius, cy + radius)],
        fill=color,
    )
    inner_r = radius * 1.25
    outer_r = radius * 1.85
    ray_w   = max(6, int(radius * 0.13))
    for i in range(12):
        angle = math.radians(30 * i - 90)
        x1 = cx + inner_r * math.cos(angle)
        y1 = cy + inner_r * math.sin(angle)
        x2 = cx + outer_r * math.cos(angle)
        y2 = cy + outer_r * math.sin(angle)
        draw.line([(x1, y1), (x2, y2)], fill=color, width=ray_w)


# ── Tipografia ───────────────────────────────────────────────────────────────

def load_font(bold, size):
    paths = (
        [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "C:\\Windows\\Fonts\\arialbd.ttf",
            "C:\\Windows\\Fonts\\segoeuib.ttf",
        ] if bold else [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "C:\\Windows\\Fonts\\arial.ttf",
            "C:\\Windows\\Fonts\\segoeui.ttf",
        ]
    )
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _text_w(draw, text, font):
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[2] - bb[0]


def _text_h(draw, text, font):
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[3] - bb[1]


def centered_text(draw, y, text, font, color, width=W):
    x = (width - _text_w(draw, text, font)) // 2
    draw.text((x, y), text, fill=color, font=font)
    return _text_h(draw, text, font)


def spaced_centered_text(draw, y, text, font, color, spacing=14, width=W):
    """Text centrat amb espaiat extra entre caràcters (efecte tipogràfic elegant)."""
    chars = list(text)
    widths = [_text_w(draw, c, font) for c in chars]
    total_w = sum(widths) + spacing * (len(chars) - 1)
    x = (width - total_w) // 2
    for c, cw in zip(chars, widths):
        draw.text((x, y), c, fill=color, font=font)
        x += cw + spacing
    return _text_h(draw, "A", font)


def wrap_text(draw, text, font, max_w):
    words, lines, cur = text.split(), [], []
    for word in words:
        cur.append(word)
        if _text_w(draw, " ".join(cur), font) > max_w and len(cur) > 1:
            cur.pop()
            lines.append(" ".join(cur))
            cur = [word]
    if cur:
        lines.append(" ".join(cur))
    return lines


def fit_text_to_area(draw, text, max_w, max_h, bold, size_max=52, size_min=26):
    for size in range(size_max, size_min - 1, -2):
        font  = load_font(bold=bold, size=size)
        lines = wrap_text(draw, text, font, max_w)
        lh    = _text_h(draw, "Ag", font) + 10
        if lh * len(lines) <= max_h:
            return font, lines, lh
    font  = load_font(bold=bold, size=size_min)
    lines = wrap_text(draw, text, font, max_w)
    lh    = _text_h(draw, "Ag", font) + 10
    return font, lines, lh


# ── Layout de contingut (compartit per totes les plantilles) ─────────────────

# Alçada fixa del bloc "Sempre Sol + separadors + poble":
#   "Sempre Sol" (~82px) + sep(4+18) + poble(~108) + sep(4+28+GAP)
_HEADER_H = 244
_GAP      = 20
_URL_H    = 100    # zona peu: separador + sempresol.cat


def _render_content(draw, town, message_text, zone_top, zone_bottom,
                    text_color=COLOR_DARK, sep_color=COLOR_ORANGE,
                    margin=MARGIN, town_spaced=False):
    """
    Renderitza dins [zone_top, zone_bottom]:
      "Sempre Sol" → sep → POBLE → sep → frase → sep → sempresol.cat
    """
    sep_bottom_y = zone_bottom - _URL_H

    msg_area_h = sep_bottom_y - (zone_top + _HEADER_H + _GAP) - _GAP
    msg_area_h = max(msg_area_h, 60)

    font_msg, lines, lh = fit_text_to_area(
        draw, message_text,
        max_w=W - 2 * margin, max_h=msg_area_h,
        bold=False, size_max=52, size_min=26,
    )
    block_h = _HEADER_H + _GAP + lh * len(lines)

    zone_h = sep_bottom_y - zone_top - _GAP
    y = zone_top + max(0, (zone_h - block_h) // 2)

    f_title = load_font(bold=True, size=68)
    f_url   = load_font(bold=True, size=42)

    # "Sempre Sol"
    centered_text(draw, y, "Sempre Sol", f_title, text_color)
    y += 82

    # Separador
    draw.line([(margin, y), (W - margin, y)], fill=sep_color, width=4)
    y += 18

    # Nom del poble
    town_upper = town.upper()
    if town_spaced:
        # Tipografia amb espaiat: redueix mida fins que càpiga
        for size in [80, 70, 60, 50, 42]:
            f_town = load_font(bold=True, size=size)
            chars  = list(town_upper)
            total_w = sum(_text_w(draw, c, f_town) for c in chars) + 14 * (len(chars) - 1)
            if total_w <= W - 2 * margin:
                break
        spaced_centered_text(draw, y, town_upper, f_town, text_color, spacing=14)
    else:
        f_town = load_font(bold=True, size=96)
        if _text_w(draw, town_upper, f_town) > W - 2 * margin:
            scale  = (W - 2 * margin) / _text_w(draw, town_upper, f_town)
            f_town = load_font(bold=True, size=max(40, int(96 * scale)))
        centered_text(draw, y, town_upper, f_town, text_color)
    y += 108

    # Separador
    draw.line([(margin, y), (W - margin, y)], fill=sep_color, width=4)
    y += 28 + _GAP

    # Frase
    for line in lines:
        centered_text(draw, y, line, font_msg, text_color)
        y += lh

    # Separador peu
    draw.line([(margin, sep_bottom_y), (W - margin, sep_bottom_y)], fill=sep_color, width=3)

    # URL
    url_y = sep_bottom_y + (_URL_H - 42) // 2
    centered_text(draw, url_y, "sempresol.cat", f_url, text_color)


# ── Plantilles ───────────────────────────────────────────────────────────────

def _t0_classica(town, msg, path):
    """Gradient vertical or→crema, sol centrat a dalt."""
    img  = _bg_vertical(COLOR_GOLD, COLOR_CREAM)
    draw = ImageDraw.Draw(img)
    cy   = 140
    draw_sun(draw, W // 2, cy, 75)
    _render_content(draw, town, msg, zone_top=cy + 75 + 30, zone_bottom=H)
    img.save(path, "PNG")


def _t1_capgirada(town, msg, path):
    """Gradient vertical crema→or, sol centrat a baix."""
    img  = _bg_vertical(COLOR_CREAM, COLOR_GOLD)
    draw = ImageDraw.Draw(img)
    cy, r = H - 140, 75
    sun_top = cy - int(r * 1.85)  # extrem superior dels raigs
    draw_sun(draw, W // 2, cy, r)
    _render_content(draw, town, msg, zone_top=50, zone_bottom=sun_top - 20)
    img.save(path, "PNG")


def _t2_lateral(town, msg, path):
    """Gradient horitzontal or(esq)→crema(dreta), sol a la cantonada superior dreta."""
    img  = _bg_horizontal(COLOR_GOLD, COLOR_CREAM)
    draw = ImageDraw.Draw(img)
    draw_sun(draw, W - 150, 150, 65)
    _render_content(draw, town, msg, zone_top=50, zone_bottom=H)
    img.save(path, "PNG")


def _t3_radial(town, msg, path):
    """Gradient radial or(centre)→crema(vores), sol centrat a dalt."""
    img  = _bg_radial(COLOR_GOLD, COLOR_CREAM)
    draw = ImageDraw.Draw(img)
    cy   = 140
    draw_sun(draw, W // 2, cy, 75)
    _render_content(draw, town, msg, zone_top=cy + 75 + 30, zone_bottom=H)
    img.save(path, "PNG")


def _t4_llevant(town, msg, path):
    """
    Paleta terracota→or viu. Sol gran blanc.
    Evoca l'alba mediterrània: viva, cromàticament diferent, para el scroll.
    """
    img  = _bg_vertical(COLOR_CORAL, COLOR_WARMGLD)
    draw = ImageDraw.Draw(img)
    cy, r = 155, 95
    # Halo suau darrere el sol (cercle difuminat)
    for offset, alpha in [(55, COLOR_CORAL), (35, (235, 110, 50)), (15, (245, 140, 60))]:
        draw.ellipse(
            [W//2 - (r + offset), cy - (r + offset),
             W//2 + (r + offset), cy + (r + offset)],
            fill=alpha,
        )
    draw_sun(draw, W // 2, cy, r, color=COLOR_CREAM_W)
    _render_content(
        draw, town, msg,
        zone_top=cy + r + 30, zone_bottom=H,
        text_color=COLOR_DARK, sep_color=COLOR_CREAM_W,
    )
    img.save(path, "PNG")


def _t5_nit(town, msg, path):
    """
    Fons ambre fosc profund. Text ivori. Accents daurats.
    Marc fi, nom amb espaiat de lletres.
    Sensació premium/editorial: màxim contrast a Instagram.
    """
    img  = _bg_vertical(COLOR_NIGHT1, COLOR_NIGHT2)
    draw = ImageDraw.Draw(img)

    # Marc decoratiu fi en daurat
    bm = 22
    draw.rectangle([bm, bm, W - bm, H - bm], outline=COLOR_GOLD, width=2)
    # Punt daurat als quatre cantons del marc
    dot_r = 7
    for px, py in [(bm, bm), (W - bm, bm), (bm, H - bm), (W - bm, H - bm)]:
        draw.ellipse([px - dot_r, py - dot_r, px + dot_r, py + dot_r], fill=COLOR_GOLD)

    # Halo lluminós difuminat darrere el sol
    cx, cy_sun = W // 2, 155
    for gr, gcol in [(160, (65, 38, 10)), (120, (80, 48, 14)), (90, (95, 58, 18))]:
        draw.ellipse([cx - gr, cy_sun - gr, cx + gr, cy_sun + gr], fill=gcol)
    draw_sun(draw, cx, cy_sun, 75, color=COLOR_GOLD)

    _render_content(
        draw, town, msg,
        zone_top=cy_sun + 75 + 30, zone_bottom=H - bm,
        text_color=COLOR_IVORY, sep_color=COLOR_GOLD,
        margin=MARGIN + bm, town_spaced=True,
    )
    img.save(path, "PNG")


_TEMPLATES = [_t0_classica, _t1_capgirada, _t2_lateral, _t3_radial, _t4_llevant, _t5_nit]

# Pesos: Clàssica/Lateral/Radial surten més, Llevant/Nit normal, Capgirada molt poc.
# Distribució aprox: Clàssica 23% · Lateral 23% · Radial 23% · Llevant 15% · Nit 15% · Capgirada 8% (→ ~1 de cada 13)  (→ ~1 de cada 13)
_PICK_TABLE = [0, 0, 0, 2, 2, 2, 3, 3, 3, 4, 4, 5, 5, 1]


def _pick_template(output_path: str) -> int:
    """Selecció determinista i ponderada de plantilla per nom de fitxer."""
    name = os.path.basename(output_path)
    idx  = int(hashlib.sha256(name.encode()).hexdigest(), 16) % len(_PICK_TABLE)
    return _PICK_TABLE[idx]


# ── Funció pública ────────────────────────────────────────────────────────────

def create_post_image(town: str, full_message: str, output_path: str,
                      template_idx: int | None = None) -> str:
    """
    Crea una imatge Instagram 1080x1080.
    Si template_idx és None, es deriva determinísticament del nom del fitxer (0-3).
    """
    msg = full_message.replace("{lugar}", town)
    idx = template_idx if template_idx is not None else _pick_template(output_path)
    _TEMPLATES[idx % len(_TEMPLATES)](town, msg, output_path)
    return output_path


# ── Test local ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    msg = "A {lugar}, el sol està tan compromès amb el seu treball que ja ha demanat fer hores extres indefinides."
    base = "C:/Windows/Temp" if sys.platform == "win32" else "/tmp"
    for i, nom in enumerate(["classica", "capgirada", "lateral", "radial", "llevant", "nit"]):
        out = f"{base}/test_sempresol_{nom}.png"
        create_post_image("Cardedeu", msg, out, template_idx=i)
        print(f"Plantilla {i} ({nom}): {out}")
