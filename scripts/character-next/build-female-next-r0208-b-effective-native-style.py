
from pathlib import Path
import bpy,numpy as np,json,datetime,time,hashlib,importlib.util,shutil
from mathutils import Matrix
p=json.loads(Path('F:/AevryndStorage/character-development-paths.json').read_text('utf-8'));A=Path(p['directCharacterArchiveAccess']);E=A/'evidence/character-female-next/r0208-complete-native-style-construction';F=Path('F:/AevryndEvidence/r0208-complete-native-style-construction');t=json.loads((E/'before.json').read_text('utf-8'));tick=time.time();ART=Path('C:/Users/USER/AppData/Local/Temp/Aevrynd-hair-editor-reference/hair.blend')
def sha(f):return hashlib.file_digest(Path(f).open('rb'),'sha256').hexdigest()
def save(name,d):(E/name).write_bytes((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
assert sha(ART)=='93aedaef061dc14618a0fcfad33c3df816fa755e8093381cbdfd0fd4c34527f5';bpy.ops.wm.open_mainfile(filepath=str(ART));orig=bpy.data.objects['basic_short_hair'];scale=np.array(orig.matrix_world.to_scale());assert np.max(np.abs(scale-scale[0]))<1e-7;sourceUnit=float(scale[0]);stageNames=['Curl Hair Curves','Hair Curves Noise','Frizz Hair Curves','Roll Hair Curves','Clump Hair Curves'];groups=[orig.modifiers[n].node_group.name for n in stageNames];effectiveInputs={}
for stageName in stageNames:
 md=orig.modifiers[stageName];values={}
 for sock in md.node_group.interface.items_tree:
  if sock.item_type!='SOCKET' or sock.in_out!='INPUT' or sock.socket_type=='NodeSocketGeometry':continue
  value=getattr(md.properties.inputs,sock.identifier);fields={}
  for prop in value.bl_rna.properties:
   if prop.identifier in ['rna_type','name'] or prop.is_readonly or prop.type in ['COLLECTION','POINTER']:continue
   v=getattr(value,prop.identifier);fields[prop.identifier]=list(v) if getattr(prop,'is_array',False) else v
  assert fields,('No actual input data',stageName,sock.identifier)
  values[sock.identifier]={'name':sock.name,'fields':fields}
 effectiveInputs[stageName]=values
save('b-actual-qualified-effective-native-inputs.json',effectiveInputs)
sourceMeta={'sourceObjectScale':scale.tolist(),'sourceWorldMatrix':[list(x) for x in orig.matrix_world],'stages':[{'name':n,'group':orig.modifiers[n].node_group.name,'RNAproperties':[x.identifier for x in orig.modifiers[n].bl_rna.properties]} for n in stageNames],'originalGeneratorAndProfileNotCopied':'Own persistent currentSkin births/own existing interpolation and fixed radius retained. This is a current authored style, not full original25324-curve reproduction.'};save('b-actual-original-stage-units.json',sourceMeta)
assert sha(t['source'])==t['sourceSha256'];bpy.ops.wm.open_mainfile(filepath=t['source']);s=bpy.context.scene;s.frame_set(1);sp=importlib.util.spec_from_file_location('r208base',A/'scripts/character-next/build-female-next-r0169-coherent-native-carrier.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a;h=m.h;old=bpy.data.objects[a.FIXED[1]];skin=bpy.data.objects[a.FIXED[0]];previous=bpy.data.objects['AFN207B_ACTUAL_SURFACE_MAPPED_ARTIST_GROOM'];births=bpy.data.objects['AFN207B_ACTUAL_CURRENT_SKIN_OWNED_BIRTHS'];protected={n:a.rawsig(bpy.data.objects[n]) for n in a.FIXED+a.MOVING};hair=previous.copy();hair.data=previous.data.copy();hair.name='AFN208B_ACTUAL_COMPLETE_NATIVE_STYLED_GROOM';s.collection.objects.link(hair)
for mod in hair.modifiers:
 if mod.type=='NODES':mod.node_group=mod.node_group.copy()
previous.hide_render=True;previous.hide_set(True);hair.hide_render=False;hair.hide_set(False);old.hide_render=True
with bpy.data.libraries.load(str(ART),link=False) as (src,dst):dst.node_groups=groups
loaded={g.name:g for g in dst.node_groups};physicalScale=1.0462071354820404;unit=sourceUnit*physicalScale;assert unit>0
# One native style construction, using physical object units; no parameter sweep.
def transform(name,amount):
 ng=bpy.data.node_groups.new(name,'GeometryNodeTree');ng.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');ng.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry');i=ng.nodes.new('NodeGroupInput');o=ng.nodes.new('NodeGroupOutput');n=ng.nodes.new('GeometryNodeTransform');n.inputs['Scale'].default_value=(amount,)*3;ng.links.new(i.outputs['Geometry'],n.inputs['Geometry']);ng.links.new(n.outputs['Geometry'],o.inputs['Geometry']);md=hair.modifiers.new(name,'NODES');md.node_group=ng;return md
transform('AFN208B_CURRENT_WORLD_TO_SOURCE_PHYSICAL_UNITS',1/unit)
for index,g in enumerate(dst.node_groups):
 md=hair.modifiers.new('AFN208B_NATIVE_'+stageNames[index].upper().replace(' ','_'),'NODES');md.node_group=g
 for identifier,row in effectiveInputs[stageNames[index]].items():
  value=getattr(md.properties.inputs,identifier)
  for field,v in row['fields'].items():setattr(value,field,v)
  for field,v in row['fields'].items():
   actual=getattr(value,field);assert (list(actual) if isinstance(v,list) else actual)==v,(stageNames[index],identifier,field,actual,v)
transform('AFN208B_SOURCE_UNITS_TO_CURRENT_WORLD',unit)
# Evaluate every displayed stage without deleting or excluding any fibre.
mods=list(hair.modifiers);stageRows=[];baseline=None
for mod in mods[2:]:mod.show_viewport=False
bpy.context.view_layer.update()
def evalState():
 P,off=m.curveworld(hair);d=hair.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;at=d.attributes.get('AFN198_PERSISTENT_BIRTH_ID');ids=h.arr(at.data,'value',len(off),dtype='i4') if at else np.array([],dtype='i4');uvattr=d.attributes.get('surface_uv_coordinate');uv=h.arr(uvattr.data,'vector',len(off),2) if uvattr else np.empty((0,2));return P,off,ids,uv
baseP,baseOff,baseIDs,baseUV=evalState();assert len(baseOff)==10191 and np.array_equal(np.sort(baseIDs),np.arange(10191));baseRoots=baseP[baseOff][np.argsort(baseIDs)]
for index,mod in enumerate(mods[2:]):
 mod.show_viewport=True;bpy.context.view_layer.update();P,off,ids,uv=evalState();good=len(off)==10191 and np.array_equal(np.sort(ids),np.arange(10191));factor=unit if index<len(mods[2:])-1 else 1;rootDelta=float(np.linalg.norm(P[off][np.argsort(ids)]*factor-baseRoots,axis=1).max()) if good else None;stageRows.append({'stage':mod.name,'actualCurves':len(off),'actualPoints':len(P),'allPersistentCurrentBirthIDs':good,'worldRootMaximumChangeM':rootDelta,'worldRootsFinite':bool(np.isfinite(P).all()),'UVunchanged':bool(good and np.array_equal(uv[np.argsort(ids)],baseUV[np.argsort(baseIDs)]))})
 assert len(P)<3000000,('Original resource cap',len(P))
assert protected=={n:a.rawsig(bpy.data.objects[n]) for n in protected};P,off,ids,uv=evalState();np.savez_compressed(E/'b-complete-native-style-displayed-lineage.npz',displayedWorld=P,offsets=off,persistentBirthIDs=ids,birthUV=uv,baseWorld=baseP,baseOffsets=baseOff,baseIDs=baseIDs,baseUV=baseUV)
save('b-actual-native-stage-geometry.json',{'UTC':stamp(),'sourceUnitM':sourceUnit,'measuredHeadWidthRatio':physicalScale,'currentUnitM':unit,'allSevenRawMeshUVSignaturesUnchanged':protected,'actualHair':hair.name,'actualSkin':skin.name,'actualBirths':births.name,'stages':stageRows,'appearanceFunctionContactRuntimeUnaccepted':True,'sourceEffectiveModifierOverridesCopiedAndReadBackExactly':True,'noDeleteHideFailedFibresRadiusDensityLightSweep':True,'constructionSecondsBeforePreview':time.time()-tick})
captures=[]
def capture(scene):
 captures.append({'UTC':stamp(),'source':bpy.data.filepath,'output':scene.render.filepath,'frame':scene.frame_current,'cameraMatrixWorld':[list(x) for x in scene.camera.matrix_world],'lens':scene.camera.data.lens,'cameraType':scene.camera.data.type,'exposure':scene.view_settings.exposure,'viewTransform':scene.view_settings.view_transform,'look':scene.view_settings.look,'samples':scene.cycles.samples,'seed':scene.cycles.seed,'newHairVisible':not hair.hide_render,'originalHairVisible':not old.hide_render,'nativeStagesRender':[{'name':md.name,'render':md.show_render,'viewport':md.show_viewport} for md in hair.modifiers],'captureStateNotRenderDepsgraphProof':True});save('b-actual-render-pre-capture-states.json',captures)
bpy.app.handlers.render_pre.append(capture);a.b.u.v.E=F;hair.hide_render=True;old.hide_render=False
# Reuse unchanged matched originalHair baseline from A; no optics or pose change.
old.hide_render=True;hair.hide_render=False
for v in ['face','body-face','oblique','profile','back']:s.camera.data.type='PERSP';a.b.u.v.image('b-effective-native-styled-groom',v)
bpy.app.handlers.render_pre.remove(capture);s.camera.matrix_world=Matrix(captures[0]['cameraMatrixWorld']);s.camera.data.lens=captures[0]['lens'];s.camera.data.type='PERSP'
for file in F.glob('matched-b-*.png'):shutil.copyfile(file,E/file.name)
output=F/'aevrynd-female-next-r0208-b-effective-native-styled-groom.blend';out=A/'assets-source/aevrynd-character/female-next/r0208-source'/output.name;out.parent.mkdir(exist_ok=True);assert not out.exists();bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(output),compress=True);assert output.stat().st_size<t['sourceBudgetBytes'];shutil.copyfile(output,out);save('b-build-summary.json',{'UTC':stamp(),'output':str(out),'userReviewSource':str(output),'sha256':sha(out),'bytes':out.stat().st_size,'actualHair':hair.name,'actualSkin':skin.name,'actualBirths':births.name,'actualCurves':len(off),'actualPoints':len(P),'oneCompleteCandidate':True,'elapsedJobSeconds':time.time()-tick,'unaccepted':True});print('R208B_ACTUAL_EFFECTIVE_NATIVE_STYLE_CURRENT_WOMAN_SAVED',json.dumps({'source':str(output),'curves':len(off),'points':len(P),'stages':stageRows}),flush=True)
