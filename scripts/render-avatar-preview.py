"""Render a deterministic review image from the generated master avatar."""
from pathlib import Path

import bpy
from mathutils import Vector

root = Path(__file__).resolve().parents[1]
output = root / "assets" / "avatar" / "references" / "generated-preview.png"


def look_at(obj, point):
    obj.rotation_euler = (Vector(point) - obj.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.object.camera_add(location=(6.8, -9.5, 5.2))
camera = bpy.context.object
camera.data.lens = 58
look_at(camera, (0, 0, 2.1))
bpy.context.scene.camera = camera

for location, energy, size, color in (
    ((-4, -5, 8), 1500, 4.0, (0.75, 0.9, 1.0)),
    ((5, -2, 5), 1100, 3.0, (0.2, 0.7, 1.0)),
    ((0, 5, 7), 1300, 3.0, (0.35, 0.55, 1.0)),
):
    bpy.ops.object.light_add(type="AREA", location=location)
    light = bpy.context.object
    light.data.energy, light.data.shape, light.data.size = energy, "DISK", size
    light.data.color = color
    look_at(light, (0, 0, 2.0))

bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
floor = bpy.context.object
floor.name = "PreviewFloor"
floor_mat = bpy.data.materials.new("PreviewFloorMaterial")
floor_mat.diffuse_color = (0.004, 0.012, 0.025, 1)
floor.data.materials.append(floor_mat)

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 900
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = str(output)
scene.render.film_transparent = False
scene.world.color = (0.002, 0.006, 0.015)
bpy.ops.render.render(write_still=True)
print("Preview rendered:", output)
