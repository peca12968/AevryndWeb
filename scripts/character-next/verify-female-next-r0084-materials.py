"""Minimum rejected material readback and exact inherited geometry premises.
Baseline views only repeated because old view-order light roundoff differs.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
R=Path(r"D:/Download/Aevrynd");E=R/"Evidence/character-female-next/r0084-physical-brown-hair"
def module(n,f):
 sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(f));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
v=module("r84native","verify-female-next-r0076-crowns.py");m=module("r84sourcecheck","build-female-next-r0081-editable-curly.py");visual=module("r84viewscheck","render-female-next-r0081-retained-study.py");visual.E=E

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,d):(E/n).write_text(json.dumps(d,indent=2)+"\n",encoding="utf-8")
def value(s):
 if not hasattr(s,"default_value"):return None
 x=s.default_value
 if isinstance(x,(str,int,float,bool)) or x is None:return x
 if hasattr(x,"name"):return x.name
 return list(x)
def main():
 tick=time.time();refs={t:json.loads((E/(t+"-build-summary.json")).read_text()) for t in "abc"};a=refs["a"];assert sha(Path(a["source"]))==a["sourceSha256"];bpy.ops.wm.open_mainfile(filepath=a["source"]);bpy.context.scene.frame_set(1);bpy.context.view_layer.update();q=m.q;o=bpy.data.objects["AFN81_EDITABLE_CURLY_GUIDES"];P=q.hair(o).copy();nativeP=q.arr(o.data.position_data,"vector",3636,3).copy();d=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;counts=np.array([c.points_length for c in d.curves]);radius=q.arr(d.attributes["radius"].data,"value",len(P)).copy();names=m.rig.native_names();sig={n:v.signature(bpy.data.objects[n]) for n in names};mats={mat.name:m.rig.k.f.v.v32.material_signature(mat) for mat in bpy.data.materials if mat.use_nodes};lights=m.m.q.lights();body=m.rig.k.mesh(bpy.data.objects["AFN60_BODY_ORAL_AND_OCULAR_LINING"]);bodyV=body["V"].copy();bodyT=body["T"].copy();context=[];seen=set()
 def materialContext(tree,depth=0):
  if tree.name in seen or depth>3:return
  seen.add(tree.name);nodes=[]
  for n in tree.nodes:
   if n.bl_idname=="ShaderNodeBsdfPrincipled":nodes.append({"name":n.name,"type":n.bl_idname,"inputs":[[i.name,value(i),[[l.from_node.name,l.from_socket.name] for l in i.links]] for i in n.inputs]})
   if n.bl_idname=="ShaderNodeTexImage" and n.image:nodes.append({"name":n.name,"image":n.image.name,"path":n.image.filepath,"size":list(n.image.size),"colourSpace":n.image.colorspace_settings.name})
   if n.type=="GROUP":materialContext(n.node_tree,depth+1)
  if nodes:context.append({"tree":tree.name,"nodes":nodes})
 skin=bpy.data.objects["AFN74_SKIN_AND_EXISTING_OCULAR_LINING"]
 for mat in skin.data.materials:
  if mat and mat.use_nodes:materialContext(mat.node_tree)
 save("existing-skin-material-context.json",{"basis":"Read-only saved baseline material context for choosing the next visible face task; not an iteration or diagnosis result.","source":a["source"],"materials":[x.name for x in skin.data.materials],"trees":context})
 rows=[]
 for view in ("face","body-face","back"):rows.append(visual.image("baseline-r81",view));save("baseline-pilot-controls.json",rows)
 results=[]
 for tag,ref in refs.items():
  assert sha(Path(ref["output"]))==ref["outputSha256"];bpy.ops.wm.open_mainfile(filepath=ref["output"]);bpy.context.scene.frame_set(1);bpy.context.view_layer.update();o=bpy.data.objects["AFN81_EDITABLE_CURLY_GUIDES"];actual=q.hair(o);assert np.array_equal(actual,P) and np.array_equal(q.arr(o.data.position_data,"vector",3636,3),nativeP);d=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;assert np.array_equal(np.array([c.points_length for c in d.curves]),counts) and np.array_equal(q.arr(d.attributes["radius"].data,"value",len(P)),radius);assert {n:v.signature(bpy.data.objects[n]) for n in names}==sig;assert {n:m.rig.k.f.v.v32.material_signature(bpy.data.materials[n]) for n in mats}==mats;assert lights==m.m.q.lights();row=m.rig.k.mesh(bpy.data.objects["AFN60_BODY_ORAL_AND_OCULAR_LINING"]);assert np.array_equal(row["V"],bodyV) and np.array_equal(row["T"],bodyT);textures=[]
  for im in bpy.data.images:
   if im.source=="FILE" and not im.packed_file:
    p=Path(bpy.path.abspath(im.filepath));assert im.filepath.startswith("//") and p.is_file();textures.append({"relative":im.filepath,"sha256":sha(p)})
  assert len(textures)==15 and not bpy.data.libraries;extra={}
  if tag=="c":
   tangent=q.arr(d.attributes["AFN84_LocalCurveTangent"].data,"vector",len(P),3);assert np.isfinite(tangent).all() and np.linalg.norm(tangent,axis=1).min()>.99;extra={"neutralTangentPointCount":len(tangent),"tangentNotIndependentlyMotionQualified":True}
  results.append({"tag":tag,"status":"PASS_MINIMUM_REJECTED_MATERIAL_SOURCE_READBACK_ONLY","source":ref["output"],"sha256":ref["outputSha256"],"actualHairCentrelineRadiiAndNeutralBodyVerticesTrianglesExactToR81B":True,"allFiveNativeCagesKeysUVWeightsDriversAndAllOriginalMaterialsLightsExact":True,"evaluatedMaterial":[x.name for x in d.materials],"nativeGuides":303,"nativePoints":3636,"evaluatedCurves":len(counts),"evaluatedPoints":len(actual),"externalTextures":textures,"extra":extra,"appearanceRejected":True,"contact":"R81B8 declared-centreline interior witnesses retain geometry/pose/radius premises. Reused scoped failure, not new sampling or installed-renderer/full-contact certificate.","skinFrameNaturalDynamicsRuntimeUnaccepted":True})
 save("minimum-source-readback.json",{"studies":results,"seconds":time.time()-tick,"baselineRerenderReason":"Prior complete-body baseline used another view order with tiny inherited light matrix rotation roundoff; fresh fixed face/body/back order required for exact controls. No acceptance expansion after visual rejection."});print("R84_MINIMUM_REJECTED_MATERIALS_READBACK_DONE",time.time()-tick,flush=True)
if __name__=="__main__":main()
