# ruff: noqa: E501
"""Generate the original LZ Agent mechanical avatar with Blender's Python API."""
from __future__ import annotations

import math
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
AVATAR = ROOT / "assets" / "avatar"
MODELS = AVATAR / "models"
SOURCE = AVATAR / "source"
ANIMATIONS = (
    "Idle_1", "Idle_2", "Idle_3", "Listening", "Thinking", "Speaking", "Acting",
    "Needs_Approval", "Success", "Warning", "Error", "Offline", "Private",
)


def material(name: str, color: tuple[float, float, float, float], metallic=0.0, emission=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = 0.22 if metallic else 0.32
    if emission:
        shader.inputs["Emission Color"].default_value = color
        shader.inputs["Emission Strength"].default_value = emission
    return mat


def uv(name, location, scale, mat, segments, rings):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    bevel = obj.modifiers.new("SoftMechanicalEdges", "BEVEL")
    bevel.width = 0.025
    bevel.segments = 2
    return obj


def cylinder(name, location, radius, depth, mat, vertices, rotation=(math.pi / 2, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    return obj


def text_mesh(name, body, location, scale, mat):
    bpy.ops.object.text_add(location=location, rotation=(math.pi / 2, 0, 0))
    obj = bpy.context.object
    obj.name = name
    obj.data.body = body
    obj.data.align_x = "CENTER"
    obj.data.align_y = "CENTER"
    obj.data.extrude = 0.025
    obj.data.bevel_depth = 0.008
    obj.scale = (scale, scale, scale)
    obj.data.materials.append(mat)
    bpy.ops.object.convert(target="MESH")
    return obj


def make_rig():
    bpy.ops.object.armature_add(enter_editmode=True, location=(0, 0, 0))
    arm = bpy.context.object
    arm.name = "LZ_Agent_Rig"
    arm.show_in_front = True
    base = arm.data.edit_bones[0]
    base.name, base.head, base.tail = "Root", Vector((0, 0, 0)), Vector((0, 0, 0.5))
    specs = {
        "Pelvis": ((0, 0, 1.8), (0, 0, 2.2), "Root"),
        "Spine": ((0, 0, 2.0), (0, 0, 3.0), "Pelvis"),
        "Neck": ((0, 0, 3.0), (0, 0, 3.35), "Spine"),
        "Head": ((0, 0, 3.3), (0, 0, 4.2), "Neck"),
        "EyesControl": ((0, -0.8, 3.8), (0, -1.0, 3.8), "Head"),
        "MouthControl": ((0, -0.8, 3.5), (0, -1.0, 3.5), "Head"),
        "LightsControl": ((0, -0.6, 2.55), (0, -0.8, 2.55), "Spine"),
    }
    for side, sign in (("L", -1), ("R", 1)):
        specs.update({
            f"Shoulder_{side}": ((0.55 * sign, 0, 2.9), (0.95 * sign, 0, 2.9), "Spine"),
            f"UpperArm_{side}": ((0.9 * sign, 0, 2.9), (1.4 * sign, 0, 2.45), f"Shoulder_{side}"),
            f"Forearm_{side}": ((1.4 * sign, 0, 2.45), (1.65 * sign, 0, 1.95), f"UpperArm_{side}"),
            f"Hand_{side}": ((1.65 * sign, 0, 1.95), (1.75 * sign, 0, 1.65), f"Forearm_{side}"),
            f"Thigh_{side}": ((0.38 * sign, 0, 1.85), (0.45 * sign, 0, 1.05), "Pelvis"),
            f"Shin_{side}": ((0.45 * sign, 0, 1.05), (0.45 * sign, 0, 0.35), f"Thigh_{side}"),
            f"Foot_{side}": ((0.45 * sign, 0, 0.35), (0.45 * sign, -0.45, 0.15), f"Shin_{side}"),
        })
        for finger in range(1, 6):
            specs[f"Finger_{side}_{finger}"] = (
                (1.72 * sign, -0.04 * finger, 1.8),
                (1.9 * sign, -0.04 * finger, 1.7),
                f"Hand_{side}",
            )
    for name, (head, tail, parent) in specs.items():
        bone = arm.data.edit_bones.new(name)
        bone.head, bone.tail = head, tail
        bone.parent = arm.data.edit_bones[parent]
    bpy.ops.object.mode_set(mode="OBJECT")
    return arm


def bone_parent(obj, arm, bone):
    world = obj.matrix_world.copy()
    obj.parent = arm
    obj.parent_type = "BONE"
    obj.parent_bone = bone
    obj.matrix_world = world


def animate(arm):
    arm.animation_data_create()
    for index, name in enumerate(ANIMATIONS):
        action = bpy.data.actions.new(name)
        action.use_fake_user = True
        arm.animation_data.action = action
        for frame in (1, 16, 32):
            phase = math.sin((frame / 32) * math.tau + index * 0.3)
            head = arm.pose.bones["Head"]
            head.rotation_mode = "XYZ"
            head.rotation_euler[2] = phase * (0.015 if name.startswith("Idle") else 0.05)
            head.keyframe_insert("rotation_euler", frame=frame)
            mouth = arm.pose.bones["MouthControl"]
            mouth.scale[2] = 1.0 + (abs(phase) * 0.8 if name == "Speaking" else 0.0)
            mouth.keyframe_insert("scale", frame=frame)
            for side, direction in (("L", -1), ("R", 1)):
                upper = arm.pose.bones[f"UpperArm_{side}"]
                upper.rotation_mode = "XYZ"
                gesture = 0.45 if name in {"Speaking", "Acting", "Needs_Approval", "Success"} else 0.04
                upper.rotation_euler[1] = direction * gesture * (0.7 + phase * 0.3)
                upper.keyframe_insert("rotation_euler", frame=frame)
        action.frame_start, action.frame_end = 1, 32
    arm.animation_data.action = bpy.data.actions.get("Idle_1")


def build(level: str, segments: int, rings: int):
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.armatures, bpy.data.meshes, bpy.data.materials, bpy.data.actions):
        for item in list(block):
            block.remove(item, do_unlink=True)
    white = material("PearlWhite", (0.82, 0.86, 0.9, 1))
    silver = material("SilverMetal", (0.3, 0.34, 0.38, 1), metallic=0.85)
    graphite = material("Graphite", (0.015, 0.02, 0.03, 1), metallic=0.35)
    cyan = material("CyanEmission", (0.0, 0.55, 1.0, 1), metallic=0.2, emission=7.0)
    arm = make_rig()
    parts = []
    parts.append((uv("HeadShell", (0, 0, 3.75), (1.05, 0.9, 0.9), white, segments, rings), "Head"))
    parts.append((uv("FaceVisor", (0, -0.88, 3.75), (0.82, 0.19, 0.62), graphite, segments, rings), "Head"))
    for x in (-0.32, 0.32):
        parts.append((uv(f"Eye_{x}", (x, -1.08, 3.87), (0.13, 0.05, 0.16), cyan, max(12, segments // 2), max(6, rings // 2)), "EyesControl"))
    parts.append((uv("DigitalMouth", (0, -1.09, 3.48), (0.3, 0.035, 0.045), cyan, max(12, segments // 2), max(6, rings // 2)), "MouthControl"))
    for x in (-1.02, 1.02):
        parts.append((cylinder(f"HeadSensor_{x}", (x, 0, 3.75), 0.3, 0.16, silver, segments, (0, math.pi / 2, 0)), "Head"))
        parts.append((cylinder(f"SensorLight_{x}", (x * 1.09, 0, 3.75), 0.17, 0.04, cyan, segments, (0, math.pi / 2, 0)), "Head"))
    parts.append((uv("Torso", (0, 0, 2.45), (0.82, 0.58, 0.9), white, segments, rings), "Spine"))
    parts.append((cylinder("ChestPanel", (0, -0.59, 2.55), 0.34, 0.07, graphite, segments), "Spine"))
    parts.append((cylinder("LZEmblem", (0, -0.64, 2.55), 0.24, 0.025, cyan, segments), "LightsControl"))
    parts.append((text_mesh("LZLetters", "LZ", (0, -0.69, 2.55), 0.18, graphite), "LightsControl"))
    for side, sign in (("L", -1), ("R", 1)):
        parts += [
            (uv(f"Shoulder_{side}", (0.85 * sign, 0, 2.85), (0.32, 0.34, 0.34), silver, segments, rings), f"Shoulder_{side}"),
            (cylinder(f"UpperArm_{side}", (1.15 * sign, 0, 2.62), 0.2, 0.62, white, segments, (0, math.pi / 4 * sign, math.pi / 2)), f"UpperArm_{side}"),
            (uv(f"Elbow_{side}", (1.42 * sign, 0, 2.35), (0.2, 0.2, 0.2), graphite, segments, rings), f"Forearm_{side}"),
            (cylinder(f"Forearm_{side}", (1.55 * sign, 0, 2.12), 0.19, 0.5, white, segments, (0, math.pi / 7 * sign, math.pi / 2)), f"Forearm_{side}"),
            (uv(f"Hand_{side}", (1.72 * sign, -0.02, 1.82), (0.27, 0.22, 0.3), silver, segments, rings), f"Hand_{side}"),
            (cylinder(f"Thigh_{side}", (0.4 * sign, 0, 1.48), 0.3, 0.72, white, segments, (0, 0, 0)), f"Thigh_{side}"),
            (uv(f"Knee_{side}", (0.42 * sign, -0.04, 1.05), (0.3, 0.3, 0.27), graphite, segments, rings), f"Shin_{side}"),
            (cylinder(f"Shin_{side}", (0.43 * sign, 0, 0.72), 0.31, 0.62, white, segments, (0, 0, 0)), f"Shin_{side}"),
            (uv(f"Foot_{side}", (0.43 * sign, -0.18, 0.27), (0.48, 0.65, 0.25), silver, segments, rings), f"Foot_{side}"),
        ]
        for finger in range(1, 6):
            y = -0.2 + finger * 0.08
            parts.append((cylinder(f"Finger_{side}_{finger}", (1.86 * sign, y, 1.72), 0.045, 0.24, silver, max(8, segments // 3), (0, math.pi / 2, 0)), f"Finger_{side}_{finger}"))
    for obj, bone in parts:
        bone_parent(obj, arm, bone)
    arm["lz_quality_level"] = level
    arm["accessibility_reduced_motion_supported"] = True
    arm["fallback_2d_supported"] = True
    animate(arm)
    return arm


def export(level: str, segments: int, rings: int, save_master=False):
    arm = build(level, segments, rings)
    if save_master:
        bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE / "LZ_Agent_Master.blend"))
    bpy.ops.object.select_all(action="SELECT")
    bpy.context.view_layer.objects.active = arm
    bpy.ops.export_scene.gltf(
        filepath=str(MODELS / f"LZ_Agent_{level}.glb"),
        export_format="GLB",
        use_selection=True,
        export_animations=True,
        export_skins=True,
        export_yup=True,
    )


def main():
    for directory in (MODELS, SOURCE):
        directory.mkdir(parents=True, exist_ok=True)
    export("Pro", 48, 24, save_master=True)
    export("Standard", 32, 16)
    export("Lite", 16, 8)
    print("LZ Agent avatar generated:", AVATAR)


if __name__ == "__main__":
    main()
