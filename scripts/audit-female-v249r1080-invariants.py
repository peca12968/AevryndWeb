"""Verify r1080 changes only owned iris geometry and eye materials."""
import hashlib,json,struct
from pathlib import Path
import bpy

ROOT=Path(__file__).resolve().parents[1]; ASSETS=ROOT/"assets-source/aevrynd-character"
SOURCE=ASSETS/"aevrynd-female-cc0-canthus-contour-r1079-study.blend"; CANDIDATE=ASSETS/"aevrynd-female-cc0-balanced-eye-optics-r1080-study.blend"
REPORT=ASSETS/"female-v249-mainline-r1080-eye-optics.invariant-audit.json"; SOURCE_BODY="AevryndFemaleCC0CanthusContour_R1079"; CANDIDATE_BODY="AevryndFemaleCC0BalancedEyeOptics_R1080"


def mesh_digest(obj,coords=True):
    value=hashlib.sha256()
    if coords:
        for vertex in obj.data.vertices:value.update(struct.pack("<3f",vertex.co.x,vertex.co.y,vertex.co.z))
    for polygon in obj.data.polygons:
        for index in polygon.vertices:value.update(struct.pack("<I",index))
    return value.hexdigest()


def body_digest(body):
    value=hashlib.sha256()
    for block in body.data.shape_keys.key_blocks:
        value.update(block.name.encode())
        for item in block.data:value.update(struct.pack("<3f",item.co.x,item.co.y,item.co.z))
    return value.hexdigest()


def weight_digest(body):
    value=hashlib.sha256()
    for vertex in body.data.vertices:
        for item in sorted(vertex.groups,key=lambda x:x.group):value.update(struct.pack("<If",item.group,item.weight))
    return value.hexdigest()


def snapshot(path,body_name):
    bpy.ops.wm.open_mainfile(filepath=str(path)); body=bpy.data.objects[body_name]; objects={}
    for name in [f"Eye_{side}_{layer}" for side in ("L","R") for layer in ("Sclera","Cornea","Iris")]:
        obj=bpy.data.objects[name]; objects[name]={"vertices":len(obj.data.vertices),"faces":len(obj.data.polygons),"geometry":mesh_digest(obj,True),"topology":mesh_digest(obj,False),"materials":[item.name if item else None for item in obj.data.materials],"matrix":[list(row) for row in obj.matrix_world]}
    return {"bodyGeometry":body_digest(body),"bodyWeights":weight_digest(body),"bodyShapeKeys":[block.name for block in body.data.shape_keys.key_blocks],"bodyTopology":mesh_digest(body,False),"objects":objects,"objectCount":len(bpy.data.objects)}


source=snapshot(SOURCE,SOURCE_BODY); candidate=snapshot(CANDIDATE,CANDIDATE_BODY)
bpy.ops.wm.open_mainfile(filepath=str(CANDIDATE)); cornea=bpy.data.objects["Eye_L_Cornea"].data.materials[0]; sclera=bpy.data.objects["Eye_L_Sclera"].data.materials[0]
cornea_links=[f"{link.from_node.name}.{link.from_socket.name}->{link.to_node.name}.{link.to_socket.name}" for link in cornea.node_tree.links]; mix=next(node for node in cornea.node_tree.nodes if node.type=="MIX_SHADER")
sclera_node=sclera.node_tree.nodes.get("Aevrynd Sclera Warm Value R1080")
checks={
    "bodyGeometryIdentical":source["bodyGeometry"]==candidate["bodyGeometry"],"bodyWeightsIdentical":source["bodyWeights"]==candidate["bodyWeights"],"bodyTopologyIdentical":source["bodyTopology"]==candidate["bodyTopology"],"bodyShapeKeysIdentical":source["bodyShapeKeys"]==candidate["bodyShapeKeys"] and len(candidate["bodyShapeKeys"])==35,
    "eyeTopologyIdentical":all(source["objects"][name]["topology"]==candidate["objects"][name]["topology"] for name in source["objects"]),
    "scleraCorneaGeometryIdentical":all(source["objects"][f"Eye_{side}_{layer}"]["geometry"]==candidate["objects"][f"Eye_{side}_{layer}"]["geometry"] for side in ("L","R") for layer in ("Sclera","Cornea")),
    "irisGeometryChangedPaired":all(source["objects"][f"Eye_{side}_Iris"]["geometry"]!=candidate["objects"][f"Eye_{side}_Iris"]["geometry"] for side in ("L","R")),
    "objectMatricesIdentical":all(source["objects"][name]["matrix"]==candidate["objects"][name]["matrix"] for name in source["objects"]),"objectCountIdentical":source["objectCount"]==candidate["objectCount"],
    "materialSlotCountsIdentical":all(len(source["objects"][name]["materials"])==len(candidate["objects"][name]["materials"]) for name in source["objects"]),
    "corneaUsesBlendedMix":cornea.surface_render_method=="BLENDED" and abs(mix.inputs[0].default_value-0.20)<1e-6 and any("Mix Shader.Shader->Material Output.Surface" in link for link in cornea_links) and not any("Principled BSDF.BSDF->Material Output.Surface" in link for link in cornea_links),
    "scleraMultiplierPresent":sclera_node is not None and abs(sclera_node.inputs[2].default_value[0]-0.88)<1e-6,
}
report={"revision":"v249r1080-eye-optics-invariants","source":str(SOURCE),"candidate":str(CANDIDATE),"sourceSummary":source,"candidateSummary":candidate,"materialAudit":{"cornea":cornea.name,"surfaceRenderMethod":cornea.surface_render_method,"mixFactor":mix.inputs[0].default_value,"links":cornea_links,"sclera":sclera.name},"checks":checks,"status":"PASS" if all(checks.values()) else "FAIL"}
REPORT.write_text(json.dumps(report,indent=2),encoding="utf-8")
print("AEVRYND_R1080_INVARIANTS="+json.dumps({"status":report["status"],"checks":checks},sort_keys=True))
