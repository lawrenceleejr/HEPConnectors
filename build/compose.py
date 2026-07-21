"""Trim, true-scale (within section), compose strips, export webp.

Usage: python3 compose.py <renders_dir> <out_dir> <webp_cfg.json>
Reads model_mm.json (real max dimension per model, mm). Every card image is
scaled so that, within its poster section, displayed size is proportional to
physical size (floor 0.12 so tiny parts stay legible; true size is printed on
the card tag from cardmm.json).
"""
import sys, pathlib, json
from PIL import Image

SRC = pathlib.Path(sys.argv[1])
OUT = pathlib.Path(sys.argv[2]); OUT.mkdir(exist_ok=True)
cfg = json.load(open(sys.argv[3]))
MM = json.load(open('model_mm.json'))

SECTION = {
 1: ['bnc','sma','smb','mcx','n','tnc','lemo','smp','f_type','uhf','din716','twinbnc','ufl'],
 2: ['shv','mhv','triax','radiall','redel'],
 3: ['lc','lclc','sc','st','fc','e2000','mu','mtpfam','mt_ferrule','splice'],
 4: ['rj45','rj11','sfp','qsfp','dac','m12'],
 5: ['din41612','nim_conn','atca_zone2','amc_edge','fmc'],
 6: ['usb_a','usb_b','usb_mini','usb_micro','usbc','usb3fam','firewire',
     'db9','db25','db37','hd15','gpib','idc','pinheader','dip','button'],
 7: ['sata','sas','minisas','ide40','m2'],
 8: ['hdmi','dp','dvi'],
 9: ['rca','jack','toslink','xlr','banana','barrel','iec','c19','minifit',
     'matenlok','microfit','powerpole'],
 10: ['firefly','vtrx','df57'],
}
SEC_OF = {slug: s for s, slugs in SECTION.items() for slug in slugs}
FLOOR = 0.2
BASE = 800   # px given to the largest card in a section

def members(spec):
    return [spec] if isinstance(spec, str) else spec['names']

def card_mm(spec):
    return max(MM.get(m, 20.0) for m in members(spec))

sec_max = {}
for slug, spec in cfg.items():
    s = SEC_OF.get(slug, 0)
    sec_max[s] = max(sec_max.get(s, 1.0), card_mm(spec))

def trim(im, pad=14):
    hard = im.getchannel('A').point(lambda a: 255 if a > 80 else 0)
    bbox = hard.getbbox()
    if not bbox: return im
    l, t, r, b = bbox
    return im.crop((max(0, l-pad), max(0, t-pad), min(im.width, r+pad), min(im.height, b+pad)))

def load(name):
    return trim(Image.open(SRC / f'{name}.png').convert('RGBA'))

def scaled(name, ref_mm):
    im = load(name)
    ratio = max(MM.get(name, 20.0) / ref_mm, FLOOR)
    target = max(1, int(BASE * ratio))
    f = target / max(im.size)
    return im.resize((max(1, int(im.width*f)), max(1, int(im.height*f))), Image.LANCZOS)

# canvas matches the .art box aspect so object-fit:contain keeps true scale
WIDE = {'mtpfam','din41612','usb3fam','db9','db25','db37','hd15','hdmi'}
CANVAS = {False: (880, 509), True: (880, 255)}   # 128/74 and 200/58
PAD = 26

sheets = {}
for slug, spec in cfg.items():
    s = SEC_OF.get(slug, 0)
    ref = sec_max.get(s, 60.0)
    ims = [scaled(m, ref) for m in members(spec)]
    gap = 24 if len(ims) > 1 else 0
    W = sum(i.width for i in ims) + gap*(len(ims)-1)
    H = max(i.height for i in ims)
    sheet = Image.new('RGBA', (max(W,1), max(H,1)), (0,0,0,0))
    x = 0
    for im in ims:
        sheet.paste(im, (x, H - im.height), im)
        x += im.width + gap
    sheets[slug] = sheet

# uniform per-section shrink so the largest sheet fits its canvas (scale stays true)
shrink = {}
for slug, sheet in sheets.items():
    cw, ch = CANVAS[slug in WIDE]
    f = min((cw - 2*PAD) / sheet.width, (ch - 2*PAD) / sheet.height, 1.0)
    s = SEC_OF.get(slug, 0)
    shrink[s] = min(shrink.get(s, 1.0), f)

MIN_W = 300   # px on the 880 canvas: legibility floor after section shrink
card_out = {}
for slug, spec in cfg.items():
    sheet = sheets[slug]
    k = shrink[SEC_OF.get(slug, 0)]
    cw0, ch0 = CANVAS[slug in WIDE]
    if sheet.width * k < MIN_W:
        k = min(MIN_W / sheet.width, (cw0 - 2*PAD) / sheet.width, (ch0 - 2*PAD) / sheet.height)
    if abs(k - 1.0) > 1e-9:
        sheet = sheet.resize((max(1, int(sheet.width*k)), max(1, int(sheet.height*k))), Image.LANCZOS)
    cw, ch = CANVAS[slug in WIDE]
    canvas = Image.new('RGBA', (cw, ch), (0, 0, 0, 0))
    canvas.paste(sheet, ((cw - sheet.width)//2, ch - sheet.height - PAD//2), sheet)
    canvas.save(OUT / f'{slug}.webp', 'WEBP', quality=82, method=6)
    card_out[slug] = card_mm(spec)
    print(slug)

json.dump(card_out, open('cardmm.json','w'), indent=1)
