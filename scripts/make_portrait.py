"""Convert portrait.jpg → ascii.svg with SMIL row-reveal animation."""
import sys
from pathlib import Path

try:
    from PIL import Image, ImageEnhance
except ImportError:
    sys.exit("pip install Pillow")

RAMP = " .:-=+*cs#%@"
COLS, ROWS = 72, 40  # character grid
CHAR_W, CHAR_H = 6.6, 13.2  # px per char (JetBrains Mono 11px)
PAD = 4
SVG_W = int(COLS * CHAR_W + PAD * 2)
SVG_H = int(ROWS * CHAR_H + PAD * 2)
ANIM_DUR = 2.0  # seconds total reveal

HERE = Path(__file__).parent
OUT = HERE.parent / "ascii.svg"
IMG = HERE / "portrait.jpg"


def img_to_grid(path: Path) -> list[str]:
    img = Image.open(path).convert("L")
    img = ImageEnhance.Contrast(img).enhance(1.4)
    # crop to target aspect ratio
    target_ratio = (COLS * CHAR_W) / (ROWS * CHAR_H)
    w, h = img.size
    current_ratio = w / h
    if current_ratio > target_ratio:
        new_w = int(h * target_ratio)
        offset = (w - new_w) // 2
        img = img.crop((offset, 0, offset + new_w, h))
    else:
        new_h = int(w / target_ratio)
        offset = (h - new_h) // 2
        img = img.crop((0, offset, w, offset + new_h))
    img = img.resize((COLS, ROWS), Image.LANCZOS)
    rows = []
    for y in range(ROWS):
        line = ""
        for x in range(COLS):
            px = img.getpixel((x, y))
            idx = int(px / 256 * len(RAMP))
            idx = min(idx, len(RAMP) - 1)
            line += RAMP[idx]
        rows.append(line)
    return rows


def build_svg(rows: list[str]) -> str:
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SVG_W} {SVG_H}" width="{SVG_W}">',
        "<defs>",
        '<style>@media(prefers-color-scheme:dark){.bg{fill:#0d1117}.fg{fill:#c9d1d9}}'
        '@media(prefers-color-scheme:light){.bg{fill:#ffffff}.fg{fill:#1f2328}}</style>',
        "</defs>",
        f'<rect class="bg" width="{SVG_W}" height="{SVG_H}" rx="6"/>',
    ]
    delay_step = ANIM_DUR / ROWS
    for i, row in enumerate(rows):
        escaped = row.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        y = PAD + (i + 1) * CHAR_H
        delay = i * delay_step
        # clip path for reveal
        clip_id = f"c{i}"
        lines.append(f'<clipPath id="{clip_id}">')
        lines.append(
            f'<rect x="0" y="{PAD + i * CHAR_H}" width="0" height="{CHAR_H}">'
            f'<animate attributeName="width" from="0" to="{SVG_W}" '
            f'dur="0.3s" begin="{delay:.2f}s" fill="freeze"/>'
            f"</rect>"
        )
        lines.append("</clipPath>")
        lines.append(
            f'<text class="fg" x="{PAD}" y="{y}" font-family="JetBrains Mono,monospace" '
            f'font-size="11" clip-path="url(#{clip_id})">{escaped}</text>'
        )
    lines.append("</svg>")
    return "\n".join(lines)


if __name__ == "__main__":
    rows = img_to_grid(IMG)
    svg = build_svg(rows)
    OUT.write_text(svg, encoding="utf-8")
    print(f"wrote {OUT} ({SVG_W}×{SVG_H})")
