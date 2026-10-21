"""Full native triangle surface crossing test: actual moving eye vs actual skin.
Exact AABB broadphase over all skin faces, float64 SAT including coplanar axes.
No sampled vertex/proxy, no signed-volume/finite-thickness/continuous pass claim.
"""
from pathlib import Path
import bpy,numpy as np,json,time,importlib.util,math
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0138-native-current-gaze';S=R/'engine/assets/characters/female-next/source'
sp=importlib.util.spec_from_file_location('r138contactbase',Path(__file__).with_name('build-female-next-r0138-native-current-gaze.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);b=a.b
EPS=1e-12
def save(n,x):a.save(n,x)
def sat(A,B):
 # Translate common coordinates before projections to avoid large-coordinate
 # cancellation; no epsilon broadphase or changed source geometry.
 origin=A[:,0].copy();A=A-origin[:,None,:];B=B-origin[:,None,:];EA=np.stack([A[:,1]-A[:,0],A[:,2]-A[:,1],A[:,0]-A[:,2]],1);EB=np.stack([B[:,1]-B[:,0],B[:,2]-B[:,1],B[:,0]-B[:,2]],1);NA=np.cross(EA[:,0],EA[:,1]);NB=np.cross(EB[:,0],EB[:,1]);nA=np.linalg.norm(NA,axis=1);nB=np.linalg.norm(NB,axis=1);ua=NA/np.maximum(nA[:,None],1e-30);ub=NB/np.maximum(nB[:,None],1e-30);axes=[ua[:,None,:],ub[:,None,:],np.cross(EA[:,:,None,:],EB[:,None,:,:]).reshape(-1,9,3),np.cross(ua[:,None,:],EA),np.cross(ua[:,None,:],EB),np.cross(ub[:,None,:],EA),np.cross(ub[:,None,:],EB)];axes=np.concatenate(axes,1);length=np.linalg.norm(axes,axis=2);valid=length>1e-20;axes=axes/np.maximum(length[:,:,None],1e-30);pa=np.einsum('nvi,nai->nav',A,axes);pb=np.einsum('nvi,nai->nav',B,axes);gap=np.maximum(pa.min(2)-pb.max(2),pb.min(2)-pa.max(2));separate=((gap>EPS)&valid).any(1);degenerate=(nA==0)|(nB==0);hit=~separate&~degenerate;da=np.einsum('nvi,ni->nv',B,ua);db=np.einsum('nvi,ni->nv',A-B[:,0,None,:],ub);strictA=(da.min(1)<-EPS)&(da.max(1)>EPS);strictB=(db.min(1)<-EPS)&(db.max(1)>EPS);proper=hit&strictA&strictB;coplanar=hit&(abs(da).max(1)<=EPS)&(abs(db).max(1)<=EPS);return hit,proper,coplanar,degenerate
def query(Skin,Eye,skinLow,skinHigh):
 low=Eye.min((0,1));high=Eye.max((0,1));whole=np.flatnonzero(np.all(skinHigh>=low,axis=1)&np.all(skinLow<=high,axis=1));SL=skinLow[whole];SH=skinHigh[whole];skinIds=[];eyeIds=[]
 for i,tri in enumerate(Eye):
  lo=tri.min(0);hi=tri.max(0);ids=whole[np.flatnonzero(np.all(SH>=lo,axis=1)&np.all(SL<=hi,axis=1))];skinIds.extend(ids.tolist());eyeIds.extend([i]*len(ids))
 si=np.array(skinIds,'i4');ei=np.array(eyeIds,'i4');hits=[];proper=[];coplanar=[];degenerate=0
 for start in range(0,len(si),20000):
  part=slice(start,start+20000);h,p,c,d=sat(Skin[si[part]],Eye[ei[part]]);pairs=np.c_[si[part],ei[part]];hits.append(pairs[h]);proper.append(pairs[p]);coplanar.append(pairs[c]);degenerate+=int(d.sum())
 merge=lambda a:np.concatenate(a) if a else np.empty((0,2),'i4');return {'candidatePairs':len(si),'skinFacesInEyeAABBCull':len(whole),'intersections':merge(hits),'properCrossings':merge(proper),'coplanarContacts':merge(coplanar),'degenerateCandidatePairs':degenerate}
def main():
 tick=time.time();construction=json.loads((E/'native-current-gaze-construction.json').read_text('utf-8'));summary=json.loads((E/'a-build-summary.json').read_text('utf-8'));bpy.ops.wm.open_mainfile(filepath=summary['source']);skin=bpy.data.objects['AFN126_COMPLETE_WOMAN_BODY_AND_ARTIST_HEAD'];W,T=a.geometry(skin);Skin=W[T];skinLow=Skin.min(1);skinHigh=Skin.max(1);skinHash=[a.a.hasharray(W),a.a.hasharray(T)];results=[];bad=False;details={}
 def pose(label,frame,angles=None):
  nonlocal bad
  bpy.context.scene.frame_set(frame);bpy.context.view_layer.update();WW,TT=a.geometry(bpy.data.objects['AFN126_COMPLETE_WOMAN_BODY_AND_ARTIST_HEAD']);assert skinHash==[a.a.hasharray(WW),a.a.hasharray(TT)]
  for name in a.MOVING:
   V,F=a.geometry(bpy.data.objects[name]);r=query(Skin,V[F],skinLow,skinHigh);key=label+'-'+name;details[key+'-crossings']=r['properCrossings'];details[key+'-allContacts']=r['intersections'];row={'pose':label,'frame':frame,'object':name,'actualSkinFaces':len(T),'actualEyeFaces':len(F),'actualSkinWorldHash':skinHash[0],'actualEyeWorldHash':a.a.hasharray(V),'aabbCandidatePairs':r['candidatePairs'],'properTriangleSurfaceCrossingPairs':len(r['properCrossings']),'allTriangleSurfaceContactPairs':len(r['intersections']),'coplanarContactPairs':len(r['coplanarContacts']),'degenerateCandidatePairs':r['degenerateCandidatePairs'],'firstProperSkinEyeFacePairs':r['properCrossings'][:20].tolist(),'globalUnsignedTriangleSurfaceMinimumM':0. if len(r['properCrossings']) else None,'globalSignedMinimumM':None,'actualGeometryAllFacesNotVertexSamples':True};results.append(row);bad=bad or len(r['properCrossings'])>0 or r['degenerateCandidatePairs']>0
 bpy.context.scene.frame_set(1);pose('baseline-r126',1);baselineBad=bad;bpy.ops.wm.open_mainfile(filepath=summary['output']);rig=bpy.data.objects[summary['actualRig']];pose('new-r138-neutral',1);newNeutralBad=bad
 # If a proper crossing already exists, this is a related known source/contact
 # failure. Do not hide it behind successful motion or run a broad full audit.
 if not bad:
  for f,y,p in a.KEYS[1:]:
   pose('action-%03d'%f,f)
   if bad:break
 bpy.context.scene.frame_set(1);bpy.context.view_layer.update();np.savez_compressed(E/'actual-ocular-surface-contact-pairs.npz',**details)
 save('actual-ocular-surface-contact.json',{'sourceBaseline':summary['source'],'sourceCandidate':summary['output'],'baselineProperCrossingOrDegeneracyObserved':baselineBad,'candidateNeutralAndRelatedSourceSurfaceFailureObserved':newNeutralBad,'observedRelatedSurfaceFailure':bad,'earlyStopAfterRelatedKnownFailure':bad,'cases':results,'method':'All actual native triangle meshes, exact float64 AABB candidate coverage over all skin faces, separating-axis triangle intersection with explicit coplanar axes and robust strict plane straddling.','numericPredicateEpsilonM':EPS,'epsilonIsNumericalClassificationNotPhysicalClearanceTolerance':True,'triangleSurfaceCrossingIsNotSignedPenetrationDepth':True,'unsignedMinimumZeroOnlyClaimedWhenActualProperCrossingProvesIt':True,'finiteLayerThicknessContainmentAndContinuousContactAccepted':False,'sourceAlphaOrOpticalWetLayerRenderOccupancyNotInferredFromGeometry':True,'noFailingFacesRemovedOrSourceWallsScaledOrMotionShrunk':True,'scope':'Only evaluated eye/reflect-vs-skin triangle surfaces at recorded poses. No whole-avatar/global finite-volume/continuous acceptance. Existing neutral proper crossings remain a related known failure unless independently rebuilt with anatomical basis.','seconds':time.time()-tick});print('R138_ACTUAL_NATIVE_OCULAR_SURFACE_CROSSING_DIAGNOSTIC_DONE',bad,[(x['pose'],x['object'],x['properTriangleSurfaceCrossingPairs']) for x in results],time.time()-tick,flush=True)
if __name__=='__main__':main()
