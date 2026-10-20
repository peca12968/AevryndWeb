"""Second construction:15 actual cap-rooted posterior guides, regional comb.
Same source complete woman, all original303 guides untouched. Rebind all actual
output roots after structural authoring. Not a natural-motion/contact pass.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
R=Path(r"D:/Download/Aevrynd");E=R/"Evidence/character-female-next/r0083-posterior-guide-authoring";S=R/"engine/assets/characters/female-next/source";SRC=S/"aevrynd-female-next-r0081-b-stable-frame-curly-study.blend";SHA="dfcc38df12c6bd93c9659b90f8b665e973b7a90f3828b134297bd6f2365898c0";OUT=S/"aevrynd-female-next-r0083-b-posterior-rooted-guide-group.blend"
def module(n,f):
 sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(f));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
m=module("r83Bbase","build-female-next-r0081-editable-curly.py");m.E=E;m.m.E=E;m.rig.E=E;m.rig.shade.g.E=E
visual=module("r83Bview","render-female-next-r0081-retained-study.py");visual.E=E

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,d):(E/n).write_text(json.dumps(d,indent=2)+"\n",encoding="utf-8")
def main():
 tick=time.time();assert not OUT.exists() and sha(SRC)==SHA;bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();o=bpy.data.objects["AFN81_EDITABLE_CURLY_GUIDES"];q=m.q;d=o.data;P=q.arr(d.position_data,"vector",len(d.position_data),3);A=np.array(o.matrix_world);W=P@A[:3,:3].T+A[:3,3];counts=np.array([c.points_length for c in d.curves]);starts=np.r_[0,np.cumsum(counts)[:-1]];assert len(counts)==303 and np.all(counts==12);cap=bpy.data.objects["AFN81_NEUTRAL_EDITABLE_GROWTH_SURFACE"];G=q.arr(cap.data.vertices,"co",len(cap.data.vertices),3);cap.data.calc_loop_triangles();T=np.array([t.vertices[:] for t in cap.data.loop_triangles]);GW=G@A[:3,:3].T+A[:3,3];tree=BVHTree.FromPolygons(GW.tolist(),T.tolist(),all_triangles=True);body=m.rig.k.mesh(bpy.data.objects["AFN60_BODY_ORAL_AND_OCULAR_LINING"]);bodyTree=BVHTree.FromPolygons(body["V"].tolist(),body["T"].tolist(),all_triangles=True);uv=q.arr(cap.data.uv_layers.active.data,"uv",len(cap.data.loops),2);extra=[];rootRows=[];templates=[]
 for z in [1.505,1.517,1.529]:
  for x in [-.025,-.0125,0,.0125,.025]:
   co,normal,face,_=tree.ray_cast(Vector((x,.2,z)),Vector((0,-1,0)),.3);assert co is not None;root=np.array(co);bc=m.rig.base.bary(root,GW[T[face]]);newUV=bc@uv[list(cap.data.loop_triangles[face].loops)];nearest=int(np.linalg.norm(W[starts]-root,axis=1).argmin());curve=[]
   for t in np.linspace(0,1,12):
    xx=x*(1-.15*t)+.002*np.sin(np.pi*t);zz=z-.065*t;surface,_,_,_=bodyTree.ray_cast(Vector((xx,.2,zz)),Vector((0,-1,0)),.3);assert surface is not None;yy=surface.y+.010*np.sin(np.pi*min(t/.55,1))**2+.005*t;point=np.array([xx,yy,zz]);curve.append(root if t==0 else point)
   extra.append(np.array(curve));templates.append(nearest);rootRows.append({"guide":303+len(extra)-1,"worldRootM":root.tolist(),"targetCapTriangle":int(face),"targetCapBarycentric":bc.tolist(),"surfaceUV":newUV.tolist(),"nearestOriginalGuide":nearest})
 # Copy native attribute values from nearest guide, then replace actual cap UV.
 snapshots=[]
 for at in d.attributes:
  if at.name=="position":continue
  kind=at.data_type;prop="vector" if kind in ("FLOAT_VECTOR","FLOAT2") else "value";width=3 if kind=="FLOAT_VECTOR" else 2 if kind=="FLOAT2" else 1;dtype="f4" if kind.startswith("FLOAT") else "i4";val=q.arr(at.data,prop,len(at.data),width,dtype);snapshots.append((at.name,prop,width,val.copy(),at.domain))
 d.add_curves([12]*len(extra));allW=np.concatenate([W]+extra);local=(allW-A[:3,3])@np.linalg.inv(A[:3,:3]).T;local=local.astype("f4");local[:len(P)]=P;d.position_data.foreach_set("vector",local.ravel())
 for name,prop,width,val,domain in snapshots:
  ext=np.array([val[g] if domain=="CURVE" else val[starts[g]:starts[g]+12] for g in templates]);ext=ext.reshape((-1,width)) if width>1 else ext.ravel();full=np.concatenate([val,ext]);
  if name=="surface_uv_coordinate":full[303:]=np.array([r["surfaceUV"] for r in rootRows])
  d.attributes[name].data.foreach_set(prop,full.ravel())
 d.update_tag()
 for name in ("AFN81_ACTUAL_RENDER_ROOT_TABLE","AFN81_LIVE_RENDER_SCALP_FRAME"):o.modifiers[name].show_viewport=o.modifiers[name].show_render=False
 bpy.context.view_layer.update();raw=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;rp=q.arr(raw.position_data,"vector",len(raw.position_data),3);rc=np.array([c.points_length for c in raw.curves]);rs=np.r_[0,np.cumsum(rc)[:-1]];rw=rp@A[:3,:3].T+A[:3,3];radius=q.arr(raw.attributes["radius"].data,"value",len(rp));ids=[];bary=[]
 for root in rw[rs]:
  co,_,face,_=bodyTree.find_nearest(Vector(root));ids.append(body["T"][face]);bary.append(m.rig.base.bary(np.array(co),body["V"][body["T"][face]]))
 ids=np.array(ids,"i4");bary=np.array(bary);tri=body["V"][ids];anchor=np.einsum("ij,ijk->ik",bary,tri);t,b,n=m.rig.frames(tri);kd=KDTree(len(body["V"]))
 for i,p in enumerate(body["V"]):kd.insert(Vector(p),i)
 kd.balance();F=np.array([[kd.find(Vector(target))[1] for target in (p-.01*tt,p+.01*tt,p+.01*bb)] for p,tt,bb in zip(anchor,t,b)],"i4");frameArea=np.linalg.norm(np.cross(body["V"][F[:,1]]-body["V"][F[:,0]],body["V"][F[:,2]]-body["V"][F[:,0]]),axis=1);assert frameArea.min()>1e-6
 table=bpy.data.objects["AFN81_RENDER_ROOT_BINDING_TABLE"];mesh=bpy.data.meshes.new("AFN83_REBOUND_ACTUAL_RENDER_ROOT_TABLE");mesh.vertices.add(len(rc));mesh.vertices.foreach_set("co",np.zeros(len(rc)*3,"f4"));mesh.update()
 def attr(name,kind,vals):
  at=mesh.attributes.new(name,kind,"POINT");at.data.foreach_set("vector" if kind=="FLOAT_VECTOR" else "value",np.array(vals).ravel())
 for j in range(3):attr("AFN69_BodyVertex"+str(j),"INT",ids[:,j]);attr("AFN81_FrameVertex"+str(j),"INT",F[:,j])
 for name,vals in [("Barycentric",bary),("RestAnchor",anchor),("RestTangent",t),("RestBinormal",b),("RestNormal",n)]:attr("AFN69_"+name,"FLOAT_VECTOR",np.array(vals,"f4"))
 table.data=mesh;table["AFN83_scope"]="Rebuilt actual-output root ID/barycentric and20mm frame metadata after adding15 native guides; not a follicle or motion/contact qualification."
 for name in ("AFN81_ACTUAL_RENDER_ROOT_TABLE","AFN81_LIVE_RENDER_SCALP_FRAME"):o.modifiers[name].show_viewport=o.modifiers[name].show_render=True
 bpy.context.view_layer.update();actual=q.hair(o);assert actual.shape==rw.shape;neutralError=float(np.linalg.norm(actual-rw,axis=1).max());assert neutralError<2e-6;assert np.isfinite(actual).all();o["AFN83_scope"]="318 editable guides: original303 unchanged plus15 rear-cap-rooted regional comb guides. Actual generated root table rebuilt. Prior r81 skin-frame target, body contact, natural dynamics and engine still unaccepted.";s["AFN83_scope"]=o["AFN83_scope"];m.rig.shade.settings();s.render.hair_subdiv=3;m.rig.k.b.camera("face");s.camera.data.lens=85;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True);np.savez_compressed(E/"b-guide-and-rebound-lineage.npz",beforeNativeLocal=P,afterNativeLocal=local,nativeCounts=np.r_[counts,[12]*len(extra)],matrix=A,evaluatedWorld=actual,evaluatedCounts=rc,evaluatedRadii=radius,bodyVertexIDs=ids,barycentric=bary,frameVertexIDs=F)
 save("b-build-summary.json",{"source":str(SRC),"sourceSha256":SHA,"output":str(OUT),"outputSha256":sha(OUT),"outputBytes":OUT.stat().st_size,"original303GuidesExact":True,"nativeGuides":318,"nativePoints":len(local),"newRootCorrespondence":rootRows,"actualEvaluatedCurves":len(rc),"actualEvaluatedPoints":len(actual),"actualRenderRootBindingsRebuilt":True,"neutralLiveFrameMaximumWorldErrorM":neutralError,"minimumDoubleFrameAreaM2":float(frameArea.min()),"radiusDensitySeedCurlAndMaterialNotRetuned":True,"secondsBeforePreview":time.time()-tick,"contactNaturalMotionRuntimeAccepted":False})
 rows=[]
 for view in ("back","face","body-face"):rows.append(visual.image("b-rooted",view));save("b-pilot-controls.json",rows)
 print("R83_POSTERIOR_ROOT_GROUP_PILOT_COMPLETE",len(rc),time.time()-tick,flush=True)
if __name__=="__main__":main()
