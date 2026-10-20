"""Exact installed-version particle diameter -> native curve radius correction.
One source-backed dimensional repair, no radius/roughness/density sweep.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0094-authored-growth-routing';S=R/'engine/assets/characters/female-next/source';SRC=S/'aevrynd-female-next-r0094-a-semantic-growth-free-volume.blend';OUT=S/'aevrynd-female-next-r0094-b-source-width-growth-volume.blend'
sp=importlib.util.spec_from_file_location('r94widthviews',Path(__file__).with_name('render-female-next-r0091-matched.py'));v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v);v.E=E;m=v.m;q=m.q
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda a:a.item() if isinstance(a,np.generic) else a.tolist())+'\n',encoding='utf8')
def main():
 tick=time.time();assert not OUT.exists();proof=json.loads((E/'radius-semantics-proof.json').read_text('utf8'));a=json.loads((E/'a-build-summary.json').read_text('utf8'));assert sha(SRC)==a['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();o=bpy.data.objects['AFN94_SEMANTIC_GROWTH_RENDER_FIBRES'];z=np.load(E/'a-growth-volume-lineage.npz');P=q.hair(o).reshape(-1,33,3);A=np.array(o.matrix_world);scale=np.linalg.norm(A[:3,0]);radiusNative=proof['sourceCyclesRootRadiusNativeM'];radiusWorld=radiusNative*scale;oldRadius=z['worldRadius'].astype('f8');delta=-z['rootNormals']*(oldRadius[:,0]-radiusWorld)[:,None]
 for i,row in enumerate(P):
  arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(row,axis=0),axis=1))];t=np.minimum(arc/a['rootJunctionTransitionWorldM'],1);blend=1-t*t*(3-2*t);P[i]+=delta[i]*blend[:,None]
 d=o.data.copy();d.name='AFN94_CORRECT_SOURCE_WIDTH';d.position_data.foreach_set('vector',((P.reshape(-1,3)-A[:3,3])@np.linalg.inv(A[:3,:3]).T).astype('f4').ravel());rad=np.full(P.shape[:2],radiusNative,'f4')
 # Source root and tip diameters equal; retain that profile, closing ONLY
 # the last point when the source-author flag does so in pinned Cycles.
 assert abs(proof['sourceRootDiameterNativeM']-proof['sourceTipDiameterNativeM'])<1e-12
 if proof['sourceCloseTip']:rad[:,-1]=0
 d.attributes['radius'].data.foreach_set('value',rad.ravel());o.data=d;o.name='AFN94_SOURCE_WIDTH_RENDER_FIBRES';o['scope']='Source-author semantic scalp domain/free-volume candidate with verified source Cycles diameter-to-radius correction and source close-tip policy. All28002 strands/centrelines retained, root surface-exit offset recomputed to corrected radius. Not biological width calibration, exact full source render/parent policy, finite shaft/self/CCD/natural dynamics or runtime proof.';bpy.context.view_layer.update();actual=q.hair(o).reshape(P.shape);err=float(np.linalg.norm(actual-P,axis=2).max());assert err<2e-6;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True);np.savez_compressed(E/'b-source-width-lineage.npz',actualWorld=P.astype('f4'),radiusNative=rad,objectMatrix=A,rootWidthExitDelta=delta,roots=P[:,0].copy());save('b-build-summary.json',{'source':str(SRC),'sourceSha256':sha(SRC),'output':str(OUT),'outputSha256':sha(OUT),'outputBytes':OUT.stat().st_size,'curveObject':o.name,'curves':len(P),'pointsEach':33,'all28002SourceStrandsRetained':True,'sourceVersionRadiusSemanticsVerified':True,'originalSourceRadiusNativeM':radiusNative,'correctedWorldRootRadiusM':radiusWorld,'previousWorldRootRadiusM':float(oldRadius[0,0]),'sourceCloseTip':proof['sourceCloseTip'],'sourceShape':proof['sourceShape'],'rootExitOffsetUpdatedWithoutChangingGrowthDomain':True,'materialLightingExposureAndAllOtherBodyFeaturesUnchanged':True,'maximumSavedWorldErrorM':err,'sourceInterpolationParentRenderPolicyOrBiologicalCalibrationNotCertified':True,'noContactNaturalMotionRuntimeOrCompleteGainAccepted':True,'secondsBeforePreview':time.time()-tick});rows=[]
 for view in ['face','back','body-face']:rows.append(v.image('b-source-width',view));save('b-view-controls.json',rows)
 print('R94_SOURCE_WIDTH_COMPLETE_PREVIEW',time.time()-tick,flush=True)
if __name__=='__main__':main()
