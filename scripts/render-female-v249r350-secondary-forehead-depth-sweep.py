import json
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1];SOURCE=ROOT/"assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-canthus-fitted-wedge-r345.blend"
REPORT=ROOT/"assets-source/aevrynd-character/female-v249-mainline-secondary-forehead-depth-r350.study.json";RENDER_DIR=ROOT.parent/"Temp/female-realism/v249r350-secondary-forehead-depth-sweep"
HAIR="AevryndFemaleSecondaryFill_R264";VARIANTS=(("a-current",None),("b-front-y-minus-0p13",-0.13),("c-front-y-minus-0p12",-0.12),("d-front-y-minus-0p11",-0.11))
def look_at(obj,target):obj.rotation_euler=(Vector(target)-obj.location).to_track_quat("-Z","Y").to_euler()
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update();hair=bpy.data.objects[HAIR];hair.data=hair.data.copy()
radius=hair.data.attributes["radius"].data;original=[v.value for v in radius];world=[[hair.matrix_world@hair.data.points[i].position for i in range(c.first_point_index,c.first_point_index+c.points_length)] for c in hair.data.curves]
scene.render.engine="BLENDER_EEVEE";scene.render.resolution_percentage=100;scene.render.image_settings.file_format="PNG";scene.view_settings.exposure=0.0;RENDER_DIR.mkdir(parents=True,exist_ok=True);camera=bpy.data.objects["Aevrynd R249 Review Camera"]
views=(("face",(0.0,-0.68,1.605),(0.0,-0.035,1.606),92),("hairline-high",(0.0,-0.57,1.76),(0.0,-0.02,1.64),92),("three-quarter",(0.45,-0.62,1.62),(0.0,-0.02,1.605),90));metrics={}
for label,y_limit in VARIANTS:
    for i,v in enumerate(original):radius[i].value=v
    flagged=[]
    if y_limit is not None:
        for ci,(curve,points) in enumerate(zip(hair.data.curves,world)):
            if any(abs(p.x)<0.075 and p.y<y_limit and 1.59<p.z<1.70 for p in points[3:]):
                flagged.append(ci)
                for i in range(curve.first_point_index,curve.first_point_index+curve.points_length):radius[i].value=0.0
    for view_name,location,target,lens in views:
        camera.location=location;camera.data.lens=lens;look_at(camera,target);scene.render.resolution_x=scene.render.resolution_y=1000;scene.render.filepath=str(RENDER_DIR/f"{label}-{view_name}.png");bpy.ops.render.render(write_still=True)
    metrics[label]={"frontYLessThanM":y_limit,"suppressedCurves":len(flagged),"retainedCurves":len(hair.data.curves)-len(flagged),"suppressedPoints":len(flagged)*24}
report={"source":str(SOURCE),"renderDirectory":str(RENDER_DIR),"variants":metrics,"method":"Expand the central-forehead SecondaryFill rejection volume in depth while holding x/z bounds fixed; suppress curves through point radius only.","status":"VISUAL_REVIEW_PENDING"}
REPORT.write_text(json.dumps(report,indent=2),encoding="utf-8");print("AEVRYND_R350_SECONDARY_FOREHEAD_DEPTH="+json.dumps(report,sort_keys=True))
