# © 2026 Ranuk IT Solutions — ranuk.dev
"""
generate_channel_branding.py — Generates broadcast-grade branding for YouTube & TikTok:
  1. YouTube Channel Banner (2560x1440 px, safe area 1546x423 px)
  2. YouTube / TikTok Profile Avatar (800x800 px)
  3. TikTok Vertical Cover / Thumbnail (1080x1920 px)
"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

REPO_ROOT = Path("/Users/emilioranucoli/Apps/ranuk-ai-debate-studio")
BRAND_DIR = REPO_ROOT / "assets" / "brand"
OUT_DIR = REPO_ROOT / "assets" / "branding_channels"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    paths = (
        ["/System/Library/Fonts/SFNS.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf"]
        if bold
        else ["/System/Library/Fonts/SFNS.ttf", "/System/Library/Fonts/Supplemental/Arial.ttf"]
    )
    for p in paths:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def load_ranuk_logo(size: int = 140) -> Image.Image:
    path = BRAND_DIR / "minilogo.png"
    raw = Image.open(path).convert("RGB")
    arr = np.array(raw, dtype=np.float32)
    lum = np.max(arr, axis=2)
    alpha = np.clip((lum - 14.0) * 2.4, 0.0, 255.0).astype(np.uint8)
    rgba = np.dstack([arr.astype(np.uint8), alpha])
    img = Image.fromarray(rgba, mode="RGBA")
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)
    img.thumbnail((size, size), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ox = (size - img.width) // 2
    oy = (size - img.height) // 2
    canvas.paste(img, (ox, oy), img)
    return canvas


def generate_avatar(out_path: Path, size: int = 800) -> Path:
    """Generate 800x800 Ultra-HD Avatar for YouTube and TikTok."""
    img = Image.new("RGBA", (size, size), (5, 7, 14, 255))
    y, x = np.mgrid[:size, :size]

    # Glowing chromatic aurora behind the logo
    dist = np.sqrt((x - size // 2) ** 2 + (y - size // 2) ** 2)
    aurora_alpha = (np.clip(1.0 - dist / (size * 0.48), 0.0, 1.0) ** 2.2) * 160.0
    r = (aurora_alpha * 0.05).astype(np.uint8)
    g = (aurora_alpha * 0.85).astype(np.uint8)
    b = (aurora_alpha * 1.00).astype(np.uint8)
    glow = Image.fromarray(np.dstack([r, g, b, aurora_alpha.astype(np.uint8)]), mode="RGBA").filter(ImageFilter.GaussianBlur(32))
    img = Image.alpha_composite(img, glow)

    draw = ImageDraw.Draw(img)

    # Concentric Apple Glass rings
    cx, cy = size // 2, size // 2
    draw.ellipse([cx - 360, cy - 360, cx + 360, cy + 360], outline=(0, 240, 255, 60), width=2)
    draw.ellipse([cx - 320, cy - 320, cx + 320, cy + 320], outline=(16, 235, 155, 45), width=1)
    draw.ellipse([cx - 260, cy - 260, cx + 260, cy + 260], fill=(12, 18, 30, 210), outline=(255, 255, 255, 55), width=2)

    # 3D Ranuk Logo centered
    logo = load_ranuk_logo(size=360)
    img.paste(logo, (cx - logo.width // 2, cy - logo.height // 2 - 15), logo)

    # Bottom pill badge: "FULL-DUPLEX AI"
    draw.rounded_rectangle([cx - 150, cy + 225, cx + 150, cy + 275], radius=25, fill=(0, 240, 255, 35), outline=(0, 240, 255, 180), width=2)
    f_badge = load_font(24, bold=True)
    draw.text((cx - 110, cy + 238), "AI DEBATE ARENA", fill=(255, 255, 255, 255), font=f_badge)

    img.convert("RGB").save(str(out_path), "PNG", quality=95)
    print("Saved Avatar:", out_path)
    return out_path


def generate_youtube_banner(out_path: Path) -> Path:
    """Generate 2560x1440 YouTube Channel Banner with 1546x423 safe area."""
    width, height = 2560, 1440
    img = Image.new("RGBA", (width, height), (5, 8, 15, 255))
    y, x = np.mgrid[:height, :width]

    # Multi-point ambient aurora mesh
    cx1, cy1 = int(width * 0.28), int(height * 0.50)
    dist1 = np.sqrt((x - cx1) ** 2 + (y - cy1) ** 2)
    a1 = (np.clip(1.0 - dist1 / 700.0, 0.0, 1.0) ** 2.0) * 110.0

    cx2, cy2 = int(width * 0.72), int(height * 0.50)
    dist2 = np.sqrt((x - cx2) ** 2 + (y - cy2) ** 2)
    a2 = (np.clip(1.0 - dist2 / 700.0, 0.0, 1.0) ** 2.0) * 110.0

    r = (a1 * 0.02 + a2 * 0.05).astype(np.uint8)
    g = (a1 * 0.85 + a2 * 0.95).astype(np.uint8)
    b = (a1 * 1.00 + a2 * 0.55).astype(np.uint8)
    aurora = Image.fromarray(np.dstack([r, g, b, np.clip(a1 + a2, 0, 180).astype(np.uint8)]), mode="RGBA").filter(ImageFilter.GaussianBlur(40))
    img = Image.alpha_composite(img, aurora)

    # Subtle grid
    grid = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(grid)
    for gx in range(0, width, 64):
        gdraw.line([(gx, 0), (gx, height)], fill=(255, 255, 255, 7), width=1)
    for gy in range(0, height, 64):
        gdraw.line([(0, gy), (width, gy)], fill=(255, 255, 255, 7), width=1)
    img = Image.alpha_composite(img, grid)

    draw = ImageDraw.Draw(img)

    # Safe Area Box (1546x423 centered)
    # cy = 720, cx = 1280
    # Safe box y: 508 to 931. Safe box x: 507 to 2053.
    # Center floating frosted glass pill in safe area
    pill_w, pill_h = 1480, 360
    px0 = (width - pill_w) // 2
    py0 = (height - pill_h) // 2

    draw.rounded_rectangle([px0, py0, px0 + pill_w, py0 + pill_h], radius=44, fill=(12, 17, 28, 175), outline=(255, 255, 255, 45), width=2)
    # Specular top highlight
    draw.rounded_rectangle([px0 + 8, py0 + 2, px0 + pill_w - 8, py0 + 5], radius=44, fill=(255, 255, 255, 95))

    # Left: 3D Ranuk Logo
    logo = load_ranuk_logo(size=220)
    img.paste(logo, (px0 + 50, py0 + (pill_h - logo.height) // 2), logo)

    # Middle / Right: Typography
    f_title = load_font(68, bold=True)
    f_sub = load_font(32, bold=False)
    f_tags = load_font(22, bold=True)

    tx = px0 + 310
    draw.text((tx, py0 + 64), "RANUK AI DEBATE STUDIO", fill=(255, 255, 255, 255), font=f_title)
    draw.text((tx, py0 + 154), "Unscripted 24kHz Full-Duplex AI Clashes  •  ~180ms Latency", fill=(165, 243, 252, 245), font=f_sub)

    # Feature badges
    by = py0 + 224
    badges = [
        ("⚡ POWERED BY NVIDIA PERSONAPLEX 7B", (118, 185, 0)),
        ("🎙️ STEREO FULL-DUPLEX AUDIO", (0, 240, 255)),
        ("🌐 RANUK.DEV/DEBATES", (16, 235, 155)),
    ]
    cur_x = tx
    for b_text, b_col in badges:
        bbox = draw.textbbox((0, 0), b_text, font=f_tags)
        bw = bbox[2] - bbox[0] + 32
        draw.rounded_rectangle([cur_x, by, cur_x + bw, by + 46], radius=23, fill=(*b_col, 30), outline=(*b_col, 170), width=1)
        draw.text((cur_x + 16, by + 11), b_text, fill=(255, 255, 255, 255), font=f_tags)
        cur_x += bw + 18

    img.convert("RGB").save(str(out_path), "PNG", quality=95)
    print("Saved YouTube Banner:", out_path)
    return out_path


if __name__ == "__main__":
    generate_avatar(OUT_DIR / "avatar_youtube_800x800.png")
    generate_avatar(OUT_DIR / "avatar_tiktok_500x500.png", size=500)
    generate_youtube_banner(OUT_DIR / "youtube_banner_2560x1440.png")
