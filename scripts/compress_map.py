from PIL import Image
import os

ASSETS = os.path.join(os.path.dirname(__file__), "..", "assets")
OUT_PNG = os.path.join(ASSETS, "venue-map.png")
OUT_JPG = os.path.join(ASSETS, "venue-map.jpg")

MAX_WIDTH = 1600  # スマホでの拡大表示に十分な解像度

# venue-map-original.jpg / .png のどちらでも受け付ける
# （新しい地図画像に差し替える際は、拡張子を気にせずこのどちらかの名前で置けばよい）
SRC = None
for ext in ("jpg", "jpeg", "png"):
    candidate = os.path.join(ASSETS, f"venue-map-original.{ext}")
    if os.path.exists(candidate):
        SRC = candidate
        break
if SRC is None:
    raise SystemExit("assets/venue-map-original.jpg（または .png）が見つかりません。")

img = Image.open(SRC).convert("RGB")
w, h = img.size
if w > MAX_WIDTH:
    ratio = MAX_WIDTH / w
    img = img.resize((MAX_WIDTH, int(h * ratio)), Image.LANCZOS)

# PNG（パレット256色）: 文字がにじまないが、写真的な階調が多い画像では逆に肥大化する場合がある
img.quantize(colors=256, method=Image.MEDIANCUT).save(OUT_PNG, optimize=True)
png_size = os.path.getsize(OUT_PNG)

# JPEG（品質85）: 階調が多い画像で有利。文字周りはやや甘くなるが実用上問題ないレベル
img.save(OUT_JPG, quality=85, optimize=True)
jpg_size = os.path.getsize(OUT_JPG)

print(f"resized to: {img.size}")
print(f"PNG : {png_size:,} bytes")
print(f"JPEG: {jpg_size:,} bytes")

if png_size <= jpg_size:
    os.remove(OUT_JPG)
    print("-> PNG を採用: assets/venue-map.png")
else:
    os.remove(OUT_PNG)
    print("-> JPEG を採用: assets/venue-map.jpg")
