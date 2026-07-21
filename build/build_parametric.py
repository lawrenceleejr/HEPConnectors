#!/usr/bin/env python3
"""Build dimension-accurate parametric connector models in bpy, export GLB.

Models the parts with no freely downloadable manufacturer CAD (fiber optic
family, pluggable transceivers, SHV...). Dimensions from datasheets, in mm.
Material name prefixes drive the render stage: P_ plastic, M_ metal, C_ ceramic.
Axis convention: connector mating face points +Y ("forward"), Z up.
"""
import bpy, math, sys, os
from mathutils import Vector

OUT = sys.argv[1] if len(sys.argv) > 1 else 'cad/param'
os.makedirs(OUT, exist_ok=True)

# ---------- palette ----------
COLS = {
    'P_blue':   (0.05, 0.16, 0.55, 1),   # SM connector body blue
    'P_aqua':   (0.10, 0.55, 0.60, 1),   # 10G aqua boot
    'P_beige':  (0.82, 0.77, 0.62, 1),
    'P_black':  (0.035, 0.035, 0.04, 1),
    'P_dark':   (0.10, 0.10, 0.11, 1),
    'P_green':  (0.08, 0.42, 0.18, 1),   # APC green
    'P_white':  (0.88, 0.88, 0.86, 1),
    'P_red':    (0.55, 0.06, 0.05, 1),
    'P_ivory':  (0.85, 0.83, 0.74, 1),
    'C_ferrule':(0.93, 0.92, 0.88, 1),   # zirconia
    'M_steel':  (0.42, 0.42, 0.44, 1),
    'M_nickel': (0.55, 0.54, 0.50, 1),
    'M_gold':   (0.70, 0.50, 0.18, 1),
}
def mat(name):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value = COLS[name]
    return m

def add(obj, name):
    o = bpy.context.object
    o.data.materials.append(mat(name))
    return o

def box(sx, sy, sz, loc=(0,0,0), m='P_blue', rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object; o.scale = (sx, sy, sz)
    o.data.materials.append(mat(m)); return o

def cyl(r, depth, loc=(0,0,0), m='M_steel', axis='Y', verts=48, r2=None):
    rot = {'Y': (math.pi/2, 0, 0), 'Z': (0,0,0), 'X': (0, math.pi/2, 0)}[axis]
    if r2 is None:
        bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, location=loc, rotation=rot, vertices=verts)
    else:
        bpy.ops.mesh.primitive_cone_add(radius1=r, radius2=r2, depth=depth, location=loc, rotation=rot, vertices=verts)
    o = bpy.context.object; o.data.materials.append(mat(m)); return o

def torus(R, r, loc=(0,0,0), m='M_steel', rot=(0,0,0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, location=loc, rotation=rot)
    o = bpy.context.object; o.data.materials.append(mat(m)); return o

def boot(r0, r1, length, y0, m):
    """tapered cable boot going -Y from y0"""
    seg = 6
    for i in range(seg):
        f = i / seg
        rr = r0 + (r1 - r0) * f
        cyl(rr, length/seg, (0, y0 - length*f - length/seg/2, 0), m)

def export(name):
    from mathutils import Matrix
    bpy.context.view_layer.update()
    for o in bpy.context.scene.objects:
        if o.type == 'MESH':
            o.data.transform(o.matrix_basis)
            o.matrix_basis = Matrix.Identity(4)
    bpy.ops.object.select_all(action='SELECT')
    path = os.path.join(OUT, name + '.glb')
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True)
    print('exported', path, flush=True)
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

def fresh():
    bpy.ops.wm.read_factory_settings(use_empty=True)

# ================= fiber =================
def lc_body(x=0, body='P_blue', bootm='P_white'):
    """LC simplex plug at x offset; front face +Y=0."""
    box(4.5, 12, 4.5, (x, -6, 2.25), body)                       # main body
    box(1.4, 7, 1.2, (x, -6.5, 5.0), body, rot=(math.radians(-8),0,0))  # latch lever
    cyl(1.6, 3.5, (x, -1.5, 2.25), 'P_white')                    # ferrule holder
    cyl(0.62, 5.5, (x, 1.5, 2.25), 'C_ferrule')                  # 1.25mm ferrule
    box(4.2, 4, 4.2, (x, -13.5, 2.25), body)
    boot(1.9, 1.1, 9, -15.5, bootm)

def m_lc():
    fresh(); lc_body(); export('p_lc')

def m_lc_duplex():
    fresh()
    lc_body(-3.4); lc_body(3.4)
    box(10.5, 5, 1.6, (0, -8.5, 6.0), 'P_blue')                  # duplex clip bridge
    export('p_lc_duplex')

def m_sc():
    fresh()
    box(7.4, 22, 7.4, (0, -11, 3.7), 'P_blue')                   # outer push-pull sleeve
    box(5.4, 4, 5.4, (0, 0.5, 3.7), 'P_white')                   # inner body
    cyl(1.24, 8, (0, 3, 3.7), 'C_ferrule')                       # 2.5mm ferrule
    box(6.0, 4, 6.0, (0, -24, 3.7), 'P_blue')
    boot(2.6, 1.4, 11, -26, 'P_blue')
    export('p_sc')

def m_st():
    fresh()
    cyl(4.6, 9, (0, -4.5, 4.6), 'M_nickel')                      # bayonet coupling ring
    torus(4.6, 0.7, (0, -1.2, 4.6), 'M_nickel', rot=(math.pi/2, 0, 0))
    cyl(0.7, 2.2, (0, -0.6, 8.9), 'M_nickel', axis='Z')          # bayonet lug
    cyl(2.4, 6, (0, 1.5, 4.6), 'M_nickel')
    cyl(1.24, 9, (0, 4, 4.6), 'C_ferrule')                       # 2.5mm ferrule
    cyl(3.4, 8, (0, -12, 4.6), 'P_black')                        # rear body
    boot(2.6, 1.3, 12, -16, 'P_black')
    export('p_st')

def m_fc():
    fresh()
    n = 24                                                        # knurled nut
    for i in range(n):
        a = i / n * 2 * math.pi
        box(0.9, 8.5, 1.6, (5.1*math.cos(a), -4.2, 4.9 + 5.1*math.sin(a)),
            'M_nickel', rot=(0, a + math.pi/2, 0))
    cyl(4.9, 8.5, (0, -4.2, 4.9), 'M_nickel')
    cyl(2.2, 5, (0, 0.5, 4.9), 'M_nickel')
    cyl(1.24, 9, (0, 3.5, 4.9), 'C_ferrule')
    box(1.6, 4, 1.2, (0, 0.5, 7.4), 'M_nickel')                  # key
    cyl(3.2, 7, (0, -11.5, 4.9), 'M_nickel')
    boot(2.6, 1.3, 12, -15, 'P_black')
    export('p_fc')

def m_mtp():
    fresh()
    box(12.4, 18, 6.4, (0, -9, 3.2), 'P_black')                  # outer housing
    box(10.2, 5, 4.6, (0, 0.5, 3.2), 'P_ivory')                  # MT ferrule
    for i in range(12):                                          # fiber row
        x = -3.44 + i * 0.625
        cyl(0.12, 0.4, (x, 3.05, 3.2), 'C_ferrule')
    cyl(0.35, 4.5, (-5.3, 1.2, 3.2), 'M_steel')                  # guide pins
    cyl(0.35, 4.5, ( 5.3, 1.2, 3.2), 'M_steel')
    box(9, 6, 5.2, (0, -21, 3.2), 'P_black')
    boot(3.0, 1.6, 12, -24, 'P_black')
    export('p_mtp')

def m_mu():
    fresh()
    box(4.4, 13, 4.4, (0, -6.5, 2.2), 'P_ivory')
    box(1.2, 6, 1.0, (0, -6.5, 4.9), 'P_ivory', rot=(math.radians(-8),0,0))
    cyl(0.62, 4.5, (0, 1.2, 2.2), 'C_ferrule')
    box(4.0, 4, 4.0, (0, -14.5, 2.2), 'P_ivory')
    boot(1.8, 1.0, 8, -16.5, 'P_ivory')
    export('p_mu')

def m_e2000():
    fresh()
    box(7.3, 20, 7.3, (0, -10, 3.65), 'P_green')                 # body
    box(7.3, 6.5, 1.4, (0, 1.5, 7.6), 'P_green',                 # spring shutter flap
        rot=(math.radians(35), 0, 0))
    box(5.2, 3, 5.2, (0, 0, 3.65), 'P_dark')
    cyl(1.24, 5.5, (0, 1.5, 3.4), 'C_ferrule')
    box(6.0, 4, 6.0, (0, -22, 3.65), 'P_green')
    boot(2.6, 1.4, 10, -24, 'P_black')
    export('p_e2000')

# ================= pluggables =================
def sfp_shell(w=13.4, h=8.5, L=56, tab='P_aqua'):
    box(w, L, h, (0, -L/2, h/2), 'M_nickel')                     # body
    box(w-2, 8, h-2, (0, 2, h/2), 'M_nickel')                    # nose
    # duplex LC ports in nose
    box(4.6, 2.4, 5.2, (-2.9, 5.2, h/2), 'P_dark')
    box(4.6, 2.4, 5.2, ( 2.9, 5.2, h/2), 'P_dark')
    # bail latch wire
    torus(5.6, 0.55, (0, 4.5, h/2), tab, rot=(0, math.pi/2, 0))
    # gold edge fingers at rear
    for i in range(10):
        x = -w/2 + 1.2 + i * (w-2.4)/9
        box(0.7, 6, 0.5, (x, -L + 3, 1.2), 'M_gold')

def m_sfp():
    fresh(); sfp_shell(); export('p_sfp')

def m_qsfp():
    fresh()
    w, h, L = 18.35, 8.5, 72
    box(w, L, h, (0, -L/2, h/2), 'M_nickel')
    box(w-2, 10, h-1.6, (0, 3, h/2), 'M_nickel')
    box(9.6, 2.4, 3.4, (0, 8.2, h/2), 'P_dark')                  # MTP port
    box(6, 26, 1.2, (0, 6, h + 0.8), 'P_black')                  # pull tab
    box(10, 6, 1.2, (0, 17, h + 0.8), 'P_black')
    for i in range(14):
        x = -w/2 + 1.4 + i * (w-2.8)/13
        box(0.7, 7, 0.5, (x, -L + 3.5, 1.2), 'M_gold')
    export('p_qsfp')

# ================= RF =================
def m_shv():
    fresh()
    # SHV bulkhead jack: bayonet shell + deep protruding insulator
    cyl(7.5, 14, (0, -7, 7.5), 'M_nickel')                       # bayonet shell
    cyl(0.9, 3.2, (-7.5, -2.5, 7.5), 'M_nickel', axis='X')       # bayonet posts
    cyl(0.9, 3.2, ( 7.5, -2.5, 7.5), 'M_nickel', axis='X')
    cyl(4.9, 12, (0, 2, 7.5), 'P_white')                         # long PTFE nose
    cyl(1.0, 14.5, (0, 2.5, 7.5), 'M_gold')                      # HV pin recessed
    cyl(8.6, 2.2, (0, -14.5, 7.5), 'M_nickel', verts=6)          # hex flange
    cyl(4.2, 10, (0, -20, 7.5), 'M_nickel')                      # rear
    export('p_shv')

def m_mhv():
    fresh()
    cyl(5.6, 11, (0, -5.5, 5.6), 'M_nickel')
    cyl(0.8, 2.6, (-5.7, -2.0, 5.6), 'M_nickel', axis='X')
    cyl(0.8, 2.6, ( 5.7, -2.0, 5.6), 'M_nickel', axis='X')
    cyl(3.4, 7, (0, 1.5, 5.6), 'P_white')
    cyl(0.9, 9.5, (0, 2.0, 5.6), 'M_gold')
    cyl(6.4, 2, (0, -12, 5.6), 'M_nickel', verts=6)
    cyl(3.6, 8, (0, -17, 5.6), 'M_nickel')
    export('p_mhv')

def m_triax():
    fresh()
    # triax BNC-style: three concentric contacts visible in face
    cyl(7.2, 13, (0, -6.5, 7.2), 'M_nickel')
    cyl(0.9, 3.0, (-7.3, -2.2, 7.2), 'M_nickel', axis='X')
    cyl(0.9, 3.0, ( 7.3, -2.2, 7.2), 'M_nickel', axis='X')
    cyl(4.6, 4, (0, 1.5, 7.2), 'P_white')                        # outer insulator
    cyl(3.0, 5, (0, 2.2, 7.2), 'M_nickel')                       # guard ring
    cyl(1.9, 5.5, (0, 2.6, 7.2), 'P_white')                      # inner insulator
    cyl(0.7, 7, (0, 3.2, 7.2), 'M_gold')                         # center pin
    cyl(8.2, 2.2, (0, -13.5, 7.2), 'M_nickel', verts=6)
    cyl(4.0, 9, (0, -19, 7.2), 'M_nickel')
    export('p_triax')

# ================= misc gaps (filled post-agent if needed) =================
def m_toslink():
    fresh()
    box(9.8, 10, 9.8, (0, -5, 4.9), 'P_black')                   # plug body
    box(7.2, 3.2, 6.4, (0, 1.4, 4.4), 'P_black')                 # nose
    cyl(1.3, 4.2, (0, 1.6, 4.4), 'P_red')                        # lit fiber tip
    box(6.2, 14, 8.2, (0, -16, 4.1), 'P_black')
    boot(3.0, 1.7, 11, -23, 'P_black')
    export('p_toslink')

def m_rca():
    fresh()
    cyl(4.1, 7, (0, -3.5, 4.1), 'M_gold')                        # outer shield ring
    cyl(0.8, 9.5, (0, 3, 4.1), 'M_gold')                         # center pin
    cyl(4.6, 1.6, (0, -7.6, 4.1), 'P_red')                       # color band
    cyl(4.4, 10, (0, -13.5, 4.1), 'M_nickel')                    # barrel
    boot(3.2, 1.8, 12, -18.5, 'P_red')
    export('p_rca')

def m_xlr_m():
    fresh()
    cyl(9.6, 15, (0, -7.5, 9.6), 'M_nickel')                     # shell
    cyl(8.2, 2.5, (0, 1.0, 9.6), 'P_dark')                       # insert
    for (dx, dz) in [(0, 3.4), (-3.0, -1.8), (3.0, -1.8)]:
        cyl(1.0, 6, (dx, 3.2, 9.6 + dz), 'M_nickel')             # 3 pins
    cyl(9.9, 12, (0, -19, 9.6), 'P_black')                       # rear grip
    boot(5.0, 2.6, 14, -25, 'P_black')
    export('p_xlr_m')

def m_rj11():
    fresh()
    box(9.6, 15, 7.6, (0, -7.5, 3.8), 'P_ivory')                 # plug body
    box(3.2, 10, 1.6, (0, -8, 8.6), 'P_ivory', rot=(math.radians(6),0,0))  # latch
    for i in range(4):
        x = -1.53 + i * 1.02
        box(0.55, 3.5, 1.6, (x, 0.8, 6.2), 'M_gold')             # contacts
    box(4.4, 5, 3.4, (0, -16, 3.6), 'P_ivory')
    boot(2.4, 1.6, 9, -18, 'P_ivory')
    export('p_rj11')

def m_gpib():
    fresh()
    # IEEE-488 micro-ribbon plug: rounded-D metal shell, black insert, bail posts
    box(52, 10, 10, (0, -5, 5), 'M_nickel')
    box(44, 6, 7, (0, 1.5, 5), 'P_black')
    for i in range(12):
        x = -18.5 + i * 3.4
        box(1.1, 2.6, 1.6, (x, 3.2, 6.6), 'M_gold')
        box(1.1, 2.6, 1.6, (x, 3.2, 3.4), 'M_gold')
    cyl(2.4, 9, (-27.5, -5, 5), 'M_steel', axis='Y')             # jack-screw posts
    cyl(2.4, 9, ( 27.5, -5, 5), 'M_steel', axis='Y')
    box(30, 12, 12, (0, -16, 5), 'P_dark')                       # cable hood
    export('p_gpib')

def m_minifit():
    fresh()
    # Molex Mini-Fit Jr 2x2 receptacle
    for (x, z) in [(-2.1, 2.1), (2.1, 2.1), (-2.1, 6.3), (2.1, 6.3)]:
        box(3.9, 12, 3.9, (x, -6, z), 'P_ivory')
        box(2.6, 1.5, 2.6, (x, 0.2, z), 'P_dark')
    box(8.8, 9, 9.2, (0, -8.5, 4.2), 'P_ivory')
    box(2.4, 9, 1.6, (0, -8.5, 9.4), 'P_ivory')                  # latch
    export('p_minifit')

def m_displayport():
    fresh()
    # DP plug: asymmetric-cornered shell
    box(16.1, 12, 4.8, (0, -6, 2.4), 'M_nickel')
    box(14.2, 3, 3.2, (0, 0.8, 2.4), 'P_black')
    box(16.5, 14, 6.4, (0, -16, 2.4), 'P_black')                 # overmold
    boot(4.2, 2.4, 12, -23, 'P_black')
    export('p_displayport')

def m_hdmi_mini():
    fresh()
    box(10.42, 8, 2.42, (0, -4, 1.21), 'M_nickel')
    box(9.2, 2.2, 1.4, (0, 0.6, 1.21), 'P_black')
    box(11.5, 10, 4.4, (0, -11, 1.4), 'P_black')
    boot(3.0, 1.8, 9, -16, 'P_black')
    export('p_hdmi_mini')

def m_powerpole():
    fresh()
    box(7.9, 24, 7.9, (0, -12, 3.95), 'P_red')
    box(7.9, 24, 7.9, (0, -12, 11.85), 'P_black')
    box(6.2, 4, 2.2, (0, -1, 2.6), 'M_steel')
    box(6.2, 4, 2.2, (0, -1, 13.2), 'M_steel')
    export('p_powerpole')

def m_dac():
    fresh()
    # SFP+ DAC: two modules joined by twinax (render one end + cable arc)
    sfp_shell(tab='P_black')
    seg = 10
    for i in range(seg):
        t = i / seg
        y = -56 - t * 30
        z = 4.25 + math.sin(t * math.pi) * 6
        cyl(2.6, 3.4, (0, y, z), 'P_dark')
    export('p_dac')

def m_splice():
    fresh()
    cyl(0.25, 46, (0, -8, 3.2), 'P_ivory')                       # bare fiber
    cyl(0.9, 3, (0, 12, 3.2), 'P_aqua')                          # coating ends
    cyl(0.9, 3, (0, -28, 3.2), 'P_aqua')
    cyl(2.0, 22, (0, -8, 3.2), 'P_white')                        # protection sleeve
    cyl(0.6, 21.5, (0, -8, 4.4), 'M_steel')                      # strength rod
    export('p_splice')

def m_twinbnc():
    fresh()
    box(16, 14, 30, (0, -7, 15), 'P_black')                      # twin shell
    for z in (7.6, 22.4):
        cyl(5.6, 10, (0, 1, z), 'M_nickel')
        cyl(0.8, 2.6, (-5.7, 3.5, z), 'M_nickel', axis='X')
        cyl(0.8, 2.6, ( 5.7, 3.5, z), 'M_nickel', axis='X')
        cyl(3.2, 4, (0, 6.5, z), 'P_white')
        cyl(0.7, 7.5, (0, 7, z), 'M_gold')
    boot(5.5, 3.0, 16, -14, 'P_black')
    export('p_twinbnc')

# ================= USB extras =================
def m_usb3_b():
    fresh()
    # USB 3.0 Type-B plug: classic B with SS hump on top
    box(12.0, 12, 10.4, (0, -6, 5.2), 'M_nickel')
    box(8.0, 12, 3.2, (0, -6, 12.0), 'M_nickel')                 # SS hump
    box(9.6, 2.5, 8.2, (0, 0.6, 5.2), 'P_blue')                  # blue tongue area
    box(13.5, 14, 13.5, (0, -14, 6.9), 'P_black')                # overmold
    boot(4.5, 2.6, 12, -21, 'P_black')
    export('p_usb3_b')

def m_usb3_micro():
    fresh()
    # USB 3.0 Micro-B: two-lobe wide plug
    box(12.2, 6, 1.8, (-4.0, -3, 0.9), 'M_nickel')
    box(7.8, 6, 1.8, (6.2, -3, 0.9), 'M_nickel')
    box(11.0, 1.8, 1.0, (-4.0, 0.2, 0.9), 'P_black')
    box(6.6, 1.8, 1.0, (6.2, 0.2, 0.9), 'P_black')
    box(21.5, 8, 4.4, (0.8, -10, 1.2), 'P_black')
    boot(3.4, 2.0, 9, -14, 'P_black')
    export('p_usb3_micro')

# ================= FireWire =================
def m_firewire6():
    fresh()
    # IEEE 1394a 6-pin plug: rectangular shell with the tapered "bullet" top
    box(11.2, 12, 4.4, (0, -6, 2.2), 'M_nickel')                 # lower shell
    box(7.4, 12, 2.0, (0, -6, 5.4), 'M_nickel')                  # tapered top (narrow)
    box(2.6, 12, 2.2, (-4.2, -6, 4.6), 'M_nickel', rot=(0, math.radians(40), 0))
    box(2.6, 12, 2.2, ( 4.2, -6, 4.6), 'M_nickel', rot=(0, math.radians(-40), 0))
    box(9.4, 1.6, 3.0, (0, 0.2, 2.6), 'P_black')                 # insert in mouth
    for i in range(6):
        x = -3.1 + i * 1.24
        box(0.6, 1.2, 1.6, (x, 0.6, 2.8), 'M_gold')              # 6 contacts
    box(12.6, 12, 7.6, (0, -14.5, 3.4), 'P_dark')                # overmold
    boot(3.8, 2.2, 11, -21, 'P_dark')
    export('p_firewire6')

def m_firewire9():
    fresh()
    # 1394b 9-pin: squarer shell, no taper, 9 contacts in two rows
    box(10.6, 11, 6.6, (0, -5.5, 3.3), 'M_nickel')
    box(8.8, 1.6, 4.8, (0, 0.2, 3.3), 'P_black')
    for i in range(5):
        box(0.55, 1.2, 1.4, (-3.2 + i*1.6, 0.6, 4.2), 'M_gold')
    for i in range(4):
        box(0.55, 1.2, 1.4, (-2.4 + i*1.6, 0.6, 2.4), 'M_gold')
    box(12.0, 11, 8.8, (0, -13.5, 4.0), 'P_black')
    boot(3.6, 2.2, 10, -19.5, 'P_black')
    export('p_firewire9')

# ================= drives =================
def m_sas():
    fresh()
    # SFF-8482 unified SAS plug: SATA-like L keys bridged
    box(18.5, 9, 5.0, (-11, -4.5, 2.5), 'P_black')               # signal segment
    box(2.2, 9, 5.0, (-1, -4.5, 2.5), 'P_black')                 # bridge
    box(21.0, 9, 5.0, (11, -4.5, 2.5), 'P_black')                # power segment
    box(16.5, 2.0, 2.2, (-11, 0.2, 2.5), 'P_ivory')
    box(19.0, 2.0, 2.2, (11, 0.2, 2.5), 'P_ivory')
    box(44, 9, 7.5, (0, -12, 3.75), 'P_dark')
    export('p_sas')

def m_minisas_hd():
    fresh()
    # SFF-8644 external mini-SAS HD plug w/ pull tab
    box(17.5, 26, 7.2, (0, -13, 3.6), 'M_nickel')
    box(15.4, 4, 5.4, (0, 0.8, 3.6), 'P_black')
    box(7.4, 3, 4.4, (-3.9, 1.6, 3.6), 'P_ivory')
    box(7.4, 3, 4.4, ( 3.9, 1.6, 3.6), 'P_ivory')
    box(17.9, 20, 8.6, (0, -32, 4.3), 'P_black')
    box(5, 24, 1.4, (0, -20, 9.6), 'P_blue')                     # pull tab
    box(9, 7, 1.4, (0, -34, 9.6), 'P_blue')
    boot(5.0, 3.0, 12, -42, 'P_black')
    export('p_minisas_hd')

def m_m2():
    fresh()
    # M.2 2280 SSD: green PCB, gold edge fingers, M-key notch
    box(22, 62, 1.2, (0, -32, 2.0), 'P_green')
    for i in range(20):
        x = -9.5 + i * 1.0
        if 5.5 < x < 8.5: continue                               # M-key notch
        box(0.55, 4.5, 1.3, (x, -3.4, 2.0), 'M_gold')
    box(16, 26, 1.6, (0, -30, 2.9), 'P_black')                   # flash package
    box(9, 11, 1.6, (0, -52, 2.9), 'P_black')
    export('p_m2')

def m_matenlok():
    fresh()
    # classic 4-pin "Molex" drive power plug
    box(21.5, 15, 6.6, (0, -7.5, 3.3), 'P_white')
    for i, x in enumerate((-8.4, -2.8, 2.8, 8.4)):
        cyl(1.5, 4, (x, -1, 3.3), 'P_white')
        cyl(0.95, 6.5, (x, 0.5, 3.3), 'M_nickel')
    box(19.5, 6, 5.4, (0, -18, 3.3), 'P_white')
    export('p_matenlok')

# ================= backplanes & crates =================
def m_nim_conn():
    fresh()
    # NIM bin rear connector (ARINC-style block, 2 columns of round pins)
    box(17, 12, 68, (0, -6, 34), 'P_dark')
    for i in range(11):
        z = 6.5 + i * 5.6
        cyl(1.05, 7, (-4.2, 0.6, z), 'M_gold')
        cyl(1.05, 7, ( 4.2, 0.6, z), 'M_gold')
    box(21, 4, 74, (0, -13.5, 37), 'M_steel')                    # mounting bar
    export('p_nim_conn')

def m_atca_zone2():
    fresh()
    # ATCA Zone-2 HM-Zd style block: array of shielded wafer cells
    box(46, 14, 26, (0, -7, 13), 'P_dark')
    for cx in range(8):
        for cz in range(4):
            x = -19.7 + cx * 5.6
            z = 3.9 + cz * 6.1
            box(4.4, 3.5, 4.9, (x, 0.9, z), 'M_gold')
            box(3.2, 1.8, 3.6, (x, 1.9, z), 'P_black')
    export('p_atca_zone2')

def m_amc_edge():
    fresh()
    # µTCA AMC: PCB tongue with 85-pos gold edge fingers (double sided)
    box(74, 32, 1.6, (0, -17, 4.0), 'P_green')
    for i in range(34):
        x = -33 + i * 2.0
        box(0.9, 6.5, 1.7, (x, -3.4, 4.0), 'M_gold')
    box(70, 9, 4.5, (0, -25, 5.4), 'P_black')                    # components hint
    box(12, 4, 1.6, (-31, -34.5, 4.0), 'P_green')
    export('p_amc_edge')

# ================= Molex family =================
def m_microfit():
    fresh()
    # Micro-Fit 3.0 2x2 plug (black)
    for (x, z) in [(-1.5, 1.5), (1.5, 1.5), (-1.5, 4.5), (1.5, 4.5)]:
        box(2.7, 9, 2.7, (x, -4.5, z), 'P_black')
        box(1.7, 1.2, 1.7, (x, 0.1, z), 'P_dark')
    box(6.4, 7, 6.4, (0, -6.5, 3.0), 'P_black')
    box(1.8, 7, 1.2, (0, -6.5, 6.6), 'P_black')
    export('p_microfit')

# ================= RF extras =================
def m_smp():
    fresh()
    # SMP male (limited detent, board mount): shroud + center pin
    cyl(2.4, 4.6, (0, -2.3, 2.4), 'M_gold')
    cyl(1.75, 1.6, (0, 0.5, 2.4), 'M_gold')
    cyl(0.45, 5.5, (0, 0.4, 2.4), 'M_gold')
    box(5.4, 4.4, 4.8, (0, -6.8, 2.4), 'M_nickel')
    export('p_smp')

def m_f_type():
    fresh()
    cyl(4.8, 9, (0, -4.5, 4.8), 'M_nickel')                      # hex/knurl nut
    cyl(3.4, 3.5, (0, 0.7, 4.8), 'M_nickel')
    cyl(0.5, 8, (0, 1.5, 4.8), 'M_steel')                        # wire centre pin
    cyl(3.1, 9, (0, -11.5, 4.8), 'M_nickel')                     # crimp barrel
    boot(3.4, 3.2, 10, -16, 'P_black')
    export('p_f_type')

def m_uhf():
    fresh()
    # PL-259 UHF plug
    n = 18
    for i in range(n):
        a = i / n * 2 * math.pi
        box(1.4, 12, 2.2, (7.6*math.cos(a), -6, 9 + 7.6*math.sin(a)), 'M_nickel', rot=(0, a + math.pi/2, 0))
    cyl(7.4, 12, (0, -6, 9), 'M_nickel')
    cyl(5.4, 5, (0, 1.5, 9), 'M_nickel')
    cyl(3.4, 4, (0, 2.5, 9), 'P_white')
    cyl(1.6, 9, (0, 3.5, 9), 'M_gold')
    cyl(4.4, 12, (0, -17, 9), 'M_nickel')
    boot(4.6, 3.4, 10, -23, 'P_black')
    export('p_uhf')

def m_din716():
    fresh()
    # 7/16 DIN high-power RF
    cyl(13, 18, (0, -9, 13), 'M_nickel', verts=6)                # big hex coupling
    cyl(10.5, 6, (0, 2, 13), 'M_nickel')
    cyl(8.0, 5, (0, 4, 13), 'P_white')
    cyl(3.5, 9, (0, 5, 13), 'M_gold')
    cyl(9, 16, (0, -25, 13), 'M_nickel')
    boot(7, 5, 14, -33, 'P_black')
    export('p_din716')

# ================= MTP variants =================
def mtp_body(colour, angled=False, pins=True):
    box(12.4, 18, 6.4, (0, -9, 3.2), colour)
    if angled:
        box(10.2, 5, 4.6, (0, 0.5, 3.2), 'P_ivory', rot=(0, 0, math.radians(8)))
    else:
        box(10.2, 5, 4.6, (0, 0.5, 3.2), 'P_ivory')
    for i in range(12):
        x = -3.44 + i * 0.625
        cyl(0.12, 0.4, (x, 3.05, 3.2), 'C_ferrule')
    if pins:
        cyl(0.35, 4.5, (-5.3, 1.2, 3.2), 'M_steel')
        cyl(0.35, 4.5, ( 5.3, 1.2, 3.2), 'M_steel')
    box(9, 6, 5.2, (0, -21, 3.2), colour)
    boot(3.0, 1.6, 12, -24, colour if colour != 'P_ivory' else 'P_black')

def m_mtp_f():
    fresh(); mtp_body('P_black', pins=False); export('p_mtp_f')

def m_mtp_apc():
    fresh(); mtp_body('P_green', angled=True, pins=True); export('p_mtp_apc')

# ================= experiment-specific =================
def m_vtrx():
    fresh()
    # VTRx+ optical module: small PCB module with MT-ferrule fibre pigtail
    box(10, 20, 2.4, (0, -12, 2.6), 'P_green')                   # module PCB
    box(8.4, 14, 2.0, (0, -12, 4.6), 'M_steel')                  # lid/shield
    box(6.4, 4, 3.2, (0, -3, 3.4), 'P_dark')                     # optics block
    box(4.9, 3.5, 2.4, (0, 0.2, 3.4), 'P_ivory')                 # MT ferrule
    for i in range(8):
        x = -1.3 + i * 0.37
        cyl(0.1, 0.3, (x, 2.0, 3.4), 'C_ferrule')
    seg = 9                                                       # fibre pigtail
    for i in range(seg):
        t = i / seg
        y = 2.5 + t * 16
        z = 3.4 + math.sin(t * math.pi * 0.5) * 2.5
        cyl(0.7, 2.2, (0, y, z), 'P_aqua')
    for i in range(10):                                          # elink flex tail
        t = i / 10
        box(7, 2.0, 0.5, (0, -22 - t * 8, 2.0 - t * 0.5), 'P_ivory')
    export('p_vtrx')

def m_radiall_hv():
    fresh()
    # Radiall 52-pin multipin HV (CAEN A996 style cable plug)
    cyl(16, 30, (0, -15, 16), 'M_nickel')                        # shell
    cyl(14, 6, (0, 1.5, 16), 'P_dark')                           # insert
    import random
    rows = [(0, 1), (5.0, 7), (8.6, 12), (12.2, 16)]             # radius, count
    for r, n in rows:
        for i in range(n):
            a = i / max(n, 1) * 2 * math.pi + (r * 0.35)
            cyl(0.75, 5.5, (r * math.cos(a), 3.6, 16 + r * math.sin(a)), 'M_gold')
    box(4, 7, 2.6, (0, 0.5, 30.6), 'M_nickel')                   # key
    cyl(17.5, 8, (0, -25, 16), 'M_nickel', verts=24)             # coupling ring
    boot(11, 7, 20, -30, 'P_black')
    export('p_radiall_hv')

def m_redel():
    fresh()
    # LEMO REDEL plastic multipin (K-series style)
    cyl(9.5, 26, (0, -13, 9.5), 'P_dark')                        # plastic shell
    cyl(8.2, 4, (0, 1, 9.5), 'P_ivory')                          # insert
    for ring, n in [(0, 1), (3.4, 6), (6.4, 12)]:
        for i in range(n):
            a = i / max(n, 1) * 2 * math.pi
            cyl(0.6, 4.5, (ring * math.cos(a), 2.8, 9.5 + ring * math.sin(a)), 'M_gold')
    cyl(10.2, 5, (0, -5, 9.5), 'P_red')                          # colour code ring
    boot(6.5, 4, 16, -26, 'P_dark')
    export('p_redel')

def m_mt_ferrule():
    fresh()
    # bare MT-12 ferrule with ribbon (ATLAS SCT/Pixel opto era)
    box(6.4, 8, 2.5, (0, -4, 1.6), 'P_ivory')
    for i in range(12):
        x = -2.2 + i * 0.4
        cyl(0.1, 0.3, (x, 0.15, 1.6), 'C_ferrule')
    cyl(0.32, 3.5, (-3.6, -1.5, 1.6), 'M_steel')
    cyl(0.32, 3.5, ( 3.6, -1.5, 1.6), 'M_steel')
    for i in range(12):                                          # fibre ribbon
        t = i / 12
        box(5.2, 2.2, 0.4, (0, -8.8 - t * 14, 1.6 + math.sin(t * 2.6) * 1.2), 'P_aqua')
    export('p_mt_ferrule')

def m_bnc_plug():
    fresh()
    # BNC male: smooth bayonet sleeve, J-slots as dark inlays, grip knurl behind
    R = 6.2
    cyl(R, 13, (0, -4.5, 6.9), 'M_nickel')                       # one smooth sleeve
    for zs in (1, -1):                                           # two J-slots
        z = 6.9 + zs * (R - 0.2)
        box(1.6, 3.2, 0.7, (0, 0.5, z), 'P_black')               # axial entry
        box(1.6, 0.7, 0.7, (zs * 1.1, -1.2, z - zs*0.35), 'P_black',
            rot=(0, math.radians(-30 * zs), 0))                  # J turn
    cyl(3.1, 4.0, (0, 1.2, 6.9), 'P_white')                      # PTFE
    cyl(0.65, 8.5, (0, 2.6, 6.9), 'M_gold')                      # pin
    m = 24
    for i in range(m):                                           # grip knurl (slimmer)
        a = i / m * 2 * math.pi
        box(1.1, 5.5, 1.0, (4.8*math.cos(a), -14.5, 6.9 + 4.8*math.sin(a)),
            'M_nickel', rot=(0, a + math.pi/2, 0))
    cyl(4.75, 5.5, (0, -14.5, 6.9), 'M_nickel')
    cyl(3.9, 7, (0, -20, 6.9), 'M_nickel')
    boot(3.5, 2.3, 11, -23.5, 'P_black')
    export('p_bnc_plug')

def m_xlr_f():
    fresh()
    # XLR female inline: shell with 3-socket face + latch
    cyl(9.6, 16, (0, -8, 9.6), 'M_nickel')
    cyl(8.4, 1.6, (0, 0.4, 9.6), 'P_dark')
    for (dx, dz) in [(0, 3.4), (-3.0, -1.8), (3.0, -1.8)]:
        cyl(1.15, 1.2, (dx, 0.9, 9.6 + dz), 'P_black')           # sockets read as holes
    box(3.2, 8, 1.6, (0, -4, 19.0), 'M_nickel')                  # latch
    cyl(9.9, 12, (0, -20, 9.6), 'P_black')
    boot(5.0, 2.6, 14, -26, 'P_black')
    export('p_xlr_f')

def m_shv_plug():
    fresh()
    # SHV male: smooth bayonet sleeve w/ J-slot inlays, deep recessed insulator
    R = 9.0
    cyl(R, 16, (0, -6, 9.2), 'M_nickel')
    for zs in (1, -1):
        z = 9.2 + zs * (R - 0.2)
        box(2.0, 4.0, 0.8, (0, 0.4, z), 'P_black')
        box(2.0, 0.8, 0.8, (zs * 1.4, -1.8, z - zs*0.45), 'P_black',
            rot=(0, math.radians(-30 * zs), 0))
    cyl(5.2, 9, (0, -3.0, 9.2), 'P_white')                       # deep insulator
    cyl(2.6, 1.5, (0, 1.4, 9.2), 'P_black')                      # recessed contact
    m = 24
    for i in range(m):
        a = i / m * 2 * math.pi
        box(1.2, 6, 1.1, (6.6*math.cos(a), -18.5, 9.2 + 6.6*math.sin(a)),
            'M_nickel', rot=(0, a + math.pi/2, 0))
    cyl(6.5, 6, (0, -18.5, 9.2), 'M_nickel')
    cyl(5.0, 9, (0, -25.5, 9.2), 'M_nickel')
    boot(4.5, 2.8, 13, -30, 'P_black')
    export('p_shv_plug')

def m_df57():
    fresh()
    # Hirose DF57 2-pos micro crimp pair (CMS 2S module LV/HV entry)
    box(5.2, 4.2, 2.0, (0, -2.1, 1.0), 'P_ivory')                # receptacle
    box(4.2, 1.6, 1.4, (0, 0.4, 1.0), 'P_ivory')
    for x in (-1.2, 1.2):
        box(0.7, 1.2, 0.9, (x, 0.5, 1.0), 'M_gold')
        cyl(0.55, 9, (x, -8.5, 1.2), 'P_red' if x > 0 else 'P_black')  # wires
    box(5.8, 4.6, 1.1, (0, -2.0, 2.4), 'M_steel')                # metal retainer
    export('p_df57')

# ================= FireFly =================
def m_firefly():
    fresh()
    # Samtec FireFly micro flyover module on its board connector
    box(14, 20, 2.2, (0, -10, 4.2), 'M_nickel')                  # module lid
    box(12.6, 18, 2.6, (0, -10, 2.0), 'P_black')                 # body/interposer
    box(10, 3.5, 1.0, (0, -23.5, 4.6), 'P_black')                # strain relief
    for i in range(12):                                          # ribbon "flyover"
        t = i / 12
        y = -25 - t * 16
        z = 4.6 + math.sin(t * math.pi * 0.9) * 5
        box(9.6, 1.9, 0.55, (0, y, z), 'P_ivory')
    box(2.6, 4, 1.4, (-6.9, -4, 5.0), 'M_steel')                 # latch ears
    box(2.6, 4, 1.4, ( 6.9, -4, 5.0), 'M_steel')
    export('p_firefly')


def m_dip():
    fresh()
    # DIP-8 slide switch bank: red body, white actuators, gull legs
    box(20, 10, 5.5, (0, -5, 2.75), 'P_red')
    for i in range(8):
        x = -7.7 + i * 2.2
        box(1.3, 3.2, 0.9, (x, -3.2, 5.8), 'P_white')            # slide slot bed
        box(1.3, 1.5, 1.5, (x, -2.5, 6.1), 'P_white')            # actuator nub
    for i in range(8):
        x = -7.7 + i * 2.2
        box(0.9, 2.2, 0.5, (x, 0.6, 0.6), 'M_nickel')            # legs near
        box(0.9, 2.2, 0.5, (x, -10.6, 0.6), 'M_nickel')          # legs far
    box(2.2, 2.2, 0.4, (-8.9, -5, 5.55), 'P_white')              # pin-1 dot
    export('p_dip')

def m_button():
    fresh()
    # 6 mm THT tactile switch + one with a red cap
    def tact(x, cap=None):
        box(6.2, 6.2, 3.6, (x, -3.1, 1.8), 'P_black')
        box(6.4, 6.4, 0.8, (x, -3.1, 3.6), 'M_steel')            # metal top plate
        cyl(1.75, 1.6, (x, -3.1, 4.6), 'P_black', axis='Z')      # plunger
        if cap:
            cyl(3.4, 2.4, (x, -3.1, 5.4), cap, axis='Z')         # round cap
        for dx in (-2.25, 2.25):
            for dy in (-6.2, 0):
                box(0.7, 0.4, 3.2, (x + dx, dy - 0.0 - 3.1 + (3.1 if dy==0 else -0.0), -1.2), 'M_nickel')
    tact(-6.5)
    tact(6.5, 'P_red')
    export('p_button')


def m_rj45_plug():
    fresh()
    # 8P8C modular cable plug: body, 8 gold blades at top of face, latch below
    box(11.7, 20, 8.1, (0, -10, 4.05), 'P_ivory')
    box(10.5, 2.0, 6.9, (0, 0.2, 4.05), 'P_ivory')
    for i in range(8):
        x = -3.57 + i * 1.02
        box(0.55, 2.6, 2.6, (x, 0.4, 6.4), 'M_gold')             # contact blades
    box(4.6, 12, 1.5, (0, -9, -0.9), 'P_ivory', rot=(math.radians(7), 0, 0))  # latch
    box(6.2, 6, 5.2, (0, -22.5, 4.05), 'P_ivory')
    boot(3.4, 2.2, 10, -25, 'P_dark')
    export('p_rj45_plug')

ALL = [m_rj45_plug, m_dip, m_button, m_lc, m_lc_duplex, m_sc, m_st, m_fc, m_mtp, m_mu, m_e2000,
       m_splice, m_twinbnc,
       m_usb3_b, m_usb3_micro, m_firewire6, m_firewire9,
       m_sas, m_minisas_hd, m_m2, m_matenlok,
       m_nim_conn, m_atca_zone2, m_amc_edge, m_microfit,
       m_smp, m_f_type, m_uhf, m_din716,
       m_mtp_f, m_mtp_apc, m_firefly,
       m_vtrx, m_radiall_hv, m_redel, m_mt_ferrule, m_df57,
       m_bnc_plug, m_xlr_f, m_shv_plug,
       m_sfp, m_qsfp, m_shv, m_mhv, m_triax,
       m_toslink, m_rca, m_xlr_m, m_rj11, m_gpib, m_minifit,
       m_displayport, m_hdmi_mini, m_powerpole, m_dac]

only = set(sys.argv[2:])
for f in ALL:
    name = f.__name__[2:]
    if only and name not in only: continue
    f()
print('ALL DONE')
