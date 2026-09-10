from PIL import Image, ImageDraw, ImageFont
import os

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")
os.makedirs(OUT_DIR, exist_ok=True)
OUT_PATH = os.path.join(OUT_DIR, "qr-card.png")
QR_SRC = os.path.join(OUT_DIR, "qr-provided.png")  # ユーザー提供済みのQR（キャラクター埋め込み・スキャン確認済み）

URL = "https://sakemorio.github.io/jizake-street-app/"

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

title_font = font("BIZ-UDGothicB.ttc", 50)
sub_font = font("YuGothM.ttc", 28)
caption_font = font("BIZ-UDGothicB.ttc", 34)
url_font = font("YuGothR.ttc", 22)

# ==== 提供済みのQR画像を読み込む（すでにキャラクター埋め込み・スキャン確認済みなので加工しない） ====
qr_img = Image.open(QR_SRC).convert("RGB")
QR_DISPLAY = 620  # カードに収めるサイズ
qr_img = qr_img.resize((QR_DISPLAY, QR_DISPLAY), Image.LANCZOS)
qr_size = QR_DISPLAY

# ==== カード全体を組み立てる ====
PAD = 90
MOUNT_PAD = 22  # QRの白背景をそのまま活かす「白いマット」の余白
HEADER_H = 190
FOOTER_H = 190
CARD_W = qr_size + PAD * 2
CARD_H = HEADER_H + qr_size + MOUNT_PAD * 2 + FOOTER_H

card = Image.new("RGB", (CARD_W, CARD_H), PAPER)
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

# QRを白い“マット”に載せて、紙色のカードとの境目を自然に見せる
qr_x = PAD
qr_y = HEADER_H
mount_box = [qr_x - MOUNT_PAD, qr_y - MOUNT_PAD, qr_x + qr_size + MOUNT_PAD, qr_y + qr_size + MOUNT_PAD]
draw.rounded_rectangle(mount_box, radius=18, fill=WHITE, outline=LINE, width=2)
card.paste(qr_img, (qr_x, qr_y))

# キャプション
cap_y = qr_y + qr_size + MOUNT_PAD + 30
cap = "QRを読み込んでアプリをチェック！"
cw = draw.textlength(cap, font=caption_font)
draw.text(((CARD_W - cw) / 2, cap_y), cap, font=caption_font, fill=HANKO)

url_text = URL.replace("https://", "")
uw = draw.textlength(url_text, font=url_font)
draw.text(((CARD_W - uw) / 2, cap_y + 52), url_text, font=url_font, fill=(91, 101, 112, 255))

note = "9/13(日) 12:00〜17:00"
nw = draw.textlength(note, font=url_font)
draw.text(((CARD_W - nw) / 2, cap_y + 86), note, font=url_font, fill=(91, 101, 112, 255))

card.save(OUT_PATH, "PNG")
print("saved:", OUT_PATH, card.size)
