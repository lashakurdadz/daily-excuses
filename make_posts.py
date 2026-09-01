#!/usr/bin/env python3
"""
Renderer for the meme page: black text on white, Poppins, justified,
1080x1080. Reads lines from a CSV (id,text,...) and writes PNGs.

Usage:
  python3 make_posts.py lines.csv outdir [--font light|regular] [--only ID]
"""
import csv, os, sys
from PIL import Image, ImageDraw, ImageFont

W = H = 1080
MARGIN_X = 84
MARGIN_TOP = 96
MARGIN_BOT = 96
LINE_SPACING = 1.62          # multiple of font size
MAX_SIZE = 148
MIN_SIZE = 54
FONTS = {
    "light":   "/usr/share/fonts/truetype/google-fonts/Poppins-Light.ttf",
    "regular": "/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf",
    "medium":  "/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf",
}

def stylize(text):
    # the page's signature: acute accent instead of apostrophe, all lowercase
    return text.replace("'", "´").replace("’", "´").lower()

def wrap(words, font, max_w, draw):
    """greedy wrap; returns list of word-lists"""
    lines, cur = [], []
    for w in words:
        test = " ".join(cur + [w])
        if draw.textlength(test, font=font) <= max_w or not cur:
            cur.append(w)
        else:
            lines.append(cur)
            cur = [w]
    if cur:
        lines.append(cur)
    return lines

def layout(text, font_path, draw):
    """largest font size whose wrapped block fits the box"""
    words = text.split()
    max_w = W - 2 * MARGIN_X
    max_h = H - MARGIN_TOP - MARGIN_BOT
    for size in range(MAX_SIZE, MIN_SIZE - 1, -2):
        font = ImageFont.truetype(font_path, size)
        # no single word may exceed the width
        if any(draw.textlength(w, font=font) > max_w for w in words):
            continue
        lines = wrap(words, font, max_w, draw)
        block_h = (len(lines) - 1) * size * LINE_SPACING + size * 1.05
        if block_h <= max_h:
            return font, size, lines
    raise ValueError(f"cannot fit: {text!r}")

def render(text, font_path, out_path):
    img = Image.new("RGB", (W, H), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    font, size, lines = layout(stylize(text), font_path, draw)
    max_w = W - 2 * MARGIN_X
    block_h = (len(lines) - 1) * size * LINE_SPACING + size * 1.05
    y = MARGIN_TOP + (H - MARGIN_TOP - MARGIN_BOT - block_h) / 2
    for i, line_words in enumerate(lines):
        last = (i == len(lines) - 1)
        if last or len(line_words) == 1:
            # last line: natural spacing, left-aligned
            draw.text((MARGIN_X, y), " ".join(line_words), font=font, fill=(17, 17, 17))
        else:
            # full justify: distribute leftover width between words
            words_w = sum(draw.textlength(w, font=font) for w in line_words)
            gap = (max_w - words_w) / (len(line_words) - 1)
            x = MARGIN_X
            for w in line_words:
                draw.text((x, y), w, font=font, fill=(17, 17, 17))
                x += draw.textlength(w, font=font) + gap
        y += size * LINE_SPACING
    img.save(out_path, "PNG")

def main():
    csv_path, outdir = sys.argv[1], sys.argv[2]
    weight = "light"
    only = None
    if "--font" in sys.argv:
        weight = sys.argv[sys.argv.index("--font") + 1]
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1]
    os.makedirs(outdir, exist_ok=True)
    font_path = FONTS[weight]
    n = 0
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if only and row["id"] != only:
                continue
            out = os.path.join(outdir, f"{int(row['id']):03d}.png")
            render(row["text"], font_path, out)
            n += 1
    print(f"rendered {n} posts -> {outdir}")

if __name__ == "__main__":
    main()
