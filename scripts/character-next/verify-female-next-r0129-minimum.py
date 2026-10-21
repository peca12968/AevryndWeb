"""Independent full-source recovery and actual guide/current-skin coupling only.
No broad contact/natural-motion audit after the actual appearance was rejected.
"""
from pathlib import Path
import bpy,numpy as np,json,time,hashlib,importlib.util
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0129-native-authored-bob';S=R/'engine/assets/characters/female-next/source'
sp=importlib.util.spec_from_file_location('r129verify',Path(__file__).with_name('build-female-next-r0129-native-bob.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);b=a.b;q=a.q
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda a:a.tolist() if isinstance(a,np.ndarray) else a.item())+'\n',encoding='utf-8')
def main():
 tick=time.time();results={};oldProtected=[];line=np.load(E/'native-bob-strand-lineage.npz');rootTri=line['actualSkinVertexIds'];bary=line['rootBarycentric'];rad=line['rootRadii'];authored=line['authoredStrandWorld'];
 for tag in ['a','b']:
  build=json.loads((E/(tag+'-build-summary.json')).read_text('utf-8'));p=Path(build['output']);assert a.a.a.sha(p)==build['sha256'];bpy.ops.wm.open_mainfile(filepath=str(p));oldProtected.append(a.a.a.protected());skin=bpy.data.objects['AFN126_COMPLETE_WOMAN_BODY_AND_ARTIST_HEAD'];_,W,T=b.u.b.geom(skin);W=W.copy();T=T.copy();guide=bpy.data.objects['AFN129_EXPLICIT_41_POINT_BOB_GUIDES'];row={'candidate':{'source':str(p),'sha256':build['sha256'],'bytes':p.stat().st_size},'independentlyReopened':True,'actualSkinWorldHash':a.a.a.hasharray(W),'actualSkinTrianglesHash':a.a.a.hasharray(T),'allCurrentSkinFinite':bool(np.isfinite(W).all()),'guideControlVertices':len(guide.data.vertices)}
  hair=bpy.data.objects['AFN129_NATIVE_AUTHORED_VISIBLE_BOB'] if tag=='b' else None
  if hair:
   rest=q.hair(hair).reshape(authored.shape).copy();radii=q.arr(hair.data.attributes['radius'].data,'value',rest.size//3).copy();assert np.isfinite(rest).all();row['actualRestAgainstAuthoredMaxM']=float(np.linalg.norm(rest-authored,axis=2).max());assert row['actualRestAgainstAuthoredMaxM']<5e-6;row['actualHairCurves']=len(hair.data.curves);row['actualHairPoints']=rest.size//3
  # Edit a free main-guide point. Only the existing source is changed in memory.
  vi=20;original=guide.data.vertices[vi].co.copy();guide.data.vertices[vi].co.y-=.001;guide.data.update();guide.update_tag();bpy.context.view_layer.update()
  if hair:
   edited=q.hair(hair).reshape(rest.shape);move=np.linalg.norm(edited-rest,axis=2);row['actualGuideEdit']={'guidePoint':vi,'controlDisplacementM':.001,'actualDisplayedStrandMaximumMoveM':float(move.max()),'actualChangedStoredPointsAbove1um':int(np.count_nonzero(move>1e-6)),'actualRootMaximumMoveM':float(move[:,0].max())};assert move.max()>1e-5 and move[:,0].max()<2e-6
  guide.data.vertices[vi].co=original;guide.data.update();guide.update_tag();bpy.context.view_layer.update()
  if hair:
   restored=q.hair(hair).reshape(rest.shape);assert np.array_equal(restored,rest);row['actualGuideEditRestoredExactly']=True
   # Edit the actual displayed scalp vertex to verify full current-surface root
   # ownership, not a stale hidden source or metadata-only binding.
   si=int(rootTri[0,0]);original=skin.data.vertices[si].co.copy();skin.data.vertices[si].co.z+=.0002;skin.data.update();skin.update_tag();bpy.context.view_layer.update();_,SW,_=b.u.b.geom(skin);SW=SW.copy();expected=np.einsum('ij,ijk->ik',bary,SW[rootTri]);normal=np.cross(SW[rootTri[:,1]]-SW[rootTri[:,0]],SW[rootTri[:,2]]-SW[rootTri[:,0]]);normal/=np.linalg.norm(normal,axis=1)[:,None];expected+=normal*rad[:,None];edited=q.hair(hair).reshape(rest.shape);err=float(np.linalg.norm(edited[:,0]-expected,axis=1).max());rootMove=float(np.linalg.norm(edited[:,0]-rest[:,0],axis=1).max());assert err<5e-6 and rootMove>1e-7;row['actualCurrentScalpEdit']={'actualSkinVertex':si,'controlDisplacementM':.0002,'actualDisplayedRootsMaximumMoveM':rootMove,'allActualRootsAgainstExpectedEditedTriangleFramesMaxM':err,'scope':'Root/frame attachment operation only, not finite full-shaft collision, whole-volume/self/continuous contact or natural dynamics.'};skin.data.vertices[si].co=original;skin.data.update();skin.update_tag();bpy.context.view_layer.update();restored=q.hair(hair).reshape(rest.shape);assert np.array_equal(restored,rest);row['actualScalpAndAllStrandPointsRestoredExactly']=True;assert np.array_equal(q.arr(hair.data.attributes['radius'].data,'value',len(radii)),radii);row['allRadiiPreservedDuringReadback']=True
  row['allReferencedExternalTextures']=[];row['packedOriginalArtistTextures']=[]
  for im in bpy.data.images:
   if im.packed_file:row['packedOriginalArtistTextures'].append({'name':im.name,'bytes':len(im.packed_file.data),'sha256':hashlib.sha256(im.packed_file.data).hexdigest()})
   elif im.source=='FILE' and im.filepath:
    ip=Path(bpy.path.abspath(im.filepath));assert ip.is_file();row['allReferencedExternalTextures'].append({'image':im.name,'relative':im.filepath,'absolute':str(ip),'sha256':a.a.a.sha(ip),'bytes':ip.stat().st_size})
  assert a.a.a.sha(p)==build['sha256'];row.update(completeOperationAccepted=False,naturalHairMotionAccepted=False,finiteSelfContinuousContactAndRuntimeAccepted=False);results[tag]=row
 bpy.ops.wm.open_mainfile(filepath=str(S/'r0126-source/aevrynd-female-next-r0126-b-source-section-neck.blend'));baseline=a.a.a.protected();assert all(v==baseline for v in oldProtected);_,W,T=b.u.b.geom(bpy.data.objects['AFN126_COMPLETE_WOMAN_BODY_AND_ARTIST_HEAD']);assert all(row['actualSkinWorldHash']==a.a.a.hasharray(W) and row['actualSkinTrianglesHash']==a.a.a.hasharray(T) for row in results.values());save('minimum-saved-native-bob-readback.json',{'sources':results,'oldHiddenCompleteRollbackAndOriginalFibresComparedAgainstOriginalR126Exactly':True,'actualVisibleCurrentSkinComparedAgainstOriginalR126Exactly':True,'scope':'Actual saved sources/edit/live guide and displayed scalp-root coupling only. Whole hairstyle appearance rejected. No complete natural-motion/finite/self/continuous-contact/runtime acceptance.','seconds':time.time()-tick});print('R129_TWO_FULL_SOURCES_AND_ACTUAL_GUIDE_SCALP_COUPLING_RECOVERED',time.time()-tick,flush=True)
if __name__=='__main__':main()
