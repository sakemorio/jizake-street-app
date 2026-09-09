import qrcode
from qrcode.constants import ERROR_CORRECT_H
from PIL import Image, ImageDraw, ImageFont
import os

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")
os.makedirs(OUT_DIR, exist_ok=True)
OUT_PATH = os.path.join(OUT_DIR, "qr-card.png")

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

# ==== 2) QR中央に小さな「酒くん」ロゴを重ねる（円形の背景であまり大きくしない） ====
def draw_bottle_face(draw, cx, cy, w, h, body_color=INDIGO, line_color=PAPER, blush=True, heart=False):
    """オリジナルの「お酒くん」キャラクター（瓶＋顔）を描く。公式イラストの模写ではない独自デザイン。"""
    neck_w = w * 0.34
    neck_h = h * 0.22
    body_top = cy - h / 2 + neck_h
    body_bottom = cy + h / 2
    body_left = cx - w / 2
    body_right = cx + w / 2

    # 首
    draw.rounded_rectangle(
        [cx - neck_w / 2, cy - h / 2, cx + neck_w / 2, body_top + h * 0.06],
        radius=neck_w * 0.25, fill=body_color
    )
    # キャップ
    cap_w = neck_w * 0.9
    draw.rounded_rectangle(
        [cx - cap_w / 2, cy - h / 2 - h * 0.07, cx + cap_w / 2, cy - h / 2 + h * 0.05],
        radius=cap_w * 0.3, fill=line_color
    )
    # 本体
    draw.rounded_rectangle(
        [body_left, body_top, body_right, body_bottom],
        radius=w * 0.22, fill=body_color
    )
    # 顔（目・口）
    eye_r = w * 0.045
    eye_y = body_top + (body_bottom - body_top) * 0.42
    draw.ellipse([cx - w * 0.16 - eye_r, eye_y - eye_r, cx - w * 0.16 + eye_r, eye_y + eye_r], fill=line_color)
    draw.ellipse([cx + w * 0.16 - eye_r, eye_y - eye_r, cx + w * 0.16 + eye_r, eye_y + eye_r], fill=line_color)
    smile_w = w * 0.22
    smile_y = eye_y + h * 0.12
    draw.arc([cx - smile_w / 2, smile_y - smile_w / 4, cx + smile_w / 2, smile_y + smile_w / 2],
              start=20, end=160, fill=line_color, width=max(2, int(w * 0.02)))
    if blush:
        blush_r = w * 0.035
        blush_y = eye_y + h * 0.05
        for sign in (-1, 1):
            bx = cx + sign * w * 0.26
            draw.ellipse([bx - blush_r, blush_y - blush_r, bx + blush_r, blush_y + blush_r], fill=HANKO)
    if heart:
        hr = w * 0.09
        hx, hy = cx + w * 0.34, body_top - h * 0.02
        draw.ellipse([hx - hr, hy - hr * 0.6, hx, hy + hr * 0.6], fill=HANKO)
        draw.ellipse([hx, hy - hr * 0.6, hx + hr, hy + hr * 0.6], fill=HANKO)
        draw.polygon([(hx - hr, hy + hr * 0.15), (hx + hr, hy + hr * 0.15), (hx, hy + hr * 1.5)], fill=HANKO)


logo_d = int(qr_size * 0.30)  # QR幅の30%の円（誤り訂正H=最大約30%まで復元可能なため十分安全なマージンを確保）
logo_layer = Image.new("RGBA", (logo_d, logo_d), (0, 0, 0, 0))
ld = ImageDraw.Draw(logo_layer)
ld.ellipse([0, 0, logo_d, logo_d], fill=PAPER, outline=INDIGO, width=max(3, logo_d // 22))
draw_bottle_face(ld, logo_d / 2, logo_d / 2 + logo_d * 0.03, logo_d * 0.5, logo_d * 0.62, blush=True, heart=False)
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

# 大きい「お酒くん」キャラクターは右側の専用パネル内（QRとは重ならない）に縦centerで配置
panel_cx = qr_x + qr_size + CHAR_PANEL_W / 2
panel_cy = qr_y + qr_size / 2
char_layer = Image.new("RGBA", (CHAR_PANEL_W, qr_size), (0, 0, 0, 0))
cd = ImageDraw.Draw(char_layer)
draw_bottle_face(cd, CHAR_PANEL_W / 2, qr_size / 2, CHAR_PANEL_W * 0.62, qr_size * 0.34, blush=True, heart=True)
card.alpha_composite(char_layer, (qr_x + qr_size, qr_y))

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
