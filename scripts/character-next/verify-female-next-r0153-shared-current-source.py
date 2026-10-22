"""Independently reopen the real shared-data woman, edit and restore it."""
from pathlib import Path
import bpy,numpy as np,json,time,importlib.util
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0153-current-hairline'
sp=importlib.util.spec_from_file_location('r153verify',Path(__file__).with_name('build-female-next-r0153-current-hairline.py'));h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h);a=h.a
def hashes(names):return {n:[a.a.hasharray(v) for v in a.geometry(bpy.data.objects[n])] for n in names}
def main():
 tick=time.time();b=json.loads((E/'a-build-summary.json').read_text());before=json.loads((E/'manifest-before.json').read_text());baseline=before['workingCompleteWomanReference'];assert a.a.sha(Path(baseline['source']))==baseline['sha256'];bpy.ops.wm.open_mainfile(filepath=baseline['source']);s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();names=a.FIXED+a.MOVING;raw={n:a.rawsig(bpy.data.objects[n]) for n in names};poses={}
 for frame in range(1,50):s.frame_set(frame);bpy.context.view_layer.update();poses[frame]=hashes(names)
 assert a.a.sha(Path(b['output']))==b['sha256'];bpy.ops.wm.open_mainfile(filepath=b['output']);s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();assert raw=={n:a.rawsig(bpy.data.objects[n]) for n in names};linked=[]
 for n in names:
  ob=bpy.data.objects[n];assert not ob.library and ob.data.library;linked.append({'object':n,'meshLibrary':ob.data.library.filepath,'meshData':ob.data.name})
 for frame in range(1,50):s.frame_set(frame);bpy.context.view_layer.update();assert hashes(names)==poses[frame],('gaze preservation',frame)
 s.frame_set(1);bpy.context.view_layer.update();hair=bpy.data.objects[b['actualHair']];skin=bpy.data.objects[b['actualSkin']];P=a.q.hair(hair);assert len(P)==16900 and len(hair.data.curves)==1300 and np.isfinite(P).all();assert not bpy.data.objects['AFN126_ORIGINAL_Hair_Hair_0'].hide_render;assert bpy.data.objects.get('AFN152_ACTUAL_NATIVE_NEIGHBOUR_GROOM') is None
 d=hair.data;native=np.empty((len(d.points),3),'f4');d.position_data.foreach_get('vector',native.ravel());edit=native.copy();edit[6,0]+=.001;d.position_data.foreach_set('vector',edit.ravel());d.update_tag();hair.update_tag();bpy.context.view_layer.update();movement=np.linalg.norm(a.q.hair(hair)-P,axis=1);affected=int(np.count_nonzero(movement>3e-6));rootMovement=float(movement[::13].max());assert affected>0 and movement.max()>.0009 and rootMovement<3e-6;d.position_data.foreach_set('vector',native.ravel());d.update_tag();hair.update_tag();bpy.context.view_layer.update();hairRestore=float(np.linalg.norm(a.q.hair(hair)-P,axis=1).max());assert hairRestore<3e-6
 # The displayed linked skin can be copied to editable local data without
 # changing its source library. Operate that actual skin, then restore reference.
 lineage=np.load(E/'hairline-authoring.npz');tri=lineage['rootTriangles'][0];bc=lineage['rootBarycentric'][0];vi=int(tri[np.argmax(bc)]);originalData=skin.data;local=originalData.copy();skin.data=local;assert local.library is None;co=local.vertices[vi].co.copy();local.vertices[vi].co.z+=.001;local.update();skin.update_tag();bpy.context.view_layer.update();rootSkinMovement=float(np.linalg.norm(a.q.hair(hair)[0]-P[0]));assert rootSkinMovement>1e-4;local.vertices[vi].co=co;local.update();skin.update_tag();bpy.context.view_layer.update();skin.data=originalData;skin.update_tag();bpy.context.view_layer.update();skinRestore=float(np.linalg.norm(a.q.hair(hair)-P,axis=1).max());assert skinRestore<3e-6 and hashes(names)==poses[1];bpy.data.meshes.remove(local)
 libraries=[]
 for lib in bpy.data.libraries:
  path=Path(bpy.path.abspath(lib.filepath));assert path.is_file();libraries.append({'relative':lib.filepath,'absolute':str(path),'sha256':a.a.sha(path),'bytes':path.stat().st_size})
 textures=[]
 for im in bpy.data.images:
  if im.source=='FILE' and not im.packed_file and im.filepath:
   path=Path(bpy.path.abspath(im.filepath,library=im.library));assert path.is_file();textures.append({'relative':im.filepath,'library':im.library.filepath if im.library else None,'absolute':str(path),'sha256':a.a.sha(path),'bytes':path.stat().st_size})
 assert a.a.sha(Path(b['output']))==b['sha256'] and a.a.sha(Path(b['source']))==b['sourceSha256'] and a.a.sha(Path(baseline['source']))==baseline['sha256'];h.save('independent-shared-current-source-readback.json',{'independentlyReopened':True,'sameSevenRawMeshesUVAnd49ActualGazePoses':True,'localCurrentObjectsRigAndAction':True,'sharedMeshes':linked,'actualHair':b['actualHair'],'actualCurves':1300,'actualPoints':len(P),'surfaceUVRootCount':len(d.attributes['surface_uv_coordinate'].data),'actualPointEditAffectedDisplayedPoints':affected,'actualPointEditRootMovementM':rootMovement,'actualPointEditRestorationM':hairRestore,'actualLocalEditableSkinCopyRootMovementM':rootSkinMovement,'actualSkinLinkedReferenceRestorationM':skinRestore,'existingSourceLibrariesAndFileHashesUnchanged':True,'relativeLibraryDependencies':libraries,'relativeExternalTextures':textures,'sharedSourceConstructionOnlyNotCharacterAppearanceFunctionContactOrRuntimeAdoption':True,'naturalHairMotionContactRuntimeUnaccepted':True,'globalSignedMinimumM':None,'seconds':time.time()-tick});print('R153_INDEPENDENT_SHARED_WOMAN_49_GAZE_EDIT_AND_RESTORE_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
