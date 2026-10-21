"""NewsIQ thumbnail card (1280x720 JPEG) from a brief JSON (English or Tamil).

Usage:  python3 newsiq_thumb.py brief.json NewsIQ_Thumb.jpg

Uses the lead story (stories[0]: cat, headline, developing) as the big headline, a topic icon on the
right, and the next three top_headlines as a strip below. No photos.
Icon: stories[0]["icon"] if set (a file name in icons/, e.g. "cloud-rain"), else picked from keywords in
the headline (English or Tamil), else the category default. Icons: Tabler Icons (MIT licence).
Needs Pillow with raqm (Tamil shaping), cairosvg, and fonts/NewsIQTamil-*.ttf next to this script.
"""
import json, os, re, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FR = os.path.join(HERE, "fonts", "NewsIQTamil-Regular.ttf")
FB = os.path.join(HERE, "fonts", "NewsIQTamil-Bold.ttf")
W, H, M = 1280, 720, 64
BG, PANEL, INK, MUTED, RED = "#11161c", "#1a212a", "#ffffff", "#9aa5b1", "#d0342c"
CAT = {"INDIA": "#2f6db3", "TAMIL NADU": "#11986b", "KONGU REGION": "#11986b", "BUSINESS": "#b07a12",
       "MARKETS": "#b07a12", "WORLD": "#6a5acd", "HEALTH": "#c03a78", "TECH & AI": "#2389b5",
       "AUTO": "#6b7280", "CONSUMER ELECTRONICS": "#6b7280", "SPORTS": "#2e9447", "WAR": "#a32020",
       "POLITICS": "#2f6db3"}
CAT_TA = {"INDIA": "இந்தியா", "TAMIL NADU": "தமிழ்நாடு", "KONGU REGION": "கொங்கு மண்டலம்", "BUSINESS": "வணிகம்",
          "MARKETS": "பங்குச் சந்தை", "WORLD": "உலகம்", "HEALTH": "சுகாதாரம்", "TECH & AI": "தொழில்நுட்பம் & AI",
          "AUTO": "வாகனம்", "CONSUMER ELECTRONICS": "மின்சாதனங்கள்", "SPORTS": "விளையாட்டு", "WAR": "போர்",
          "POLITICS": "அரசியல்"}

ICON_DEFAULT = {"INDIA": "flag", "TAMIL NADU": "map-pin", "KONGU REGION": "map-pin", "BUSINESS": "briefcase",
                "MARKETS": "chart-candle", "WORLD": "world", "HEALTH": "stethoscope", "TECH & AI": "cpu",
                "AUTO": "car", "CONSUMER ELECTRONICS": "air-conditioning", "SPORTS": "trophy", "WAR": "shield",
                "POLITICS": "scale"}
ICON_WORDS = [  # (icon, keywords - English lower-case or Tamil)
    ("id", ["voter", "electoral", "election", "ballot", "வாக்காள", "தேர்தல்"]),
    ("cloud-storm", ["cyclone", "storm", "புயல்"]),
    ("cloud-rain", ["rain", "flood", "monsoon", "மழை", "வெள்ள"]),
    ("thermometer", ["heatwave", "heat wave", "temperature", "வெப்ப"]),
    ("gas-station", ["crude", "oil", "petrol", "diesel", "brent", "எண்ணெய்", "பெட்ரோல்"]),
    ("chart-candle", ["sensex", "nifty", "ipo", "shares", "stock", "market", "சென்செக்ஸ்", "நிஃப்டி", "பங்கு"]),
    ("coin-rupee", ["rupee", "inflation", "rbi", "ரூபாய்", "பணவீக்க"]),
    ("gavel", ["court", "verdict", "judge", "நீதிமன்ற", "தீர்ப்பு"]),
    ("virus", ["ebola", "virus", "outbreak", "covid", "dengue", "வைரஸ்", "எபோலா", "டெங்கு"]),
    ("vaccine", ["vaccine", "தடுப்பூசி"]),
    ("cricket", ["cricket", "t20", "odi", "test match", "ipl", "ranji", "கிரிக்கெட்", "இருபது ஓவர்"]),
    ("ball-football", ["football", "fifa", "கால்பந்து"]),
    ("charging-pile", ["electric vehicle", "electric car", " ev ", "ev ", "மின்சார வாகன", "மின்சார கார்"]),
    ("robot", [" ai ", "artificial intelligence", "ai agent", "chatbot", "செயற்கை நுண்ணறிவு"]),
    ("plane", ["airport", "flight", "airline", "விமான"]),
    ("train", ["railway", "metro", "train", "ரயில்", "மெட்ரோ"]),
    ("school", ["school", "exam", "students", "பள்ளி", "தேர்வு", "மாணவ"]),
    ("tank", ["war", "military", "missile", "strike", "போர்", "ராணுவ"]),
    ("world", ["peace", "summit", "diplomat", "envoy", "அமைதி", "தூதர்"]),
]

def pick_icon(story):
    if story.get("icon"):
        return story["icon"]
    text = " " + plain(story.get("headline", "")).lower() + " "
    for icon, words in ICON_WORDS:
        if any(w in text for w in words):
            return icon
    return ICON_DEFAULT.get(story.get("cat", ""), "news")

def draw_icon(img, name, cx, cy, size, color):
    import io, cairosvg
    path = os.path.join(HERE, "icons", name + ".svg")
    if not os.path.exists(path):
        path = os.path.join(HERE, "icons", "news.svg")
    svg = open(path, encoding="utf-8").read().replace("currentColor", color)
    png = cairosvg.svg2png(bytestring=svg.encode(), output_width=size, output_height=size)
    ic = Image.open(io.BytesIO(png)).convert("RGBA")
    img.paste(ic, (int(cx - size / 2), int(cy - size / 2)), ic)

def font(path, size):
    return ImageFont.truetype(path, size, layout_engine=ImageFont.Layout.RAQM)

def plain(s):
    return re.sub(r"<[^>]+>", "", s or "").replace("&amp;", "&").replace("&nbsp;", " ").strip()

def wrap(d, text, f, width, max_lines):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= width:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        while d.textlength(lines[-1] + "…", font=f) > width and " " in lines[-1]:
            lines[-1] = lines[-1].rsplit(" ", 1)[0]
        lines[-1] += "…"
    return lines

def chip(d, x, y, text, color, f):
    w = d.textlength(text, font=f)
    d.rounded_rectangle([x, y, x + w + 28, y + 44], radius=8, fill=color)
    d.text((x + 14, y + 22), text, font=f, fill=INK, anchor="lm")
    return x + w + 28 + 12

def make(data, out):
    ta = data.get("lang") == "ta"
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 10], fill=RED)
    # masthead
    fm = font(FB, 40)
    d.text((M, 62), "NEWS", font=fm, fill=INK, anchor="ls")
    x = M + d.textlength("NEWS", font=fm)
    d.text((x, 62), "IQ", font=fm, fill=RED, anchor="ls")
    x += d.textlength("IQ", font=fm)
    d.text((x + 12, 62), "BRIEF", font=fm, fill=INK, anchor="ls")
    fs = font(FR, 24)
    sub = f"{data.get('date_label', '')}  ·  {data.get('edition', '')}"
    d.text((W - M, 62), sub if d.textlength(sub, font=fs) < 640 else data.get("date_label", ""),
           font=fs, fill=MUTED, anchor="rs")
    d.line([M, 88, W - M, 88], fill="#2b3440", width=2)
    # lead story
    s = (data.get("stories") or [{}])[0]
    cat = s.get("cat", "INDIA")
    fc = font(FB, 22)
    cx = chip(d, M, 118, CAT_TA.get(cat, cat) if ta else cat, CAT.get(cat, "#6b7280"), fc)
    if s.get("developing"):
        chip(d, cx, 118, "தொடரும் செய்தி" if ta else "DEVELOPING", RED, fc)
    head = plain(s.get("headline") or (data.get("top_headlines") or [""])[0])
    # topic icon in a circle on the right
    R, icx, icy = 128, W - M - 128, 300
    col = CAT.get(cat, "#6b7280")
    d.ellipse([icx - R, icy - R, icx + R, icy + R], fill="#1c2632", outline=col, width=6)
    draw_icon(img, pick_icon(s), icx, icy, 150, "#ffffff")
    tw = W - 2 * M - 2 * R - 40
    size, lh = (52, 1.45) if ta else (58, 1.18)
    fh = font(FB, size)
    lines = wrap(d, head, fh, tw, 4 if ta else 4)
    while lines and lines[-1].endswith("…") and size > 40:
        size -= 4; fh = font(FB, size); lines = wrap(d, head, fh, tw, 4)
    y = 186
    for ln in lines:
        d.text((M, y), ln, font=fh, fill=INK, anchor="la"); y += int(size * lh)
    # secondary headlines
    rest = [plain(h) for h in (data.get("top_headlines") or [])][1:4]
    if rest:
        top = max(y + 24, 470)
        d.rectangle([0, top, W, H], fill=PANEL)
        d.rectangle([0, top, 8, H], fill=RED)
        fr = font(FR, 25 if ta else 27)
        yy = top + 26
        step = int((H - top - 40) / max(len(rest), 1))
        for h in rest:
            for ln in wrap(d, h, fr, W - 2 * M - 30, 1):
                d.ellipse([M, yy + 13, M + 10, yy + 23], fill=RED)
                d.text((M + 28, yy), ln, font=fr, fill="#dfe5ec", anchor="la")
            yy += step
    img.save(out, "JPEG", quality=88, optimize=True, progressive=True)

if __name__ == "__main__":
    make(json.load(open(sys.argv[1], encoding="utf-8")), sys.argv[2])
    print("ok", sys.argv[2])
