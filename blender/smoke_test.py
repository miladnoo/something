"""Headless Blender smoke test.

Run with:
    blender --background --python blender/smoke_test.py

Builds a procedural snowman scene, verifies geometry, exports a GLB,
and renders a small Cycles (CPU) thumbnail. Prints a PASS/FAIL summary
and exits non-zero if any check fails.
"""

import os
import sys

import bpy

CHECKS = []


def check(name, ok, detail=""):
    CHECKS.append((name, bool(ok), detail))
    print(("PASS" if ok else "FAIL") + f"  {name}" + (f"  ({detail})" if detail else ""))


def main():
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(out_dir, exist_ok=True)
    glb_path = os.path.join(out_dir, "snowman.glb")
    png_path = os.path.join(out_dir, "snowman.png")

    # ---------------------------------------------------------------- scene
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene

    def add_sphere(radius, location, name):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=location, segments=24, ring_count=16)
        obj = bpy.context.active_object
        obj.name = name
        bpy.ops.object.shade_smooth()
        return obj

    def add_mat(obj, color):
        mat = bpy.data.materials.new(obj.name + "_mat")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        obj.data.materials.append(mat)

    # Snowman: body, head, nose, eyes
    body = add_sphere(1.0, (0, 0, 1.0), "Body")
    head = add_sphere(0.6, (0, 0, 2.35), "Head")
    nose = add_sphere(0.12, (0, -0.62, 2.45), "Nose")
    eye_l = add_sphere(0.07, (-0.18, -0.55, 2.62), "EyeL")
    eye_r = add_sphere(0.07, (0.18, -0.55, 2.62), "EyeR")

    add_mat(body, (1.0, 1.0, 1.0))
    add_mat(head, (1.0, 1.0, 1.0))
    add_mat(nose, (1.0, 0.35, 0.05))
    add_mat(eye_l, (0.02, 0.02, 0.02))
    add_mat(eye_r, (0.02, 0.02, 0.02))

    mesh_objs = [o for o in scene.objects if o.type == "MESH"]
    check("scene_built", len(mesh_objs) == 5, f"{len(mesh_objs)} mesh objects")
    total_verts = sum(len(o.data.vertices) for o in mesh_objs)
    check("geometry_nonempty", total_verts > 100, f"{total_verts} verts total")

    # Light + camera
    bpy.ops.object.light_add(type="SUN", location=(4, -4, 6))
    sun = bpy.context.active_object
    sun.data.energy = 4.0

    bpy.ops.object.camera_add(location=(0, -7.5, 2.2))
    cam = bpy.context.active_object
    scene.camera = cam
    target = bpy.data.objects.new("CamTarget", None)
    target.location = (0, 0, 1.7)
    scene.collection.objects.link(target)
    con = cam.constraints.new(type="TRACK_TO")
    con.target = target

    world = bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.45, 0.65, 0.9, 1.0)  # sky blue
    bg.inputs[1].default_value = 1.0

    # ---------------------------------------------------------------- GLB export
    try:
        bpy.ops.export_scene.gltf(filepath=glb_path, export_format="GLB", export_apply=True)
    except Exception as exc:  # report as a failed check instead of aborting the run
        print(f"GLB export error: {exc}")
    glb_size = os.path.getsize(glb_path) if os.path.exists(glb_path) else 0
    check("glb_exported", glb_size > 1000, f"{glb_size} bytes")
    if glb_size:
        with open(glb_path, "rb") as f:
            magic = f.read(4)
        check("glb_magic", magic == b"glTF", repr(magic))

    # ---------------------------------------------------------------- render
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 16
    scene.cycles.use_denoising = False
    scene.render.resolution_x = 640
    scene.render.resolution_y = 360
    scene.render.filepath = png_path
    try:
        bpy.ops.render.render(write_still=True)
    except Exception as exc:
        print(f"Render error: {exc}")

    png_size = os.path.getsize(png_path) if os.path.exists(png_path) else 0
    check("png_rendered", png_size > 10000, f"{png_size} bytes")
    if png_size:
        with open(png_path, "rb") as f:
            sig = f.read(8)
        check("png_signature", sig == b"\x89PNG\r\n\x1a\n", repr(sig))

    # ---------------------------------------------------------------- summary
    failed = [c for c in CHECKS if not c[1]]
    print(f"\n{len(CHECKS) - len(failed)}/{len(CHECKS)} checks passed")
    if failed:
        print("SMOKE TEST: FAIL")
        sys.exit(1)
    print("SMOKE TEST: PASS")
    print(f"GLB: {glb_path}\nPNG: {png_path}")


main()
