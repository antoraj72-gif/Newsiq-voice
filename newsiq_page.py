"""Build the private NewsIQ Tamil page (published as a Claude artifact) for one edition.

Usage:
  python3 newsiq_page.py brief_ta.json OUT_DIR --pdf Tamil.pdf --mp3 Voice.mp3 --thumb Thumb_EN.jpg --thumb-ta Thumb_TA.jpg

Writes OUT_DIR/index.html plus the files it references (voice.mp3, thumb_en.jpg, thumb_ta.jpg,
brief_ta.pdf and one PNG per Tamil PDF page so the brief can be read directly on the page).
Then publish OUT_DIR/index.html with the Artifact tool, passing every other file in OUT_DIR in `files`
({"voice.mp3": "OUT_DIR/voice.mp3", ...}).
"""
import argparse, glob, html, json, os, shutil, subprocess

ap = argparse.ArgumentParser()
ap.add_argument("brief"); ap.add_argument("out")
ap.add_argument("--pdf"); ap.add_argument("--mp3"); ap.add_argument("--thumb"); ap.add_argument("--thumb-ta")
a = ap.parse_args()
d = json.load(open(a.brief, encoding="utf-8"))
os.makedirs(a.out, exist_ok=True)
files = {}
for src, name in ((a.mp3, "voice.mp3"), (a.thumb, "thumb_en.jpg"), (a.thumb_ta, "thumb_ta.jpg"), (a.pdf, "brief_ta.pdf")):
    if src and os.path.exists(src):
        shutil.copy(src, os.path.join(a.out, name)); files[name] = True
pages = []
if files.get("brief_ta.pdf"):
    subprocess.run(["pdftoppm", "-r", "110", "-jpeg", "-jpegopt", "quality=82",
                    os.path.join(a.out, "brief_ta.pdf"), os.path.join(a.out, "page")], check=True)
    pages = sorted(os.path.basename(p) for p in glob.glob(os.path.join(a.out, "page-*.jpg")))

e = html.escape
date, edition = e(d.get("date_label", "")), e(d.get("edition", ""))
heads = "".join(f"<li>{h}</li>" for h in d.get("top_headlines", []))  # already simple <b> markup
audio = ('<section class="card"><h2>தமிழ் குரல் செய்தி</h2><p class="muted">Tamil voice note · male voice · 1.2x</p>'
         '<audio controls preload="metadata" src="voice.mp3"></audio></section>') if files.get("voice.mp3") else \
        '<section class="card"><p>தமிழ் குரல் செய்தி இன்று கிடைக்கவில்லை (Tamil voice note not available today).</p></section>'
thumbs = "".join(f'<figure><img src="{n}" alt="{c}" width="1280" height="720"><figcaption>{c}</figcaption></figure>'
                 for n, c in (("thumb_ta.jpg", "Thumbnail · தமிழ்"), ("thumb_en.jpg", "Thumbnail · English")) if files.get(n))
pdf_pages = "".join(f'<img class="pg" src="{p}" alt="Tamil brief page {i}" loading="lazy">' for i, p in enumerate(pages, 1))

page = f"""<title>NewsIQ தமிழ் · {date}</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+Tamil:wght@400;700&family=Noto+Sans:wght@400;700&display=swap">
<style>
/* Layout: one narrow reading column - player first, then thumbnails, headlines, full Tamil brief pages */
:root {{ --bg:#f5f6f8; --surface:#ffffff; --fg:#1b1f24; --muted:#5b6470; --line:#dde1e6; --accent:#b3261e;
  --body:"Noto Sans Tamil","Noto Sans",system-ui,sans-serif; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --bg:#0f1318; --surface:#171d24; --fg:#eef1f4; --muted:#9aa5b1; --line:#2a333d; --accent:#e5534b; color-scheme: dark }} }}
:root[data-theme="dark"] {{ --bg:#0f1318; --surface:#171d24; --fg:#eef1f4; --muted:#9aa5b1; --line:#2a333d; --accent:#e5534b; color-scheme: dark }}
body {{ background: var(--bg); color: var(--fg); font-family: var(--body); line-height: 1.6;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); padding-block: 20px 40px; }}
main {{ max-width: 760px; margin: 0 auto; display: grid; gap: 20px; }}
header h1 {{ margin: 0; font: 700 1.6rem/1.2 "Noto Sans", sans-serif; letter-spacing: .02em }} header h1 span {{ color: var(--accent) }}
.muted {{ color: var(--muted); margin: 4px 0 0; font-size: .92rem }}
.card {{ background: var(--surface); border: 1px solid var(--line); border-radius: 10px; padding: 16px; }}
h2 {{ margin: 0 0 4px; font-size: 1.15rem; text-wrap: balance }}
audio {{ width: 100%; margin-top: 12px }}
figure {{ margin: 0 }} figure img, .pg {{ width: 100%; height: auto; display: block; border-radius: 8px; border: 1px solid var(--line) }}
figcaption {{ color: var(--muted); font-size: .85rem; margin-top: 6px }}
.thumbs {{ display: grid; gap: 16px }}
ul {{ margin: 8px 0 0; padding-left: 1.2em }} li {{ margin: 6px 0 }}
.pages {{ display: grid; gap: 12px }} .pg {{ background: #fff }}
</style>
<main>
<header><h1>NEWS<span>IQ</span> தமிழ்</h1><p class="muted">{date} · {edition}</p></header>
{audio}
<section class="thumbs">{thumbs}</section>
<section class="card"><h2>முக்கியச் செய்திகள்</h2><ul>{heads}</ul></section>
{('<section><h2>முழு செய்திச் சுருக்கம் (Tamil brief)</h2><p class="muted">Full Tamil PDF, page by page.</p><div class="pages">' + pdf_pages + '</div></section>') if pdf_pages else ''}
<p class="muted">NewsIQ · compiled from live web sources · translated from the verified English brief.</p>
</main>
"""
open(os.path.join(a.out, "index.html"), "w", encoding="utf-8").write(page)
others = sorted(f for f in os.listdir(a.out) if f != "index.html")
print(json.dumps({"index": os.path.join(a.out, "index.html"),
                  "files": {f: os.path.join(os.path.abspath(a.out), f) for f in others}}, ensure_ascii=False))
