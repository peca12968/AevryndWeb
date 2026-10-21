"""Independent minimum readback of the complete stitched character, not global proof."""
from pathlib import Path
import bpy,numpy as np,json,time,hashlib,importlib.util
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0112-topological-ocular-graft';S=R/'engine/assets/characters/female-next/source'
def mod(n,p):
 sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(p));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
b=mod('r112saved','build-female-next-r0112-topological-character.py');v=mod('r112hash','verify-female-next-r0105-saved-chart.py');q=b.q
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def graph(d):return v.hasharray(np.r_[q.arr(d.polygons,'loop_total',len(d.polygons),dtype='i4'),q.arr(d.loops,'vertex_index',len(d.loops),dtype='i4')])
def sample(ob):
 d,W,T=b.u.b.geom(ob);W=W.copy();T=T.copy();loops=q.arr(d.loop_triangles,'loops',len(T),3,dtype='i4');select=np.max(W[T][:,:,2],axis=1)<1.30
 return {'trianglesAllBelowWorldZ1p30':int(select.sum()),'worldTrianglePointsHash':v.hasharray(W[T[select]]),'cornerUVHashes':{x.name:v.hasharray(q.arr(x.data,'uv',len(d.loops),2)[loops[select]]) for x in d.uv_layers}}
def main():
 tick=time.time();src=S/'aevrynd-female-next-r0107-b-native-pinned-lids.blend';out=S/'aevrynd-female-next-r0112-a-sewn-topological-ocular.blend';digest=sha(out)
 bpy.ops.wm.open_mainfile(filepath=str(src));old=bpy.data.objects['AFN104_COMPLETE_WOMAN_WITH_NATIVE_ANIMATION_HEAD'];body0=sample(old);mat=v.material(old.data.materials[4]);hair0=q.hair(bpy.data.objects['AFN97_TUCKED_ARTIST_BOB_CHILDREN']).copy();source={'source':str(src),'sourceSha256':sha(src),'sourceBytes':src.stat().st_size}
 bpy.ops.wm.open_mainfile(filepath=str(out));skin=bpy.data.objects['AFN112_COMPLETE_WOMAN_SEWN_OCULAR_SKIN'];d,W,T=b.u.b.geom(skin);W=W.copy();T=T.copy();G=graph(d);skinStats={'vertices':len(W),'triangles':len(T)};body1=sample(skin);cor=np.load(E/'complete-skin-source-correspondence.npz');art=np.load(E/'stitched-ocular-authoring.npz');ids=cor['finiteSourceToBody'];actual=np.max(np.linalg.norm(W[ids]-art['finiteNeutralWorld'],axis=1));states=[]
 for label,value in [('neutral',0),('half',.5),('closed',1),('restored',0)]:
  b.deliver(value);dd,P,PT=b.u.b.geom(skin);P=P.copy();assert np.isfinite(P).all();states.append({'state':label,'assignedBlink':value,'maximumActualSkinMoveM':float(np.linalg.norm(P-W,axis=1).max()),'evaluatedPolygonLoopGraphEqualsNeutral':graph(dd)==G,'actualKeys':{k.name:k.value for k in skin.data.shape_keys.key_blocks if k.name!='Basis'}})
 assert states[-1]['maximumActualSkinMoveM']==0
 hg=q.hair(bpy.data.objects['AFN97_TUCKED_ARTIST_BOB_CHILDREN']);groomError=float(np.linalg.norm(hg-hair0,axis=1).max());assert groomError==0
 textures=[]
 for im in bpy.data.images:
  if im.source=='FILE' and not im.packed_file and im.filepath:
   path=Path(bpy.path.abspath(im.filepath));assert path.is_file(),str(path);textures.append({'name':im.name,'relative':im.filepath,'absolute':str(path),'sha256':sha(path),'bytes':path.stat().st_size})
 lookup={tuple(sorted(map(int,t))):t for t in T};bindings=json.loads((E/'a-mobile-lash-bindings.json').read_text('utf8'));frames={'allCurves':len(bindings),'consistentWithActualTriangleWinding':0,'reversed':0,'notActualTriangle':0}
 for row in bindings:
  tri=np.array(row['actualNewUnifiedSkinTriangle']);stored=lookup.get(tuple(sorted(map(int,tri))))
  if stored is None:frames['notActualTriangle']+=1;continue
  a=np.cross(W[tri[1]]-W[tri[0]],W[tri[2]]-W[tri[0]]);z=np.cross(W[stored[1]]-W[stored[0]],W[stored[2]]-W[stored[0]]);frames['reversed' if np.dot(a,z)<0 else 'consistentWithActualTriangleWinding']+=1
 assert frames['allCurves']==412
 hidden=bpy.data.objects['AFN112_PREVIOUS_COMPLETE_SKIN_REFERENCE'].hide_render and all(bpy.data.objects['AFN104_NATIVE_'+s+'_'+p].hide_render for s in ['L','R'] for p in ['SCLERA','IRIS']);assert hidden
 unchanged=sha(out)==digest;assert unchanged
 result={'status':'INDEPENDENT_COMPLETE_SOURCE_REOPEN_AND_ACTUAL_OPERATION_READBACK_NOT_APPEARANCE_OR_CONTACT_APPROVAL','baseline':source,'candidate':{'source':str(out),'sourceSha256':digest,'sourceBytes':out.stat().st_size,'actualSkin':skinStats,'externalTextures':textures},'states':states,'actualNewNeutralSourceMaxMatchingErrorM':float(actual),'originalBodyAllTrianglePointsAndUVBelowZ1p30ExactInRecordedOrder':body0==body1,'lowerBodyBaseline':body0,'lowerBodyCandidate':body1,'originalSkinShaderGraphExact':v.material(skin.data.materials[4])==mat,'restoredGroomMaximumWorldErrorM':groomError,'all412LashFrames':frames,'oldFullSkinAndOpticsRetainedHidden':hidden,'sourceUnchangedDuringVerification':unchanged,'contact':{'status':'UNACCEPTED_SHORT_RETURN_ATTACHMENT_INTERNAL_OPEN_BOUNDARIES_SELF_CONTACT_AND_OPTICS_REQUIRE_PROOF','globalSignedMinimumM':None,'oldContactWitnessCountsNotTransferredToNewGeometry':True,'sampledStaticNotContinuousOrGlobal':True,'fullFiniteSelfHairClothContinuousNaturalMotionCertified':False},'wholeBodyRigGuideEditingAndCompleteBlinkUnaccepted':True,'runtimeAccepted':False,'seconds':time.time()-tick}
 (E/'minimum-saved-seam-readback.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print('R112_COMPLETE_SEWN_SOURCE_READBACK_DONE',frames,time.time()-tick,flush=True)
if __name__=='__main__':main()
