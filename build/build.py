#!/usr/bin/env python3
"""Inline the woff2 fonts into poster_template.html -> poster.html"""
import base64, pathlib, re, sys

here = pathlib.Path(__file__).parent
fonts = {
    "ARCHIVO800": "fonts/archivo-800.woff2",
    "ARCHIVO600": "fonts/archivo-600.woff2",
    "PLEXSANS400": "fonts/plexsans-400.woff2",
    "PLEXSANS600": "fonts/plexsans-600.woff2",
    "PLEXMONO400": "fonts/plexmono-400.woff2",
    "PLEXMONO600": "fonts/plexmono-600.woff2",
}
tpl = (here / "poster_template.html").read_text()
for key, rel in fonts.items():
    data = (here / rel).read_bytes()
    b64 = base64.b64encode(data).decode()
    uri = f"data:font/woff2;base64,{b64}"
    tpl = tpl.replace("{{%s}}" % key, uri)

missing = re.findall(r"\{\{[A-Z0-9_]+\}\}", tpl)
if missing:
    print("UNRESOLVED:", set(missing)); sys.exit(1)

out = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else here / "poster.html"
out.write_text(tpl)
print(f"wrote {out} ({len(tpl)} bytes)")
