"""Audit selected r1080 eye optics across body, attachment and internal-layer gates."""
import json
from pathlib import Path
import bpy
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[1]; ASSETS=ROOT/"assets-source/aevrynd-character"; CANDIDATE=ASSETS/"aevrynd-female-cc0-balanced-eye-optics-r1080-study.blend"; REPORT=ASSETS/"female-v249-mainline-r1080-eye-optics.collision-audit.json"
BODY="AevryndFemaleCC0BalancedEyeOptics_R1080"; FRAMES=(1,20,33,61); EXPRESSIONS=("Aevrynd_MouthOpenTest_R1030","Aevrynd_SmileTest_R1030")
ATTACHMENTS=("Brow_L","Brow_L_Density","Brow_R","Brow_R_Density","Eye_L_Sclera","Eye_L_Cornea","Eye_L_Iris","Eye_L_UpperLashes","Eye_L_LowerLashes","Eye_R_Sclera","Eye_R_Cornea","Eye_R_Iris","Eye_R_UpperLashes","Eye_R_LowerLashes","Eye_L_MedialCaruncle_R1023","Eye_R_MedialCaruncle_R1023")


def tree(obj,deps):
    evaluated=obj.evaluated_get(deps);mesh=evaluated.to_mesh();vertices=[evaluated.matrix_world@v.co for v in mesh.vertices];mesh.calc_loop_triangles();triangles=[tuple(t.vertices) for t in mesh.loop_triangles];evaluated.to_mesh_clear();return BVHTree.FromPolygons(vertices,triangles,all_triangles=True),triangles


def self_test(body):
    deps=bpy.context.evaluated_depsgraph_get();deps.update();item,triangles=tree(body,deps);pairs=[(a,b) for a,b in item.overlap(item) if a<b and set(triangles[a]).isdisjoint(triangles[b])];return {"nonAdjacentPairs":len(pairs),"samplePairs":[list(p) for p in pairs[:24]],"status":"PASS" if not pairs else "FAIL"}


bpy.ops.wm.open_mainfile(filepath=str(CANDIDATE));scene=bpy.context.scene;body=bpy.data.objects[BODY];blocks=body.data.shape_keys.key_blocks;zero=sum(1 for v in body.data.vertices if sum(x.weight for x in v.groups)<1e-8);frames={};attachments={};failures=[]
for frame in FRAMES:
    scene.frame_set(frame);bpy.context.view_layer.update();frames[str(frame)]=self_test(body);deps=bpy.context.evaluated_depsgraph_get();body_tree,_=tree(body,deps);attachments[str(frame)]={}
    for name in ATTACHMENTS:
        obj=bpy.data.objects.get(name)
        if obj is None:continue
        count=len(body_tree.overlap(tree(obj,deps)[0]));attachments[str(frame)][name]=count
        if count:failures.append({"frame":frame,"object":name,"triangleOverlapCount":count})
scene.frame_set(1);deps=bpy.context.evaluated_depsgraph_get();internal={};internal_failures=[]
for side in ("L","R"):
    pairs=(("Iris","Cornea"),("Iris","Sclera"),("Cornea","Sclera"));internal[side]={}
    for first,second in pairs:
        count=len(tree(bpy.data.objects[f"Eye_{side}_{first}"],deps)[0].overlap(tree(bpy.data.objects[f"Eye_{side}_{second}"],deps)[0]));internal[side][f"{first}-{second}"]=count
        if count:internal_failures.append({"side":side,"pair":f"{first}-{second}","triangleOverlapCount":count})
stored={name:blocks[name].value for name in EXPRESSIONS};expressions={}
for name in EXPRESSIONS:
    for reset in EXPRESSIONS:blocks[reset].value=0.0
    blocks[name].value=1.0;bpy.context.view_layer.update();expressions[name]=self_test(body)
for name,value in stored.items():blocks[name].value=value
checks=[len(blocks)==35,zero==0,not failures,not internal_failures]+[x["status"]=="PASS" for x in frames.values()]+[x["status"]=="PASS" for x in expressions.values()]
report={"revision":"v249r1080-eye-optics-collision","candidate":str(CANDIDATE),"body":BODY,"shapeKeys":len(blocks),"zeroWeightVertices":zero,"fourFrameBodySelfCollision":frames,"fourFrameBodyAttachmentCollision":attachments,"attachmentFailures":failures,"internalEyeLayerCollision":internal,"internalEyeLayerFailures":internal_failures,"expressionSelfCollision":expressions,"status":"PASS" if all(checks) else "FAIL"}
REPORT.write_text(json.dumps(report,indent=2),encoding="utf-8")
print("AEVRYND_R1080_COLLISION="+json.dumps({"status":report["status"],"selfPairs":{k:v["nonAdjacentPairs"] for k,v in frames.items()},"expressionPairs":{k:v["nonAdjacentPairs"] for k,v in expressions.items()},"attachmentFailures":len(failures),"internalFailures":len(internal_failures)},sort_keys=True))
