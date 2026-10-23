"""Direct sculpt strokes on the verified actual191 control-volume geometry.
No new whole-head groom formula, density/radius/material change or cover.
"""
from pathlib import Path
import bpy,numpy as np,json,datetime,time,hashlib,importlib.util
from mathutils import Matrix
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');E=C/'evidence/character-female-next/r0192-sculpted-growth-volume';OUT=C/'assets-source/aevrynd-character/female-next/r0192-source/aevrynd-female-next-r0192-coarse-sculpted-growth-volume.blend'
sp=importlib.util.spec_from_file_location('r192base',C/'scripts/character-next/build-female-next-r0169-coherent-native-carrier.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a;h=m.h
def save(n,x):(E/n).write_bytes((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
def sha(p):return hashlib.file_digest(open(p,'rb'),'sha256').hexdigest()
def ah(x):return hashlib.sha256(np.asarray(x,'f4').tobytes()).hexdigest()
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def strokes():
 result=[]
 for side in [-1,1]:
  result.extend([
   {'name':f'{side}_CROWN_ARCH','centre':[side*.038,-.027,1.550],'radii':[.042,.078,.027],'delta':[side*.004,0,.014]},
   {'name':f'{side}_TEMPORAL_FORWARD_WAVE','centre':[side*.084,-.057,1.486],'radii':[.030,.047,.034],'delta':[side*.010,-.012,.002]},
   {'name':f'{side}_EAR_TO_REAR_TURN','centre':[side*.085,.003,1.455],'radii':[.027,.040,.035],'delta':[side*.009,.011,.002]},
   {'name':f'{side}_MID_LENGTH_OUTWARD_ROLL','centre':[side*.092,-.030,1.414],'radii':[.033,.064,.027],'delta':[side*.017,.009,-.003]},
   {'name':f'{side}_INWARD_TIP','centre':[side*.096,-.025,1.348],'radii':[.034,.069,.025],'delta':[-side*.017,.006,.004 if side<0 else .008]},
   {'name':f'{side}_REAR_LAYER_DEPTH','centre':[side*.049,.085,1.430],'radii':[.050,.034,.060],'delta':[side*.003,.014,0]},
   {'name':f'{side}_NAPE_TIP_TURN','centre':[side*.032,.095,1.348],'radii':[.039,.035,.024],'delta':[side*.003,-.009,.008 if side<0 else .003]}
  ])
 return result
def sculpt(points,nv,K):
 layer=(np.arange(len(points))//nv)%K;rootProtection=np.minimum(layer/5.,1.)**2;delta=np.zeros_like(points,dtype='f8')
 for stroke in strokes():
  d=(points-np.array(stroke['centre']))/np.array(stroke['radii']);w=np.exp(-2*np.sum(d*d,axis=1))*rootProtection;delta+=w[:,None]*np.array(stroke['delta'])
 return (points+delta).astype('f4'),delta
def main():
 tick=time.time();t=json.loads((E/'before.json').read_text());assert not OUT.exists() and sha(t['source'])==t['sourceSha256'];bpy.ops.wm.open_mainfile(filepath=t['source']);s=bpy.context.scene;s.frame_set(1);s.camera.data.type='PERSP';hair=bpy.data.objects['AFN191_ACTUAL_NATIVE_VOLUME_DRIVEN_GROWTH'];cage=bpy.data.objects['AFN191_ACTUAL_EDITABLE_GROWTH_VOLUME'];skin=bpy.data.objects['AFN126_COMPLETE_WOMAN_BODY_AND_ARTIST_HEAD'];oldHair=bpy.data.objects['AFN126_ORIGINAL_Hair_Hair_0'];protected={n:a.rawsig(bpy.data.objects[n]) for n in a.FIXED+a.MOVING};before,off=m.curveworld(hair);CV=h.arr(cage.data.vertices,'co',len(cage.data.vertices),3);line=np.load(E.parent/'r0191-native-growth-volume/native-growth-volume-lineage.npz');K=int(line['layerCount']);nv=int(line['cageVertexCountPerLayer']);N=len(off)
 # Actual same-woman artist geometry is a spatial silhouette reference only.
 RV,RT=a.geometry(oldHair);envelope=[]
 for z in [1.56,1.51,1.46,1.41,1.36]:
  p=RV[np.abs(RV[:,2]-z)<.012]
  if len(p):envelope.append({'zBandCentre':z,'verticesInBand':len(p),'worldMin':p.min(0).tolist(),'worldMax':p.max(0).tolist()})
 changed,delta=sculpt(CV,nv,K);cage.data.vertices.foreach_set('co',changed.ravel());cage.data.update();cage.update_tag();hair.update_tag();bpy.context.view_layer.update();actual,ao=m.curveworld(hair);rootError=float(np.linalg.norm(actual[off]-before[off],axis=1).max());movement=np.linalg.norm(actual-before,axis=1);assert rootError<3e-6 and np.array_equal(off,ao) and movement.max()>.005;assert protected=={n:a.rawsig(bpy.data.objects[n]) for n in protected};cage['Aevrynd_sculpt_revision']='r0192 direct current-world anatomical strokes'
 proof={'UTC':stamp(),'actualHair':hair.name,'actualCage':cage.name,'actualSkin':skin.name,'inputCageSHA256':ah(CV),'sculptedCageSHA256':ah(changed),'inputDisplayedGeometrySHA256':ah(before),'sculptedDisplayedGeometrySHA256':ah(actual),'cageVertices':len(CV),'nativeCurves':N,'pointsPerCurve':K,'controlTopologyUVAndNativeDriverUnchanged':True,'allOriginalRootIDsRetained':True,'rootCentreMovementMaximumM':rootError,'displayedGeometryMovementM':{'median':float(np.median(movement)),'p90':float(np.quantile(movement,.9)),'max':float(movement.max())},'actualControlVertexDisplacementMaximumM':float(np.linalg.norm(delta,axis=1).max()),'referenceArtistHair':oldHair.name,'referenceOnlyArtist3DSilhouetteBands':envelope,'noReferenceFollicleUVOrFlowInferenceOrMeshImport':True,'nativeRadiusMaterialCountUnchangedFrom191':True,'actualSculptStrokes':strokes(),'rootLayerProtection':'Actual control-volume layer0 unchanged; smooth first5-layer sculpt falloff. All other full-length regions remain editable.','noBlanketNormalProjectionOrContactPassClaim':True,'protectedRawMeshUVSignatures':protected,'secondsBeforePreview':time.time()-tick}
 save('coarse-sculpt-summary.json',proof);save('sculpt-strokes.json',strokes());captures=[]
 def capture(scene):
  captures.append({'UTC':stamp(),'loadedSourceAtCapture':bpy.data.filepath,'plannedSavedCandidate':str(OUT),'output':scene.render.filepath,'frame':scene.frame_current,'camera':scene.camera.name,'cameraMatrixWorld':[list(x) for x in scene.camera.matrix_world],'lens':scene.camera.data.lens,'cameraType':scene.camera.data.type,'viewTransform':scene.view_settings.view_transform,'look':scene.view_settings.look,'exposure':scene.view_settings.exposure,'resolution':[scene.render.resolution_x,scene.render.resolution_y,scene.render.resolution_percentage],'cyclesSamples':scene.cycles.samples,'cyclesSeed':scene.cycles.seed,'actualHair':hair.name,'sculptedCageSHA256':proof['sculptedCageSHA256'],'viewportEvaluatedGeometryPreviouslyCheckedNotRenderDepsgraphProof':True});save('actual-render-pre-capture-states.json',captures)
 bpy.app.handlers.render_pre.append(capture);a.b.u.v.E=E
 for view in ['face','body-face','oblique','profile','back']:s.camera.data.type='PERSP';a.b.u.v.image('coarse-sculpted-growth-volume',view)
 bpy.app.handlers.render_pre.remove(capture);s.camera.matrix_world=Matrix(captures[0]['cameraMatrixWorld']);s.camera.data.lens=captures[0]['lens'];s.camera.data.type=captures[0]['cameraType'];OUT.parent.mkdir(parents=True,exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True);save('a-build-summary.json',{'UTC':stamp(),'output':str(OUT),'sha256':sha(OUT),'bytes':OUT.stat().st_size,'actualHair':hair.name,'actualCage':cage.name,'coarseOnly':True,'completeFineCandidates':0,'oneSculptedStateOneMethod':True,'elapsedJobSeconds':time.time()-tick,'appearanceCompleteOperationContactRuntimeUnaccepted':True});print('R192_ONE_COMPLETE_DIRECT_SCULPTED_VOLUME_SAVED',flush=True)
if __name__=='__main__':main()
