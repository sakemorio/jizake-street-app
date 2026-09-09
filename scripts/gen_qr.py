import qrcode
from qrcode.constants import ERROR_CORRECT_H
from PIL import Image, ImageDraw, ImageFont
import os

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")
os.makedirs(OUT_DIR, exist_ok=True)
OUT_PATH = os.path.join(OUT_DIR, "qr-card.png")
CHAR_SRC = os.path.join(OUT_DIR, "character-source.png")

URL = "https://sakemorio.github.io/jizake-street-app/"

CHARACTER = Image.open(CHAR_SRC).convert("RGBA")

def fit_character(max_w, max_h):
    """character-source.png をアスペクト比を保ったまま max_w x max_h に収める（原画そのまま、描き直しなし）"""
    w, h = CHARACTER.size
    ratio = min(max_w / w, max_h / h)
    new_size = (max(1, int(w * ratio)), max(1, int(h * ratio)))
    return CHARACTER.resize(new_size, Image.LANCZOS)

# ==== 配色（アプリ本体と統一） ====
PAPER = (243, 241, 231, 255)
INDIGO = (34, 69, 107, 255)
INDIGO_DEEP = (20, 48, 74, 255)
HANKO = (184, 65, 46, 255)
LINE = (218, 214, 200, 255)
WHITE = (255, 255, 255, 255)

FONT_DIR = "C:/Windows/Fonts"
def font(name, size, index=0):
    return ImageFont.truetype(os.path.join(FONT_DIR, name), size, index=index)

title_font = font("BIZ-UDGothicB.ttc", 54)
sub_font = font("YuGothM.ttc", 30)
caption_font = font("BIZ-UDGothicB.ttc", 34)
url_font = font("YuGothR.ttc", 22)

# ==== 1) QRコード本体を生成（誤り訂正レベルH＝中央に小さなロゴを置いても読める） ====
qr = qrcode.QRCode(error_correction=ERROR_CORRECT_H, box_size=12, border=2)
qr.add_data(URL)
qr.make(fit=True)
qr_img = qr.make_image(fill_color=INDIGO, back_color=PAPER).convert("RGBA")
qr_size = qr_img.size[0]

# ==== 2) QR中央に「日本酒くん」ロゴ（原画）を重ねる（円形の背景であまり大きくしない） ====
logo_d = int(qr_size * 0.30)  # QR幅の30%の円（誤り訂正H=最大約30%まで復元可能なため十分安全なマージンを確保）
logo_layer = Image.new("RGBA", (logo_d, logo_d), (0, 0, 0, 0))
ld = ImageDraw.Draw(logo_layer)
ld.ellipse([0, 0, logo_d, logo_d], fill=PAPER, outline=INDIGO, width=max(3, logo_d // 22))
logo_char = fit_character(int(logo_d * 0.82), int(logo_d * 0.82))
lc_x = (logo_d - logo_char.width) // 2
lc_y = (logo_d - logo_char.height) // 2
logo_layer.alpha_composite(logo_char, (lc_x, lc_y))
qr_img.alpha_composite(logo_layer, ((qr_size - logo_d) // 2, (qr_size - logo_d) // 2))

# ==== 3) カード全体を組み立てる ====
# キャラクターはQRの実データ領域には一切重ねない（右側に専用スペースを確保して配置する）
PAD = 90
CHAR_PANEL_W = 170
CARD_W = PAD + qr_size + CHAR_PANEL_W
HEADER_H = 190
FOOTER_H = 230
CARD_H = HEADER_H + qr_size + FOOTER_H

card = Image.new("RGBA", (CARD_W, CARD_H), PAPER)
draw = ImageDraw.Draw(card)

# 外枠
draw.rectangle([14, 14, CARD_W - 15, CARD_H - 15], outline=INDIGO, width=4)
draw.rectangle([26, 26, CARD_W - 27, CARD_H - 27], outline=LINE, width=2)

# タイトル
title = "地酒ストリート2026"
tw = draw.textlength(title, font=title_font)
draw.text(((CARD_W - tw) / 2, 46), title, font=title_font, fill=INDIGO_DEEP)
sub = "清水駅前銀座商店街"
sw = draw.textlength(sub, font=sub_font)
draw.text(((CARD_W - sw) / 2, 118), sub, font=sub_font, fill=(91, 101, 112, 255))

# QR配置
qr_x = PAD
qr_y = HEADER_H
card.alpha_composite(qr_img, (qr_x, qr_y))

# 大きい「日本酒くん」（原画）は右側の専用パネル内（QRとは重ならない）に縦centerで配置
big_char = fit_character(int(CHAR_PANEL_W * 0.92), int(qr_size * 0.55))
bx = qr_x + qr_size + (CHAR_PANEL_W - big_char.width) // 2
by = qr_y + (qr_size - big_char.height) // 2
card.alpha_composite(big_char, (bx, by))

# キャプション
cap = "QRを読み込んでアプリをチェック！"
cw = draw.textlength(cap, font=caption_font)
draw.text(((CARD_W - cw) / 2, qr_y + qr_size + 26), cap, font=caption_font, fill=HANKO)

url_text = URL.replace("https://", "")
uw = draw.textlength(url_text, font=url_font)
draw.text(((CARD_W - uw) / 2, qr_y + qr_size + 78), url_text, font=url_font, fill=(91, 101, 112, 255))

note = "9/13(日) 12:00〜17:00"
nw = draw.textlength(note, font=url_font)
draw.text(((CARD_W - nw) / 2, qr_y + qr_size + 112), note, font=url_font, fill=(91, 101, 112, 255))

card.convert("RGB").save(OUT_PATH, "PNG")
print("saved:", OUT_PATH, card.size)
