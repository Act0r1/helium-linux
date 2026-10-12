#!/usr/bin/env python3
"""Generates Argon branding assets in resources/branding from one chevron geometry.

Requires rsvg-convert. Output files are committed; rerun after changing geometry.
"""

import math
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

OUT = Path(__file__).resolve().parent / "branding"

HALF_WIDTH = 72.0
HALF_HEIGHT = 51.0
STEP = 38.0
RADIUS = 11.0
KNOCK_RADIUS = 21.0
LAYER_ALPHAS = (1.0, 0.45, 0.2)

MONO_COLOR = "#3C4043"
FONT = "Adwaita Sans"


@dataclass(frozen=True)
class Point:
    x: float
    y: float

    def __add__(self, other: "Point") -> "Point":
        return Point(self.x + other.x, self.y + other.y)

    def scaled(self, k: float) -> "Point":
        return Point(self.x * k, self.y * k)


@dataclass(frozen=True)
class Transform:
    scale: float
    dx: float
    dy: float

    def apply(self, p: Point) -> Point:
        return Point(p.x * self.scale + self.dx, p.y * self.scale + self.dy)


Segment = tuple[str, Point, float]


def chevron_outline(top: float, radius: float) -> list[Segment]:
    """Outline of a chevron centred on x=0 with its apex centreline at y=top.

    Returns a closed path as (command, point, arc_radius) where command is
    "M", "L" or "A" (clockwise arc of arc_radius ending at point).
    """
    arm = math.hypot(HALF_WIDTH, 2 * HALF_HEIGHT)
    left_out = Point(-2 * HALF_HEIGHT / arm, -HALF_WIDTH / arm)
    right_out = Point(-left_out.x, left_out.y)
    apex = Point(0, top)
    left_foot = Point(-HALF_WIDTH, top + 2 * HALF_HEIGHT)
    right_foot = Point(HALF_WIDTH, top + 2 * HALF_HEIGHT)
    inner_apex = Point(0, top + radius * arm / HALF_WIDTH)
    return [
        ("M", left_foot + left_out.scaled(radius), 0),
        ("L", apex + left_out.scaled(radius), 0),
        ("A", apex + right_out.scaled(radius), radius),
        ("L", right_foot + right_out.scaled(radius), 0),
        ("A", right_foot + right_out.scaled(-radius), radius),
        ("L", inner_apex, 0),
        ("L", left_foot + left_out.scaled(-radius), 0),
        ("A", left_foot + left_out.scaled(radius), radius),
    ]


def layer_tops() -> list[float]:
    """Apex centreline y of each layer, top layer first; the mark is centred on y=0."""
    span = 2 * HALF_HEIGHT + STEP * (len(LAYER_ALPHAS) - 1)
    first = -span / 2
    return [first + STEP * i for i in range(len(LAYER_ALPHAS))]


def svg_path(segments: list[Segment], t: Transform) -> str:
    parts: list[str] = []
    for command, point, radius in segments:
        p = t.apply(point)
        if command == "A":
            r = radius * t.scale
            parts.append(f"A{r:.2f} {r:.2f} 0 0 1 {p.x:.2f} {p.y:.2f}")
        else:
            parts.append(f"{command}{p.x:.2f} {p.y:.2f}")
    return " ".join(parts) + " Z"


def icon_path(segments: list[Segment], t: Transform) -> list[str]:
    lines: list[str] = []
    names = {"M": "MOVE_TO", "L": "LINE_TO"}
    for command, point, radius in segments:
        p = t.apply(point)
        if command == "A":
            r = radius * t.scale
            lines.append(f"ARC_TO, {r:.2f}f, {r:.2f}f, 0, 0, 1, {p.x:.2f}f, {p.y:.2f}f,")
        else:
            lines.append(f"{names[command]}, {p.x:.2f}f, {p.y:.2f}f,")
    lines.append("CLOSE,")
    return lines


def mark_svg(t: Transform, color: str, top_fill: str) -> str:
    """Chevron layers; each lower layer is masked by a wider outline of the layer above."""
    tops = layer_tops()
    body: list[str] = []
    for i, (top, alpha) in enumerate(zip(tops, LAYER_ALPHAS)):
        fill = top_fill if i == 0 else color
        shape = f'd="{svg_path(chevron_outline(top, RADIUS), t)}"'
        if i == 0:
            body.append(f'<path {shape} fill="{fill}"/>')
            continue
        knock = svg_path(chevron_outline(tops[i - 1], KNOCK_RADIUS), t)
        body.append(
            f'<mask id="k{i}" maskUnits="userSpaceOnUse" x="-1000" y="-1000" width="3000" height="3000">'
            f'<rect x="-1000" y="-1000" width="3000" height="3000" fill="#fff"/>'
            f'<path d="{knock}" fill="#000"/></mask>'
            f'<path {shape} fill="{fill}" fill-opacity="{alpha}" mask="url(#k{i})"/>'
        )
    return "".join(reversed(body))


def app_icon_svg() -> str:
    t = Transform(1.0, 128, 128)
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">'
        '<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#26262A"/><stop offset="1" stop-color="#0E0E10"/></linearGradient>'
        '<linearGradient id="w" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#FFFFFF"/><stop offset="1" stop-color="#D4D4D8"/></linearGradient></defs>'
        '<rect width="256" height="256" rx="58" fill="url(#bg)"/>'
        '<rect x="1.5" y="1.5" width="253" height="253" rx="56.5" fill="none" '
        'stroke="#FFFFFF" stroke-opacity="0.08" stroke-width="3"/>'
        + mark_svg(t, "#FFFFFF", "url(#w)")
        + "</svg>\n"
    )


def mark_extent() -> tuple[float, float]:
    """Width and height of the mark outline including stroke radius."""
    arm = math.hypot(HALF_WIDTH, 2 * HALF_HEIGHT)
    width = 2 * (HALF_WIDTH + RADIUS * 2 * HALF_HEIGHT / arm)
    tops = layer_tops()
    height = (tops[-1] + 2 * HALF_HEIGHT + RADIUS) - (tops[0] - RADIUS)
    return width, height


def mono_svg(size: int, color: str) -> str:
    _, height = mark_extent()
    t = Transform((size - 2) / height, size / 2, size / 2)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">'
        + mark_svg(t, color, color)
        + "</svg>\n"
    )


def wordmark_svg(color: str) -> str:
    width, height = mark_extent()
    scale = 26.0 / height
    t = Transform(scale, 4 + width * scale / 2, 16)
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="140" height="32" viewBox="0 0 140 32">'
        + mark_svg(t, color, color)
        + f'<text x="37" y="25" font-family="{FONT}" font-size="27" font-weight="500" '
        f'letter-spacing="-0.4" fill="{color}">Argon</text></svg>\n'
    )


def product_logo_icon(canvas: int, background: bool) -> str:
    """Skia .icon commands: layers drawn bottom-up, each knocked out by the one above."""
    _, height = mark_extent()
    margin = 28 if background else 1
    t = Transform((canvas - 2 * margin) / height, canvas / 2, canvas / 2)
    lines = [
        "// Copyright 2026 The Argon Authors",
        "// You can use, redistribute, and/or modify this source code under",
        "// the terms of the GPL-3.0 license that can be found in the LICENSE file.",
        "",
        f"CANVAS_DIMENSIONS, {canvas},",
    ]
    if background:
        lines += ["NEW_PATH,", "PATH_COLOR_ARGB, 0xFF, 0x1A, 0x1A, 0x1D,",
                  f"ROUND_RECT, 0, 0, {canvas}, {canvas}, 58,"]
    tops = layer_tops()
    for i in reversed(range(len(tops))):
        alpha = round(LAYER_ALPHAS[i] * 255)
        lines.append("NEW_PATH,")
        if background:
            lines.append(f"PATH_COLOR_ARGB, 0x{alpha:02X}, 0xFF, 0xFF, 0xFF,")
        elif alpha != 255:
            lines.append(f"PATH_COLOR_ALPHA, 0x{alpha:02X},")
        lines += icon_path(chevron_outline(tops[i], RADIUS), t)
        if i > 0 and not background:
            lines += ["NEW_PATH,", "PATH_MODE_CLEAR,"]
            lines += icon_path(chevron_outline(tops[i - 1], KNOCK_RADIUS), t)
        elif i > 0:
            lines += ["NEW_PATH,", "PATH_COLOR_ARGB, 0xFF, 0x1A, 0x1A, 0x1D,"]
            lines += icon_path(chevron_outline(tops[i - 1], KNOCK_RADIUS), t)
    return "\n".join(lines) + "\n"


def rasterize(svg: Path, png: Path, width: int, height: int) -> None:
    subprocess.run(["rsvg-convert", "-w", str(width), "-h", str(height), str(svg), "-o", str(png)],
                   check=True)


def main() -> None:
    (OUT / "app_icon").mkdir(parents=True, exist_ok=True)
    svgs = {
        "product_logo.svg": app_icon_svg(),
        "mono.svg": mono_svg(22, MONO_COLOR),
        "wordmark.svg": wordmark_svg("#000000"),
        "wordmark_white.svg": wordmark_svg("#FFFFFF"),
    }
    for name, text in svgs.items():
        (OUT / name).write_text(text)

    rasterize(OUT / "product_logo.svg", OUT / "app_icon/raw.png", 1024, 1024)
    rasterize(OUT / "mono.svg", OUT / "product_logo_22_mono.png", 22, 22)
    rasterize(OUT / "wordmark.svg", OUT / "product_logo.png", 140, 32)
    rasterize(OUT / "wordmark.svg", OUT / "product_logo_200.png", 280, 64)
    rasterize(OUT / "wordmark_white.svg", OUT / "product_logo_white.png", 140, 32)
    rasterize(OUT / "wordmark_white.svg", OUT / "product_logo_white_200.png", 280, 64)
    for name in ("mono.svg", "wordmark.svg", "wordmark_white.svg"):
        (OUT / name).unlink()

    (OUT / "product_logo.icon").write_text(product_logo_icon(56, background=False))
    (OUT / "product_logo_color.icon").write_text(product_logo_icon(256, background=True))
    print(f"Generated branding in {OUT}", file=sys.stderr)


if __name__ == "__main__":
    main()
