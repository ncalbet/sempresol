"""
generate_image.py
Genera imatges quadrades 1080x1080 per a Instagram amb l'estètica de sempresol.cat
"""

import math
from PIL import Image, ImageDraw, ImageFont


# ── Colors ──────────────────────────────────────────────────────────────────
COLOR_GOLD        = (255, 215,   0)   # #FFD700 — groc daurat top
COLOR_CREAM       = (255, 248, 220)   # #FFF8DC — crema suau bottom
COLOR_ORANGE      = (255, 184,   0)   # #FFB800 — taronja sol / separadors
COLOR_DARK        = ( 51,  51,  51)   # #333333 — text principal
COLOR_GRAY        = (120, 120, 120)   # gris subtítols
COLOR_WHITE       = (255, 255, 255)


# ── Utilitats ────────────────────────────────────────────────────────────────

def gradient_background(width: int, height: int) -> Image.Image:
    """Gradient vertical de daurat a crema."""
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)
    r1, g1, b1 = COLOR_GOLD
    r2, g2, b2 = COLOR_CREAM
    for y in range(height):
        t = y / height
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        draw.line([(0, y), (width - 1, y)], fill=(r, g, b))
    return img


def draw_sun(draw: ImageDraw.Draw, cx: int, cy: int, radius: int):
    """Dibuixa un sol geomètric (cercle + 12 raigs)."""
    # Cercle interior
    draw.ellipse(
        [(cx - radius, cy - radius), (cx + radius, cy + radius)],
        fill=COLOR_ORANGE
    )
    # Raigs
    num_rays = 12
    inner_r  = radius * 1.25
    outer_r  = radius * 1.85
    ray_w    = max(6, int(radius * 0.13))
    for i in range(num_rays):
        angle = math.radians(360 / num_rays * i - 90)
        x1 = cx + inner_r * math.cos(angle)
        y1 = cy + inner_r * math.sin(angle)
        x2 = cx + outer_r * math.cos(angle)
        y2 = cy + outer_r * math.sin(angle)
        draw.line([(x1, y1), (x2, y2)], fill=COLOR_ORANGE, width=ray_w)


def load_font(bold: bool, size: int) -> ImageFont.FreeTypeFont:
    """Carrega DejaVu (disponible a Ubuntu/GitHub Actions)."""
    paths_bold    = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    paths_regular = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    paths = paths_bold if bold else paths_regular
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    # Fallback PIL default (sense mida)
    return ImageFont.load_default()


def centered_text(draw: ImageDraw.Draw, y: int, text: str,
                  font: ImageFont.FreeTypeFont, color, width: int):
    """Escriu text centrat horitzontalment."""
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    x = (width - w) // 2
    draw.text((x, y), text, fill=color, font=font)
    return bbox[3] - bbox[1]   # alçada de la línia


def wrap_text(draw: ImageDraw.Draw, text: str,
              font: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    """Parteix text en línies que caben dins max_w."""
    words, lines, cur = text.split(), [], []
    for word in words:
        cur.append(word)
        bb = draw.textbbox((0, 0), " ".join(cur), font=font)
        if bb[2] > max_w and len(cur) > 1:
            cur.pop()
            lines.append(" ".join(cur))
            cur = [word]
    if cur:
        lines.append(" ".join(cur))
    return lines


def fit_text_to_area(draw: ImageDraw.Draw, text: str, max_w: int,
                     max_h: int, bold: bool,
                     size_max: int = 52, size_min: int = 28) -> tuple:
    """
    Troba la mida de font més gran que fa cabre el text dins max_w × max_h.
    Retorna (font, lines, line_height).
    """
    for size in range(size_max, size_min - 1, -2):
        font  = load_font(bold=bold, size=size)
        lines = wrap_text(draw, text, font, max_w)
        bb    = draw.textbbox((0, 0), "Ag", font=font)
        lh    = bb[3] - bb[1] + 10
        total = lh * len(lines)
        if total <= max_h:
            return font, lines, lh
    # Si no cap ni amb la mida mínima, retorna igualment
    font  = load_font(bold=bold, size=size_min)
    lines = wrap_text(draw, text, font, max_w)
    bb    = draw.textbbox((0, 0), "Ag", font=font)
    lh    = bb[3] - bb[1] + 10
    return font, lines, lh


# ── Funció principal ─────────────────────────────────────────────────────────

def create_post_image(town: str, full_message: str, output_path: str) -> str:
    """
    Crea una imatge Instagram 1080x1080 per a SempreSol.

    Layout:
      ┌─────────────────────────────┐
      │  ☀️  Sempre Sol             │  (~260px)
      ├─────────────────────────────┤
      │  NOM DEL POBLE              │  (~100px)
      ├─────────────────────────────┤
      │  Frase completa del dia     │  (~520px, auto-fit)
      ├─────────────────────────────┤
      │  sempresol.cat              │  (~100px)
      └─────────────────────────────┘
    """
    W, H   = 1080, 1080
    MARGIN = 75

    # ── Fons ──────────────────────────────────────────────────────────────────
    img  = gradient_background(W, H)
    draw = ImageDraw.Draw(img)

    # ── Sol (flotant a dalt, independent del bloc de text) ───────────────────
    sun_cy = 140
    draw_sun(draw, W // 2, sun_cy, 75)

    # ── Fonts fixos ───────────────────────────────────────────────────────────
    f_title = load_font(bold=True, size=68)
    f_url   = load_font(bold=True, size=42)

    # ── Calcula primer la zona del peu i de la frase ──────────────────────────
    sep_bottom_y = H - 110
    url_zone_h   = 110

    # Alçada del bloc títol+separadors+poble:
    # "Sempre Sol" (~82px) + sep(4+18) + poble(~108px) + sep(4+28) = ~244px
    HEADER_BLOCK_H = 244
    GAP_ABOVE_MSG  = 20   # espai entre el bloc i la frase

    # Frase: calcula quant espai ocupa
    message_text = full_message.replace("{lugar}", town)

    # Reservem espai per a la frase (màxim fins al peu)
    # Primer estimem amb text_area provisional
    text_area_max = sep_bottom_y - (sun_cy + 75 + HEADER_BLOCK_H + GAP_ABOVE_MSG) - GAP_ABOVE_MSG
    font_msg, lines, lh = fit_text_to_area(
        draw, message_text,
        max_w    = W - 2 * MARGIN,
        max_h    = text_area_max,
        bold     = False,
        size_max = 52,
        size_min = 26,
    )
    block_msg_h = lh * len(lines)

    # ── Posiciona el bloc "Sempre Sol / poble" just a sobre de la frase ───────
    # La frase la centrem en la zona disponible entre el sol i el peu
    zone_top    = sun_cy + 75 + 30        # mínim: 30px sota el sol
    zone_bottom = sep_bottom_y - 20
    zone_h      = zone_bottom - zone_top

    # El bloc títol+poble+frase junts, centrats verticalment en la zona
    total_content_h = HEADER_BLOCK_H + GAP_ABOVE_MSG + block_msg_h
    y = zone_top + max(0, (zone_h - total_content_h) // 2)

    # ── "Sempre Sol" ──────────────────────────────────────────────────────────
    centered_text(draw, y, "Sempre Sol", f_title, COLOR_DARK, W)
    y += 82

    # ── Separador superior ────────────────────────────────────────────────────
    draw.line([(MARGIN, y), (W - MARGIN, y)], fill=COLOR_ORANGE, width=4)
    y += 18

    # ── Nom del poble (auto-mida) ─────────────────────────────────────────────
    town_upper = town.upper()
    f_town     = load_font(bold=True, size=96)
    bb = draw.textbbox((0, 0), town_upper, font=f_town)
    if bb[2] - bb[0] > W - 2 * MARGIN:
        scale  = (W - 2 * MARGIN) / (bb[2] - bb[0])
        f_town = load_font(bold=True, size=max(40, int(96 * scale)))

    centered_text(draw, y, town_upper, f_town, COLOR_DARK, W)
    y += 108

    # ── Separador intermedi ───────────────────────────────────────────────────
    draw.line([(MARGIN, y), (W - MARGIN, y)], fill=COLOR_ORANGE, width=4)
    y += 28 + GAP_ABOVE_MSG

    # ── Frase completa ────────────────────────────────────────────────────────
    y_text = y
    for line in lines:
        centered_text(draw, y_text, line, font_msg, COLOR_DARK, W)
        y_text += lh

    # ── Separador peu ─────────────────────────────────────────────────────────
    draw.line([(MARGIN, sep_bottom_y), (W - MARGIN, sep_bottom_y)],
              fill=COLOR_ORANGE, width=3)

    # ── URL ───────────────────────────────────────────────────────────────────
    url_y = sep_bottom_y + (url_zone_h - 42) // 2
    centered_text(draw, url_y, "sempresol.cat", f_url, COLOR_DARK, W)

    # ── Desa ──────────────────────────────────────────────────────────────────
    img.save(output_path, "PNG")
    return output_path


# ── Test local ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    msg = "A {lugar}, el sol està tan compromès amb el seu treball que ja ha demanat fer hores extres indefinides."
    out = "/tmp/test_sempresol.png"
    create_post_image("Cardedeu", msg, out)
    print(f"Imatge creada: {out}")
