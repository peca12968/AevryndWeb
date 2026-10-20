"""Independent artist-data/UV/packed-map and failed-flow readback only.
Reads upstream texts as license data with auto-execution disabled, never runs
the studio rig/shading scripts. No broad acceptance tests after visual failure.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
R=Path(r'D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0090-native-scalp-groom';REF=R/'Reference/character/blender-studio-rain-v3-cc-by4';RAIN=REF/'Rain v3.3/rain_v3.2.blend'
def mod(n,f):
 sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(f));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
m=mod('r90raincheck','build-female-next-r0081-editable-curly.py');q=m.q;native=mod('r90rainnative','verify-female-next-r0076-crowns.py');helpers=mod('r90rainmin','verify-female-next-r0090-saved-guides.py')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,x):(E/n).write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def open_file(p):bpy.ops.wm.open_mainfile(filepath=str(p));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
def world(o):
 A=np.array(o.matrix_world);return q.arr(o.data.vertices,'co',len(o.data.vertices),3).astype('f8')@A[:3,:3].T+A[:3,3]
def rig_signature():
 o=bpy.data.objects['AFN69_BODY_CONTROLS'];h=hashlib.sha256()
 for b in o.data.bones:h.update(b.name.encode());h.update((b.parent.name if b.parent else '').encode());h.update(np.array(b.matrix_local,'f8').tobytes())
 for b in o.pose.bones:h.update(b.name.encode());h.update(np.array(b.matrix_basis,'f8').tobytes())
 return h.hexdigest(),len(o.data.bones)
def main():
 tick=time.time();assert sha(RAIN)=='831ab6d837c679040285862b15dc9ee5180b018442a88aeaf92aaa7509b80258';up={};upMats={};names=['GEO-rain-hair_main','GEO-rain-hair_ponytail','GEO-rain-hair_strand','GEO-rain-hairband']
 with bpy.data.libraries.load(str(RAIN),link=False) as (src,dst):dst.objects=names;dst.texts=['ReadMe.txt','cloudrig.py','rain_shading.py']
 for o in dst.objects:
  d=o.data;up[o.name]={'world':world(o),'loops':q.arr(d.loops,'vertex_index',len(d.loops),dtype='i4'),'uv':{a.name:q.arr(a.data,'uv',len(d.loops),2).copy() for a in d.uv_layers}}
  for mat in d.materials:
   if mat and mat.use_nodes:
    signature=m.rig.k.f.v.v32.material_signature(mat)
    for row in signature['nodes']:
     if row['image'] and row['imagePackedSha256'] is None:
      image=bpy.data.images[row['image']];path=Path(bpy.path.abspath(image.filepath));assert path.is_file() and image.name.startswith('TEX-rain_hair_');row['imagePackedSha256']=sha(path)
    upMats[mat.name]=signature
 textInfo=[{'name':t.name,'bytes':len(t.as_string().encode()),'containsGPLNotice':'GNU General Public License' in t.as_string(),'containsBY4URL':'https://creativecommons.org/licenses/by/4.0/' in t.as_string(),'executed':False} for t in dst.texts];save('rain-source-license-and-script-scope.json',{'publisherBlendSha256':sha(RAIN),'publisherZipSha256':sha(REF/'Rain-v3.3.zip'),'characterDataLicense':'CC-BY4.0 per embedded ReadMe and official download page license link','requiredCredit':'Rain Rig (CC) Blender Foundation | studio.blender.org','sourceTexts':textInfo,'sourceToolCodeImportedIntoDerivedRuntimeOrRequired':False,'note':'Unmodified publisher archive retains original source-text notices. Studio tool texts are not present or required in derivative study files; no code from them executed.'});open_file(S/'aevrynd-female-next-r0088-b-supported-lid-aperture.blend');ns=m.rig.native_names()+['AFN59_LASHES_NATIVE_POINT_POSES'];sig={n:native.signature(bpy.data.objects[n]) for n in ns};other={n:helpers.cap_signature(bpy.data.objects[n]) for n in ('AFN74_UPPER_TEETH_RIGID','AFN74_LOWER_TEETH_RIGID','AFN81_NEUTRAL_EDITABLE_GROWTH_SURFACE')};oldHair=helpers.hair_signature(bpy.data.objects['AFN81_EDITABLE_CURLY_GUIDES']);facial={n:q.hair(bpy.data.objects[n]).copy() for n in ('AFN57_NATIVE_BROWS','AFN57_NATIVE_LASHES')};rig=rig_signature();texts=set(bpy.data.texts.keys());mats={x.name:m.rig.k.f.v.v32.material_signature(x) for x in bpy.data.materials if x.use_nodes and (x.users or x.use_fake_user)};lights=m.m.q.lights();base=E/'b-rain-hair-lineage.npz';z=np.load(base);refs=[('b','b-build-summary.json'),('c-guide','c-guide-build-summary.json'),('c-v-guide','c-v-guide-build-summary.json')];results=[]
 for tag,summary in refs:
  ref=json.loads((E/summary).read_text());out=Path(ref['output']);assert sha(out)==ref['outputSha256'];open_file(out);assert {n:native.signature(bpy.data.objects[n]) for n in ns}==sig;assert {n:helpers.cap_signature(bpy.data.objects[n]) for n in other}==other;assert helpers.hair_signature(bpy.data.objects['AFN81_EDITABLE_CURLY_GUIDES'])==oldHair;assert rig_signature()==rig;assert {n:m.rig.k.f.v.v32.material_signature(bpy.data.materials[n]) for n in mats}==mats;assert m.m.q.lights()==lights;assert set(bpy.data.texts.keys())==texts and not bpy.data.libraries;assert not any('RIG-rain' in o.name for o in bpy.data.objects)
  for n,P in facial.items():assert np.array_equal(q.hair(bpy.data.objects[n]),P)
  meshRows=[]
  for objName in ['AFN90_RAIN_HAIR_MAIN','AFN90_RAIN_HAIR_PONYTAIL','AFN90_RAIN_HAIR_STRAND','AFN90_RAIN_HAIRBAND']:
   o=bpy.data.objects[objName];d=o.data;sourceName='GEO-rain-'+objName.removeprefix('AFN90_RAIN_').lower();wanted=up[sourceName];P=world(o);err=float(np.linalg.norm(P-z[objName+'_targetWorld'],axis=1).max());assert err<2e-6 and np.array_equal(wanted['world'],z[objName+'_sourceWorld']);assert np.array_equal(q.arr(d.loops,'vertex_index',len(d.loops),dtype='i4'),wanted['loops']);assert not o.constraints and not o.parent and not o.animation_data and not d.shape_keys and not o.vertex_groups;assert all(md.type=='SUBSURF' for md in o.modifiers)
   for uv in d.uv_layers:assert np.array_equal(q.arr(uv.data,'uv',len(d.loops),2),wanted['uv'][uv.name])
   meshRows.append({'object':objName,'sourceObject':sourceName,'nativeVertices':len(P),'nativeFaces':len(d.polygons),'sourceUVAndLoopTopologyExact':True,'savedWorldMaximumErrorM':err,'noForeignRigLatticeWeightsOrScripts':True})
  assert {n:m.rig.k.f.v.v32.material_signature(bpy.data.materials[n]) for n in upMats}==upMats;packed=[];external=[]
  for im in bpy.data.images:
   if im.name.startswith('TEX-rain_hair_'):
    assert im.packed_file;blob=bytes(im.packed_file.data);path=RAIN.parent/'textures'/im.name;assert hashlib.sha256(blob).hexdigest()==sha(path);packed.append({'name':im.name,'sha256':sha(path),'packed':True})
   elif im.source=='FILE' and not im.packed_file:
    path=Path(bpy.path.abspath(im.filepath));assert im.filepath.startswith('//') and path.is_file();external.append({'relative':im.filepath,'sha256':sha(path)})
  assert len(packed)==3 and len(external)==15;flow=None
  if tag!='b':
   line=np.load(E/(tag+'-lineage.npz'));g=bpy.data.objects[ref['guideObject']];A=np.array(g.matrix_world);P=world(g);expect=line['pathsWorld'].reshape(-1,3);err=float(np.linalg.norm(P-expect,axis=1).max());assert err<2e-6;diag=bpy.data.objects[ref['renderObject']];C=np.array([p.co[:3] for sp in diag.data.splines for p in sp.points]);C=C@A[:3,:3].T+A[:3,3];assert float(np.linalg.norm(C-P,axis=1).max())<2e-6;assert len(g.data.vertices)==128*96 and len(diag.data.splines)==128;assert np.array_equal(line['failedRootIDs'],ref['failedRootIDs']) and len(line['failedRootIDs'])==ref['failedTraceCount'];flow={'attemptedRoots':128,'allRetained':True,'failed':ref['failedTraceCount'],'savedGuideMaximumWorldErrorM':err,'noDenseExpansionOrGrowthAcceptance':True}
  row={'status':'PASS_MINIMUM_SAVED_ART_DATA_AND_FAILED_TRACE_READBACK_ONLY','source':str(out),'sha256':sha(out),'rainMeshComponents':meshRows,'allOriginalCagesKeysUVWeightsDriversMaterialTreesLightsTeethCurlyCapAndGuidesPreserved':True,'rigBonesUnchanged':rig[1],'evaluatedBrowsLashesExactAtNeutral':True,'rainOriginalMaterialTreesUVTopologyAndPackedMapsVerified':True,'packedHairMaps':packed,'externalTextures':external,'sourceRigToolCodeNotInDerivedBlend':True,'flow':flow,'completeAppearanceContactNaturalMotionRuntimeAccepted':False};save(tag+'-minimum-readback.json',row);results.append(row);print('R90_RAIN_FLOW_SOURCE_CHECK',tag,flow,flush=True)
 save('rain-and-flow-minimum-readback.json',{'status':'PASS_MINIMUM_SAVED_COMPONENT_DATA_ONLY','sources':results,'sourceRightsAndScripts':'rain-source-license-and-script-scope.json','seconds':time.time()-tick,'noBroadTestsAfterVisualRejection':True})
if __name__=='__main__':main()
