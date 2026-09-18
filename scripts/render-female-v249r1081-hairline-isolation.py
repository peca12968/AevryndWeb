"""Render r1081 hair/scalp layers independently to identify the bright part source."""
import json
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1];ASSETS=ROOT/"assets-source/aevrynd-character";SOURCE=ASSETS/"aevrynd-female-cc0-balanced-eye-optics-r1080-study.blend";REPORT=ASSETS/"female-v249-mainline-r1081-hairline-isolation.render.json";OUT=ROOT.parent/"Temp/female-realism/v249r1081-hairline-isolation";HAIR="AevryndFemaleCoherentClumpGroom_R981";SCALP="AevryndFemaleTargetScalp_R976"
def look_at(obj,target):obj.rotation_euler=(Vector(target)-obj.location).to_track_quat("-Z","Y").to_euler()
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.context.scene;scene.frame_set(1);scene.view_settings.view_transform="Standard";scene.view_settings.look="None";scene.view_settings.exposure=0.0;scene.view_settings.gamma=1.0;OUT.mkdir(parents=True,exist_ok=True);camera=scene.camera;camera.location=(0.0,-0.53,1.57);camera.data.lens=115;look_at(camera,(0.0,-0.03,1.54));scene.render.resolution_x,scene.render.resolution_y=1400,850;scene.render.resolution_percentage=100
for obj in scene.objects:
    name=obj.name.lower()
    if obj.type=="CURVES" or any(token in name for token in ("groom","scalp","haircard","hairfiber")):obj.hide_render=obj.name not in (HAIR,SCALP)
body=next(obj for obj in scene.objects if obj.name.startswith("AevryndFemaleCC0BalancedEyeOptics"));baseline={obj.name:obj.hide_render for obj in scene.objects};renders=[]
for label,hidden in (("a-composite",()),("b-no-hair",(HAIR,)),("c-no-scalp",(SCALP,)),("d-scalp-only",(HAIR,body.name))):
    for obj in scene.objects:obj.hide_render=baseline[obj.name]
    for name in hidden:bpy.data.objects[name].hide_render=True
    path=OUT/f"{label}.png";scene.render.filepath=str(path);bpy.ops.render.render(write_still=True);renders.append({"label":label,"path":str(path)})
REPORT.write_text(json.dumps({"revision":"v249r1081-hairline-isolation","source":str(SOURCE),"renders":renders},indent=2),encoding="utf-8");print("AEVRYND_R1081_HAIRLINE_ISOLATION="+json.dumps({"renders":len(renders),"output":str(OUT)},sort_keys=True))
