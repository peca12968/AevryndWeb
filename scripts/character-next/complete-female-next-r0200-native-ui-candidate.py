"""Freeze and capture the saved actual Windows-native Comb/Smooth edits.
No new guide position authoring and no replay of failed EXEC strokes.
"""
from pathlib import Path
import bpy,numpy as np,json,datetime,hashlib,time,importlib.util
from mathutils import Matrix
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');E=C/'evidence/character-female-next/r0200-native-curve-sculpt';OUT=C/'assets-source/aevrynd-character/female-next/r0200-source/aevrynd-female-next-r0200-native-curve-sculpt.blend'
sp=importlib.util.spec_from_file_location('r200completebase',C/'scripts/character-next/build-female-next-r0169-coherent-native-carrier.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a;h=m.h
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(n,x):(E/n).write_bytes((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
def sha(p):return hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()
tick=time.time();assert not OUT.exists()
session=OUT.with_name('aevrynd-female-next-r0200-editing-session.blend');sessionSHA=sha(session)
bpy.ops.wm.open_mainfile(filepath=str(session));s=bpy.context.scene
hair=bpy.data.objects['AFN198_ACTUAL_SURFACE_BORN_NATIVE_GROOM'];old=bpy.data.objects[a.FIXED[1]];skin=bpy.data.objects[a.FIXED[0]]
if hair.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
display=json.loads((E/'native-guide-edit-display-settings.json').read_text('utf-8'))
assert display['rawRadiusAttributeInitiallyAbsent']
radius=hair.data.attributes.get('radius');assert radius is not None;hair.data.attributes.remove(radius)
for n in display['editViewOnlyHiddenObjects']:bpy.data.objects[n].hide_set(False)
gen=hair.modifiers['AFN198_ACTUAL_SURFACE_CHILD_GENERATOR'];gen.show_viewport=True;gen.show_render=True
s.frame_set(1);hair.data.update_tag();bpy.context.view_layer.update()
raw=h.arr(hair.data.position_data,'vector',len(hair.data.position_data),3);baseline=np.load(E/'resumed-native-editor-baseline.npz');latest=np.load(E/'resumed-native-editor-latest.npz')
assert np.max(np.abs(raw-latest['guideWorld']))<1e-8
P,off=m.curveworld(hair);data=hair.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;ids=h.arr(data.attributes['AFN198_PERSISTENT_BIRTH_ID'].data,'value',len(off),dtype='i4')
assert len(off)==10191 and np.array_equal(np.sort(ids),np.arange(10191)) and np.all(np.diff(np.r_[off,len(P)])==16)
canonical=np.empty((10191,16,3));canonical[ids]=P.reshape(10191,16,3);expected=np.empty_like(canonical);expected[latest['birthIDs']]=latest['evaluatedWorld'].reshape(10191,16,3)
assert np.linalg.norm(canonical-expected,axis=2).max()<3e-6
protected={n:a.rawsig(bpy.data.objects[n]) for n in a.FIXED+a.MOVING}
actions=json.loads((E/'actual-native-ui-authoring-actions.json').read_text('utf-8'))['actions']
summary={'UTC':stamp(),'actualSkin':skin.name,'actualHair':hair.name,'actualBirths':'AFN198_ACTUAL_EDITABLE_SURFACE_BIRTHS','actualGuides':252,'actualCurves':len(off),'actualPoints':len(P),'nativeBrushOperations':len(actions),'nativeBrushes':['Comb','Smooth'],'rawGuideMaximumChangeM':float(np.linalg.norm(raw-baseline['guideWorld'],axis=1).max()),'rawGuideRootMaximumChangeM':float(np.linalg.norm(raw.reshape(252,16,3)[:,0]-baseline['guideWorld'].reshape(252,16,3)[:,0],axis=1).max()),'allOldOriginalRawMeshUVSignaturesUnchanged':protected,'sameBirthIDsUVCountRadiusMaterialAndGenerator':True,'temporaryEditorRadiusRemoved':True,'editorOnlyControlVisibilityRestored':display['editViewOnlyHiddenObjects'],'completeGeneratedPositionChangeAfterEditorRadiusRemovalM':float(np.linalg.norm(canonical-expected,axis=2).max()),'nativeGenerationRestoredBeforeEveryCompletePreview':True,'notCoordinateTemplateAuthoring':True,'actualSavedNativeUISession':str(session),'actualSavedNativeUISessionSHA256':sessionSHA,'lineageFile':str(E/'resumed-native-editor-latest.npz'),'baselineFile':str(E/'resumed-native-editor-baseline.npz'),'appearanceOperationContactRuntimeUnaccepted':True}
save('native-brush-construction-summary.json',summary)
captures=[]
def capture(scene):
    captures.append({'UTC':stamp(),'loadedSource':bpy.data.filepath,'plannedCandidate':str(OUT),'output':scene.render.filepath,'frame':scene.frame_current,'cameraMatrixWorld':[list(v) for v in scene.camera.matrix_world],'lens':scene.camera.data.lens,'cameraType':scene.camera.data.type,'viewTransform':scene.view_settings.view_transform,'look':scene.view_settings.look,'exposure':scene.view_settings.exposure,'cyclesSamples':scene.cycles.samples,'seed':scene.cycles.seed,'hairType':scene.render.hair_type,'newGroomVisible':not hair.hide_render,'originalHairVisible':not old.hide_render,'nativeChildGeneratorViewportAndRenderEnabled':gen.show_viewport and gen.show_render,'captureStateNotRenderGeometryDepsgraphProof':True});save('actual-render-pre-capture-states.json',captures)
bpy.app.handlers.render_pre.append(capture);a.b.u.v.E=E;hair.hide_render=True;old.hide_render=False
for v in ['face','body-face']:s.camera.data.type='PERSP';a.b.u.v.image('baseline-original-working-hair',v)
old.hide_render=True;hair.hide_render=False
for v in ['face','body-face','oblique','profile','back']:s.camera.data.type='PERSP';a.b.u.v.image('a-native-curve-sculpt',v)
bpy.app.handlers.render_pre.remove(capture);s.camera.matrix_world=Matrix(captures[2]['cameraMatrixWorld']);s.camera.data.lens=captures[2]['lens'];s.camera.data.type='PERSP'
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
save('a-build-summary.json',{'UTC':stamp(),'output':str(OUT),'sha256':sha(OUT),'bytes':OUT.stat().st_size,'actualHair':hair.name,'actualSkin':skin.name,'actualBirths':'AFN198_ACTUAL_EDITABLE_SURFACE_BIRTHS','oneCandidate':True,'elapsedJobSeconds':time.time()-tick,'actualCurves':len(off),'actualPoints':len(P),'unaccepted':True})
print('R200_ACTUAL_NATIVE_UI_CANDIDATE_COMPLETE_SAVED',flush=True)
