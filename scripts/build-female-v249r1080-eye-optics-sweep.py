"""Sweep iris scale/depth/convergence and owned sclera response on r1079."""
import hashlib
import json
import math
import struct
from pathlib import Path

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[1]; ASSETS=ROOT/"assets-source/aevrynd-character"
SOURCE=ASSETS/"aevrynd-female-cc0-canthus-contour-r1079-study.blend"
OUTPUT=ASSETS/"aevrynd-female-cc0-balanced-eye-optics-r1080-study.blend"
REPORT=ASSETS/"female-v249-mainline-r1080-eye-optics-sweep.study.json"
OUT=ROOT.parent/"Temp/female-realism/v249r1080-eye-optics"
BODY="AevryndFemaleCC0CanthusContour_R1079"; TARGET="AevryndFemaleCC0BalancedEyeOptics_R1080"; FRAMES=(1,20,33,61)
# label, iris radial scale, depth mm, convergence degrees, sclera multiplier, cornea BSDF mix (None keeps control wiring)
VARIANTS=(
    ("a-control",1.00,0.00,0.00,1.00,None),
    ("b-iris-1.10",1.10,0.00,0.00,1.00,None),
    ("c-iris-1.16",1.16,0.00,0.00,1.00,None),
    ("d-optical-1.16",1.16,0.08,0.75,1.00,None),
    ("e-optical-sclera-0.88",1.16,0.08,0.75,0.88,None),
    ("f-cornea-0.12",1.16,0.08,0.75,0.88,0.12),
    ("g-cornea-0.20",1.16,0.08,0.75,0.88,0.20),
    ("h-cornea-0.30",1.16,0.08,0.75,0.88,0.30),
    ("i-strong-1.20",1.20,0.10,1.00,0.84,0.20),
)
SELECTED="g-cornea-0.20"


def look_at(camera,target): camera.rotation_euler=(Vector(target)-camera.location).to_track_quat("-Z","Y").to_euler()


def geometry_digest(obj):
    digest=hashlib.sha256()
    for vertex in obj.data.vertices: digest.update(struct.pack("<3f",vertex.co.x,vertex.co.y,vertex.co.z))
    return digest.hexdigest()


def world_bounds(obj):
    points=[obj.matrix_world@vertex.co for vertex in obj.data.vertices]
    return {axis:[min(getattr(point,axis) for point in points),max(getattr(point,axis) for point in points)] for axis in ("x","y","z")}


def tune_iris(iris,sclera,scale,depth_mm,convergence_deg,side):
    points=[iris.matrix_world@vertex.co for vertex in iris.data.vertices]
    iris_center=Vector(tuple(sum(point[axis] for point in points)/len(points) for axis in range(3)))
    sclera_points=[sclera.matrix_world@vertex.co for vertex in sclera.data.vertices]
    eye_center=Vector(tuple(sum(point[axis] for point in sclera_points)/len(sclera_points) for axis in range(3)))
    angle=math.radians((-1.0 if side=="L" else 1.0)*convergence_deg); rotation=Matrix.Rotation(angle,4,"Z")
    inverse=iris.matrix_world.inverted()
    for vertex,world in zip(iris.data.vertices,points):
        scaled=Vector((iris_center.x+(world.x-iris_center.x)*scale,world.y+depth_mm/1000.0,iris_center.z+(world.z-iris_center.z)*scale))
        rotated=eye_center+rotation@(scaled-eye_center); vertex.co=inverse@rotated
    iris.data.update()
    bounds=world_bounds(iris)
    return {"scale":scale,"depthMm":depth_mm,"convergenceDeg":convergence_deg,"sizeMm":{axis:1000.0*(bounds[axis][1]-bounds[axis][0]) for axis in bounds},"centerWorld":[0.5*(bounds[axis][0]+bounds[axis][1]) for axis in ("x","y","z")]}


def tune_sclera(factor):
    source=bpy.data.objects["Eye_L_Sclera"].data.materials[0]; material=source.copy(); material.name=f"Aevrynd_Eye_Sclera_R1080_{factor:.2f}"
    nodes=material.node_tree.nodes; links=material.node_tree.links; shader=next(node for node in nodes if node.type=="BSDF_PRINCIPLED"); base=shader.inputs["Base Color"]
    old=base.links[0] if base.links else None
    multiply=nodes.new("ShaderNodeMixRGB"); multiply.name="Aevrynd Sclera Warm Value R1080"; multiply.blend_type="MULTIPLY"; multiply.inputs[0].default_value=1.0; multiply.inputs[2].default_value=(factor,factor*0.985,factor*0.95,1.0)
    if old:
        socket=old.from_socket; links.remove(old); links.new(socket,multiply.inputs[1])
    else: multiply.inputs[1].default_value=base.default_value
    links.new(multiply.outputs[0],base)
    for side in ("L","R"): bpy.data.objects[f"Eye_{side}_Sclera"].data.materials[0]=material
    return {"factor":factor,"material":material.name,"nodeCount":len(nodes)}


def tune_cornea(factor):
    source=bpy.data.objects["Eye_L_Cornea"].data.materials[0]; material=source.copy(); material.name=f"Aevrynd_Eye_Cornea_R1080_{factor:.2f}"
    material.surface_render_method="BLENDED"
    nodes=material.node_tree.nodes; links=material.node_tree.links
    shader=next(node for node in nodes if node.type=="BSDF_PRINCIPLED"); transparent=next(node for node in nodes if node.type=="BSDF_TRANSPARENT"); mix=next(node for node in nodes if node.type=="MIX_SHADER"); output=next(node for node in nodes if node.type=="OUTPUT_MATERIAL")
    for link in list(output.inputs["Surface"].links): links.remove(link)
    for socket in mix.inputs[1:]:
        for link in list(socket.links): links.remove(link)
    links.new(transparent.outputs[0],mix.inputs[1]); links.new(shader.outputs[0],mix.inputs[2]); mix.inputs[0].default_value=factor; links.new(mix.outputs[0],output.inputs["Surface"])
    for side in ("L","R"): bpy.data.objects[f"Eye_{side}_Cornea"].data.materials[0]=material
    return {"factor":factor,"material":material.name,"surfaceRenderMethod":material.surface_render_method,"surfaceLink":f"{mix.name}.Shader->{output.name}.Surface","nodeCount":len(nodes)}


def tree(obj,depsgraph):
    evaluated=obj.evaluated_get(depsgraph); mesh=evaluated.to_mesh(); vertices=[evaluated.matrix_world@vertex.co for vertex in mesh.vertices]; mesh.calc_loop_triangles(); triangles=[tuple(item.vertices) for item in mesh.loop_triangles]; evaluated.to_mesh_clear(); return BVHTree.FromPolygons(vertices,triangles,all_triangles=True)


def collision_frames(body):
    results={}; failures=[]
    for frame in FRAMES:
        bpy.context.scene.frame_set(frame); deps=bpy.context.evaluated_depsgraph_get(); deps.update(); body_tree=tree(body,deps); result={}
        for side in ("L","R"):
            result[side]={}
            for layer in ("Sclera","Cornea","Iris","UpperLashes","LowerLashes"):
                count=len(body_tree.overlap(tree(bpy.data.objects[f"Eye_{side}_{layer}"],deps))); result[side][layer]=count
                if count: failures.append({"frame":frame,"side":side,"layer":layer,"triangleOverlapCount":count})
        results[str(frame)]=result
    return results,failures


def render(scene,label,view):
    camera=scene.camera
    if view=="eye-front": camera.location,target,camera.data.lens,size=(0.0,-0.405,1.449),(0.0,-0.105,1.449),135,(1400,760)
    elif view=="eye-oblique": camera.location,target,camera.data.lens,size=(0.235,-0.405,1.451),(0.0,-0.105,1.449),135,(1400,760)
    elif view=="face-front": camera.location,target,camera.data.lens,size=(0.0,-0.72,1.445),(0.0,-0.025,1.440),88,(1000,1000)
    else: camera.location,target,camera.data.lens,size=(0.45,-0.62,1.460),(0.0,-0.015,1.440),88,(1000,1000)
    look_at(camera,target); scene.render.resolution_x,scene.render.resolution_y=size; scene.render.resolution_percentage=100; path=OUT/f"{label}-{view}.png"; scene.render.filepath=str(path); bpy.ops.render.render(write_still=True); return str(path)


OUT.mkdir(parents=True,exist_ok=True); variants=[]
for label,scale,depth,convergence,sclera_factor,cornea_factor in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE)); scene=bpy.context.scene; scene.frame_set(1); body=bpy.data.objects[BODY]
    scene.view_settings.view_transform="Standard"; scene.view_settings.look="None"; scene.view_settings.exposure=0.0; scene.view_settings.gamma=1.0
    for obj in scene.objects:
        name=obj.name.lower()
        if obj.type=="CURVES" or any(token in name for token in ("groom","scalp","haircard","hairfiber")):
            if not any(token in name for token in ("brow","lash")): obj.hide_render=True
    body_digest=geometry_digest(body); iris_before={side:geometry_digest(bpy.data.objects[f"Eye_{side}_Iris"]) for side in ("L","R")}
    optics={side:tune_iris(bpy.data.objects[f"Eye_{side}_Iris"],bpy.data.objects[f"Eye_{side}_Sclera"],scale,depth,convergence,side) for side in ("L","R")}
    sclera=tune_sclera(sclera_factor) if sclera_factor<0.999 else {"factor":1.0,"material":bpy.data.objects["Eye_L_Sclera"].data.materials[0].name,"nodeCount":len(bpy.data.objects["Eye_L_Sclera"].data.materials[0].node_tree.nodes)}
    cornea=tune_cornea(cornea_factor) if cornea_factor is not None else {"factor":None,"material":bpy.data.objects["Eye_L_Cornea"].data.materials[0].name,"surfaceLink":"Principled BSDF.BSDF->Material Output.Surface","nodeCount":len(bpy.data.objects["Eye_L_Cornea"].data.materials[0].node_tree.nodes)}
    bpy.context.view_layer.update(); collisions,failures=collision_frames(body); scene.frame_set(1); bpy.context.view_layer.update(); renders=[render(scene,label,view) for view in ("eye-front","eye-oblique","face-front","face-three-quarter")]
    metrics={"optics":optics,"sclera":sclera,"cornea":cornea,"bodyGeometryUnchanged":body_digest==geometry_digest(body),"irisGeometryChanged":{side:iris_before[side]!=geometry_digest(bpy.data.objects[f"Eye_{side}_Iris"]) for side in ("L","R")},"objectCount":len(bpy.data.objects),"materialSlotCounts":{side:len(bpy.data.objects[f"Eye_{side}_Sclera"].data.materials) for side in ("L","R")}}
    variants.append({"label":label,"metrics":metrics,"collisionFrames":collisions,"collisionFailures":failures,"renders":renders,"status":"TECHNICAL_PASS" if not failures and metrics["bodyGeometryUnchanged"] else "TECHNICAL_FAIL"})
    if label==SELECTED:
        body.name=TARGET; body["aevrynd_revision"]="v249r1080-balanced-eye-optics"; body["aevrynd_source"]=SOURCE.name
        scene["aevrynd_release_state"]="VISUAL_REVIEW_PENDING"; scene["aevrynd_website_promotion"]="forbidden"; bpy.context.preferences.filepaths.save_version=0; bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report={"revision":"v249r1080-eye-optics-sweep","source":str(SOURCE),"output":str(OUTPUT),"method":"scale the existing owned iris meshes about their centres, recess them along view depth, rotate them on the scleral sphere for subtle convergence, and multiply the existing owned sclera texture inside its current shader","variants":variants,"selectedVariant":SELECTED,"topologyChanged":False,"newObjects":0,"materialSlotDelta":0,"websitePromotionApproved":False,"candidateStatus":"VISUAL_REVIEW_PENDING"}
REPORT.write_text(json.dumps(report,indent=2),encoding="utf-8")
print("AEVRYND_R1080_EYE_OPTICS="+json.dumps({"selected":SELECTED,"variants":[{"label":item["label"],"failures":len(item["collisionFailures"]),"status":item["status"],"L":item["metrics"]["optics"]["L"],"sclera":item["metrics"]["sclera"],"cornea":item["metrics"]["cornea"]} for item in variants]},sort_keys=True))
