"""Minimum independent reopen and causal failure readback, not a broad audit."""
from pathlib import Path
import bpy,numpy as np,json,time,importlib.util
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0106-native-head-operation';S=R/'engine/assets/characters/female-next/source'
def mod(name,file):
 sp=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);return a
v=mod('r106readback','verify-female-next-r0105-saved-chart.py');b=mod('r106controls','build-female-next-r0106-native-lid-operation.py');q=v.q
def main():
 tick=time.time();baseline=v.snapshot(S/'aevrynd-female-next-r0105-a-native-lip-chart.blend');candidate=v.snapshot(S/'aevrynd-female-next-r0106-a-native-lid-operation.blend');keys=['vertices','triangles','worldVertexSha256','triangleSha256','materialIndexSha256','canonicalUVSha256','skinMaterialGraphSha256','groomWorldSha256','optics','externalTextures'];assert all(baseline[k]==candidate[k] for k in keys);skin=bpy.data.objects['AFN104_COMPLETE_WOMAN_WITH_NATIVE_ANIMATION_HEAD'];_,W,T=v.u.b.geom(skin);W=W.copy();T=T.copy();raw=skin.data;basis=q.arr(raw.shape_keys.key_blocks['Basis'].data,'co',len(raw.vertices),3);sourceKeys={}
 for side in ['L','R']:
  K=q.arr(raw.shape_keys.key_blocks['AFN106_NATIVE_BLINK_'+side].data,'co',len(raw.vertices),3);delta=np.linalg.norm(K-basis,axis=1);sourceKeys[side]={'movedSourceVertices':int(np.count_nonzero(delta>1e-8)),'maximumLocalDeltaM':float(delta.max())}
 motion=[]
 for value in [0,.5,1,0]:
  b.deliver(value);_,P,TT=v.u.b.geom(skin);motion.append({'assignedBlink':value,'evaluatedKeys':[skin.data.shape_keys.key_blocks['AFN106_NATIVE_BLINK_'+s].value for s in ['L','R']],'actualDisplayedMaximumWorldMoveM':float(np.linalg.norm(P-W,axis=1).max()),'actualTopologyRetained':bool(np.array_equal(T,TT))})
 assert all(row['actualDisplayedMaximumWorldMoveM']==0 for row in motion),'Failure premise changed; inspect new evidence'
 # Check every retained lash frame against actual source surface orientation.
 lookup={tuple(sorted(map(int,tri))):tri for tri in T};helper=bpy.data.objects['AFN59_LASHES_NATIVE_POINT_POSES'];rows=json.loads((E/'a-lash-native-margin-bindings.json').read_text());frameCounts={'allCurves':len(rows),'consistentWithSkinWinding':0,'reversedRelativeToSkinWinding':0,'notActualSkinTriangle':0};reversedIDs=[]
 for index,row in enumerate(rows):
  ids=np.array(row['actualSkinTriangle'],dtype=int);original=lookup.get(tuple(sorted(map(int,ids))))
  if original is None:frameCounts['notActualSkinTriangle']+=1;continue
  a=np.cross(W[ids[1]]-W[ids[0]],W[ids[2]]-W[ids[0]]);n=np.cross(W[original[1]]-W[original[0]],W[original[2]]-W[original[0]])
  if np.dot(a,n)<0:frameCounts['reversedRelativeToSkinWinding']+=1;reversedIDs.append(index)
  else:frameCounts['consistentWithSkinWinding']+=1
 row={'status':'REOPENED_REJECTED_OPERATION_KEY_INPUT_SUPPRESSED_AND_RAW_LID_SHAPE_FAILS','baseline':baseline,'candidate':candidate,'exactNeutralUnchangedFields':keys,'sourceNativeKeysActuallyContainDeltas':sourceKeys,'actualBlinkReadback':motion,'lashActualMarginFrameOrientation':frameCounts,'reversedLashCurveIDs':reversedIDs,'frameOrientationNotQualifiedDespiteActualMarginEdges':True,'rawPoseEvidence':'modifier-order-causal-test.json','rawPoseVisibleOutcome':'Unsaved bound-modifier-off test moves actual skin, but closed lids form severe segmented/folded pale blocks; art rejected. No corrective weight/radius/geodesic sweep.','contact':{'status':'UNACCEPTED_INHERITED_NEUTRAL_OPTICAL_FAILURE_AND_UNQUALIFIED_LASH_FRAMES','baselineEvidence':str(E.parent/'r0104-native-artist-ocular-foundation/minimum-saved-readback.json'),'neutralOpticalGeometryByteIdentical':True,'priorCandidatePairsL':284,'priorCandidatePairsR':311,'priorStoredIntersectionOrTouchWitnessesPerSide':16,'countsNotGlobalTotals':True,'globalSignedMinimumM':None,'finiteSelfHairClothContinuousCertified':False},'completeCapabilityOrAppearanceAccepted':False,'runtimeAccepted':False,'seconds':time.time()-tick};(E/'independent-saved-operation-failure.json').write_text(json.dumps(row,indent=2)+'\n',encoding='utf8',newline='\n');print('R106_SAVED_OPERATION_FAILURE_VERIFIED',frameCounts,time.time()-tick,flush=True)
if __name__=='__main__':main()
