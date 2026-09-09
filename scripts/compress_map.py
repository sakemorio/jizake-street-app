from PIL import Image
import os

SRC = os.path.join(os.path.dirname(__file__), "..", "assets", "venue-map-original.png")
OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "venue-map.png")

MAX_WIDTH = 1600  # スマホでの拡大表示に十分な解像度

img = Image.open(SRC).convert("RGB")
w, h = img.size
if w > MAX_WIDTH:
    ratio = MAX_WIDTH / w
    img = img.resize((MAX_WIDTH, int(h * ratio)), Image.LANCZOS)

# 文字がにじまないよう、PNG + パレット量子化で圧縮（JPEGのブロックノイズを避ける）
quantized = img.quantize(colors=256, method=Image.MEDIANCUT)
quantized.save(OUT, optimize=True)

print("resized to:", img.size)
print("output bytes:", os.path.getsize(OUT))
