"""Generate SVG section headings with hairline rule."""
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE.parent
W = 620

HEADINGS = {
    "hd-about.svg": "about",
    "hd-stack.svg": "stack",
    "hd-projects.svg": "projects",
    "hd-stats.svg": "stats",
    "hd-connect.svg": "connect",
}


def heading_svg(label: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} 28" width="{W}">
<defs><style>
@media(prefers-color-scheme:dark){{.t{{fill:#c9d1d9}}.l{{stroke:#30363d}}}}
@media(prefers-color-scheme:light){{.t{{fill:#1f2328}}.l{{stroke:#d0d7de}}}}
</style></defs>
<text class="t" x="0" y="16" font-family="JetBrains Mono,monospace" font-size="14" font-weight="600">{label}</text>
<line class="l" x1="0" y1="27" x2="{W}" y2="27" stroke-width="1"/>
</svg>"""


if __name__ == "__main__":
    for fname, label in HEADINGS.items():
        (OUT / fname).write_text(heading_svg(label), encoding="utf-8")
        print(f"wrote {fname}")
