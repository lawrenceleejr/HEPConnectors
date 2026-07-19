# Connectors of the Particle Physics Lab

A print-ready wall poster / field guide to the connectors of the crate, the rack
and the counting room — every card **rendered in Blender (Cycles) from a CAD
model of the real part**. Male / female shown wherever the gender differs, each
entry has a one-line "what it's for" plus Wikipedia and DigiKey links, and
**colour encodes the signal medium**: copper = electrical, aqua = optical fibre.

| File | What it is |
|------|------------|
| [`poster.html`](poster.html) | The poster — one self-contained HTML file (fonts + WebP renders inlined, no network needed). Adapts to light/dark; prints clean. |
| `poster-light.png` / `poster-dark.png` | High-resolution rendered posters for large-format printing. |
| `build/` | The full reproducible pipeline (see below). |
| `.github/workflows/pages.yml` | Deploys `poster.html` to GitHub Pages on push to `main`. |

## Live page

Once this branch is merged to `main`, the Pages workflow publishes the poster at
the repository's GitHub Pages URL (Settings → Pages must allow GitHub Actions;
the workflow attempts to enable it automatically). Every card links out to
Wikipedia and a DigiKey search; links are hidden in print.

## What's on it

~70 connectors across 10 sections + reference panels:

1. **RF & coaxial** — BNC, SMA, SMB/SMC, MCX/MMCX, N, TNC, LEMO 00, SMP/SMPM, F, UHF/PL-259, 7/16 DIN, Twin-BNC, U.FL
2. **High voltage & multipin** — SHV, MHV, triax, Radiall 52-pin (CAEN A996), REDEL/LEMO multipin
3. **Fibre optic** — LC, LC-duplex, SC, ST, FC, E-2000, MU, MTP/MPO (male / female / APC), bare MT ferrule, fusion splice
4. **Network & pluggables** — RJ45, RJ11, SFP cage, QSFP-DD cage, DAC, M12
5. **Backplanes & crates** — DIN 41612 (VME, M+F), NIM bin connector, ATCA Zone 2, µTCA AMC edge, FMC
6. **Data & instrumentation** — USB A/B/Mini/Micro/C + 3.0 B & Micro-B, FireWire 1394a/b, DB9 (M+F), DB25, DB37, HD-15, GPIB, IDC, 0.1″ headers
7. **Storage** — SATA, SAS, Mini-SAS HD, IDE, M.2
8. **Video** — HDMI A/Mini/Micro, DisplayPort, DVI
9. **Audio & power** — RCA, phone jacks, TOSLINK, XLR, banana, DC barrel, IEC C13/C14 & C19/C20, Mini-Fit, MATE-N-LOK, Micro-Fit, Anderson Powerpole
10. **At the experiments** — Samtec FireFly, VTRx+, Hirose DF57, plus a panel mapping connectors to their ATLAS/CMS roles (TTC on ST, FELIX MTP-24/48, MARATON on DB37, CAEN HV multipin, CMS DTC FireFly links…)

Reference panels: fibre jacket colour code (OM1–OM5, OS1/2), UPC vs APC,
MTP male/female, and field cheats (SHV≠MHV≠BNC, 50 vs 75 Ω, SM ≠ MM).

## How the art is made (`build/`)

Every connector image is a Cycles render of a 3D model, staged identically
(warm key + neutral fill area lights inside an enclosing emissive sphere,
shadow catcher, consistent ¾ camera). Model sources, in order of preference:

1. **KiCad `kicad-packages3D`** (CC-BY-SA) — BNC, SMA, LEMO EPL/EPG, D-subs,
   DIN 41612, HDMI, DVI, USB, RJ45, Samtec FMC, IEC C14, banana, IDC, SATA…
   (`convert_vendor.py`-style raw downloads from GitLab; see `build/cad/vendor/manifest.json`
   for the vendor list.)
2. **Manufacturer STEP** (no-login downloads) — Würth (N, TNC, SMB, RJ11, USB-B,
   M12 M+F, Mini-Fit-class MPC4), Neutrik XLR, NorComp GPIB, Adam Tech
   (DisplayPort, HDMI Mini, SFP & QSFP-DD cages), CLIFF TOSLINK, Same Sky RCA,
   Anderson Powerpole, Qualtek C20. Sources and part numbers:
   `build/cad/vendor/manifest.json`.
3. **Parametric bpy models** (datasheet dimensions) — the fibre family, SHV/MHV/
   triax, HV multipin, pluggable modules, backplane connectors, FireFly, VTRx+,
   and other parts whose CAD is login-gated: `build/build_parametric.py`.

Pipeline (needs `pip install bpy cascadio trimesh pillow`):

```bash
cd build
python3 build_parametric.py cad/param            # parametric models → GLB
# (re-download KiCad/vendor STEP per manifest, convert with convert_vendor.py)
python3 render_connectors.py cad/all renders     # Cycles renders (view_tweaks.json)
python3 compose.py renders webp webp_cfg.json    # trim/compose → WebP
python3 generate_poster.py ../poster.html        # emit self-contained poster
```

Type: **Archivo** (display), **IBM Plex Sans** (body), **IBM Plex Mono**
(labels) — all OFL, embedded in the HTML.

Research notes: the "At the Experiments" section is sourced from the CMS
Tracker Phase-2 TDR ecosystem (VTRx+ application note, Serenity/Apollo specs,
TWEPP proceedings) and ATLAS documentation (opto WG report, ELMB user guide,
FELIX manual, Pixel DCS papers).
