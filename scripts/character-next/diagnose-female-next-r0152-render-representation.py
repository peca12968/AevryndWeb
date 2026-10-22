"""One bounded representation comparison; no source edits or new character round."""
from pathlib import Path
import bpy,numpy as np,json,time,datetime,importlib.util,hashlib
from mathutils import Matrix
R=Path('D:/Download/Aevrynd');OLD=R/'Evidence/character-female-next/r0152-layered-groom'
E=R/'Evidence/character-female-next/support-r0152-render-representation'
SRC=R/'engine/assets/characters/female-next/source/r0152-source/aevrynd-female-next-r0152-a-layered-native-groom.blend'
sp=importlib.util.spec_from_file_location('r152representation',Path(__file__).with_name('build-female-next-r0152-layered-current-source.py'));h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h);a=h.a
def save(n,x):(E/n).write_bytes((json.dumps(x,indent=2,ensure_ascii=False,default=str)+'\n').encode())
def state(s):
 return {'primitive':s.render.hair_type,'subdivision':s.render.hair_subdiv,'engine':s.render.engine,'device':s.cycles.device,'samples':s.cycles.samples,'denoise':s.cycles.use_denoising,'seed':s.cycles.seed,'threads':s.render.threads,'resolution':[s.render.resolution_x,s.render.resolution_y,s.render.resolution_percentage],'exposure':s.view_settings.exposure,'look':s.view_settings.look,'transform':s.view_settings.view_transform,'camera':np.array(s.camera.matrix_world).tolist(),'lens':s.camera.data.lens,'lights':a.b.u.v.m.m.q.lights()}
def main():
 tick=time.time();E.mkdir(exist_ok=False);assert a.a.sha(SRC)=='6d14dcca0c0a3dc2a8be613d92377a663522dbb8d31a3f26ec894132723f1480'
 save('before.json',{'entryStartedUTC':'2026-10-22T06:21:50+00:00','supportDeadlineUTC':'2026-10-22T06:31:50+00:00','startedUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'originalR152StartedUTC':'2026-10-22T05:16:30+00:00','originalR152Before':str(OLD/'before.json'),'source':str(SRC),'sourceSha256':a.a.sha(SRC),'sourceOnlyReadNoNewBlend':True,'hypothesis':'Matched helper resets saved STRIP to CYLINDER. Test only primitive while keeping actual evaluated geometry/radius/shader/camera/light/exposure/sample/denoise state identical. No appearance acceptance or new character round.','previousGoalTurnClassification':'Prompt maintenance v49 changed execution instructions only; no character appearance gain.','newEvidenceBudgetBytes':7000000})
 bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();hair=bpy.data.objects['AFN152_ACTUAL_NATIVE_NEIGHBOUR_GROOM'];geometry=a.q.hair(hair);geoHash=a.a.hasharray(geometry);raw={n:a.rawsig(bpy.data.objects[n]) for n in a.FIXED+a.MOVING};saved=state(s)
 # Exactly the setting/camera pipeline used by the matched-image helper.
 a.b.u.v.m.rig.shade.settings();s.camera.data.lens=85;s.render.hair_subdiv=3;s.render.resolution_x=s.render.resolution_y=640;s.cycles.samples=16
 helper=state(s);save('saved-and-helper-settings.json',{'saved':saved,'actualMatchedHelperBeforePrimitiveOverride':helper,'geometrySha256':geoHash,'savedAndActualHelperPrimitiveDiffer':saved['primitive']!=helper['primitive'],'captureTimeRecordsFollow':True})
 views=json.loads((OLD/'a-view-controls.json').read_text());rows=[]
 for view in ['face','back']:
  ref=next(r for r in views if r['view']==view);s.camera.matrix_world=Matrix(ref['camera']);s.camera.data.lens=ref['lensMM'];bpy.context.view_layer.update()
  pair=[]
  for primitive in ['CYLINDER','STRIP']:
   s.render.hair_type=primitive;s.render.filepath=str(E/(view+'-'+primitive.lower()+'.png'));bpy.context.view_layer.update();pre=state(s);assert a.a.hasharray(a.q.hair(hair))==geoHash
   captured=[]
   def pre_handler(scene,*_):captured.append(state(scene))
   bpy.app.handlers.render_pre.append(pre_handler)
   try:bpy.ops.render.render(write_still=True)
   finally:bpy.app.handlers.render_pre.remove(pre_handler)
   assert captured and captured[-1]==pre
   pair.append({'view':view,'file':s.render.filepath,'actualRenderPre':captured[-1],'geometrySha256':geoHash,'bytes':Path(s.render.filepath).stat().st_size,'completedUTC':datetime.datetime.now(datetime.timezone.utc).isoformat()});rows.append(pair[-1]);save('actual-capture-records.json',rows)
  x=dict(pair[0]['actualRenderPre']);y=dict(pair[1]['actualRenderPre']);x.pop('primitive');y.pop('primitive');assert x==y
 assert a.a.hasharray(a.q.hair(hair))==geoHash and raw=={n:a.rawsig(bpy.data.objects[n]) for n in raw};assert a.a.sha(SRC)=='6d14dcca0c0a3dc2a8be613d92377a663522dbb8d31a3f26ec894132723f1480'
 save('result.json',{'rows':rows,'geometryAndCurrentMeshesUnchanged':True,'onlyPrimitiveChangedPerPair':True,'noSourceFileWritten':True,'newProductionRound':False,'appearanceAdoption':False,'elapsedSeconds':time.time()-tick,'humanReviewRequired':True});print('R152_ACTUAL_RENDER_REPRESENTATION_COMPARISON_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
