"""Resume already saved candidate after metadata error; no second geometry candidate."""
from pathlib import Path
import bpy,json,importlib.util,time,datetime
R=Path('D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0116-native-compatible-eyes';BASE=S/'r0115-source/aevrynd-female-next-r0115-b-continuous-native-neutral.blend';OUT=S/'r0116-source/aevrynd-female-next-r0116-a-native-paired-eyes.blend'
sp=importlib.util.spec_from_file_location('r116resume',Path(__file__).with_name('build-female-next-r0116-native-eye-character.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);b=a.b
tick=time.time();digest=a.sha(OUT);bpy.ops.wm.open_mainfile(filepath=str(BASE));b.deliver(0);before=a.protected();oldImages={im.name:im.filepath for im in bpy.data.images};bpy.ops.wm.open_mainfile(filepath=str(OUT));b.deliver(0);after=a.protected();assert before==after
for name,path in oldImages.items():assert bpy.data.images[name].filepath==path
source=json.loads((E/'native-eye-source-authoring.json').read_text(encoding='utf-8'));names=[p['name'] for p in source['actualSourceParts']]
for n in names:assert not bpy.data.objects[n].hide_render
oldNames=['AFN113_'+side+'_'+part for side in ['L','R'] for part in ['SCLERA','IRIS']]
for n in oldNames:assert bpy.data.objects[n].hide_render
a.save('a-build-summary.json',{'source':str(BASE),'output':str(OUT),'sha256':digest,'bytes':OUT.stat().st_size,'newActualSourceEyeObjects':names,'oldOpticsPreservedHidden':oldNames,'actualSourceReference':'reference-native-eye-structure-oblique.png','originalNativeEyeTopologyAndUVPreserved':True,'originalBodyAllKeysAndHairBrowLashPointsRadiiHashesBefore':before,'originalBodyAllKeysAndHairBrowLashPointsRadiiHashesAfter':after,'allProtectedGeometryByteExact':True,'oldImagePathsUnchanged':True,'originalStartAndDeadlineRetained':True,'firstMetadataFailurePreserved':'first-character-metadata-failure.log','resumeUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'resumeIsExistingCompleteSavedCandidateNotNewGeometry':True,'nativeMappingAndPBRApproximations':'native-eye-source-authoring.json','irisPupilIndependentGeometryFiniteCornealWallNaturalGazeAndContactUnaccepted':True})
views=[]
for view in ['face','body-face','profile','oblique','back']:
    views.append(b.u.v.image('a-native-paired-eyes',view));a.save('a-view-controls.json',views)
for label,value in [('half',.5),('closed',1.),('restored',0.)]:
    b.deliver(value);views.append(b.u.v.image('a-native-paired-eyes-'+label,'face'));a.save('a-view-controls.json',views)
assert a.sha(OUT)==digest;print('R116_SAVED_COMPLETE_NATIVE_EYES_PREVIEW_RESUMED_DONE',time.time()-tick,flush=True)
