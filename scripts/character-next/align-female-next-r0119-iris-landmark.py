"""One source-datum correction: helper origin is not the visible native iris plane."""
from pathlib import Path
import bpy,numpy as np,json,time,datetime,importlib.util
R=Path('D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0119-anatomical-eye-rebuild';SRC=S/'r0119-source/aevrynd-female-next-r0119-a-anatomical-eye-assembly.blend';OUT=S/'r0119-source/aevrynd-female-next-r0119-b-native-iris-landmark-eyes.blend'
sp=importlib.util.spec_from_file_location('r119align',Path(__file__).with_name('build-female-next-r0119-anatomical-eyes.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);b=a.b;q=a.q;b.u.v.E=E
def main():
 tick=time.time();assert not OUT.exists();uv=[];vu={}
 for l in (R/'Reference/character/makehuman-core-cc0/system-eyes/high-poly.obj').read_text('utf-8').splitlines():
  p=l.split()
  if not p:continue
  if p[0]=='vt':uv.append(list(map(float,p[1:3])))
  elif p[0]=='f':
   for t in p[1:]:v,u=t.split('/')[:2];vu[int(v)-1]=int(u)-1
 UV=np.array(uv);W=np.load(E.parent/'r0116-native-compatible-eyes/native-eye-source-lineage.npz')['actualWorld'];reference=json.loads((E.parent/'r0116-native-compatible-eyes/native-eye-source-authoring.json').read_text('utf-8'));digest=a.a.sha(SRC);bpy.ops.wm.open_mainfile(filepath=str(SRC));b.deliver(0);before=a.a.protected();rows=[]
 for part in reference['actualSourceParts']:
  if 'SCLERA' not in part['role']:continue
  side=part['side'];ids=np.array(part['sourceVertexIDs']);u=UV[[vu[int(i)] for i in ids]];centre=np.array([.2842,.2451]) if side=='L' else np.array([.7041,.7031]);rho=np.linalg.norm(u-centre,axis=1);chosen=ids[(rho>.095)&(rho<.135)];assert len(chosen)>=16;plane=float(np.median(W[chosen,1]));root=bpy.data.objects['AFN119_'+side+'_EYE_GAZE_CONTROL'];old=np.array(root.location);target=old.copy();target[1]=plane+a.APEX-a.IRIS_DEPTH;root.location=target;root.update_tag();rows.append({'side':side,'actualOriginalNativeOpaqueSourceVertexIDs':chosen,'actualNativePointsWorld':W[chosen],'sourceTextureRingUVRadiusBand':[.095,.135],'sourcePlaneMethod':'Median Y of actual native eye vertices at original source iris/limbus texture ring; original X/Z and neutral gaze retained. This source landmark is not histology/physical contact qualification.','nativeIrisPlaneY':plane,'oldHelperOrigin':old,'newSourceLandmarkOrigin':target,'actualCorrectionM':float(target[1]-old[1])})
 bpy.context.view_layer.update();assert a.a.protected()==before;arrays={}
 for ob in bpy.data.objects:
  if ob.name.startswith('AFN119_') and ob.type=='MESH':d,P,T=b.u.b.geom(ob);arrays[ob.name+'_world']=P.copy();arrays[ob.name+'_triangles']=T.copy()
 np.savez_compressed(E/'b-anatomical-eye-assembly-lineage.npz',**arrays);a.save('b-build-summary.json',{'source':str(SRC),'output':str(OUT),'sourceSha256':digest,'sourceDatumCorrection':rows,'allOriginalExternalGeometryAndParametersUnchangedExceptDataDerivedAssemblyYPlacement':True,'allProtectedBodyKeysHairBrowsLashesBefore':before,'allProtectedBodyKeysHairBrowsLashesAfter':a.a.protected(),'allProtectedGeometryAndRadiiByteExact':True,'parametersReusedWithoutSweep':'anatomical-reference-and-parameters.json','firstCompleteARejectedTooDeepAndDark':True,'oneDatumCorrectionNoFurtherPositionVariantsAllowed':True,'actualCandidateCountInRound':2,'notNewRoundOrTimeReset':True,'secondsBeforePreview':time.time()-tick});bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=False);assert a.a.sha(SRC)==digest;views=[]
 for view in ['face','body-face','oblique','profile','back']:views.append(b.u.v.image('b-native-iris-landmark-eyes',view));a.save('b-view-controls.json',views)
 for label,value in [('half',.5),('closed',1.),('restored',0.)]:b.deliver(value);views.append(b.u.v.image('b-native-iris-landmark-eyes-'+label,'face'));a.save('b-view-controls.json',views)
 print('R119_NATIVE_IRIS_LANDMARK_COMPLETE_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
