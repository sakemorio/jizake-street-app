from PIL import Image, ImageDraw
import os

OUT = os.path.join(os.path.dirname(__file__), "..", "icons")
os.makedirs(OUT, exist_ok=True)

INDIGO = (34, 69, 107, 255)
PAPER = (243, 241, 231, 255)
HANKO = (184, 65, 46, 255)

def make_icon(size, path, maskable=False):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pad = int(size * 0.06) if not maskable else 0
    d.rounded_rectangle([pad, pad, size - pad, size - pad], radius=int(size * 0.22), fill=INDIGO)

    # sake cup (simple cup silhouette)
    cx, cy = size / 2, size / 2 + size * 0.03
    cup_w, cup_h = size * 0.46, size * 0.30
    d.rounded_rectangle(
        [cx - cup_w / 2, cy - cup_h / 2, cx + cup_w / 2, cy + cup_h / 2],
        radius=int(cup_h * 0.18), fill=PAPER
    )
    # liquid line
    d.rectangle(
        [cx - cup_w / 2 + size * 0.02, cy - cup_h / 2 + size * 0.02,
         cx + cup_w / 2 - size * 0.02, cy - cup_h / 2 + size * 0.09],
        fill=HANKO
    )
    # hanko dot accent
    r = size * 0.045
    d.ellipse([cx + cup_w / 2 - r * 1.6, cy - cup_h / 2 - r * 1.6,
               cx + cup_w / 2 + r * 0.4, cy - cup_h / 2 + r * 0.4], fill=HANKO)

    img.save(path)

make_icon(192, os.path.join(OUT, "icon-192.png"))
make_icon(512, os.path.join(OUT, "icon-512.png"))
make_icon(512, os.path.join(OUT, "icon-512-maskable.png"), maskable=True)
print("icons generated")
