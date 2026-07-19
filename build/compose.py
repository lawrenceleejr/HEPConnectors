"""Trim, compose (family strips), and export webp data-URI-ready images."""
import sys, pathlib, base64, json
from PIL import Image

SRC = pathlib.Path(sys.argv[1])   # renders dir
OUT = pathlib.Path(sys.argv[2]); OUT.mkdir(exist_ok=True)

def trim(im, pad=14):
    bbox = im.getchannel('A').getbbox()
    if not bbox: return im
    l, t, r, b = bbox
    return im.crop((max(0, l-pad), max(0, t-pad), min(im.width, r+pad), min(im.height, b+pad)))

def load(name):
    return trim(Image.open(SRC / f'{name}.png').convert('RGBA'))

def strip(names, heights=None, gap=26):
    """side-by-side composite, aligned on baseline"""
    ims = [load(n) for n in names]
    if heights:  # relative visual heights
        H = 300
        ims = [im.resize((int(im.width*(H*h)/im.height), int(H*h))) for im, h in zip(ims, heights)]
    tot_w = sum(im.width for im in ims) + gap*(len(ims)-1)
    H = max(im.height for im in ims)
    sheet = Image.new('RGBA', (tot_w, H), (0,0,0,0))
    x = 0
    for im in ims:
        sheet.paste(im, (x, H - im.height), im)
        x += im.width + gap
    return sheet

def save(im, name, maxw=880):
    if im.width > maxw:
        im = im.resize((maxw, int(im.height*maxw/im.width)), Image.LANCZOS)
    im.save(OUT / f'{name}.webp', 'WEBP', quality=82, method=6)

cfg = json.load(open(sys.argv[3]))
for name, spec in cfg.items():
    if isinstance(spec, str):
        save(load(spec), name)
    else:
        save(strip(spec['names'], spec.get('heights'), spec.get('gap', 26)), name, spec.get('maxw', 880))
    print(name)
