"""Render the r1080-carried r981 groom for r1081 hairline diagnosis."""
import json
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1];ASSETS=ROOT/"assets-source/aevrynd-character";SOURCE=ASSETS/"aevrynd-female-cc0-balanced-eye-optics-r1080-study.blend";REPORT=ASSETS/"female-v249-mainline-r1081-hairline-baseline.render.json";OUT=ROOT.parent/"Temp/female-realism/v249r1081-hairline-baseline"
KEEP=("AevryndFemaleTargetScalp_R976","AevryndFemaleCoherentClumpGroom_R981")


def look_at(obj,target):obj.rotation_euler=(Vector(target)-obj.location).to_track_quat("-Z","Y").to_euler()


bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.context.scene;scene.frame_set(1);scene.view_settings.view_transform="Standard";scene.view_settings.look="None";scene.view_settings.exposure=0.0;scene.view_settings.gamma=1.0;scene.render.image_settings.file_format="PNG";OUT.mkdir(parents=True,exist_ok=True)
for obj in scene.objects:
    name=obj.name.lower()
    if obj.type=="CURVES" or any(token in name for token in ("groom","scalp","haircard","hairfiber")):obj.hide_render=obj.name not in KEEP
camera=scene.camera;views=[]
specs=(("01-front",(0.0,-0.72,1.445),(0.0,-0.025,1.440),88,(1000,1000)),("02-left-three-quarter",(0.45,-0.62,1.46),(0.0,-0.015,1.44),88,(1000,1000)),("03-right-three-quarter",(-0.45,-0.62,1.46),(0.0,-0.015,1.44),88,(1000,1000)),("04-profile",(0.70,-0.03,1.45),(0.0,-0.015,1.44),92,(1000,1000)),("05-back",(0.0,0.72,1.445),(0.0,0.025,1.44),88,(1000,1000)),("06-top",(0.0,-0.25,2.00),(0.0,0.015,1.51),78,(1000,1000)),("07-hairline-front",(0.0,-0.53,1.57),(0.0,-0.03,1.54),115,(1400,850)),("08-hairline-top",(0.0,-0.32,1.86),(0.0,-0.015,1.55),110,(1400,850)))
for label,location,target,lens,size in specs:
    camera.location=location;camera.data.lens=lens;look_at(camera,target);scene.render.resolution_x,scene.render.resolution_y=size;scene.render.resolution_percentage=100;path=OUT/f"{label}.png";scene.render.filepath=str(path);bpy.ops.render.render(write_still=True);views.append({"label":label,"path":str(path)})
REPORT.write_text(json.dumps({"revision":"v249r1081-hairline-baseline","source":str(SOURCE),"hairLayers":list(KEEP),"views":views,"status":"STRICT_DIAGNOSIS_PENDING"},indent=2),encoding="utf-8")
print("AEVRYND_R1081_HAIRLINE_BASELINE="+json.dumps({"views":len(views),"output":str(OUT)},sort_keys=True))
