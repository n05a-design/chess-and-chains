#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Export the GitHub social preview and the technical logo overview (developer tool).

    python3 scripts/build_marketing_images.py

Outputs:
    marketing/social/chess-and-chains-social-preview.png   1280 x 640, < 1 MB
    docs/reports/assets/2026-11-26-branding/logo-overview.png

Editable source of the social card: ``marketing/source/chess-and-chains-social-preview.svg``
(same layout, live text). This export needs Pillow and system fonts (Segoe UI
on Windows, DejaVu Sans elsewhere) plus the OFL Manufacturing Consent font of
the wordmark, so its bytes are not reproduced in CI. Logo pixels always come
from the generated Logo 03/02/01 rasters (``scripts/build_brand_assets.py``).
"""
from __future__ import annotations

from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from chess_and_chains.ui import brand_raster as br  # noqa: E402

SOCIAL = ROOT / "marketing/social/chess-and-chains-social-preview.png"
OVERVIEW = ROOT / "docs/reports/assets/2026-11-26-branding/logo-overview.png"
SCREENSHOT = ROOT / "marketing/screenshots/2026-11-26/main-cobalt-original.png"
TITLE_FONT = ROOT / "design/brand_exploration/Chess & Chains – Grafik-Elemente/Manufacturing_Consent/ManufacturingConsent-Regular.ttf"
DARK, PAPER, YELLOW, BLUE = (23, 25, 32), (250, 246, 236), (255, 220, 11), (36, 71, 216)


def _font(bold: bool, size: int) -> ImageFont.FreeTypeFont:
    candidates = (
        ["C:/Windows/Fonts/segoeuib.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
         "/System/Library/Fonts/Supplemental/Arial Bold.ttf"]
        if bold else
        ["C:/Windows/Fonts/segoeui.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
         "/System/Library/Fonts/Supplemental/Arial.ttf"]
    )
    for path in candidates:
        if Path(path).is_file():
            return ImageFont.truetype(path, size)
    raise SystemExit("No suitable system font found (Segoe UI / DejaVu Sans / Arial).")


def _png(path: Path) -> Image.Image:
    rows = br.decode_png(path.read_bytes())
    width, height = len(rows[0]) // 4, len(rows)
    return Image.frombytes("RGBA", (width, height), b"".join(rows))


def _rounded(image: Image.Image, radius: int) -> Image.Image:
    mask = Image.new("L", image.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, image.width - 1, image.height - 1), radius, fill=255)
    out = image.convert("RGBA")
    out.putalpha(mask)
    return out


def social_preview() -> None:
    card = Image.new("RGBA", (1280, 640), DARK + (255,))
    draw = ImageDraw.Draw(card)
    # Screenshot of the real app on the right, slightly cropped to the board area.
    shot = Image.open(SCREENSHOT).convert("RGB")
    shot = shot.resize((int(shot.width * 0.62), int(shot.height * 0.62)), Image.Resampling.LANCZOS)
    shot = _rounded(shot, 18)
    card.alpha_composite(shot, (1280 - shot.width + 120, 92))
    # Fade the screenshot into the dark card so the text side stays calm.
    fade = Image.new("RGBA", (260, 640))
    for x in range(260):
        ImageDraw.Draw(fade).line((x, 0, x, 640), fill=DARK + (int(255 * (1 - x / 259)),))
    card.alpha_composite(fade, (1280 - shot.width + 120, 0))
    draw.rectangle((0, 0, 1280 - shot.width + 120, 640), fill=DARK)

    icon = _png(ROOT / "assets/branding/icons/chess-and-chains-512.png").resize((176, 176), Image.Resampling.LANCZOS)
    card.alpha_composite(icon, (72, 84))
    draw.text((72, 292), "Chess & Chains", font=ImageFont.truetype(str(TITLE_FONT), 92), fill=PAPER)
    draw.text((76, 404), "Play. Think. Connect.", font=_font(True, 40), fill=YELLOW)
    draw.text((76, 462), "Offline-first desktop chess · Puzzle Lab · original piece sets",
              font=_font(False, 24), fill=PAPER)
    draw.text((76, 556), "V.0.3.0 DEVELOPMENT SNAPSHOT  ·  OPEN SOURCE  ·  MPL-2.0",
              font=_font(True, 18), fill=(184, 189, 199))
    draw.rectangle((76, 530, 76 + 88, 534), fill=BLUE)
    SOCIAL.parent.mkdir(parents=True, exist_ok=True)
    card.convert("RGB").save(SOCIAL, optimize=True)
    print(SOCIAL.relative_to(ROOT), SOCIAL.stat().st_size, "bytes")


def overview() -> None:
    sheet = Image.new("RGBA", (1500, 930), (245, 245, 247, 255))
    draw = ImageDraw.Draw(sheet)
    label, small = _font(True, 22), _font(False, 17)
    draw.text((40, 24), "Chess & Chains – logo masters and derived resources (2026-11-26)", font=_font(True, 28), fill=DARK)
    masters = (
        ("Logo 01 · in_app (original colours)", ROOT / "assets/branding/signet/chess-and-chains-signet-512.png"),
        ("Logo 02 · internal_brand (About)", ROOT / "assets/branding/emblem/chess-and-chains-emblem-512.png"),
        ("Logo 03 · app_icon (icon, README)", ROOT / "assets/branding/icons/chess-and-chains-512.png"),
    )
    x = 40
    for text, path in masters:
        image = _png(path)
        image.thumbnail((300, 300), Image.Resampling.LANCZOS)
        sheet.alpha_composite(image, (x, 80 + (300 - image.height) // 2))
        draw.text((x, 392), text, font=label, fill=DARK)
        x += 480
    # Runtime tint of Logo 01: transparent cut-outs, theme colour, light and dark surfaces.
    sys.path.insert(0, str(ROOT / "src"))
    doc = br.parse_svg((ROOT / "src/chess_and_chains/ui/brand_assets/signet.svg").read_bytes())
    box = br.signet_visible_box(doc)
    draw.text((40, 450), "Logo 01 at runtime – tinted with ThemePalette.view_title, separators transparent",
              font=label, fill=DARK)
    tints = (("#0767C7", (255, 255, 255)), ("#0E7490", (255, 255, 255)), ("#945400", (255, 255, 255)),
             ("#FFC038", (28, 28, 30)), ("#40C8E0", (28, 28, 30)), ("#30D158", (17, 17, 19)))
    x = 40
    for colour, surface in tints:
        rgb = tuple(int(colour[i:i + 2], 16) for i in (1, 3, 5))
        rows = br.render(br.signet_layers(doc, (rgb, rgb)), br.Frame.fit(box, 180, 121))
        tile = Image.new("RGBA", (220, 160), surface + (255,))
        tile.alpha_composite(Image.frombytes("RGBA", (180, 121), b"".join(rows)), (20, 18))
        sheet.alpha_composite(tile, (x, 490))
        draw.text((x, 656), colour, font=small, fill=DARK)
        x += 240
    draw.text((40, 712), "Logo 03 icon sizes (16 – 256 px, shown at 1:1)", font=label, fill=DARK)
    x = 40
    for size in (16, 24, 32, 48, 64, 128):
        image = _png(ROOT / f"assets/branding/icons/chess-and-chains-{size}.png")
        sheet.alpha_composite(image, (x, 752))
        draw.text((x, 752 + size + 6), f"{size}", font=small, fill=DARK)
        x += size + 40
    image = _png(ROOT / "assets/branding/icons/chess-and-chains-macos-1024.png").resize((128, 128), Image.Resampling.LANCZOS)
    draw.rectangle((x + 20, 752, x + 148, 880), outline=(184, 189, 199))
    sheet.alpha_composite(image, (x + 20, 752))
    draw.text((x + 160, 800), "macOS ICNS body 824/1024", font=small, fill=DARK)
    OVERVIEW.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(OVERVIEW, optimize=True)
    print(OVERVIEW.relative_to(ROOT), OVERVIEW.stat().st_size, "bytes")


if __name__ == "__main__":
    social_preview()
    overview()
