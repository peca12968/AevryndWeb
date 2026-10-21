"""Independent actual displayed pose recovery and cheap ocular falsification."""
from pathlib import Path
import bpy,numpy as np,json,time,importlib.util,ast,hashlib
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0127-native-lid-closure'
sp=importlib.util.spec_from_file_location('r127verify',Path(__file__).with_name('build-female-next-r0127-native-lid-closure.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);b=a.b
def main():
 tick=time.time();build=json.loads((E/'a-build-summary.json').read_text('utf-8'));p=Path(build['output']);assert a.a.sha(p)==build['sha256'];bpy.ops.wm.open_mainfile(filepath=str(p));skin=bpy.data.objects[build['actualDisplayedSkin']];line=np.load(E/'native-lid-authoring-lineage.npz');rest=None;rows=[];contact=[];parsed=ast.parse(Path(__file__).with_name('verify-female-next-r0037-eye-margin.py').read_text('utf-8'));ns={'np':np};exec(compile(ast.Module(body=[n for n in parsed.body if isinstance(n,ast.FunctionDef) and n.name in ['inside','intersections']],type_ignores=[]),'unchanged-r37-surface-intersections','exec'),ns)
 for label,value in [('neutral',0.),('quarter',.25),('half',.5),('closed',1.),('restored',0.)]:
  a.deliver(value);_,W,T=b.u.b.geom(skin);W=W.copy();T=T.copy();assert np.isfinite(W).all()
  if rest is None:rest=W.copy()
  extra={}
  for name in build['nativeAttachments']:
   _,P,PT=b.u.b.geom(bpy.data.objects[name]);assert np.isfinite(P).all();extra[name]={'vertices':len(P),'finite':True}
  rows.append({'state':label,'control':value,'actualDisplayedSkinMaxMoveM':float(np.linalg.norm(W-rest,axis=1).max()),'attachments':extra})
  if label in ['neutral','half','closed']:
   bt=BVHTree.FromPolygons(W.tolist(),T.tolist(),all_triangles=True,epsilon=0.)
   for name in ['AFN126_ORIGINAL_Eye_Eye_0','AFN126_ORIGINAL_EyeScleraReflect_EyeScleraReflect_0']:
    _,P,PT=b.u.b.geom(bpy.data.objects[name]);P=P.copy();PT=PT.copy();pairs=bt.overlap(BVHTree.FromPolygons(P.tolist(),PT.tolist(),all_triangles=True,epsilon=0.));hits=[];tested=0
    for i,j in pairs:
     pts=ns['intersections'](W[T[i]],P[PT[j]]);tested+=1
     if pts:hits.append({'skinTriangle':i,'eyeTriangle':j,'worldIntersectionOrTouchPointsM':pts[:4]})
     if len(hits)>=8:break
    contact.append({'state':label,'pair':'actual displayed skin vs '+name,'BVHBroadphasePairs':len(pairs),'pairsRefinedUntilCap':tested,'cap':8,'surfaceIntersectionOrTouchWitnesses':hits,'notGlobalSignedMinimumFiniteThicknessContainmentOrContinuousProof':True,'noRegionExcluded':True})
 assert rows[-1]['actualDisplayedSkinMaxMoveM']==0.;a.deliver(1.);views=json.loads((E/'a-view-controls.json').read_text('utf-8'));cam=bpy.context.scene.camera;cam.matrix_world=Matrix(views[0]['camera']);cam.data.lens=85.;sc=bpy.context.scene;sc.render.resolution_x=sc.render.resolution_y=640;deps=bpy.context.evaluated_depsgraph_get();proj=cam.calc_matrix_camera(deps,x=640,y=640).inverted();origin=cam.matrix_world.translation;trees=[]
 for ob in bpy.data.objects:
  if ob.type!='MESH' or ob.hide_render:continue
  _,W,T=b.u.b.geom(ob);trees.append((ob.name,BVHTree.FromPolygons(W.tolist(),T.tolist(),all_triangles=True,epsilon=0.)))
 rays=[]
 for x in [239,252,265,277,359,370,383,395]:
  for y in [246,251,255]:
   v=proj@Vector(((x+.5)/320-1,1-(y+.5)/320,-1,1));v/=v.w;direction=(cam.matrix_world.to_3x3()@v.to_3d()).normalized();hits=[]
   for name,bt in trees:
    pnt,nor,fi,dist=bt.ray_cast(origin,direction)
    if pnt is not None:hits.append({'object':name,'distanceM':dist,'triangle':fi,'world':list(pnt)})
   rays.append({'pixel':[x,y],'hitsFrontToBack':sorted(hits,key=lambda h:h['distanceM'])[:5]})
 a.deliver(0.);currentRollback=a.a.protected()
 # Test an editable displayed closed-pose key, not property existence alone.
 a.deliver(1.);_,closed,_=b.u.b.geom(skin);closed=closed.copy();key=skin.data.shape_keys.key_blocks['AFN127_R_Closed'];raw=np.array([v.co[:] for v in key.data]);basis=np.array([v.co[:] for v in skin.data.shape_keys.key_blocks['Basis'].data]);vi=int(np.argmax(np.linalg.norm(raw-basis,axis=1)));original=key.data[vi].co.copy();key.data[vi].co.y-=.0001;skin.data.update();skin.update_tag();bpy.context.view_layer.update();_,edited,_=b.u.b.geom(skin);editMove=float(np.linalg.norm(edited-closed,axis=1).max());assert editMove>5e-5;key.data[vi].co=original;skin.data.update();skin.update_tag();bpy.context.view_layer.update();_,restored,_=b.u.b.geom(skin);assert np.array_equal(closed,restored);a.deliver(0.)
 textures=[];packed=[]
 for im in bpy.data.images:
  if im.packed_file:packed.append({'name':im.name,'sha256':hashlib.sha256(im.packed_file.data).hexdigest(),'bytes':len(im.packed_file.data)})
  elif im.source=='FILE' and im.filepath:
   ip=Path(bpy.path.abspath(im.filepath));assert ip.is_file();textures.append({'image':im.name,'relative':im.filepath,'absolute':str(ip),'sha256':a.a.sha(ip),'bytes':ip.stat().st_size})
 assert a.a.sha(p)==build['sha256'];bpy.ops.wm.open_mainfile(filepath=str(a.SRC));assert a.a.protected()==currentRollback;_,sourceNeutral,_=b.u.b.geom(bpy.data.objects[build['actualDisplayedSkin']]);assert np.array_equal(sourceNeutral,rest)
 a.save('minimum-saved-native-lid-readback.json',{'candidate':{'source':str(p),'sha256':build['sha256'],'bytes':p.stat().st_size},'independentlyReopened':True,'actualDisplayedPoseStates':rows,'neutralRestoredExactly':True,'actualClosedKeyEdit':{'vertex':vi,'actualDisplayedEditMaxM':editMove,'closedPoseRestoredExactly':True},'actualNeutralGeometryMatchesIndependentlyReopenedR126Exactly':True,'oldHiddenRollbackKeysAndAllOriginalFibresMatchIndependentlyReopenedR126Exactly':True,'allReferencedExternalTextures':textures,'packedOriginalArtistTextures':packed,'actualGrayBandDiagnosticRays':rays,'actualOcularSurfaceContactWitnesses':contact,'finiteThicknessSelfContinuousAndRuntimeUnaccepted':True,'globalSignedMinimumM':None,'completeOperationAccepted':False,'seconds':time.time()-tick});print('R127_SAVED_NATIVE_LIDS_READBACK_AND_SCOPED_DIAGNOSIS_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
