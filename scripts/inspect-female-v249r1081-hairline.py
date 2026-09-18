"""Inspect the r981 owned groom carried by the r1080 authority file."""
import json,math
from pathlib import Path
import bpy

ROOT=Path(__file__).resolve().parents[1];ASSETS=ROOT/"assets-source/aevrynd-character";SOURCE=ASSETS/"aevrynd-female-cc0-balanced-eye-optics-r1080-study.blend";REPORT=ASSETS/"female-v249-mainline-r1081-hairline.inspection.json"


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
hair_objects=[]
for obj in bpy.data.objects:
    name=obj.name.lower()
    if obj.type=="CURVES" or any(token in name for token in ("groom","scalp","haircard","hairfiber")):
        entry={"name":obj.name,"type":obj.type,"hideRender":obj.hide_render,"materials":[item.name if item else None for item in obj.data.materials] if hasattr(obj.data,"materials") else []}
        if obj.type=="CURVES": entry.update({"curves":len(obj.data.curves),"points":len(obj.data.points),"attributes":[item.name for item in obj.data.attributes]})
        elif obj.type=="MESH": entry.update({"vertices":len(obj.data.vertices),"faces":len(obj.data.polygons)})
        hair_objects.append(entry)

hair=bpy.data.objects["AevryndFemaleCoherentClumpGroom_R981"];matrix=hair.matrix_world
roots=[];lengths=[];points_per_curve=[]
for curve in hair.data.curves:
    points=[matrix@hair.data.points[curve.first_point_index+i].position for i in range(curve.points_length)];roots.append(points[0]);points_per_curve.append(curve.points_length);lengths.append(sum((points[i]-points[i-1]).length for i in range(1,len(points))))
root_bounds={axis:[min(getattr(point,axis) for point in roots),max(getattr(point,axis) for point in roots)] for axis in ("x","y","z")}
part_bins=[];y_min,y_max=root_bounds["y"]
for bin_index in range(12):
    low=y_min+(y_max-y_min)*bin_index/12;high=y_min+(y_max-y_min)*(bin_index+1)/12;items=sorted(abs(point.x) for point in roots if low<=point.y<high and point.z>1.50)
    part_bins.append({"yRange":[low,high],"rootCount":len(items),"minimumAbsXmm":1000.0*items[0] if items else None,"p10AbsXmm":1000.0*items[min(len(items)-1,int(len(items)*0.10))] if items else None})
frontal=[point for point in roots if point.y<y_min+0.30*(y_max-y_min) and point.z>1.45]
report={"revision":"v249r1081-hairline-inspection","source":str(SOURCE),"hairObjects":hair_objects,"authorityHair":hair.name,"curveCount":len(hair.data.curves),"pointCount":len(hair.data.points),"rootBounds":root_bounds,"pointsPerCurve":{"minimum":min(points_per_curve),"maximum":max(points_per_curve)},"curveLengthM":{"minimum":min(lengths),"maximum":max(lengths),"mean":sum(lengths)/len(lengths)},"partBins":part_bins,"frontalRootCount":len(frontal),"frontalRootBounds":{axis:[min(getattr(point,axis) for point in frontal),max(getattr(point,axis) for point in frontal)] for axis in ("x","y","z")},"shortCurveCountUnder80mm":sum(length<0.08 for length in lengths)}
scalp_material=bpy.data.objects["AevryndFemaleTargetScalp_R976"].data.materials[0];shader=next(node for node in scalp_material.node_tree.nodes if node.type=="BSDF_PRINCIPLED")
report["scalpMaterial"]={"name":scalp_material.name,"inputs":{name:(list(shader.inputs[name].default_value) if hasattr(shader.inputs[name].default_value,"__len__") else shader.inputs[name].default_value) for name in ("Base Color","Roughness","Specular IOR Level","Coat Weight","Coat Roughness")},"links":[f"{link.from_node.name}.{link.from_socket.name}->{link.to_node.name}.{link.to_socket.name}" for link in scalp_material.node_tree.links]}
radius=hair.data.attributes.get("radius")
if radius:
    values=[item.value for item in radius.data];report["radiusM"]={"minimum":min(values),"maximum":max(values),"mean":sum(values)/len(values)}
REPORT.write_text(json.dumps(report,indent=2),encoding="utf-8")
print("AEVRYND_R1081_HAIRLINE="+json.dumps({key:report[key] for key in ("authorityHair","curveCount","pointCount","rootBounds","partBins","frontalRootCount","frontalRootBounds","shortCurveCountUnder80mm")},sort_keys=True))
