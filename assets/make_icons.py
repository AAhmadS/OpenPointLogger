r"""Render every raster icon Trailmark needs, from one definition of the mark.

Run:  python assets\make_icons.py

There is no SVG rasteriser in the dependency list and there is not going to be
one - the mark is five rounded rectangles, and Pillow draws those. Keeping the
geometry here, in the same numbers as assets/mark.svg, means a change to the
logo is a change to one tuple list and a re-run, instead of a round trip through
a drawing program and an auto-tracer.

Outputs:
  icon.png icon-32 icon-64 icon-96 icon-256    amber, transparent - app + web
  logo.png                                     amber wordmark-free mark, large
  tray-dark.png / tray-light.png               silhouettes for the notification area
  app.ico                                      multi-size Windows icon
"""

from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent

#: x, y, w, h, r in the mark's own 1349x1568 box (see mark.svg)
BARS = [
    (0, 0, 1347, 279, 46),
    (597, 180, 147, 1388, 46),
    (206, 679, 392, 138, 46),
    (206, 984, 392, 139, 46),
    (744, 1259, 395, 140, 46),
]
BOX_W, BOX_H = 1349, 1568

AMBER = (240, 169, 74, 255)          # #f0a94a - the app accent
INK = (18, 22, 30, 255)              # for a light taskbar
PAPER = (255, 255, 255, 255)         # for a dark one

#: drawn at 4x and downsampled - Pillow has no anti-aliased rounded_rectangle
SS = 4


def render(size, colour, pad=0.08):
    """The mark, centred in a transparent square of `size` px."""
    n = size * SS
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    inner = n * (1 - 2 * pad)
    scale = min(inner / BOX_W, inner / BOX_H)
    ox = (n - BOX_W * scale) / 2
    oy = (n - BOX_H * scale) / 2
    for x, y, w, h, r in BARS:
        d.rounded_rectangle(
            [ox + x * scale, oy + y * scale,
             ox + (x + w) * scale, oy + (y + h) * scale],
            radius=max(1, r * scale), fill=colour)
    return img.resize((size, size), Image.LANCZOS)


def main():
    for name, size in (("icon.png", 256), ("icon-32.png", 32), ("icon-64.png", 64),
                       ("icon-96.png", 96), ("icon-256.png", 256), ("logo.png", 512)):
        render(size, AMBER).save(HERE / name)
        print("wrote", name)

    # The tray sits on the taskbar, not on the app's own surface, so it follows
    # Windows' theme rather than Trailmark's. A silhouette reads at 16px where a
    # coloured mark turns to mud; padding is tighter because the tray gives you
    # sixteen pixels and no more.
    render(64, PAPER, pad=0.04).save(HERE / "tray-dark.png")
    render(64, INK, pad=0.04).save(HERE / "tray-light.png")
    print("wrote tray-dark.png, tray-light.png")

    ico = HERE.parent / "app.ico"
    render(256, AMBER).save(ico, sizes=[(16, 16), (24, 24), (32, 32), (48, 48),
                                        (64, 64), (128, 128), (256, 256)])
    print("wrote", ico)


if __name__ == "__main__":
    main()
