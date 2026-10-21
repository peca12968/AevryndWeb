"""Relevant attachment seam checks and matched alternate-light/context poses."""
from pathlib import Path
import bpy,numpy as np,json,time,math,importlib.util
from mathutils import Matrix,Vector
sp=importlib.util.spec_from_file_location('r139finishverify',Path(__file__).with_name('verify-female-next-r0139-minimum.py'));v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v);h=v.h;a=h.a;E=h.E
def light():
 controls=json.loads((E.parent/'r0116-native-compatible-eyes/a-view-controls.json').read_text('utf-8'))[0];expected=json.loads((E.parent/'r0116-native-compatible-eyes/matched-second-light-controls.json').read_text('utf-8'))[0];s=bpy.context.scene;a.b.u.v.image.__globals__['m'].rig.shade.settings();s.camera.matrix_world=Matrix(controls['camera']);s.camera.data.lens=controls['lensMM'];s.render.resolution_x=s.render.resolution_y=640;s.render.resolution_percentage=100;s.cycles.samples=16;s.cycles.seed=controls['seed'];s.render.hair_subdiv=3;s.view_settings.exposure=controls['exposure'];s.view_settings.look=controls['look'];target=Vector((0,-.04,1.43))
 for name,row in controls['lights'].items():
  ob=bpy.data.objects[name];ob.matrix_world=Matrix(row['matrix']);ob.location.x=-ob.location.x;ob.rotation_euler=(target-ob.location).to_track_quat('-Z','Y').to_euler();ob.data.energy=row['energy'];ob.data.color=row['color']
 bpy.context.view_layer.update();row={'camera':np.array(s.camera.matrix_world).tolist(),'lensMM':s.camera.data.lens,'lights':{o.name:{'matrix':np.array(o.matrix_world).tolist(),'energy':o.data.energy,'color':list(o.data.color)} for o in s.objects if o.type=='LIGHT'},'exposure':s.view_settings.exposure,'look':s.view_settings.look,'samples':16,'resolution':[640,640],'seed':s.cycles.seed,'hairSubdiv':3,'neutralInput':0.}
 assert row=={k:val for k,val in expected.items() if k!='file'};return row
def duplicate_pairs(ob,P):
 _,inv=np.unique(P,axis=0,return_inverse=True);points={};edges={}
 for i,g in enumerate(inv):points.setdefault(int(g),[]).append(i)
 for e in ob.data.edges:
  i,j=map(int,e.vertices)
  if inv[i]>inv[j]:i,j=j,i
  edges.setdefault((int(inv[i]),int(inv[j])),[]).append((i,j))
 pp=[(ids[0],j) for ids in points.values() for j in ids[1:]];ep=[pair for pairs in edges.values() for p in pairs[1:] for pair in zip(pairs[0],p)]
 return np.array(pp,dtype='i4').reshape(-1,2),np.array(ep,dtype='i4').reshape(-1,2)
def render(n):s=bpy.context.scene;s.render.filepath=str(E/n);bpy.ops.render.render(write_still=True)
def main():
 tick=time.time();contact=json.loads((E/'actual-lid-ocular-surface-contact.json').read_text('utf-8'));assert not contact['relatedRawSurfaceFailureObserved'] and contact['allRequestedPoseObjectCasesCompleted'];summary=json.loads((E/'a-build-summary.json').read_text('utf-8'));src=Path(summary['output']);bpy.ops.wm.open_mainfile(filepath=str(src));s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();rig=bpy.data.objects['AFN138_ACTUAL_CURRENT_GAZE_RIG'];neutral={n:a.geometry(bpy.data.objects[n])[0] for n in h.ATTACH};pairs={n:duplicate_pairs(bpy.data.objects[n],neutral[n]) for n in h.ATTACH};rows=[];bad=False
 for frame in [1,37,45,49]:
  s.frame_set(frame);bpy.context.view_layer.update()
  for n in h.ATTACH:
   W,T=a.geometry(bpy.data.objects[n]);pp,ep=pairs[n];pd=float(np.linalg.norm(W[pp[:,0]]-W[pp[:,1]],axis=1).max()) if len(pp) else 0.;ed=float(np.linalg.norm(W[ep[:,0]]-W[ep[:,1]],axis=1).max()) if len(ep) else 0.;rows.append({'frame':frame,'object':n,'exactNeutralDuplicatePointPairs':len(pp),'exactNeutralDuplicateEdgeEndpointPairs':len(ep),'posedDuplicatePointDivergenceMaxM':pd,'posedDuplicateEdgeEndpointDivergenceMaxM':ed});bad=bad or ed>1e-6
 h.save('actual-attachment-seam-check.json',{'source':str(src),'sha256':summary['sha256'],'cases':rows,'duplicateEdgeOpeningBeyondEvaluationBoundObserved':bad,'evaluationBoundM':1e-6,'boundNotContactTolerance':True,'scope':'Exact coincident source raw edge endpoints only; geometric duplication does not prove source anatomical intent, alpha-rendered follicle contact or all attachment quality. Existing rest offsets remain unqualified.'})
 assert not bad,'Known related raw attachment edge separation; do not adopt complete operation or expand light audit'
 records={};stage=light();s.frame_set(1);bpy.context.view_layer.update();render('second-light-a-neutral-face.png');s.frame_set(37);bpy.context.view_layer.update();render('second-light-a-up-face.png');records['candidateSecondLight']=stage
 # Entire current woman under the actual eye/lid operation and restoration.
 stageBody=v.setup('body-face')
 for frame in [37,49]:
  s.frame_set(frame);bpy.context.view_layer.update();render('actual-lid-gaze-body-frame-%03d.png'%frame)
 records['bodyPoseStage']=stageBody
 v.setup('oblique');s.frame_set(37);bpy.context.view_layer.update();render('actual-lid-up-oblique.png');records['candidateObliqueStage']=v.setup('oblique')
 bpy.ops.wm.open_mainfile(filepath=str(h.SRC));s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();old=light();assert old==stage;s.frame_set(37);bpy.context.view_layer.update();render('second-light-baseline-up-face.png');records['baselineSecondLight']=old
 oldOblique=v.setup('oblique');assert oldOblique==records['candidateObliqueStage'];s.frame_set(37);bpy.context.view_layer.update();render('baseline-lid-up-oblique.png');records['baselineObliqueStage']=oldOblique
 assert a.a.sha(src)==summary['sha256'];h.save('matched-operation-extra-view-controls.json',{'actualSourceCandidate':str(src),'actualSourceBaseline':str(h.SRC),'sourceFilesUnmodified':True,'controls':records,'secondLightAndObliqueStagesExactlyMatched':True,'nativePoseFrame':37,'originalEyePitchDeg':10,'relatedRawEdgeSeamCheckBeforeLightExpansion':True,'seconds':time.time()-tick});print('R139_ACTUAL_NATIVE_LID_ATTACHMENT_AND_MATCHED_EXTRA_POSES_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
