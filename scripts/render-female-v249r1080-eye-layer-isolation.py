"""Render matched control/selected eye layers to verify the cornea wiring repair."""
import json
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]; ASSETS=ROOT/"assets-source/aevrynd-character"
CONTROL=ASSETS/"aevrynd-female-cc0-canthus-contour-r1079-study.blend"; SELECTED=ASSETS/"aevrynd-female-cc0-balanced-eye-optics-r1080-study.blend"
REPORT=ASSETS/"female-v249-mainline-r1080-eye-layer-isolation.render.json"; OUT=ROOT.parent/"Temp/female-realism/v249r1080-eye-optics-isolation"


def look_at(obj,target): obj.rotation_euler=(Vector(target)-obj.location).to_track_quat("-Z","Y").to_euler()


def render_source(path,prefix):
    bpy.ops.wm.open_mainfile(filepath=str(path)); scene=bpy.context.scene; scene.frame_set(1); scene.view_settings.view_transform="Standard"; scene.view_settings.look="None"; scene.view_settings.exposure=0.0; scene.view_settings.gamma=1.0
    camera=scene.camera; camera.location=(0.0,-0.405,1.449); camera.data.lens=135; look_at(camera,(0.0,-0.105,1.449)); scene.render.resolution_x,scene.render.resolution_y=1400,760; scene.render.resolution_percentage=100
    for obj in scene.objects:
        name=obj.name.lower()
        if obj.type=="CURVES" or any(token in name for token in ("groom","scalp","haircard","hairfiber")):
            if not any(token in name for token in ("brow","lash")): obj.hide_render=True
    baseline={obj.name:obj.hide_render for obj in scene.objects}; output=[]
    eye_prefixes=("Eye_L_Sclera","Eye_R_Sclera","Eye_L_Cornea","Eye_R_Cornea","Eye_L_Iris","Eye_R_Iris")
    eye_only=tuple(obj.name for obj in scene.objects if obj.type=="MESH" and not obj.name.startswith(eye_prefixes))
    for label,hidden in (("composite",()),("eye-only",eye_only),("no-cornea",("Eye_L_Cornea","Eye_R_Cornea")),("eye-only-no-cornea",eye_only+("Eye_L_Cornea","Eye_R_Cornea"))):
        for obj in scene.objects: obj.hide_render=baseline[obj.name]
        for name in hidden:
            if bpy.data.objects.get(name): bpy.data.objects[name].hide_render=True
        target=OUT/f"{prefix}-{label}.png"; scene.render.filepath=str(target); bpy.ops.render.render(write_still=True); output.append({"label":f"{prefix}-{label}","path":str(target)})
    return output


OUT.mkdir(parents=True,exist_ok=True); renders=render_source(CONTROL,"control")+render_source(SELECTED,"selected")
REPORT.write_text(json.dumps({"revision":"v249r1080-eye-layer-isolation","control":str(CONTROL),"selected":str(SELECTED),"renders":renders},indent=2),encoding="utf-8")
print("AEVRYND_R1080_EYE_ISOLATION="+json.dumps({"renders":len(renders),"output":str(OUT)},sort_keys=True))
