"""Independent saved-source/edit/restore recovery after visible appearance rejection.
No broad contact/physics/runtime qualification of a visually ineffective trial.
"""
from pathlib import Path
import bpy,numpy as np,json,time,importlib.util
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0125-craniofacial-rest-shape'
sp=importlib.util.spec_from_file_location('r125saved',Path(__file__).with_name('build-female-next-r0125-craniofacial-rest.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a)
def main():
 tick=time.time();build=json.loads((E/'a-build-summary.json').read_text('utf-8-sig'));p=Path(build['output']);assert a.a.sha(p)==build['sha256'];bpy.ops.wm.open_mainfile(filepath=str(p));a.b.deliver(0.);skin=bpy.data.objects[build['actualSkinObject']];edit=bpy.data.objects[build['coarseSculptObject']];a.set_control(0.);zero=a.a.protected();assert zero==build['beforeProtected'];_,Z,_=a.b.u.b.geom(skin);Z=Z.copy();states=[]
 for value in [.5,1.]:
  a.set_control(value);_,W,_=a.b.u.b.geom(skin);W=W.copy();states.append({'control':value,'maximumActualDisplayedSkinMovementFromOriginalM':float(np.linalg.norm(W-Z,axis=1).max()),'verticesMovedAbove0P1Micrometre':int((np.linalg.norm(W-Z,axis=1)>1e-7).sum())})
 one=a.a.protected();assert one==build['afterProtected'];_,B,_=a.b.u.b.geom(skin);B=B.copy();cage=bpy.data.objects[build['cageObject']];point=cage.data.points[88];original=point.co_deform.copy();point.co_deform.y+=.002;cage.data.update_tag();cage.update_tag();edit.update_tag();bpy.context.view_layer.update();_,V,_=a.b.u.b.geom(skin);V=V.copy();move=float(np.linalg.norm(V-B,axis=1).max());assert move>1e-7;point.co_deform=original;cage.data.update_tag();cage.update_tag();edit.update_tag();bpy.context.view_layer.update();_,restored,_=a.b.u.b.geom(skin);assert np.array_equal(restored,B);assert a.a.protected()==one
 textures=[]
 for im in bpy.data.images:
  if im.source=='FILE' and im.filepath:
   ip=Path(bpy.path.abspath(im.filepath));row={'image':im.name,'relative':im.filepath,'absolute':str(ip),'packed':im.packed_file is not None,'exists':ip.is_file()}
   if ip.is_file():row.update(sha256=a.a.sha(ip),bytes=ip.stat().st_size)
   assert row['packed'] or row['exists'],row;textures.append(row)
 a.set_control(0.);assert a.a.protected()==zero;a.set_control(1.);assert a.a.protected()==one;assert a.a.sha(p)==build['sha256'];assert np.isfinite(B).all()
 a.save('minimum-saved-source-readback.json',{'candidate':{'source':str(p),'sha256':a.a.sha(p),'bytes':p.stat().st_size},'independentlyReopened':True,'control0ActualDisplayAndAllOriginalRawKeysFibresExactlyRecoverBaseline':True,'control1ExactlyRecoversBuildEvidence':True,'actualControlStates':states,'oneActualVolumeCagePointEdited':88,'temporaryEditWorldDisplayMovementM':move,'temporaryEditActualDisplayRestoredExactly':True,'allOriginalRawClosureKeysPreservedAtControl1':True,'allOriginalFibresAtControl1Exact':build['allOriginalFibreGeometryAndRadiusHashesStillExact'],'actualSourceAndCandidateFibreHashes':{'before':zero['allOriginalFibres'],'after':one['allOriginalFibres']},'originalControl0AndCandidateControl1BothRestoredExactly':True,'allReferencedExternalTextures':textures,'savedSourceBytesUnchangedByReadback':True,'actualDisplayedGeometryFinite':True,'newCompleteOperationAccepted':False,'scope':'Saved authoring/source recovery only. Craniofacial anatomy/continuity and affected finite self/inner surface contacts not qualified. Existing blink previews are discrete source poses, not a newly accepted complete facial operation. No natural-hair/body/clothing/motion/runtime/LOD/performance qualification.','seconds':time.time()-tick})
 print('R125_MINIMUM_SOURCE_EDIT_RESTORE_DONE',move,time.time()-tick,flush=True)
if __name__=='__main__':main()
