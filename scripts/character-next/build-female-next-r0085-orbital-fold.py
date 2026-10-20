"""One full source-authored CC0 upper-eyelid crease on the same complete woman.
Native-index sculpt geometry, not a dark painted crease, skin shader or weight sweep.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
R=Path(r"D:/Download/Aevrynd");S=R/"engine/assets/characters/female-next/source";E=R/"Evidence/character-female-next/r0085-orbital-fold";D=R/"Reference/character/charmorph-vitruvian-cc0/r0085-orbital-fold";SRC=S/"aevrynd-female-next-r0081-b-stable-frame-curly-study.blend";OUT=S/"aevrynd-female-next-r0085-a-native-upper-lid-fold-study.blend"
def module(n,f):
 sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(f));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
m=module("r85basis","build-female-next-r0081-editable-curly.py");m.E=E;m.m.E=E;m.rig.E=E;m.rig.shade.g.E=E;v=module("r85render","render-female-next-r0081-retained-study.py");v.E=E

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,d):(E/n).write_text(json.dumps(d,indent=2)+"\n",encoding="utf-8")
def main():
 tick=time.time();assert not OUT.exists() and sha(SRC)=="dfcc38df12c6bd93c9659b90f8b665e973b7a90f3828b134297bd6f2365898c0";morph=D/"Eyes_EyelidsCrease.npz";assert sha(morph)=="4e062e7b37cd4da4c1ca438b21cdeda2480ab0914ea0036011d0af8fa25aacb5";bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();q=m.q;hair=bpy.data.objects["AFN81_EDITABLE_CURLY_GUIDES"];hairBefore=q.hair(hair).copy();native=np.load(R/"Reference/character/charmorph-vitruvian-cc0/Default.npy");z=np.load(morph);delta=np.zeros_like(native);delta[z["idx"]]=z["delta"];changes=[];preflight=[];allIDs=[];mats={mat.name:m.rig.k.f.v.v32.material_signature(mat) for mat in bpy.data.materials if mat.use_nodes};lights=m.m.q.lights()
 for name in m.rig.native_names():
  o=bpy.data.objects[name];ids=q.arr(o.data.attributes["AFN60_NativeVertexID"].data,"value",len(o.data.vertices),dtype="i4");allIDs.extend(ids.tolist());dd=delta[ids];active=np.linalg.norm(dd,axis=1)>1e-10;preflight.append({"object":name,"affectedNativeVertices":int(active.sum())})
  if not np.any(active):continue
  assert name=="AFN60_BODY_ORAL_AND_OCULAR_LINING","Unexpected eye/optical component deformation";roles=set()
  for f in o.data.polygons:
   if any(active[i] for i in f.vertices):roles.add(o.data.materials[f.material_index].name)
  assert roles=={"AFN57_CANONICAL_SKIN"},roles;basis=np.array([p.co[:] for p in o.data.shape_keys.key_blocks[0].data]);assert np.max(np.abs(basis-native[ids]))<1e-7;key=o.shape_key_add(name="AFN85_CC0_UPPER_LID_CREASE",from_mix=False);key.relative_key=o.data.shape_keys.key_blocks[0];key.data.foreach_set("co",(basis+dd).astype("f4").ravel());key.value=1;key.slider_min=0;key.slider_max=1;changes.append({"object":name,"shapeKey":key.name,"value":1,"affectedNativeVertices":int(active.sum()),"incidentMaterialRoles":list(roles),"maximumNativeDeltaM":float(np.linalg.norm(dd,axis=1).max())})
 assert sorted(allIDs)==list(range(37436));bpy.context.view_layer.update();hairError=float(np.linalg.norm(q.hair(hair)-hairBefore,axis=1).max());assert hairError<2e-6;assert mats=={mat.name:m.rig.k.f.v.v32.material_signature(mat) for mat in bpy.data.materials if mat.use_nodes} and lights==m.m.q.lights();s["AFN85_scope"]="One source-native CC0 upper-eyelid fold sculpt at author endpoint1.108 native skin vertices; all optical components, original keys/UV/rig/materials preserved. Current eye/lid contact and expressions require affected checks; no old pass inherited. Hair/cloth/natural dynamics/engine unaccepted.";m.rig.shade.settings();s.render.hair_subdiv=3;m.rig.k.b.camera("face");s.camera.data.lens=85;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True);np.savez_compressed(E/"a-native-fold-delta.npz",delta=delta,nativeIDs=z["idx"]);save("a-build-summary.json",{"source":str(SRC),"sourceSha256":sha(SRC),"output":str(OUT),"outputSha256":sha(OUT),"outputBytes":OUT.stat().st_size,"nativeSculptSource":str(morph),"nativeSculptSha256":sha(morph),"authorEndpointNotWeightSweep":1,"preflight":preflight,"changes":changes,"neutralHairMaximumWorldChangeM":hairError,"originalMaterialsLightsRigAndExistingShapeKeysPreserved":True,"noEyeOrMouthComponentAuthoredDelta":True,"secondsBeforePreview":time.time()-tick,"affectedContactBlinkOrFullCharacterAcceptance":False});rows=[]
 for view in ("face","body-face","profile","oblique"):rows.append(v.image("a-fold",view));save("a-pilot-controls.json",rows)
 print("R85_NATIVE_UPPER_LID_FOLD_PILOT_DONE",time.time()-tick,flush=True)
if __name__=="__main__":main()
