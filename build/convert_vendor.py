import cascadio, pathlib, sys, json
src = pathlib.Path('cad/vendor'); dst = pathlib.Path('cad/all')
ok, bad = [], []
for f in sorted(list(src.glob('*.st*p')) + list(src.glob('*.STEP')) + list(src.glob('*.STP'))):
    head = f.read_bytes()[:200]
    if b'ISO-10303-21' not in head:
        bad.append((f.name, 'not STEP')); continue
    out = dst / ('v_' + f.stem.replace('.', '_') + '.glb')
    try:
        cascadio.step_to_glb(str(f), str(out), tol_linear=0.05, tol_angular=0.3)
        ok.append((f.name, out.name, out.stat().st_size))
    except Exception as e:
        bad.append((f.name, str(e)[:80]))
print(json.dumps({'ok': ok, 'bad': bad}, indent=1))
