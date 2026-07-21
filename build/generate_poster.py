#!/usr/bin/env python3
"""Generate the self-contained HEP connector poster.

Reads fonts/*.woff2 and webp/<art>.webp, emits a single HTML file with
everything inlined. Usage: python3 generate_poster.py <out.html>
"""
import base64, pathlib, sys, html, json

HERE = pathlib.Path(__file__).parent
WEBP = HERE / 'webp'
FONTS = HERE / 'fonts'

W = 'https://en.wikipedia.org/wiki/'
def dk(q): return 'https://www.digikey.com/en/products/result?keywords=' + q.replace(' ', '%20')

# card: (slug, name, sub, gender('MF'|''|label), desc, tag, ref_url, dk_query_or_None, wide?)
SECTIONS = [
 ('RF & Coaxial — signals, pulses & timing', '50 Ω unless noted', 'cu', [
  ('bnc', 'BNC', '', 'MF',
   'Quarter-turn bayonet lock. The workhorse for scope leads and NIM/detector pulses. Plug & jack shown.',
   '50/75 Ω · bayonet', W+'BNC_connector', 'BNC connector', 0),
  ('sma', 'SMA', '', 'MF',
   'Screw-thread microwave connector to ~18 GHz. Clocks, RF and timing distribution.',
   '50 Ω · threaded', W+'SMA_connector', 'SMA connector', 0),
  ('smb', 'SMB / SMC', '', 'MF',
   'Miniature snap-on (SMB) or threaded (SMC) coax for tight, dense RF wiring.',
   '50 Ω · snap', W+'SMB_connector', 'SMB connector', 0),
  ('mcx', 'MCX / MMCX', '', 'MF',
   'Micro snap coax. Board-edge and on-detector RF where space is scarce.',
   '50 Ω · micro', W+'MCX_connector', 'MMCX connector', 0),
  ('n', 'N-type', '', 'MF',
   'Rugged weatherproof RF to ~11 GHz. Antennas, high-power feeds, long runs. Plug & jack shown.',
   '50/75 Ω · threaded', W+'N_connector', 'N type connector', 0),
  ('tnc', 'TNC', '', 'MF',
   'Threaded BNC. Same size, but the screw coupling shrugs off vibration. Plug & jack shown.',
   '50 Ω · threaded', W+'TNC_connector', 'TNC connector', 0),
  ('lemo', 'LEMO 00', '0S', 'MF',
   'Push-pull self-latching, keyed. The HEP staple — PMTs, front-end & fast NIM timing.',
   'push-pull · NIM', W+'LEMO', 'LEMO 00 connector', 0),
  ('smp', 'SMP / SMPM', '', 'MF',
   'Push-on detent micro-coax to 40 GHz — board-to-board RF links & test fixtures.',
   'push-on · µwave', W+'SMP_connector', 'SMP connector', 0),
  ('f_type', 'F-type', '', 'MF',
   'Threaded CATV coax — the centre pin is the cable’s own conductor. RF monitors & RG-6 runs.',
   '75 Ω · CATV', W+'F_connector', 'F connector', 0),
  ('uhf', 'UHF', 'PL-259', 'MF',
   'Pre-war threaded coax, still on ham gear and older amplifiers. Not actually UHF-worthy.',
   'legacy · ham', W+'UHF_connector', 'PL-259', 0),
  ('din716', '7/16 DIN', '', 'MF',
   'Big high-power RF feeder coupling — transmitters, cavities & accelerator RF.',
   '50 Ω · high power', W+'7/16_DIN_connector', '7/16 DIN connector', 0),
  ('twinbnc', 'Twin-BNC', 'Twinax', 'MF',
   'Two isolated coax paths in one bayonet shell. Differential and balanced pairs.',
   '78/95 Ω · dual', W+'Twinaxial_cabling', 'twinax connector', 0),
  ('ufl', 'U.FL / IPEX', '', 'MF',
   'Tiny snap-on board coax — GPS antennas, clock pickoffs. Rated only ~30 mating cycles.',
   'micro · board', W+'Hirose_U.FL', 'U.FL connector', 0),
 ]),
 ('High Voltage & Multipin', 'label your HV', 'cu', [
  ('shv', 'SHV', '', 'MF',
   'Safe high voltage to ~5 kV — PMT, SiPM & wire-chamber bias. Deep insulator keeps live contacts unreachable. Plug & jack shown.',
   'HV · 5 kV', W+'SHV_connector', 'SHV connector', 0),
  ('mhv', 'MHV', '', 'MF',
   'Older ~3 kV HV that looks like BNC — and half-mates with it. Being retired in favour of SHV.',
   'HV · legacy', W+'MHV_connector', 'MHV connector', 0),
  ('triax', 'Triax', '', 'MF',
   'Signal + guard + shield, three concentric contacts. Guarded low-current & detector bias lines.',
   'guarded · 3-layer', W+'Triaxial_cable', 'triaxial connector', 0),
  ('radiall', 'Radiall 52-pin HV', 'CAEN A996', 'MF',
   '52 HV channels in one keyed shell — the block on CAEN mainframes feeding ATLAS & CMS muon/calo HV.',
   'multipin · 52 ch', 'https://www.caen.it/products/a996/', 'Radiall HV connector', 0),
  ('redel', 'REDEL multipin', 'LEMO K', 'MF',
   'Plastic-shell LEMO multipin — 51-pin option on CAEN floating-return HV & lab DC distribution.',
   'multipin · plastic', W+'LEMO', 'LEMO Redel', 0),
 ]),
 ('Fibre Optic — data & timing over light', 'boot colour ≠ fibre type', 'aq', [
  ('lc', 'LC', '', 'latch',
   'Small-form latching ferrule — the default face of SFP/SFP+ transceivers.',
   '1.25 mm ferrule', W+'Optical_fiber_connector', 'LC fiber connector', 0),
  ('lclc', 'LC-LC duplex', '', '',
   'Clipped LC pair — one fibre transmits, one receives. The clip usually pulls apart into two simplex plugs (one-piece uniboot types don\u2019t).',
   'Tx + Rx pair', W+'Optical_fiber_connector', 'LC duplex cable', 0),
  ('sc', 'SC', '', '',
   'Square push-pull, 2.5 mm ferrule. Rugged datacom & passive-optical trunks.',
   '2.5 mm ferrule', W+'Optical_fiber_connector', 'SC fiber connector', 0),
  ('st', 'ST', '', '',
   'Bayonet twist-lock, keyed. Legacy multimode links — and ATLAS’s TTC timing fan-out.',
   'bayonet · TTC', W+'Optical_fiber_connector', 'ST fiber connector', 0),
  ('fc', 'FC', '', '',
   'Metal screw coupling, keyed. Single-mode, metrology & high-vibration mounts. Panel feedthrough shown.',
   'threaded · SM', W+'Optical_fiber_connector', 'FC fiber connector', 0),
  ('e2000', 'E-2000 / LSH', '', '',
   'Push-pull with a spring-loaded laser-safety shutter. The single-mode staple of CERN’s fibre plant.',
   'shuttered · SM', W+'Optical_fiber_connector', 'E2000 fiber connector', 0),
  ('mu', 'MU', '', '',
   'Half-size push-pull (1.25 mm). Ultra-dense backbone & telecom shelves.',
   'mini ferrule', W+'Optical_fiber_connector', 'MU fiber connector', 0),
  ('mtpfam', 'MTP / MPO', 'male · female · APC', '',
   'Ribbon fibre in one ferrule — male has guide pins, female doesn’t; green = 8° APC. 12/24-fibre trunks, FELIX MTP-24/48, CMS 144-fibre DTC trunks.',
   '12–48 fibre', W+'Multi-fiber_push_on', 'MTP MPO cable', 1),
  ('mt_ferrule', 'MT ferrule', 'MT-8/12/16', '',
   'The bare ribbon ferrule inside MTP — clipped pin-to-pinless in ATLAS SCT/Pixel opto ribbons & VTRx+ pigtails.',
   'ribbon · bare', W+'Optical_fiber_connector', 'MT ferrule', 0),
  ('splice', 'Fusion splice', '', '',
   'Bare fibres welded end-to-end in a protective sleeve. Lowest-loss joints & pigtails.',
   'bare · pigtail', W+'Fusion_splicing', 'fusion splice sleeve', 0),
 ]),
 ('Network & Pluggable Transceivers — DAQ & slow control', 'copper ↔ optical', 'hy', [
  ('rj45', 'RJ45', '8P8C', 'MF',
   'Twisted-pair Ethernet — slow-control, DAQ networks and IPMI everywhere. Plug & jack shown.',
   'Ethernet · latch', W+'Modular_connector', 'RJ45 connector', 0),
  ('rj11', 'RJ11', '6P4C', 'MF',
   'Smaller modular plug & jack — telephone, and the odd RS-232-over-RJ console port.',
   'legacy · latch', W+'Registered_jack', 'RJ11 connector', 0),
  ('sfp', 'SFP / SFP+', '', 'MF',
   'Hot-plug transceiver cage — 1 to 10/25 G. Swap between copper, DAC or LC optics.',
   '1–25 G · bail', W+'Small_Form-factor_Pluggable', 'SFP+ transceiver', 0),
  ('qsfp', 'QSFP / QSFP-DD', '', 'MF',
   'Quad-lane 40/100/400 G module cage. Spine uplinks and HL-LHC read-out aggregation.',
   '40–400 G · quad', W+'QSFP', 'QSFP28 transceiver', 0),
  ('dac', 'DAC / Twinax', '', '',
   'Direct-attach copper cable with fixed SFP/QSFP ends. Cheap short in-rack links.',
   'passive · <7 m', W+'Twinaxial_cabling', 'SFP+ DAC cable', 0),
  ('m12', 'M12', 'A / D / X code', 'MF',
   'Screw-locking industrial circular — sensors, PROFINET & Ethernet on movers and magnets.',
   'IP67 · fieldbus', W+'M12_connector', 'M12 connector', 0),
 ]),
 ('Backplanes & Crates', 'VME · NIM · ATCA · µTCA', 'cu', [
  ('din41612', 'DIN 41612', 'VME J1/J2', 'MF',
   'Two/three-row 64–96-pin Eurocard backplane connector — every VME, VXI & CAMAC-era crate. Male & female shown.',
   'backplane · 96-pin', W+'DIN_41612', 'DIN 41612', 1),
  ('nim_conn', 'NIM bin connector', '', 'MF',
   'The 42-position pin block at the rear of every NIM module — ±12/±24 V power since 1964.',
   'crate · power', W+'Nuclear_Instrumentation_Module', 'NIM bin connector', 0),
  ('atca_zone2', 'ATCA Zone 2', 'HM-Zd / ADF', 'MF',
   'Differential wafer array behind ATCA blades — GbE base + fabric & TCDS2 clock on Serenity/Apollo DTCs.',
   'ATCA · 40 pair', W+'Advanced_Telecommunications_Computing_Architecture', 'HM-Zd connector', 0),
  ('amc_edge', 'AMC card edge', 'µTCA', 'MF',
   '170-pad gold-finger edge of Advanced Mezzanine Cards — µTCA crates of many mid-size DAQs.',
   'µTCA · 170 pad', W+'Advanced_Mezzanine_Card', 'AMC connector', 0),
  ('fmc', 'FMC', 'VITA 57', 'MF',
   'FPGA mezzanine connector — ADC/DAC & I/O daughterboards on read-out carriers.',
   'mezzanine · 400 pin', W+'FPGA_Mezzanine_Card', 'FMC connector VITA 57', 0),
 ]),
 ('Data, Serial & Instrumentation Buses', 'the back of every rack', 'cu', [
  ('usb_a', 'USB-A', '', 'MF',
   'The host-side rectangle — one-way only. Peripherals, dongles & front panels.',
   'host · 4-pin+', W+'USB_hardware', 'USB A connector', 0),
  ('usb_b', 'USB-B', '', 'MF',
   'The square device-side uplink — scopes, instruments & anything bench-sized.',
   'device · square', W+'USB_hardware', 'USB B connector', 0),
  ('usb_mini', 'USB Mini-B', '', 'MF',
   'Early-2000s portable port — still on older scopes, cameras & dev kits.',
   'legacy · 5-pin', W+'USB_hardware', 'USB mini B connector', 0),
  ('usb_micro', 'USB Micro-B', '', 'MF',
   'The phone-era micro port — SBCs, dev boards & battery gadgets.',
   'micro · 5-pin', W+'USB_hardware', 'USB micro B connector', 0),
  ('usbc', 'USB-C', '', 'MF',
   'Reversible power + data up to 240 W / 40 Gb/s — and Thunderbolt in disguise.',
   'reversible · PD', W+'USB-C', 'USB C connector', 0),
  ('usb3fam', 'USB 3.0 B & Micro-B', 'SuperSpeed', '',
   'The odd ones: 3.0 Type-B grows a hump, 3.0 Micro-B grows a sidecar. Scopes, DAQ boxes, external disks.',
   '5 Gb/s · wide', W+'USB_3.0', 'USB 3.0 connector', 1),
  ('firewire', 'FireWire', 'IEEE 1394', 'MF',
   '6-pin 1394a & 9-pin 1394b — legacy cameras and older DAQ front-ends.',
   'legacy · 400/800 M', W+'IEEE_1394', 'FireWire connector', 0),
  ('db9', 'DB9', 'DE-9', 'MF',
   'RS-232 serial — consoles, HV crates, motion controllers, ELMB CANbus. Male & female shown.',
   'RS-232 · CAN', W+'D-subminiature', 'DB9 connector', 1),
  ('db25', 'DB25', '', 'MF',
   'Wide D-sub — legacy serial, parallel (LPT) and some GPIB break-outs. Male & female shown.',
   'parallel / serial', W+'D-subminiature', 'DB25 connector', 1),
  ('db37', 'DB37', 'DC-37', 'MF',
   'Fat D-sub — MARATON LV front panels, ELMB breakouts & multichannel analogue I/O. Male & female shown.',
   'LV · analogue I/O', W+'D-subminiature', 'DB37 connector', 1),
  ('hd15', 'HD-15', 'VGA', 'MF',
   '15-pin, three rows — analogue RGBHV video to projectors & old crate displays. Male & female shown.',
   'analogue video', W+'VGA_connector', 'VGA connector', 1),
  ('gpib', 'GPIB', 'IEEE-488', 'MF',
   'Stackable 24-pin micro-ribbon — the classic bench-instrument bus for automated measurement.',
   'instrument bus', W+'IEEE-488', 'GPIB connector', 0),
  ('idc', 'IDC ribbon', '2.54 mm', 'MF',
   'Mass-terminated box header + flat cable. Internal bus, JTAG & front-end wiring.',
   'header · ribbon', W+'Insulation-displacement_connector', 'IDC header 2.54', 0),
  ('pinheader', '0.1″ header', 'Molex KK', 'MF',
   'Friction pin headers & crimp housings — fans, jumpers, debug UARTs, GPIO.',
   'pins · crimp', W+'Pin_header', '2.54mm pin header', 0),
  ('dip', 'DIP switch', '', 'genderless',
   'Bank of tiny slide switches — board-level config: addresses, bus termination, boot modes.',
   'config · slide', W+'DIP_switch', 'DIP switch', 0),
  ('button', 'Tactile switch', '6 mm', 'genderless',
   'The clicky momentary PCB button — resets, manual triggers & front-panel pokes.',
   'momentary · THT', W+'Push-button', 'tactile switch 6mm', 0),
 ]),
 ('Storage & Drives', 'event builders & disk arrays', 'cu', [
  ('sata', 'SATA', '', 'MF',
   'L-keyed serial storage link — every DAQ server, disk array and event-builder node.',
   '6 Gb/s · L-key', W+'SATA', 'SATA connector', 0),
  ('sas', 'SAS', 'SFF-8482', 'MF',
   'Unified SATA-shape plug that bridges both segments — dual-port enterprise drives.',
   '12 Gb/s · dual port', W+'Serial_Attached_SCSI', 'SAS connector', 0),
  ('minisas', 'Mini-SAS HD', 'SFF-8644', 'MF',
   'Quad-lane external storage fan-out with pull-tab latch — JBODs & RAID shelves.',
   '4× 12 G · pull tab', W+'Serial_Attached_SCSI', 'mini SAS HD cable', 0),
  ('ide40', 'IDE / PATA', '40-pin', 'MF',
   'The old 40-pin ribbon header — parallel ATA disks in legacy DAQ PCs.',
   'legacy · ribbon', W+'Parallel_ATA', 'IDE 40 pin', 0),
  ('m2', 'M.2', 'M-key', 'MF',
   'Gumstick SSD card edge — NVMe scratch disks in every modern DAQ node.',
   'NVMe · card edge', W+'M.2', 'M.2 SSD', 0),
 ]),
 ('Video & Display', 'counting-room walls', 'cu', [
  ('hdmi', 'HDMI', 'A · Mini · Micro', 'MF',
   'Full, Mini and Micro. Digital A/V for monitors, DAQ dashboards and cameras.',
   'digital A/V', W+'HDMI', 'HDMI connector', 1),
  ('dp', 'DisplayPort', '', 'MF',
   'Latching digital display link — high-refresh, multi-monitor control walls.',
   'DP / mDP · latch', W+'DisplayPort', 'DisplayPort connector', 0),
  ('dvi', 'DVI', 'D / I', 'MF',
   'Digital/analogue transitional video with the flat analogue blade beside the pins.',
   'DVI-D / -I', W+'Digital_Visual_Interface', 'DVI connector', 0),
 ]),
 ('Audio, Analogue I/O & Power', 'triggers, DMMs & mains', 'cu', [
  ('rca', 'RCA', 'phono', 'MF',
   'Single-ended coax plug — analogue audio/video and the odd lab reference signal.',
   '75 Ω · unbalanced', W+'RCA_connector', 'RCA connector', 0),
  ('jack', 'Phone jack', '3.5 / 6.35 mm', 'MF',
   'TS/TRS/TRRS barrel — audio, and a handy source of trigger & gate pulses.',
   'TS / TRS / TRRS', W+'Phone_connector_(audio)', '3.5mm jack', 0),
  ('toslink', 'TOSLINK', '', 'MF',
   'Square optical S/PDIF — galvanically isolated, ground-loop-free digital audio.',
   'optical S/PDIF', W+'TOSLINK', 'TOSLINK connector', 0),
  ('xlr', 'XLR', '', 'MF',
   'Locking 3-pin balanced audio — long, low-noise runs & PA in the control room. Male & female shown.',
   'balanced · locking', W+'XLR_connector', 'XLR connector', 0),
  ('banana', 'Banana', '4 mm', 'MF',
   'Spring-sprung 4 mm plug — DMMs, bench PSUs & test-point patching.',
   'DMM · 4 mm', W+'Banana_connector', 'banana plug', 0),
  ('barrel', 'DC barrel', '', 'MF',
   'Coaxial low-voltage power jack — bench bricks feeding modules & accessories.',
   'power · centre +/–', W+'Coaxial_power_connector', 'DC barrel jack', 0),
  ('iec', 'IEC C13/C14', '', 'MF',
   'The “kettle lead” mains pair — every crate, PC, PSU and rack PDU on the floor.',
   'AC mains · 10 A', W+'IEC_60320', 'IEC C14 inlet', 0),
  ('c19', 'IEC C19/C20', '', 'MF',
   'The C13’s big sibling — 16 A feeds for servers, blade shelves & big PDUs.',
   'AC mains · 16 A', W+'IEC_60320', 'IEC C20 inlet', 0),
  ('minifit', 'Mini-Fit', '4.2 mm', 'MF',
   'Keyed dual-row crimp power (Molex Mini-Fit Jr & friends) — PC/ATX and detector LV.',
   'DC · keyed', W+'Molex_connector', 'Molex Mini-Fit Jr', 0),
  ('matenlok', 'MATE-N-LOK', '“Molex”', 'MF',
   'The classic 4-pin drive-power plug everyone calls “a Molex”. Disks, fans, LED strips.',
   'DC · 4-pin', W+'Molex_connector', 'MATE-N-LOK 4 pin', 0),
  ('microfit', 'Micro-Fit', '3.0 mm', 'MF',
   'Mini-Fit’s small sibling — dense DC power to boards and front-end crates.',
   'DC · 3 mm', W+'Molex_connector', 'Molex Micro-Fit', 0),
  ('powerpole', 'Anderson Powerpole', '', 'genderless',
   'Genderless stackable DC — the amateur-radio-standard 12 V bench feed.',
   'DC · stackable', W+'Anderson_Powerpole', 'Anderson Powerpole', 0),
 ]),
 ('At the Experiments — CMS & ATLAS', 'HL-LHC read-out chain', 'hy', [
  ('firefly', 'Samtec FireFly', 'ECUO / CERN-B', '',
   'Micro flyover engine — 16 sites per Serenity DTC daughter-card, 25 Gb/s; CERN-B optical pigtails end in male MTP.',
   '25 G · flyover', 'https://www.samtec.com/optics/optical-cable/mid-board/firefly', 'Samtec FireFly', 0),
  ('vtrx', 'VTRx+', 'Versatile Link+', '',
   'Rad-hard optical module of the HL-LHC trackers — lpGBT links out over a 12-way female MT pigtail; seats on a Hirose DF40.',
   'rad-hard · 4+1 ch', 'https://twiki.nevis.columbia.edu/twiki/pub/ATLAS/V2FEB2Prototype/VTRxPlusApplicationNote.pdf', None, 0),
  ('df57', 'Hirose DF57', '2-pos', 'MF',
   'The tiny crimp pair that powers a CMS 2S module — LV in, sensor HV in. Rated 30 matings; handle with care.',
   'micro · 30 cycles', 'https://www.hirose.com/product/series/DF57', 'Hirose DF57', 0),
 ]),
]

ALSO = [
 ('MT-RJ', 'duplex fibre, RJ-style latch'), ('2.92 mm “K” / 3.5 mm', 'precision RF to 40 GHz'),
 ('FAKRA', 'keyed automotive SMB'), ('QMA', 'quick-lock SMA'),
 ('VHDCI / SCSI', 'legacy parallel storage'), ('Centronics', 'printer-era parallel'),
 ('PS/2 mini-DIN', 'legacy keyboards & mice'), ('MIL-DTL-38999', 'keyed circular mil/aero'),
 ('OCuLink', 'PCIe over cable'), ('OSFP / CFP', '400/800 G optics'),
 ('AOC', 'active optical QSFP cables'), ('FFC / FPC', 'flat-flex board jumpers'),
 ('PCIe / DIMM edge', 'gold-finger card slots'), ('Phoenix blocks', 'screw-terminal field wiring'),
 ('Samtec Z-RAY', '1990-pin Serenity interposer'), ('Panasonic A35', 'CMS 2S hybrid-to-hybrid'),
 ('Positronic V34', 'ATLAS Pixel LV bulk'), ('JAE 80-pin', 'ATLAS Pixel PP0 services'),
 ('ATCA Zone 1', '−48 V + IPMB (Positronic)'), ('Würth REDCUBE', '50 A board power posts'),
 ('ITk twinax bundles', '34–36 AWG data links'), ('Speakon', 'locking loudspeaker power'),
]

EXP_NOTES = [
 ('ATLAS TTC', 'ST single-mode tree couplers fan the LHC clock out of TTCex crates.'),
 ('ATLAS SCT/Pixel', 'MT-8/12/16 ribbon ferrules at PP0/PPB1; MARATON LV lands on DB37; Pixel LV on Positronic V34.'),
 ('ATLAS FELIX', 'MTP-24/48 trunk couplers feed MiniPOD optics — 48 duplex links per FLX-712.'),
 ('ATLAS / CMS HV', 'CAEN mainframes hand out HV through Radiall 52-pin multipin (A996 cables) & REDEL 51-pin.'),
 ('CMS 2S module', 'Panasonic A35 hybrids, Hirose DF57 power entry, VTRx+ on Hirose DF40, MT-12 fibre pigtail.'),
 ('CMS DTC', 'Serenity/Apollo ATCA blades: FireFly links, Zone-1 −48 V (Positronic), Zone-2 ADF fabric, 144-fibre female-MTP trunks.'),
 ('ELMB / DCS', 'CANbus daisy-chains on DB9; 3M 34-pin headers carry 64 ADC channels per ELMB.'),
]

def b64(p, mime):
    return f'data:{mime};base64,' + base64.b64encode(p.read_bytes()).decode()

def font(name): return b64(FONTS / name, 'font/woff2')

CARDMM = json.loads(pathlib.Path('cardmm.json').read_text()) if pathlib.Path('cardmm.json').exists() else {}

def art(slug):
    p = WEBP / f'{slug}.webp'
    if not p.exists():
        raise SystemExit(f'MISSING ART: {slug}.webp')
    return b64(p, 'image/webp')

def esc(s): return html.escape(s, quote=False)

def card(c):
    slug, name, sub, gender, desc, tag, ref, dkq, wide = c
    if gender == 'MF':
        mf = '<span class="mf"><b class="m">M</b><b class="f">F</b></span>'
    elif gender:
        mf = f'<span class="mf"><b class="na">{esc(gender)}</b></span>'
    else:
        mf = ''
    subh = f' <small>{esc(sub)}</small>' if sub else ''
    mm = CARDMM.get(slug)
    if mm:
        tag = f"{tag} · {mm:.0f} mm" if mm >= 10 else f"{tag} · {mm:.1f} mm"
    reflabel = 'wiki' if ref.startswith(W) else 'spec'
    links = f'<a href="{ref}" target="_blank" rel="noopener">{reflabel}</a>'
    if dkq:
        links += f'<a href="{dk(dkq)}" target="_blank" rel="noopener">digikey</a>'
    return f'''      <figure class="card{' wide' if wide else ''}">
        <div class="art"><img src="{art(slug)}" alt="{esc(name)} connector"></div>
        <div class="nm"><span class="cn">{esc(name)}{subh}</span>{mf}</div>
        <p class="desc">{desc}</p>
        <div class="meta"><span class="tag"><span class="d"></span>{esc(tag)}</span>
        <nav class="lnk">{links}</nav></div>
      </figure>'''

def section(i, title, note, medium, cards):
    inner = '\n'.join(card(c) for c in cards)
    return f'''  <section class="sec m-{medium}">
    <div class="sec-head"><span class="idx">{i:02d}</span><h2>{esc(title)}</h2><div class="rule"></div><span class="note">{esc(note)}</span></div>
    <div class="grid">
{inner}
    </div>
  </section>'''

CSS = r'''
@font-face{font-family:"Archivo";src:url("@@A8@@") format("woff2");font-weight:800;font-display:swap}
@font-face{font-family:"Archivo";src:url("@@A6@@") format("woff2");font-weight:600;font-display:swap}
@font-face{font-family:"Plex Sans";src:url("@@S4@@") format("woff2");font-weight:400;font-display:swap}
@font-face{font-family:"Plex Sans";src:url("@@S6@@") format("woff2");font-weight:600;font-display:swap}
@font-face{font-family:"Plex Mono";src:url("@@M4@@") format("woff2");font-weight:400;font-display:swap}
@font-face{font-family:"Plex Mono";src:url("@@M6@@") format("woff2");font-weight:600;font-display:swap}

:root{
  --paper:#e9ebe4; --panel:#f5f6f1; --panel2:#eef0e9;
  --ink:#191d1b; --muted:#5b625d; --faint:#8a918b;
  --line:#d2d6cc; --line2:#c3c8bd;
  --cu:#b65e30; --aq:#0c8f9c;
  --shadow:0 1px 0 rgba(0,0,0,.04),0 18px 40px -24px rgba(20,30,25,.5);
  --artbg:linear-gradient(180deg,#f8f9f5,#e7e9e1);
}
@media (prefers-color-scheme:dark){:root{
  --paper:#0d1210; --panel:#141b18; --panel2:#111815;
  --ink:#e8ebe4; --muted:#9aa39c; --faint:#6c746d;
  --line:#243029; --line2:#2d3b33;
  --cu:#e0824a; --aq:#3bc3cf;
  --shadow:0 1px 0 rgba(0,0,0,.4),0 22px 46px -26px rgba(0,0,0,.8);
  --artbg:linear-gradient(180deg,#232c27,#161d1a);
}}
:root[data-theme="light"]{
  --paper:#e9ebe4; --panel:#f5f6f1; --panel2:#eef0e9;
  --ink:#191d1b; --muted:#5b625d; --faint:#8a918b;
  --line:#d2d6cc; --line2:#c3c8bd;
  --cu:#b65e30; --aq:#0c8f9c;
  --shadow:0 1px 0 rgba(0,0,0,.04),0 18px 40px -24px rgba(20,30,25,.5);
  --artbg:linear-gradient(180deg,#f8f9f5,#e7e9e1);
}
:root[data-theme="dark"]{
  --paper:#0d1210; --panel:#141b18; --panel2:#111815;
  --ink:#e8ebe4; --muted:#9aa39c; --faint:#6c746d;
  --line:#243029; --line2:#2d3b33;
  --cu:#e0824a; --aq:#3bc3cf;
  --shadow:0 1px 0 rgba(0,0,0,.4),0 22px 46px -26px rgba(0,0,0,.8);
  --artbg:linear-gradient(180deg,#232c27,#161d1a);
}
*{box-sizing:border-box}
html,body{margin:0}
body{
  background:
    radial-gradient(1200px 700px at 15% -8%, color-mix(in srgb,var(--cu) 7%, transparent), transparent 60%),
    radial-gradient(1100px 650px at 92% 4%, color-mix(in srgb,var(--aq) 8%, transparent), transparent 60%),
    var(--paper);
  color:var(--ink); font-family:"Plex Sans",system-ui,sans-serif;
  -webkit-font-smoothing:antialiased; line-height:1.45; padding:34px 22px 60px;
}
.poster{max-width:1520px;margin:0 auto;background:var(--panel);border:1px solid var(--line2);
  border-radius:14px;box-shadow:var(--shadow);padding:40px 42px 30px;position:relative;overflow:hidden}
.poster::before,.poster::after{content:"";position:absolute;width:22px;height:22px;opacity:.5}
.poster::before{top:14px;left:14px;border-left:2px solid var(--line2);border-top:2px solid var(--line2)}
.poster::after{bottom:14px;right:14px;border-right:2px solid var(--line2);border-bottom:2px solid var(--line2)}
.mast{display:grid;grid-template-columns:1fr auto;gap:22px;align-items:end;border-bottom:2px solid var(--ink);padding-bottom:20px;margin-bottom:6px}
.eyebrow{font-family:"Plex Mono",monospace;font-size:12px;letter-spacing:.32em;text-transform:uppercase;color:var(--cu);margin:0 0 10px}
h1{font-family:"Archivo",sans-serif;font-weight:800;line-height:.94;font-size:clamp(30px,5.2vw,62px);letter-spacing:-.015em;margin:0;text-wrap:balance}
h1 .thin{color:var(--muted)}
.sub{margin:14px 0 0;max-width:64ch;color:var(--muted);font-size:15px}
.masthead-key{display:flex;flex-direction:column;gap:10px;justify-self:end;font-family:"Plex Mono",monospace;font-size:11.5px;color:var(--muted);text-align:right}
.keyrow{display:flex;align-items:center;gap:8px;justify-content:flex-end}
.dot{width:11px;height:11px;border-radius:50%;flex:none}
.dot.cu{background:var(--cu)} .dot.aq{background:var(--aq)}
.dot.hy{background:linear-gradient(90deg,var(--cu) 0 50%,var(--aq) 50% 100%)}
.mfkey b{display:inline-grid;place-items:center;width:17px;height:17px;border-radius:4px;font-weight:600;font-size:10px;margin-left:3px;font-family:"Plex Mono",monospace}
.mfkey .bm{background:color-mix(in srgb,var(--ink) 84%,transparent);color:var(--panel)}
.mfkey .bf{color:var(--ink);box-shadow:inset 0 0 0 1.5px var(--line2)}
.sec{margin-top:30px}
.sec-head{display:flex;align-items:baseline;gap:14px;margin-bottom:15px}
.sec-head h2{font-family:"Archivo",sans-serif;font-weight:800;font-size:16px;letter-spacing:.02em;margin:0;text-transform:uppercase}
.sec-head .idx{font-family:"Plex Mono",monospace;font-size:12px;color:var(--cu);font-weight:600}
.sec-head .rule{flex:1;height:2px;background:var(--line2);border-radius:2px}
.sec-head .note{font-family:"Plex Mono",monospace;font-size:11px;color:var(--faint)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(224px,1fr));gap:13px}
.card{background:var(--panel2);border:1px solid var(--line);border-radius:10px;padding:12px 13px 13px;display:flex;flex-direction:column;gap:9px;min-width:0}
.art{background:var(--artbg);border:1px solid var(--line);border-radius:8px;aspect-ratio:128/74;display:grid;place-items:center;overflow:hidden}
.art img{width:94%;height:92%;object-fit:contain}
.wide{grid-column:span 2}
.wide .art{aspect-ratio:200/58}
@media (max-width:560px){.wide{grid-column:span 1}}
.nm{display:flex;align-items:center;justify-content:space-between;gap:8px}
.cn{font-family:"Archivo",sans-serif;font-weight:800;font-size:15px;letter-spacing:-.01em}
.cn small{font-family:"Plex Mono",monospace;font-weight:400;font-size:10.5px;color:var(--faint)}
.mf{display:flex;gap:3px;flex:none}
.mf b{display:inline-grid;place-items:center;width:16px;height:16px;border-radius:4px;font-family:"Plex Mono",monospace;font-weight:600;font-size:9.5px;line-height:1}
.mf .m{background:color-mix(in srgb,var(--ink) 84%,transparent);color:var(--panel)}
.mf .f{color:var(--ink);box-shadow:inset 0 0 0 1.4px var(--line2)}
.mf .na{color:var(--faint);box-shadow:inset 0 0 0 1.4px var(--line);width:auto;padding:0 5px}
.desc{font-size:12.5px;color:var(--muted);margin:0;line-height:1.36;flex:1}
.meta{display:flex;align-items:center;justify-content:space-between;gap:8px}
.tag{display:inline-flex;align-items:center;gap:6px;font-family:"Plex Mono",monospace;font-size:10px;color:var(--muted);border:1px solid var(--line2);border-radius:20px;padding:3px 9px 3px 7px}
.tag .d{width:7px;height:7px;border-radius:50%}
.m-cu .tag .d{background:var(--cu)} .m-aq .tag .d{background:var(--aq)}
.m-hy .tag .d{background:linear-gradient(90deg,var(--cu) 0 50%,var(--aq) 50% 100%)}
.lnk{display:flex;gap:7px}
.lnk a{font-family:"Plex Mono",monospace;font-size:9.5px;color:var(--faint);text-decoration:none;border-bottom:1px dotted var(--line2);padding-bottom:1px}
.lnk a:hover{color:var(--cu);border-color:var(--cu)}
.ref{display:grid;grid-template-columns:1.15fr 1fr 1fr;gap:14px;margin-top:14px}
@media (max-width:1000px){.ref{grid-template-columns:1fr}}
.panelbox{background:var(--panel2);border:1px solid var(--line);border-radius:10px;padding:15px 16px}
.panelbox h3{font-family:"Archivo",sans-serif;font-weight:800;font-size:13px;margin:0 0 3px;text-transform:uppercase;letter-spacing:.03em}
.panelbox .lead{font-size:12px;color:var(--muted);margin:0 0 13px}
.fibers{display:flex;flex-direction:column;gap:7px}
.fiber{display:grid;grid-template-columns:80px 1fr;align-items:center;gap:11px;font-size:12px}
.swatch{height:20px;border-radius:5px;border:1px solid rgba(0,0,0,.28);box-shadow:inset 0 0 0 1px rgba(255,255,255,.14)}
.fiber .lab{font-family:"Plex Mono",monospace;font-weight:600;font-size:11.5px}
.fiber .use{color:var(--muted);font-size:11.5px}
.polish{display:flex;gap:10px;margin-top:14px}
.polish .p{flex:1;border:1px solid var(--line);border-radius:8px;padding:9px 11px;display:flex;gap:10px;align-items:center}
.boot{width:16px;height:24px;border-radius:3px;flex:none;border:1px solid rgba(0,0,0,.3)}
.polish .p b{font-family:"Plex Mono",monospace;font-size:12px;display:block}
.polish .p span{font-size:11px;color:var(--muted)}
.tips{display:flex;flex-direction:column;gap:9px}
.tip{display:flex;gap:9px;font-size:12px;color:var(--muted);line-height:1.4}
.tip b{color:var(--ink);font-family:"Plex Mono",monospace;font-weight:600;font-size:11px;flex:none;width:84px}
.also{display:flex;flex-wrap:wrap;gap:7px;margin-top:14px}
.also span{font-family:"Plex Mono",monospace;font-size:10.5px;color:var(--muted);border:1px solid var(--line2);border-radius:16px;padding:4px 10px}
.also b{color:var(--ink);font-weight:600}
footer{margin-top:26px;padding-top:16px;border-top:1px solid var(--line2);display:flex;flex-wrap:wrap;justify-content:space-between;gap:10px;font-family:"Plex Mono",monospace;font-size:11px;color:var(--faint)}
footer .cu{color:var(--cu)}
@media print{body{padding:0;background:var(--panel)}.poster{box-shadow:none;border:none;border-radius:0}.lnk{display:none}}
'''

def build():
    sects = '\n'.join(section(i+1, *s) for i, s in enumerate(SECTIONS))
    also = '\n'.join(f'      <span><b>{esc(n)}</b> — {esc(d)}</span>' for n, d in ALSO)
    exp = '\n'.join(f'          <div class="tip"><b>{esc(n)}</b><span>{esc(d)}</span></div>' for n, d in EXP_NOTES)
    css = CSS
    for k, f in [('A8','archivo-800.woff2'), ('A6','archivo-600.woff2'),
                 ('S4','plexsans-400.woff2'), ('S6','plexsans-600.woff2'),
                 ('M4','plexmono-400.woff2'), ('M6','plexmono-600.woff2')]:
        css = css.replace('@@'+k+'@@', font(f))
    n_ref = len(SECTIONS) + 1
    return f'''<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Connectors of the Particle Physics Lab — A Bench & Rack Field Guide</title>
<style>{css}</style>
<div class="poster">
  <header class="mast">
    <div>
      <p class="eyebrow">Bench &amp; Rack Field Guide · Rev. 2026</p>
      <h1>Connectors of the<br>Particle&nbsp;Physics&nbsp;Lab <span class="thin">— what plugs into what</span></h1>
      <p class="sub">The coax, fibre, network, backplane, data, video and power interconnects of the crate,
        the rack and the counting room — rendered from CAD models of the real parts. M/F badges mark gendered connectors; paired
        art shows male on the left, female on the right. Colour marks the signal medium; within a section, connectors are drawn to relative scale — true sizes on the tags; the tiniest parts are enlarged a touch to stay visible.</p>
    </div>
    <div class="masthead-key">
      <div class="keyrow"><span>copper / electrical</span><span class="dot cu"></span></div>
      <div class="keyrow"><span>optical / fibre</span><span class="dot aq"></span></div>
      <div class="keyrow"><span>hybrid link</span><span class="dot hy"></span></div>
      <div class="keyrow mfkey" style="margin-top:4px"><span>plug&nbsp;/&nbsp;jack</span><b class="bm">M</b><b class="bf">F</b></div>
    </div>
  </header>
{sects}
  <section class="sec">
    <div class="sec-head"><span class="idx">{n_ref:02d}</span><h2>Reading the Fibre &amp; the Coax</h2><div class="rule"></div><span class="note">before you plug it in</span></div>
    <div class="ref">
      <div class="panelbox">
        <h3>Fibre by jacket colour</h3>
        <p class="lead">Convention (TIA-598). Jacket colour tells you the glass; confirm before mating.</p>
        <div class="fibers">
          <div class="fiber"><div class="swatch" style="background:#f6871f"></div><span class="use"><span class="lab">OM1·OM2</span> — 62.5/50 µm MM · orange</span></div>
          <div class="fiber"><div class="swatch" style="background:#33c1cf"></div><span class="use"><span class="lab">OM3</span> — 50 µm laser-opt MM · aqua</span></div>
          <div class="fiber"><div class="swatch" style="background:linear-gradient(90deg,#33c1cf,#7b5cc4)"></div><span class="use"><span class="lab">OM4</span> — 50 µm MM · aqua/violet</span></div>
          <div class="fiber"><div class="swatch" style="background:#b7d94c"></div><span class="use"><span class="lab">OM5</span> — wideband MM · lime</span></div>
          <div class="fiber"><div class="swatch" style="background:#ffd21e"></div><span class="use"><span class="lab">OS1·OS2</span> — 9 µm single-mode · yellow</span></div>
        </div>
        <div class="polish">
          <div class="p"><span class="boot" style="background:#2f6fe0"></span><div><b>UPC</b><span>blue boot · flat polish</span></div></div>
          <div class="p"><span class="boot" style="background:#1f9d55"></span><div><b>APC</b><span>green boot · 8° angled</span></div></div>
        </div>
      </div>
      <div class="panelbox">
        <h3>Field cheats</h3>
        <div class="tips">
          <div class="tip"><b>M vs F</b><span>Male carries the pin/centre-conductor; female has the socket. Barrels &amp; gender-changers bridge like-to-like.</span></div>
          <div class="tip"><b>50 vs 75 Ω</b><span>BNC comes in both — 50 Ω for data/RF &amp; NIM logic, 75 Ω for video. Don't mix on long runs.</span></div>
          <div class="tip"><b>SHV≠MHV≠BNC</b><span>MHV half-mates with BNC — a 3 kV surprise. SHV won't mate with either. Label your HV.</span></div>
          <div class="tip"><b>APC ≠ UPC</b><span>Never mate a green (angled) ferrule to a blue (flat) one — you'll wreck the end-face.</span></div>
          <div class="tip"><b>SM ≠ MM</b><span>Yellow single-mode and aqua/orange multimode don't interoperate. Match the glass, not just the connector.</span></div>
          <div class="tip"><b>MTP M vs F</b><span>Male MTP has two steel guide pins; female has holes. Trunks are female; transceiver pigtails male.</span></div>
        </div>
      </div>
      <div class="panelbox">
        <h3>Where they live at the LHC</h3>
        <div class="tips">
{exp}
        </div>
      </div>
    </div>
    <div class="also">
{also}
    </div>
  </section>
  <footer>
    <span>Connectors of the Particle Physics Lab · a bench &amp; rack field guide</span>
    <span>rendered from CAD (KiCad libs · manufacturer STEP · parametric)&nbsp;·&nbsp;<span class="cu">copper</span> / optical&nbsp;·&nbsp;print at A0/A1</span>
  </footer>
</div>
'''

if __name__ == '__main__':
    out = pathlib.Path(sys.argv[1])
    html_text = build()
    out.write_text(html_text)
    print(f'wrote {out} ({len(html_text)/1e6:.2f} MB)')
