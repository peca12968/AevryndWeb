"""Minimum rejected-fold readback and actual neutral reversal; no broad tests."""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
R=Path(r"D:/Download/Aevrynd");E=R/"Evidence/character-female-next/r0085-orbital-fold"
def module(n,f):
 sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(f));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
v=module("r85native","verify-female-next-r0076-crowns.py");m=module("r85basecheck","build-female-next-r0081-editable-curly.py")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 tick=time.time();refs={t:json.loads((E/(t+"-build-summary.json")).read_text()) for t in "ab"};assert sha(Path(refs["a"]["source"]))==refs["a"]["sourceSha256"];bpy.ops.wm.open_mainfile(filepath=refs["a"]["source"]);bpy.context.scene.frame_set(1);bpy.context.view_layer.update();q=m.q;names=m.rig.native_names();sig={n:v.signature(bpy.data.objects[n]) for n in names};base={n:m.rig.k.mesh(bpy.data.objects[n])["V"].copy() for n in names};skinName="AFN74_SKIN_AND_EXISTING_OCULAR_LINING";base[skinName]=m.rig.k.mesh(bpy.data.objects[skinName])["V"].copy();hairNames=("AFN81_EDITABLE_CURLY_GUIDES","AFN57_NATIVE_BROWS","AFN57_NATIVE_LASHES");hair={n:q.hair(bpy.data.objects[n]).copy() for n in hairNames};mats={mat.name:m.rig.k.f.v.v32.material_signature(mat) for mat in bpy.data.materials if mat.use_nodes};lights=m.m.q.lights();out=[]
 for tag,ref in refs.items():
  assert sha(Path(ref["output"]))==ref["outputSha256"];bpy.ops.wm.open_mainfile(filepath=ref["output"]);bpy.context.scene.frame_set(1);bpy.context.view_layer.update();body=bpy.data.objects["AFN60_BODY_ORAL_AND_OCULAR_LINING"];keyName="AFN85_CC0_UPPER_LID_CREASE" if tag=="a" else ref["shapeKey"];key=body.data.shape_keys.key_blocks[keyName];ids=q.arr(body.data.attributes["AFN60_NativeVertexID"].data,"value",len(body.data.vertices),dtype="i4");delta=np.load(E/(tag+"-native-fold-delta.npz"))["delta"];basis=np.array([p.co[:] for p in body.data.shape_keys.key_blocks[0].data]);assert np.array_equal(q.arr(key.data,"co",len(key.data),3),(basis+delta[ids]).astype("f4"));assert key.value==1 and key.relative_key==body.data.shape_keys.key_blocks[0];parts={}
  for n in names+[skinName]:
   actual=m.rig.k.mesh(bpy.data.objects[n])["V"];assert actual.shape==base[n].shape and np.isfinite(actual).all();change=np.linalg.norm(actual-base[n],axis=1);parts[n]={"maximumWorldDeltaM":float(change.max()),"changedOver1Micrometre":int((change>1e-6).sum())}
   if n in names[:4]:assert np.array_equal(actual,base[n]),n
  hairErrors={n:float(np.linalg.norm(q.hair(bpy.data.objects[n])-hair[n],axis=1).max()) for n in hairNames};key.value=0;bpy.context.view_layer.update()
  for n in names+[skinName]:assert np.array_equal(m.rig.k.mesh(bpy.data.objects[n])["V"],base[n]),n
  for n in hairNames:assert np.array_equal(q.hair(bpy.data.objects[n]),hair[n]),n
  body.shape_key_remove(key);assert {n:v.signature(bpy.data.objects[n]) for n in names}==sig;assert {n:m.rig.k.f.v.v32.material_signature(bpy.data.materials[n]) for n in mats}==mats and m.m.q.lights()==lights;textures=[]
  for im in bpy.data.images:
   if im.source=="FILE" and not im.packed_file:
    path=Path(bpy.path.abspath(im.filepath));assert im.filepath.startswith("//") and path.is_file();textures.append({"relative":im.filepath,"sha256":sha(path)})
  assert len(textures)==15 and not bpy.data.libraries;assert sha(Path(ref["output"]))==ref["outputSha256"];out.append({"tag":tag,"status":"PASS_MINIMUM_REJECTED_SCULPT_AND_NEUTRAL_REVERSAL_ONLY","source":ref["output"],"sha256":ref["outputSha256"],"storedDeltaExact":True,"actualNeutralPartChanges":parts,"hairAndFacialFibreMaximumWorldChangesM":hairErrors,"disablingNewKeyRecoversExactCompleteNeutralIncludingHair":True,"allOriginalNativeDataKeysUVWeightsDriversMaterialsLightsExactAfterRemovingAddedKeyInMemory":True,"externalTextures":textures,"savedSourceNotModified":True,"newEyelidOpticalAndSkinSelfContactsNotQualified":True,"blinkAndNaturalDynamicsRuntimeNotQualified":True})
 (E/"minimum-source-readback.json").write_text(json.dumps({"studies":out,"seconds":time.time()-tick,"scope":"Saved new sculpt data, actual displayed geometry and exact neutral reversal only. No broader testing after visual rejection."},indent=2)+"\n");print("R85_MINIMUM_REJECTED_SCULPT_READBACK_DONE",time.time()-tick,flush=True)
if __name__=="__main__":main()
