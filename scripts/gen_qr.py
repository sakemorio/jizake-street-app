import qrcode
from qrcode.constants import ERROR_CORRECT_H
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
import os

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")
os.makedirs(OUT_DIR, exist_ok=True)
OUT_PATH = os.path.join(OUT_DIR, "qr-card.png")
CHAR_SRC = os.path.join(OUT_DIR, "character-source.png")

URL = "https://sakemorio.github.io/jizake-street-app/"

# ==== 配色（アプリ本体と統一） ====
PAPER = (243, 241, 231, 255)
INDIGO = (34, 69, 107, 255)
INDIGO_DEEP = (20, 48, 74, 255)
HANKO = (184, 65, 46, 255)
LINE = (218, 214, 200, 255)

def recolor_white_bg(img, target=PAPER, threshold=235):
    """キャラクター原画の白い背景（ステッカー状の縁）だけを紙色に置き換える。
    線画・配色はそのまま、背景だけをカードの地の色に馴染ませて「貼った感」を消す。"""
    arr = np.array(img).astype(np.float32)
    rgb, a = arr[..., :3], arr[..., 3]
    is_bg = (rgb.min(axis=-1) >= threshold) & (a > 0)
    arr[..., 0][is_bg] = target[0]
    arr[..., 1][is_bg] = target[1]
    arr[..., 2][is_bg] = target[2]
    return Image.fromarray(arr.astype(np.uint8), "RGBA")

CHARACTER = recolor_white_bg(Image.open(CHAR_SRC).convert("RGBA"))

def fit_character(max_w, max_h):
    """character-source.png をアスペクト比を保ったまま max_w x max_h に収める（線画・配色はそのまま）"""
    w, h = CHARACTER.size
    ratio = min(max_w / w, max_h / h)
    new_size = (max(1, int(w * ratio)), max(1, int(h * ratio)))
    return CHARACTER.resize(new_size, Image.LANCZOS)

def soft_shadow(img, blur, opacity=0.30):
    alpha = img.split()[3]
    shadow = Image.new("L", img.size, 0)
    shadow.paste(alpha, (0, 0))
    shadow = shadow.filter(ImageFilter.GaussianBlur(blur))
    layer = Image.new("RGBA", img.size, (20, 24, 28, 0))
    layer.putalpha(shadow.point(lambda a: int(a * opacity)))
    return layer

FONT_DIR = "C:/Windows/Fonts"
def font(name, size, index=0):
    return ImageFont.truetype(os.path.join(FONT_DIR, name), size, index=index)

title_font = font("BIZ-UDGothicB.ttc", 50)
sub_font = font("YuGothM.ttc", 28)
caption_font = font("BIZ-UDGothicB.ttc", 34)
url_font = font("YuGothR.ttc", 22)

# ==== 1) QRコード本体（クワイエットゾーンを広めにとり、キャラクターが深く重なれるようにする） ====
BORDER = 8
BOX = 12
qr = qrcode.QRCode(error_correction=ERROR_CORRECT_H, box_size=BOX, border=BORDER)
qr.add_data(URL)
qr.make(fit=True)
qr_img = qr.make_image(fill_color=INDIGO, back_color=PAPER).convert("RGBA")
qr_size = qr_img.size[0]
quiet = BORDER * BOX  # クワイエットゾーンの実ピクセル幅（この範囲は実データが一切ないので自由に重ねられる）

# ==== 2) カード全体を組み立てる（縦一列。キャラクターはQR上端のクワイエットゾーンに深く沈めて“一体化”させる） ====
PAD = 90
TOP_H = 150
FOOTER_H = 190

top_char = fit_character(int(qr_size * 0.42), int(qr_size * 0.42))
OVERLAP = min(int(top_char.height * 0.52), int(quiet * 0.92))  # 実データ領域には絶対に掛からない範囲で深めに沈める

CARD_W = qr_size + PAD * 2
CARD_H = TOP_H + (top_char.height - OVERLAP) + qr_size + FOOTER_H

card = Image.new("RGBA", (CARD_W, CARD_H), PAPER)
draw = ImageDraw.Draw(card)

# 外枠
draw.rectangle([14, 14, CARD_W - 15, CARD_H - 15], outline=INDIGO, width=4)
draw.rectangle([26, 26, CARD_W - 27, CARD_H - 27], outline=LINE, width=2)

# タイトル
title = "地酒ストリート2026"
tw = draw.textlength(title, font=title_font)
draw.text(((CARD_W - tw) / 2, 40), title, font=title_font, fill=INDIGO_DEEP)
sub = "清水駅前銀座商店街"
sw = draw.textlength(sub, font=sub_font)
draw.text(((CARD_W - sw) / 2, 104), sub, font=sub_font, fill=(91, 101, 112, 255))

# QR配置
qr_x = PAD
qr_y = TOP_H + (top_char.height - OVERLAP)
card.alpha_composite(qr_img, (qr_x, qr_y))

# 「日本酒くん」：QR上端のクワイエットゾーンに深く沈める。背景を紙色に馴染ませた上で、
# 影をQRの余白に落として“のっている”接地感を出す（実データ領域には一切重ねない）
top_x = qr_x + (qr_size - top_char.width) // 2
top_y = qr_y - top_char.height + OVERLAP
shadow_top = soft_shadow(top_char, blur=14, opacity=0.22)
card.alpha_composite(shadow_top, (top_x + 5, top_y + 12))
card.alpha_composite(top_char, (top_x, top_y))

# キャプション
cap = "QRを読み込んでアプリをチェック！"
cw = draw.textlength(cap, font=caption_font)
draw.text(((CARD_W - cw) / 2, qr_y + qr_size + 24), cap, font=caption_font, fill=HANKO)

url_text = URL.replace("https://", "")
uw = draw.textlength(url_text, font=url_font)
draw.text(((CARD_W - uw) / 2, qr_y + qr_size + 76), url_text, font=url_font, fill=(91, 101, 112, 255))

note = "9/13(日) 12:00〜17:00"
nw = draw.textlength(note, font=url_font)
draw.text(((CARD_W - nw) / 2, qr_y + qr_size + 110), note, font=url_font, fill=(91, 101, 112, 255))

card.convert("RGB").save(OUT_PATH, "PNG")
print("saved:", OUT_PATH, card.size, "qr_size:", qr_size, "quiet:", quiet, "overlap:", OVERLAP)
