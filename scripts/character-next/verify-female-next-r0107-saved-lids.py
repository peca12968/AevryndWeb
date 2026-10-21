"""Independent scoped readback: actual visible response, graph and aperture rays."""
from pathlib import Path
import bpy,numpy as np,json,time,importlib.util
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0107-native-coarse-lid-cage';S=R/'engine/assets/characters/female-next/source'
def mod(name,file):
 sp=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
v=mod('r107verify','verify-female-next-r0105-saved-chart.py');b=mod('r107deliver','build-female-next-r0107-pinned-character.py');q=v.q
def graph(d):return v.hasharray(np.r_[q.arr(d.polygons,'loop_total',len(d.polygons),dtype='i4'),q.arr(d.loops,'vertex_index',len(d.loops),dtype='i4')])
def main():
 tick=time.time();baseline=v.snapshot(S/'aevrynd-female-next-r0105-a-native-lip-chart.blend');a=v.snapshot(S/'aevrynd-female-next-r0107-a-native-coarse-lids.blend');c=v.snapshot(S/'aevrynd-female-next-r0107-b-native-pinned-lids.blend');keys=['vertices','triangles','worldVertexSha256','triangleSha256','materialIndexSha256','canonicalUVSha256','skinMaterialGraphSha256','groomWorldSha256','optics','externalTextures'];assert all(baseline[k]==a[k]==c[k] for k in keys);skin=bpy.data.objects['AFN104_COMPLETE_WOMAN_WITH_NATIVE_ANIMATION_HEAD'];d,W,T=v.u.b.geom(skin);W=W.copy();T=T.copy();G=graph(d);neutral=W.copy();originalHair=q.hair(bpy.data.objects['AFN97_TUCKED_ARTIST_BOB_CHILDREN']).copy();camera=np.array(bpy.context.scene.camera.matrix_world)[:3,3];targets={}
 for side in ['L','R']:
  dd,P,TT=v.u.b.geom(bpy.data.objects['AFN104_NATIVE_'+side+'_SCLERA']);P=P.copy();targets[side]=P[P[:,1]<(P[:,1].min()+P[:,1].max())/2]
 states=[]
 for label,value in [('neutral',0),('half',.5),('closed',1),('restored',0)]:
  b.deliver(value);d,V,TT=v.u.b.geom(skin);V=V.copy();TT=TT.copy();zmin=min(camera[2],min(x[:,2].min() for x in targets.values()));selected=np.flatnonzero(V[TT,2].max(1)>=zmin-1e-5);used,inverse=np.unique(TT[selected],return_inverse=True);tree=BVHTree.FromPolygons(V[used].tolist(),inverse.reshape(-1,3).tolist(),all_triangles=True);rays={}
  for side,P in targets.items():
   clear=[]
   for i,target in enumerate(P):
    vector=target-camera;distance=float(np.linalg.norm(vector));hit,no,fi,length=tree.ray_cast(Vector(camera),Vector(vector/distance),distance-1e-7)
    if hit is None:clear.append(i)
   rays[side]={'frontHalfOpticalVertexSamples':len(P),'withoutInterveningSkin':len(clear),'unblockedSampleIDs':clear,'sampleDefinition':'Every actual sclera vertex in its negative-world-Y half. Geometric camera-to-optical-vertex rays only; not global aperture, rendered refraction/occupancy or continuous proof.'}
  states.append({'state':label,'assignedBlink':value,'evaluatedKeys':{k.name:k.value for k in skin.data.shape_keys.key_blocks if k.name!='Basis'},'maximumDisplayedSkinMoveM':float(np.linalg.norm(V-neutral,axis=1).max()),'evaluatedPolygonLoopGraphEqualsNeutral':graph(d)==G,'evaluatedLoopTriangleArrayEqualsNeutral':bool(np.array_equal(TT,T)),'apertureRaySamples':rays});(E/'saved-pose-readback.json').write_text(json.dumps(states,indent=2)+'\n',encoding='utf8',newline='\n')
 assert states[-1]['maximumDisplayedSkinMoveM']==0 and all(x['evaluatedPolygonLoopGraphEqualsNeutral'] for x in states);restoreHair=float(np.linalg.norm(q.hair(bpy.data.objects['AFN97_TUCKED_ARTIST_BOB_CHILDREN'])-originalHair,axis=1).max());assert restoreHair==0;lookup={tuple(sorted(map(int,tri))):tri for tri in T};bindings=json.loads((E/'b-native-seam-lash-bindings.json').read_text('utf8'));frames={'allCurves':len(bindings),'consistentWithActualSkinWinding':0,'reversed':0,'notActualSkinTriangle':0}
 for row in bindings:
  ids=np.array(row['actualSkinTriangle']);original=lookup.get(tuple(sorted(map(int,ids))))
  if original is None:frames['notActualSkinTriangle']+=1;continue
  n=np.cross(W[ids[1]]-W[ids[0]],W[ids[2]]-W[ids[0]]);other=np.cross(W[original[1]]-W[original[0]],W[original[2]]-W[original[0]])
  frames['reversed' if np.dot(n,other)<0 else 'consistentWithActualSkinWinding']+=1
 assert frames['allCurves']==412 and frames['reversed']==0 and frames['notActualSkinTriangle']==0
 result={'status':'REOPENED_NEUTRAL_ART_PRESERVED_PARTIAL_LID_MOTION_DELIVERED_FULL_BLINK_UNACCEPTED','baseline':baseline,'a':a,'b':c,'exactNeutralUnchangedFields':keys,'states':states,'restoredGroomMaximumWorldErrorM':restoreHair,'lashFrames':frames,'nativeUVSeamNotProvenVisibleAnatomicalMargin':True,'triangleComparatorInterpretation':'A preview field actualTopologyUnchanged compares evaluated loop-triangle arrays only. These may differ through tessellation; unchanged polygon-loop graph is separately verified here. Actual current triangle arrays must be used per pose for any triangle query.','contact':{'status':'UNACCEPTED_INHERITED_NEUTRAL_OPTICAL_WITNESSES','evidence':str(E.parent/'r0104-native-artist-ocular-foundation/minimum-saved-readback.json'),'neutralActualSkinAndOpticsByteEqualToR105':True,'priorCandidatePairsL':284,'priorCandidatePairsR':311,'priorStoredIntersectionOrTouchWitnessesPerSide':16,'countsNotGlobalTotals':True,'globalSignedMinimumM':None,'finiteSelfHairClothContinuousOrNaturalMotionCertified':False},'runtimeAccepted':False,'completeCapabilityOrAppearanceAccepted':False,'seconds':time.time()-tick};(E/'independent-saved-lid-readback.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8',newline='\n');print('R107_SAVED_NATIVE_LIDS_READBACK_DONE',frames,time.time()-tick,flush=True)
if __name__=='__main__':main()
