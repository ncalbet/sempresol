#!/usr/bin/env python3
"""Generate OG image for Sempresol website."""

from PIL import Image, ImageDraw, ImageFont
import math

WIDTH = 1200
HEIGHT = 630

# Create image
img = Image.new("RGB", (WIDTH, HEIGHT), color=(255, 140, 0))
draw = ImageDraw.Draw(img)

# --- Gradient background (orange to golden yellow) ---
for y in range(HEIGHT):
    t = y / HEIGHT
    r = int(255 * (1 - t * 0.05))   # stays near 255
    g = int(140 + (215 - 140) * t)  # 140 -> 215
    b = int(0 + 0 * t)              # stays 0
    draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))

# Subtle diagonal lighter band
overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
ov_draw = ImageDraw.Draw(overlay)
for i in range(300):
    alpha = int(30 * (1 - i / 300))
    ov_draw.line(
        [(0 + i * 2, 0), (WIDTH, HEIGHT - i * 2)],
        fill=(255, 255, 200, alpha),
        width=2,
    )
img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
draw = ImageDraw.Draw(img)

# --- Sun graphic (center-left area) ---
sun_cx = 310
sun_cy = 280
sun_r = 120   # main circle radius
glow_r = 145  # inner glow ring

# Glow rings
for i in range(4, 0, -1):
    glow_alpha = 40 + i * 15
    glow_size = glow_r + i * 22
    # Draw as filled circle with transparency via composite
    glow_img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow_img)
    gd.ellipse(
        [sun_cx - glow_size, sun_cy - glow_size, sun_cx + glow_size, sun_cy + glow_size],
        fill=(255, 255, 180, glow_alpha),
    )
    img = Image.alpha_composite(img.convert("RGBA"), glow_img).convert("RGB")
    draw = ImageDraw.Draw(img)

# Sun rays (lines radiating outward)
num_rays = 16
ray_inner = glow_r + 10
ray_outer = glow_r + 65
for i in range(num_rays):
    angle = math.radians(i * (360 / num_rays))
    x1 = sun_cx + ray_inner * math.cos(angle)
    y1 = sun_cy + ray_inner * math.sin(angle)
    x2 = sun_cx + ray_outer * math.cos(angle)
    y2 = sun_cy + ray_outer * math.sin(angle)
    # Thick rays
    draw.line([(x1, y1), (x2, y2)], fill=(255, 255, 200), width=6)

# Short secondary rays between main rays
for i in range(num_rays):
    angle = math.radians(i * (360 / num_rays) + (360 / num_rays / 2))
    x1 = sun_cx + (ray_inner + 8) * math.cos(angle)
    y1 = sun_cy + (ray_inner + 8) * math.sin(angle)
    x2 = sun_cx + (ray_outer - 20) * math.cos(angle)
    y2 = sun_cy + (ray_outer - 20) * math.sin(angle)
    draw.line([(x1, y1), (x2, y2)], fill=(255, 255, 200), width=3)

# Sun circle - warm white-yellow gradient simulation via concentric circles
for step in range(sun_r, 0, -3):
    t = step / sun_r  # 1 at edge, 0 at center
    r_col = int(255)
    g_col = int(220 + (255 - 220) * (1 - t))
    b_col = int(80 + (160 - 80) * (1 - t))
    draw.ellipse(
        [sun_cx - step, sun_cy - step, sun_cx + step, sun_cy + step],
        fill=(r_col, g_col, b_col),
    )

# Sun face highlight (small brighter circle, top-left of sun)
draw.ellipse(
    [sun_cx - 45, sun_cy - 55, sun_cx + 5, sun_cy - 15],
    fill=(255, 255, 220),
)

# --- Fonts ---
font_main = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 110)
font_sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 38)
font_url = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
font_tagline_light = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 38)

# --- Text area (right/center) ---
text_x = 580   # start x for main text block

# Shadow helper
def draw_text_shadow(draw, pos, text, font, fill, shadow_color=(0,0,0,80), offset=3):
    draw.text((pos[0] + offset, pos[1] + offset), text, font=font, fill=shadow_color)
    draw.text(pos, text, font=font, fill=fill)

# "Sempre Sol" main title
title = "Sempre Sol"
# measure
bbox = draw.textbbox((0, 0), title, font=font_main)
tw = bbox[2] - bbox[0]
# center in right portion
right_width = WIDTH - text_x - 40
title_x = text_x + (right_width - tw) // 2
title_y = 155

# Drop shadow
draw.text((title_x + 4, title_y + 4), title, font=font_main, fill=(180, 80, 0))
draw.text((title_x, title_y), title, font=font_main, fill=(255, 255, 255))

# Subtitle
subtitle = "Sempre assolellat arreu del món"
bbox2 = draw.textbbox((0, 0), subtitle, font=font_tagline_light)
sw = bbox2[2] - bbox2[0]
sub_x = text_x + (right_width - sw) // 2
sub_y = title_y + 125

draw.text((sub_x + 2, sub_y + 2), subtitle, font=font_tagline_light, fill=(180, 80, 0))
draw.text((sub_x, sub_y), subtitle, font=font_tagline_light, fill=(255, 245, 220))

# Decorative line below subtitle
line_y = sub_y + 60
line_x1 = text_x + 40
line_x2 = WIDTH - 40
draw.line([(line_x1, line_y), (line_x2, line_y)], fill=(255, 255, 200, 180), width=2)

# URL bottom-right
url_text = "sempresol.cat"
bbox3 = draw.textbbox((0, 0), url_text, font=font_url)
uw = bbox3[2] - bbox3[0]
url_x = WIDTH - uw - 50
url_y = HEIGHT - 75

draw.text((url_x + 2, url_y + 2), url_text, font=font_url, fill=(180, 80, 0))
draw.text((url_x, url_y), url_text, font=font_url, fill=(255, 255, 255))

# Small sun icon next to URL
mini_sun_cx = url_x - 28
mini_sun_cy = url_y + 16
mini_r = 11
draw.ellipse(
    [mini_sun_cx - mini_r, mini_sun_cy - mini_r, mini_sun_cx + mini_r, mini_sun_cy + mini_r],
    fill=(255, 255, 200),
)
for i in range(8):
    angle = math.radians(i * 45)
    x1 = mini_sun_cx + (mini_r + 2) * math.cos(angle)
    y1 = mini_sun_cy + (mini_r + 2) * math.sin(angle)
    x2 = mini_sun_cx + (mini_r + 8) * math.cos(angle)
    y2 = mini_sun_cy + (mini_r + 8) * math.sin(angle)
    draw.line([(x1, y1), (x2, y2)], fill=(255, 255, 200), width=2)

# --- Bottom decorative band ---
band_y = HEIGHT - 30
for i in range(band_y, HEIGHT):
    alpha = int(60 * (i - band_y) / 30)
    draw.line([(0, i), (WIDTH, i)], fill=(200, 80, 0))

# Save
out_path = "/home/user/sempresol/og-image.png"
img.save(out_path, "PNG", optimize=True)
print(f"Saved to {out_path}")
print(f"Size: {img.size}")
