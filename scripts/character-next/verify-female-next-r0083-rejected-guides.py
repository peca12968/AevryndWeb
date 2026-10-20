"""Minimum safe readback of visually rejected studies; no broad acceptance suite."""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
R=Path(r"D:/Download/Aevrynd");E=R/"Evidence/character-female-next/r0083-posterior-guide-authoring"
def module(n,f):
 sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(f));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
v=module("read83native","verify-female-next-r0076-crowns.py");m=module("read83base","build-female-next-r0081-editable-curly.py");visual=module("read83views","render-female-next-r0081-retained-study.py");visual.E=E;m.E=E

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,d):(E/n).write_text(json.dumps(d,indent=2)+"\n",encoding="utf-8")
def main():
 tick=time.time();a=json.loads((E/"a-build-summary.json").read_text());b=json.loads((E/"b-build-summary.json").read_text());assert sha(Path(a["source"]))==a["sourceSha256"];bpy.ops.wm.open_mainfile(filepath=a["source"]);bpy.context.scene.frame_set(1);q=m.q;names=m.rig.native_names();native={n:v.signature(bpy.data.objects[n]) for n in names};materials={mat.name:m.rig.k.f.v.v32.material_signature(mat) for mat in bpy.data.materials if mat.use_nodes};lights=m.m.q.lights();oldNative=q.arr(bpy.data.objects["AFN81_EDITABLE_CURLY_GUIDES"].data.position_data,"vector",3636,3).copy();teeth={n:q.arr(bpy.data.objects[n].data.vertices,"co",len(bpy.data.objects[n].data.vertices),3).copy() for n in ("AFN74_UPPER_TEETH_RIGID","AFN74_LOWER_TEETH_RIGID")};refRows=[]
 for view in ("back","face","body-face"):refRows.append(visual.image("baseline-r81",view));save("baseline-r81-pilot-controls.json",refRows)
 outcomes=[]
 for tag,ref,lineage in [("a",a,"a-guide-edit-and-evaluated-lineage.npz"),("b",b,"b-guide-and-rebound-lineage.npz")]:
  assert sha(Path(ref["output"]))==ref["outputSha256"];bpy.ops.wm.open_mainfile(filepath=ref["output"]);bpy.context.scene.frame_set(1);bpy.context.view_layer.update();assert {n:v.signature(bpy.data.objects[n]) for n in names}==native;assert {n:m.rig.k.f.v.v32.material_signature(bpy.data.materials[n]) for n in materials}==materials;assert lights==m.m.q.lights()
  for n,p in teeth.items():assert np.array_equal(q.arr(bpy.data.objects[n].data.vertices,"co",len(p),3),p)
  o=bpy.data.objects["AFN81_EDITABLE_CURLY_GUIDES"];z=np.load(E/lineage);P=q.arr(o.data.position_data,"vector",len(o.data.position_data),3);assert np.array_equal(P,z["afterNativeLocal"]);assert np.array_equal(np.array([c.points_length for c in o.data.curves]),z["nativeCounts"]);actual=q.hair(o);expected=z["afterEvaluatedWorld"] if tag=="a" else z["evaluatedWorld"];err=float(np.linalg.norm(actual-expected,axis=1).max());assert err<2e-6;assert np.isfinite(actual).all();d=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;rc=np.array([c.points_length for c in d.curves]);assert np.array_equal(rc,z["evaluatedCounts"]);assert np.array_equal(q.arr(d.attributes["radius"].data,"value",len(actual)),z["evaluatedRadii"])
  extraRootError=None
  if tag=="b":
   assert np.array_equal(P[:3636],oldNative);A=np.array(o.matrix_world);roots=P[np.arange(303,318)*12].astype("f8")@A[:3,:3].T+A[:3,3];cap=bpy.data.objects["AFN81_NEUTRAL_EDITABLE_GROWTH_SURFACE"];cap.data.calc_loop_triangles();G=q.arr(cap.data.vertices,"co",len(cap.data.vertices),3).astype("f8")@A[:3,:3].T+A[:3,3];T=np.array([t.vertices[:] for t in cap.data.loop_triangles]);target=np.array([np.array(row["targetCapBarycentric"])@G[T[row["targetCapTriangle"]]] for row in ref["newRootCorrespondence"]]);extraRootError=float(np.linalg.norm(roots-target,axis=1).max());assert extraRootError<2e-6;table=bpy.data.objects["AFN81_RENDER_ROOT_BINDING_TABLE"].data;assert len(table.vertices)==len(rc);assert all(len(at.data)==len(rc) for at in table.attributes if at.name.startswith(("AFN69_","AFN81_")))
  textures=[]
  for im in bpy.data.images:
   if im.source=="FILE" and not im.packed_file:
    p=Path(bpy.path.abspath(im.filepath));assert im.filepath.startswith("//") and p.is_file();textures.append({"relative":im.filepath,"sha256":sha(p)})
  assert len(textures)==15 and not bpy.data.libraries;outcomes.append({"tag":tag,"source":ref["output"],"sha256":ref["outputSha256"],"status":"PASS_MINIMUM_REJECTED_SOURCE_READBACK_ONLY","nativeGuides":len(o.data.curves),"nativePoints":len(P),"evaluatedCurves":len(rc),"evaluatedPoints":len(actual),"neutralReadbackMaximumErrorM":err,"allFiveNativeCagesKeysUVWeightsDriversExact":True,"originalMaterialsLightsDentalDataExact":True,"newBRootCapCorrespondenceMaximumErrorM":extraRootError,"externalTextures":textures,"appearanceRejectedBeforeBroadChecks":True,"fullContactDynamicsRuntimeUnaccepted":True})
 save("minimum-source-readback.json",{"studies":outcomes,"seconds":time.time()-tick,"notAFullFunctionOrContactCertificate":True});print("R83_MINIMUM_REJECTED_SOURCE_READBACK_DONE",time.time()-tick,flush=True)
if __name__=="__main__":main()
