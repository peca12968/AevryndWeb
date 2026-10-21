"""Minimum independently reopened finite-layer failure and source recovery.
No broad contact audits after the actual closed appearance has failed.
"""
from pathlib import Path
import bpy,numpy as np,json,time,importlib.util,hashlib
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0128-finite-native-lid-walls';S=R/'engine/assets/characters/female-next/source'
sp=importlib.util.spec_from_file_location('r128read',Path(__file__).with_name('articulate-female-next-r0128-finite-plates.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);b=a.b
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda a:a.tolist() if isinstance(a,np.ndarray) else a.item())+'\n',encoding='utf-8')
def raw_pose(ob):
 base=np.array([p.co[:] for p in ob.data.vertices]);sk=ob.data.shape_keys
 if sk:
  base=np.array([p.co[:] for p in sk.key_blocks[0].data]);basis=base.copy()
  for key in list(sk.key_blocks)[1:]:base+=key.value*(np.array([p.co[:] for p in key.data])-basis)
 M=np.array(ob.matrix_world);return base@M[:3,:3].T+M[:3,3]
def main():
 tick=time.time();results={};protected=None
 for name in ['a','b']:
  build=json.loads((E/(name+'-build-summary.json')).read_text('utf-8'));p=Path(build['output']);assert a.a.a.sha(p)==build['sha256'];bpy.ops.wm.open_mainfile(filepath=str(p));skin=bpy.data.objects['AFN126_COMPLETE_WOMAN_BODY_AND_ARTIST_HEAD'];protected=a.a.a.protected();beforeRest=None;states=[]
  for label,value in [('neutral',0.),('quarter',.25),('half',.5),('closed',1.),('restored',0.)] if name=='b' else [('neutral',0.)]:
   if name=='b':a.deliver(value)
   _,W,T=b.u.b.geom(skin);W=W.copy();T=T.copy();assert np.isfinite(W).all()
   if beforeRest is None:beforeRest=W.copy()
   layers=[]
   for side in ['L','R']:
    ob=bpy.data.objects['AFN128_'+side+'_FINITE_TARSAL_PLATE'];_,V,TT=b.u.b.geom(ob);V=V.copy();TT=TT.copy();raw=raw_pose(ob);assert np.isfinite(V).all() and np.isfinite(raw).all();nn=len(raw);outer=V[:nn];inner=V[nn:2*nn];rawAreas=np.linalg.norm(np.cross(raw[np.array([f.vertices[:] for f in ob.data.polygons])[:,1]]-raw[np.array([f.vertices[:] for f in ob.data.polygons])[:,0]],raw[np.array([f.vertices[:] for f in ob.data.polygons])[:,2]]-raw[np.array([f.vertices[:] for f in ob.data.polygons])[:,0]]),axis=1)*.5;layers.append({'object':ob.name,'rawVertices':nn,'evaluatedVertices':len(V),'evaluatedTriangles':len(TT),'allFinite':True,'boundsWorldM':[V.min(0),V.max(0)],'nominalModifierThicknessM':ob.modifiers[0].thickness,'modifierEvenOffset':ob.modifiers[0].use_even_offset,'evaluatedFirstBlockAgainstActualRawPoseMaxM':float(np.linalg.norm(outer-raw,axis=1).max()),'evaluatedInnerBlockAgainstActualRawPoseOffsetRangeM':[float(np.linalg.norm(inner-raw,axis=1).min()),float(np.linalg.norm(inner-raw,axis=1).max())] if len(V)==2*nn else None,'rawOuterTriangleAreaRangeM2':[float(rawAreas.min()),float(rawAreas.max())],'actualFiniteSelfContactOrContinuousProof':False})
   states.append({'state':label,'control':value,'actualSkinMaximumMoveM':float(np.linalg.norm(W-beforeRest,axis=1).max()),'finiteLayers':layers})
  if name=='b':assert states[-1]['actualSkinMaximumMoveM']==0.
  # Directly edit an actual displayed finite-plate exterior key/vertex and
  # restore. This proves source edit recovery, not a usable closed eyelid.
  ob=bpy.data.objects['AFN128_R_FINITE_TARSAL_PLATE'];key=ob.data.shape_keys.key_blocks['Basis'] if ob.data.shape_keys else None;points=key.data if key else ob.data.vertices;_,A,_=b.u.b.geom(ob);A=A.copy();vi=0;old=points[vi].co.copy();points[vi].co.y-=.0001;ob.data.update();ob.update_tag();bpy.context.view_layer.update();_,B,_=b.u.b.geom(ob);editMove=float(np.linalg.norm(B-A,axis=1).max());assert editMove>1e-5;points[vi].co=old;ob.data.update();ob.update_tag();bpy.context.view_layer.update();_,B,_=b.u.b.geom(ob);assert np.array_equal(A,B);textures=[];packed=[]
  for im in bpy.data.images:
   if im.packed_file:packed.append({'name':im.name,'bytes':len(im.packed_file.data),'sha256':hashlib.sha256(im.packed_file.data).hexdigest()})
   elif im.source=='FILE' and im.filepath:
    ip=Path(bpy.path.abspath(im.filepath));assert ip.is_file();textures.append({'image':im.name,'relative':im.filepath,'absolute':str(ip),'bytes':ip.stat().st_size,'sha256':a.a.a.sha(ip)})
  assert a.a.a.sha(p)==build['sha256'];results[name]={'candidate':{'source':str(p),'sha256':build['sha256'],'bytes':p.stat().st_size},'independentlyReopened':True,'actualPoseStates':states,'actualFiniteLayerEditMaxM':editMove,'actualEditRestoredExactly':True,'allReferencedExternalTextures':textures,'packedOriginalArtistTextures':packed,'newCompleteOperationAccepted':False,'finiteSelfContinuousContactRuntimeAccepted':False}
 # Old hidden complete rollback/fibres are independently compared to original.
 bpy.ops.wm.open_mainfile(filepath=str(S/'r0126-source/aevrynd-female-next-r0126-b-source-section-neck.blend'));assert protected==a.a.a.protected();save('minimum-saved-finite-lid-readback.json',{'sources':results,'oldHiddenRollbackComparedAgainstIndependentlyReopenedR126Exactly':True,'scope':'Saved sources/actual finite geometry/edit recovery and witnessed failed closure only. No global contacts, anatomy, complete usable blink or runtime acceptance.','seconds':time.time()-tick});print('R128_TWO_FULL_SOURCES_AND_FAILED_FINITE_LAYER_RECOVERED',time.time()-tick,flush=True)
if __name__=='__main__':main()
