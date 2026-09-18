"""Measure current r1079 eye geometry, transforms and material controls."""
import json
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-canthus-contour-r1079-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1080-eye-optics.inspection.json"


def value(socket):
    item = socket.default_value
    if hasattr(item, "__len__"): return [float(number) for number in item]
    return float(item)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
objects = {}
for obj in bpy.data.objects:
    if not obj.name.startswith(("Eye_L_", "Eye_R_")) or obj.type != "MESH": continue
    points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    bounds = {axis: [min(getattr(point,axis) for point in points),max(getattr(point,axis) for point in points)] for axis in ("x","y","z")}
    materials = []
    for material in obj.data.materials:
        if material is None: continue
        nodes = []
        if material.use_nodes:
            for node in material.node_tree.nodes:
                if node.type not in {"BSDF_PRINCIPLED","BSDF_GLASS","BSDF_TRANSPARENT","MIX_SHADER","TEX_IMAGE"}: continue
                entry={"name":node.name,"type":node.bl_idname}
                if node.type in {"BSDF_PRINCIPLED","BSDF_GLASS"}:
                    entry["inputs"]={socket.name:value(socket) for socket in node.inputs if socket.name in {"Base Color","Roughness","IOR","Alpha","Coat Weight","Coat Roughness","Transmission Weight","Metallic","Specular IOR Level"}}
                if node.type=="TEX_IMAGE":
                    entry["image"]=node.image.name if node.image else None
                    entry["imagePath"]=bpy.path.abspath(node.image.filepath) if node.image else None
                nodes.append(entry)
        links=[f"{link.from_node.name}.{link.from_socket.name}->{link.to_node.name}.{link.to_socket.name}" for link in material.node_tree.links] if material.use_nodes else []
        materials.append({"name":material.name,"surfaceRenderMethod":getattr(material,"surface_render_method",None),"nodes":nodes,"links":links})
    objects[obj.name]={
        "vertices":len(obj.data.vertices),"faces":len(obj.data.polygons),"parent":obj.parent.name if obj.parent else None,
        "location":list(obj.location),"rotationEuler":list(obj.rotation_euler),"scale":list(obj.scale),
        "boundsWorld":bounds,"sizeMm":{axis:1000.0*(bounds[axis][1]-bounds[axis][0]) for axis in bounds},
        "centerWorld":[sum(point[axis] for point in points)/len(points) for axis in range(3)],"materials":materials,
    }

summary={}
for side in ("L","R"):
    entries={kind:objects.get(f"Eye_{side}_{kind}") for kind in ("Sclera","Cornea","Iris","IrisFibers","LimbalRing","Pupil")}
    summary[side]={kind:{"sizeMm":entry["sizeMm"],"centerWorld":entry["centerWorld"],"frontY":entry["boundsWorld"]["y"][0]} for kind,entry in entries.items() if entry}
    if entries["Iris"] and entries["Cornea"]:
        summary[side]["irisToCorneaFrontDepthMm"]=1000.0*(entries["Iris"]["boundsWorld"]["y"][0]-entries["Cornea"]["boundsWorld"]["y"][0])
report={"revision":"v249r1080-eye-optics-inspection","source":str(SOURCE),"objects":objects,"summary":summary}
REPORT.write_text(json.dumps(report,indent=2),encoding="utf-8")
print("AEVRYND_R1080_EYE_OPTICS="+json.dumps(summary,sort_keys=True))
