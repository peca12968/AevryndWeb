"""One regional native-guide lift and inward comb on the SAME complete woman.
Root coordinates/order, publisher generation parameters and material are fixed.
No all-point registration, density/radius sweep or opaque scalp cover.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
R=Path(r"D:/Download/Aevrynd");S=R/"engine/assets/characters/female-next/source";E=R/"Evidence/character-female-next/r0083-posterior-guide-authoring";SRC=S/"aevrynd-female-next-r0081-b-stable-frame-curly-study.blend";SHA="dfcc38df12c6bd93c9659b90f8b665e973b7a90f3828b134297bd6f2365898c0";OUT=S/"aevrynd-female-next-r0083-a-regional-posterior-guide-sculpt.blend"
def module(n,f):
 sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(f));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
m=module("r83base","build-female-next-r0081-editable-curly.py");m.E=E;m.m.E=E;m.rig.E=E;m.rig.shade.g.E=E
visual=module("r83views","render-female-next-r0081-retained-study.py");visual.E=E

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,d):(E/n).write_text(json.dumps(d,indent=2)+"\n",encoding="utf-8")
def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
def main():
 tick=time.time();assert not OUT.exists() and sha(SRC)==SHA;bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();o=bpy.data.objects["AFN81_EDITABLE_CURLY_GUIDES"];q=m.q;P=q.arr(o.data.position_data,"vector",len(o.data.position_data),3);A=np.array(o.matrix_world);W=P@A[:3,:3].T+A[:3,3];counts=np.array([c.points_length for c in o.data.curves]);starts=np.r_[0,np.cumsum(counts)[:-1]];Q=W.copy();edits=[];before=m.q.hair(o).copy();d=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;renderCounts=np.array([c.points_length for c in d.curves]);renderStarts=np.r_[0,np.cumsum(renderCounts)[:-1]];radii=q.arr(d.attributes["radius"].data,"value",len(before)).copy();mats={mat.name:m.rig.k.f.v.v32.material_signature(mat) for mat in bpy.data.materials if mat.use_nodes};lights=m.m.q.lights()
 for ci,(st,n) in enumerate(zip(starts,counts)):
  root=W[st];weight=float(smooth(.025,.038,root[1])*smooth(1.47,1.49,root[2])*(1-smooth(.035,.05,abs(root[0]))))
  if weight<=.01:continue
  t=np.linspace(0,1,n);shape=smooth(0,.16,t)*(1-smooth(.50,.84,t));delta=np.zeros((n,3));delta[:,1]=.012*weight*shape;delta[:,0]=-.18*root[0]*weight*shape;Q[st:st+n]+=delta;edits.append({"guide":ci,"rootWorldM":root.tolist(),"regionalWeight":weight,"maximumControlMoveM":float(np.linalg.norm(delta,axis=1).max())})
 local=(Q-A[:3,3])@np.linalg.inv(A[:3,:3]).T;local=local.astype("f4");local[starts]=P[starts];o.data.position_data.foreach_set("vector",local.ravel());o.data.update_tag();bpy.context.view_layer.update();after=m.q.hair(o);d=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;newCounts=np.array([c.points_length for c in d.curves]);assert np.array_equal(newCounts,renderCounts),"Structural output changed: must rebind before source save";newRadii=q.arr(d.attributes["radius"].data,"value",len(after));assert np.array_equal(newRadii,radii);rootError=float(np.linalg.norm(after[renderStarts]-before[renderStarts],axis=1).max());assert rootError<2e-6,"Generated root correspondence changed: must rebind";assert np.array_equal(local[starts],P[starts]);assert np.isfinite(after).all();assert {mat.name:m.rig.k.f.v.v32.material_signature(mat) for mat in bpy.data.materials if mat.use_nodes}==mats;assert lights==m.m.q.lights();change=np.linalg.norm(after-before,axis=1);assert change.max()>.001
 o["AFN83_scope"]="Regional native-guide proximal lift/inward comb only; roots/counts/radii/material fixed and generated root table correspondence checked. Inherited r81 skin-frame target failure, neutral body intersections and missing natural dynamics remain unaccepted.";s["AFN83_scope"]=o["AFN83_scope"];m.rig.shade.settings();s.render.hair_subdiv=3;m.rig.k.b.camera("face");s.camera.data.lens=85;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True);np.savez_compressed(E/"a-guide-edit-and-evaluated-lineage.npz",beforeNativeLocal=P,afterNativeLocal=local,nativeCounts=counts,matrix=A,beforeEvaluatedWorld=before,afterEvaluatedWorld=after,evaluatedCounts=renderCounts,evaluatedRadii=newRadii)
 save("a-build-summary.json",{"source":str(SRC),"sourceSha256":SHA,"output":str(OUT),"outputSha256":sha(OUT),"outputBytes":OUT.stat().st_size,"nativeGuides":len(counts),"nativePoints":len(local),"editedGuides":edits,"actualEvaluatedCurves":len(renderCounts),"actualEvaluatedPoints":len(after),"generatedRootCorrespondenceMaximumWorldErrorM":rootError,"rootCountOrderAndCoordinatesRetained":True,"sameIndexedR81BindingsRetainedOnlyAfterActualRootReadback":True,"radiusDensitySeedCurlAndMaterialsUnchanged":True,"maximumEvaluatedPointMoveM":float(change.max()),"secondsBeforePreview":time.time()-tick,"contactNaturalMotionRuntimeAccepted":False})
 rows=[]
 for view in ("back","face","body-face"):
  rows.append(visual.image("a-regional",view));save("a-pilot-controls.json",rows)
 print("R83_REGIONAL_GUIDE_PILOT_COMPLETE",len(edits),float(change.max()),time.time()-tick,flush=True)
if __name__=="__main__":main()
