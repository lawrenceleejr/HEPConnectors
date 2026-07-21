#!/usr/bin/env python3
"""Render connector GLB models to consistent catalog stills (Cycles, house style).

Usage: python3 render_connectors.py <glb_dir> <out_dir> [--preview] [name ...]
Style: warm key + neutral fill area lighting inside an enclosing soft emissive
sphere; transparent film with shadow catcher; consistent 3/4 camera, DOF on.
"""
import bpy, sys, json, math, os
from mathutils import Vector

args = [a for a in sys.argv[1:] if a not in ('--preview','--tiny','--spin')]
PREVIEW = '--preview' in sys.argv or '--tiny' in sys.argv or '--spin' in sys.argv
TINY = '--tiny' in sys.argv or '--spin' in sys.argv
SPIN = '--spin' in sys.argv
GLB_DIR, OUT_DIR = args[0], args[1]
ONLY = set(args[2:])

HERE = os.path.dirname(os.path.abspath(__file__))
TW_PATH = os.path.join(HERE, 'view_tweaks.json')
TWEAK = json.load(open(TW_PATH)) if os.path.exists(TW_PATH) else {}

def set_temp(light, kelvin):
    try:
        light.data.use_temperature = True
        light.data.temperature = kelvin
    except AttributeError:
        pass

def build_stage():
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = (12 if TINY else 32) if PREVIEW else 128
    sc.cycles.use_denoising = True
    sc.cycles.device = 'CPU'
    sc.render.resolution_x = (300 if TINY else 480) if PREVIEW else 880
    sc.render.resolution_y = (178 if TINY else 284) if PREVIEW else 520
    sc.render.film_transparent = True
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'AgX - Medium High Contrast'
    sc.view_settings.exposure = 0.15

    # enclosing near-neutral soft sphere (contained, even light)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=60)
    sph = bpy.context.object; sph.name = 'EnvSphere'
    m = bpy.data.materials.new('env'); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = (1.0, 0.97, 0.92, 1)
    em.inputs['Strength'].default_value = 0.5
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(em.outputs[0], out.inputs[0])
    sph.data.materials.append(m)
    sph.visible_camera = False
    sph.visible_shadow = False

    def area(name, loc, rot, size, power, kelvin):
        bpy.ops.object.light_add(type='AREA', location=loc, rotation=rot)
        L = bpy.context.object; L.name = name
        L.data.size = size; L.data.energy = power
        set_temp(L, kelvin)
    # warm key, neutral fill + cool rim so metals read as metal
    area('Key',  ( 6,  -7,  8), (math.radians(50), 0, math.radians( 40)), 10, 320, 3500)
    area('Fill', (-8,  -5,  4), (math.radians(65), 0, math.radians(-55)), 12, 110, 5000)
    area('Rim',  ( 0,  9.5, 7), (math.radians(-45), 0, 0),                 8, 260, 5600)

    bpy.ops.mesh.primitive_plane_add(size=80, location=(0, 0, 0))
    bpy.context.object.name = 'Ground'
    bpy.context.object.is_shadow_catcher = True

    bpy.ops.object.camera_add()
    cam = bpy.context.object; cam.name = 'Cam'
    cam.data.lens = 40
    cam.data.dof.use_dof = True
    cam.data.dof.aperture_fstop = 5.6
    sc.camera = cam
    return cam

def material_pass():
    """Give flat glTF materials sensible metal/plastic response."""
    for m in bpy.data.materials:
        if not m.use_nodes or m.name == 'env': continue
        bsdf = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if not bsdf: continue
        # explicit hints from parametric models: P_* plastic, M_* metal, C_* ceramic/matte
        base = m.name.split('.')[0]
        if base.startswith('P_') or base.startswith('C_'):
            bsdf.inputs['Metallic'].default_value = 0.0
            bsdf.inputs['Roughness'].default_value = 0.5 if base.startswith('P_') else 0.35
            continue
        if base.startswith('M_'):
            bsdf.inputs['Metallic'].default_value = 1.0
            bsdf.inputs['Roughness'].default_value = 0.32
            continue
        r, g, b, a = bsdf.inputs['Base Color'].default_value
        mx, mn = max(r, g, b), min(r, g, b)
        sat = 0 if mx == 0 else (mx - mn) / mx
        lum = 0.2126*r + 0.7152*g + 0.0722*b
        goldish = sat > 0.2 and r > g > b and lum > 0.12
        metal_gray = sat <= 0.22 and lum > 0.28
        if goldish:
            bsdf.inputs['Metallic'].default_value = 1.0
            bsdf.inputs['Roughness'].default_value = 0.25
        elif metal_gray:
            bsdf.inputs['Metallic'].default_value = 1.0
            bsdf.inputs['Roughness'].default_value = 0.35
        else:
            bsdf.inputs['Metallic'].default_value = 0.0
            bsdf.inputs['Roughness'].default_value = 0.45


# vendor CAD ships colorless; recolor near-white materials (or force) per model
NICKEL = (0.55, 0.54, 0.50, 1.0, 0.35)   # r,g,b,metallic,rough
TINT = {
  'v_adamtech_dpc-f-s-ra-smt-bl': {'white': NICKEL},
  'v_adamtech_mchdmi-s-ra-1-smt': {'white': NICKEL},
  'v_adamtech_qsfp1-dd-emi-hsk-lp-s3': {'white': NICKEL},
  'v_adamtech_sfc-1-emi': {'white': NICKEL},
  'v_neutrik_nc3mxx': {'white': NICKEL},
  'v_norcomp_111-024-113L001': {'white': NICKEL},
  'v_samesky_rcj-041': {'white': NICKEL},
  'v_wurth_60412042241503': {'white': NICKEL},
  'v_wurth_67012002221502': {'white': NICKEL},
  'v_wurth_61400416121': {'white': NICKEL},
  'v_wurth_643150100604': {'white': NICKEL},
  'v_wurth_643160100604': {'white': NICKEL},
  'v_anderson_pp15-45': {'force': (0.48, 0.05, 0.045, 0.0, 0.45)},
  'v_qualtek_744w-00-01': {'force': (0.05, 0.05, 0.055, 0.0, 0.45)},
  'v_wurth_649004113322': {'force': (0.82, 0.79, 0.70, 0.0, 0.5)},
  'v_radiall_bnc_plug': {'white': NICKEL},
  'v_radiall_tnc_plug': {'white': NICKEL},
  'v_radiall_n_plug': {'white': NICKEL},
  'v_radiall_716_plug': {'white': NICKEL},
  'v_radiall_smp': {'white': NICKEL},
  'v_radiall_mhv_plug': {'white': NICKEL},
  'v_radiall_shv_plug': {'white': NICKEL},
  'v_radiall_shv_jack': {'white': NICKEL},
  'v_adamtech_rj11_plug': {'force': (0.80, 0.78, 0.72, 0.0, 0.25)},
  'v_adamtech_rj45_plug': {'force': (0.80, 0.78, 0.72, 0.0, 0.25)},
  'v_neutrik_lc_duplex': {'force': (0.06, 0.06, 0.065, 0.0, 0.4)},
  'v_bkl_f_plug': {'white': NICKEL},
  'v_cliff_fc': {'white': NICKEL},
}

def apply_tint(name):
    spec = TINT.get(name)
    if not spec: return
    mode, (r, g, b, met, rgh) = next(iter(spec.items()))
    for m in bpy.data.materials:
        if not m.use_nodes or m.name == 'env': continue
        bsdf = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if not bsdf: continue
        cr, cg, cb, ca = bsdf.inputs['Base Color'].default_value
        if mode == 'force' or min(cr, cg, cb) > 0.55:
            bsdf.inputs['Base Color'].default_value = (r, g, b, 1)
            bsdf.inputs['Metallic'].default_value = met
            bsdf.inputs['Roughness'].default_value = rgh

def frame_and_render(name, glb, out_png):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=glb)
    objs = [o for o in set(bpy.data.objects) - before if o.type == 'MESH']
    if not objs:
        print('NO MESH', name); return False
    for o in objs:                      # STEP w/o colors -> GLB w/o materials
        if not o.data.materials:
            am = bpy.data.materials.new('auto'); am.use_nodes = True
            o.data.materials.append(am)
    material_pass()
    apply_tint(name)

    bpy.ops.object.empty_add(); root = bpy.context.object; root.name = 'Root'
    for o in objs: o.parent = root

    tw = TWEAK.get(name, {})
    root.rotation_euler = (math.radians(tw.get('rx', 0)),
                           math.radians(tw.get('ry', 0)),
                           math.radians(tw.get('rz', 180)))
    bpy.context.view_layer.update()

    def world_bounds():
        pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
        lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
        hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
        return lo, hi
    lo, hi = world_bounds()
    dim = hi - lo
    s = 4.0 / max(dim.x, dim.y, dim.z)
    root.scale = (s, s, s)
    bpy.context.view_layer.update()
    lo, hi = world_bounds()
    ctr = (lo + hi) / 2
    root.location = Vector((-ctr.x, -ctr.y, -lo.z))
    bpy.context.view_layer.update()
    lo, hi = world_bounds(); ctr = (lo + hi) / 2
    radius = max((hi - lo).length / 2, 0.1)

    cam = bpy.data.objects['Cam']
    az = math.radians(tw.get('az', -32))
    el = math.radians(tw.get('el', 20))
    cam.data.lens = tw.get('lens', 40)
    fov = min(cam.data.angle_x, cam.data.angle_y)
    dist = tw.get('zoom', 0.92) * radius / math.sin(fov / 2) * 1.08
    cam.location = (ctr.x + dist*math.cos(el)*math.sin(az),
                    ctr.y - dist*math.cos(el)*math.cos(az),
                    ctr.z + dist*math.sin(el))
    d = Vector(ctr) - cam.location
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    cam.data.dof.focus_distance = d.length

    bpy.context.scene.render.filepath = out_png
    bpy.ops.render.render(write_still=True)

    for o in objs: bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.objects.remove(root, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        if mesh.users == 0: bpy.data.meshes.remove(mesh)
    for m in list(bpy.data.materials):
        if m.users == 0 and m.name != 'env': bpy.data.materials.remove(m)
    return True

def main():
    import pathlib
    glbs = sorted(pathlib.Path(GLB_DIR).glob('*.glb'))
    if ONLY: glbs = [g for g in glbs if g.stem in ONLY]
    os.makedirs(OUT_DIR, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    build_stage()
    for g in glbs:
        print('render', g.stem, flush=True)
        if SPIN:
            for yaw in (0, 90, 180, 270):
                TWEAK.setdefault(g.stem, {})['rz'] = yaw
                frame_and_render(g.stem, str(g), os.path.join(OUT_DIR, f'{g.stem}__{yaw:03d}.png'))
        else:
            frame_and_render(g.stem, str(g), os.path.join(OUT_DIR, g.stem + '.png'))
    print('DONE')

if __name__ == '__main__':
    main()
