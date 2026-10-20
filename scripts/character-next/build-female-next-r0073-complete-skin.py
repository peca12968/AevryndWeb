"""Complete author skin network and exact native source masks, one fixed trial.

Source placeholder UDIM leaves are supplied via the existing verified flat
maps/UV lookup. Original shader math/settings remain unchanged. No sweeps.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,time,sys,importlib.util,shutil
def module(n,p):
    s=importlib.util.spec_from_file_location(n,Path(__file__).with_name(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
m=module('skin73rig','build-female-next-r0069-complete-controls.py');render=module('skin73stage','build-female-next-r0071-hair-scattering.py')
R=m.R;S=m.S;D=R/'Reference/character/charmorph-vitruvian-cc0';E=R/'Evidence/character-female-next/r0073-complete-skin';SRC=S/'aevrynd-female-next-r0069-a-complete-controls-study.blend';HIGH_SOURCE='--source-resolution' in sys.argv;TAG='b' if HIGH_SOURCE else 'a';OUT=S/('aevrynd-female-next-r0073-b-original-4k-skin-study.blend' if HIGH_SOURCE else 'aevrynd-female-next-r0073-a-complete-source-skin-study.blend');SOURCE_SHA='f358d3c5a4d00ee6ad94d324612b33bdcf5aa4dde0bb19382d72bc7afabbb667'
RAW_TEXTURES=[]
MASKS=('ColLipMask','MicroNormals','HairAO','BeardShadowMask')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,x):(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def restore_masks():
    ref=json.loads((E.parent/'r0057-coherent-foundation/canonical-library.json').read_text());assert sha(Path(ref['output']))==ref['sha256']
    with bpy.data.libraries.load(ref['output'],link=False) as (src,dst):dst.objects=['cm_vitruvian']
    source=dst.objects[0];mesh=source.data;assert len(mesh.vertices)==37436
    source_faces=[tuple(p.vertices) for p in mesh.polygons];source_loops=[{int(v):p.loop_start+j for j,v in enumerate(p.vertices)} for p in mesh.polygons];arrays={};source_meta={}
    for name in MASKS:
        a=mesh.color_attributes.get(name);assert a is not None,(name,list(mesh.color_attributes.keys()));arr=np.empty((len(a.data),4),'f4');a.data.foreach_get('color',arr.ravel());assert np.isfinite(arr).all();arrays[name]=(a.data_type,a.domain,arr);source_meta[name]={'type':a.data_type,'domain':a.domain,'count':len(arr),'sha256':hashlib.sha256(arr.tobytes()).hexdigest(),'range':[float(arr.min()),float(arr.max())]}
    results=[]
    for name in m.native_names():
        o=bpy.data.objects[name];me=o.data;ids=np.empty(len(me.vertices),'i4');me.attributes['AFN60_NativeVertexID'].data.foreach_get('value',ids);face_ids=np.empty(len(me.polygons),'i4');me.attributes['AFN60_NativeFaceID'].data.foreach_get('value',face_ids);corner_map=np.empty(len(me.loops),'i4')
        for p,f in zip(me.polygons,face_ids):
            native=[int(ids[v]) for v in p.vertices];assert set(native)==set(source_faces[int(f)]),(name,int(f));corner_map[p.loop_start:p.loop_start+p.loop_total]=[source_loops[int(f)][v] for v in native]
        for mask,(kind,domain,arr) in arrays.items():
            assert me.color_attributes.get(mask) is None
            values=arr[ids if domain=='POINT' else corner_map];a=me.color_attributes.new(name=mask,type=kind,domain=domain);a.data.foreach_set('color',values.ravel());out=np.empty_like(values);a.data.foreach_get('color',out.ravel());assert np.array_equal(out,values)
            results.append({'object':name,'mask':mask,'type':kind,'domain':domain,'count':len(values),'expectedColorSha256':hashlib.sha256(values.tobytes()).hexdigest(),'range':[float(values.min()),float(values.max())]})
    bpy.data.objects.remove(source,do_unlink=True)
    if mesh.users==0:bpy.data.meshes.remove(mesh)
    save('restored-native-mask-data.json',{'canonicalLibrary':ref,'sourceMasks':source_meta,'restored':results,'mapping':'POINT by original native vertex ID; CORNER by original native face ID plus matching native vertex, no nearest-surface approximation.'})
def lookup(kind):
    t=bpy.data.node_groups.new('AFN73_VERIFIED_FLAT_UDIM_'+kind,'ShaderNodeTree');t.interface.new_socket(name='Color',in_out='OUTPUT',socket_type='NodeSocketColor');out=t.nodes.new('NodeGroupOutput');uv=t.nodes.new('ShaderNodeUVMap');uv.uv_map='VitruvianUV.UDIM';sep=t.nodes.new('ShaderNodeSeparateXYZ');floor=t.nodes.new('ShaderNodeMath');floor.operation='FLOOR';t.links.new(uv.outputs['UV'],sep.inputs[0]);t.links.new(sep.outputs['X'],floor.inputs[0]);previous=None
    for number in range(1001,1005):
        if HIGH_SOURCE:
            filename=kind+'.'+str(number)+'.exr';origin=D/'textures-4k'/filename;target=S/'study-vitruvian-textures-source4k'/filename;target.parent.mkdir(exist_ok=True);metadata=next(x for x in json.loads((E.parent/'r0057-coherent-foundation/texture-derivatives.json').read_text())['files'] if x['file']==filename);assert sha(origin)==metadata['sourceSHA256']
            if target.exists():assert sha(target)==metadata['sourceSHA256']
            else:shutil.copyfile(origin,target)
            im=bpy.data.images.load(str(target),check_existing=True);im.filepath='//study-vitruvian-textures-source4k/'+filename;im.colorspace_settings.name='Non-Color' if kind in ('Skin_Roughness','Skin_Height') else 'Linear Rec.709';assert list(im.size)==metadata['sourceSize']==[4096,4096];images=[im];RAW_TEXTURES.append({'file':filename,'sourceSha256':metadata['sourceSHA256'],'actualSha256':sha(target),'size':list(im.size),'relative':im.filepath,'bytes':target.stat().st_size,'oldDerivativeSize':metadata['size'],'sourceByteCopyNoResamplingOrRequantization':True})
        else:
            images=[im for im in bpy.data.images if im.filepath.replace('\\','/').endswith('/'+kind+'.'+str(number)+'.exr')];assert len(images)==1,(kind,number)
        node=t.nodes.new('ShaderNodeTexImage');node.image=images[0];node.extension='REPEAT';node.interpolation='Linear';t.links.new(uv.outputs['UV'],node.inputs['Vector'])
        if previous is None:previous=node.outputs['Color']
        else:
            pick=t.nodes.new('ShaderNodeMath');pick.operation='GREATER_THAN';pick.inputs[1].default_value=number-1001-.5;t.links.new(floor.outputs[0],pick.inputs[0]);mix=t.nodes.new('ShaderNodeMixRGB');t.links.new(pick.outputs[0],mix.inputs[0]);t.links.new(previous,mix.inputs[1]);t.links.new(node.outputs['Color'],mix.inputs[2]);previous=mix.outputs[0]
    t.links.new(previous,out.inputs['Color']);return t
def pilot(view):
    s=bpy.context.scene;m.shade.settings();m.k.b.camera(view);s.camera.data.lens=85;s.render.resolution_x=s.render.resolution_y=640;s.cycles.samples=16
    ctl={'camera':np.array(s.camera.matrix_world).tolist(),'lights':render.lights(),'samples':16,'resolution':640,'seed':s.cycles.seed,'exposure':s.view_settings.exposure,'look':s.view_settings.look,'frame':s.frame_current,'engine':s.render.engine,'hairPrimitive':s.render.hair_type};old=E.parent/'r0071-hair-scattering';p=old/('baseline-pilot-controls.json' if view=='face' else 'baseline-body-pilot-controls.json');assert ctl==json.loads(p.read_text());s.render.filepath=str(E/(TAG+'-pilot-'+view+'.png'));bpy.ops.render.render(write_still=True);save(TAG+'-pilot-'+view+'-controls.json',{'candidate':ctl,'reusedBaselineControls':str(p),'reusedBaselineImage':str(old/('baseline-pilot-'+view+'.png'))})
def main():
    tick=time.time();m.shade.g.E=E
    if '--views' in sys.argv:
        assert sha(OUT)==json.loads((E/(TAG+'-build-summary.json')).read_text())['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(OUT));bpy.context.scene.frame_set(1);m.shade.settings();save(TAG+'-full-view-controls.json',m.shade.render(TAG+'-skin',('face','body-face','oblique','profile','back','alternate-oblique')));return
    assert not OUT.exists() and sha(SRC)==SOURCE_SHA;bpy.ops.wm.open_mainfile(filepath=str(SRC));bpy.context.scene.frame_set(1);lights=render.lights();restore_masks()
    assert sha(D/'char.blend')=='7e9581c30b48f1409dfeec4a5ec0736014318fc8825ca6d4728f2b543bb02126'
    with bpy.data.libraries.load(str(D/'char.blend'),link=False) as (src,dst):dst.materials=['UDIM.Skin']
    mat=dst.materials[0];mat.name='AFN73_COMPLETE_SOURCE4K_SKIN' if HIGH_SOURCE else 'AFN73_COMPLETE_AUTHORED_SKIN';skin=mat.node_tree.nodes['Group'].node_tree;replacements=[]
    for leaf,kind in [('tex_Skin_Height.<UDIM>','Skin_Height'),('tex_Skin_Roughness.<UDIM>','Skin_Roughness'),('tex_Light_Skin_Color.<UDIM>','Light_Skin_Color')]:
        node=skin.nodes[leaf];assert node.image is None and not node.inputs['Vector'].is_linked;new=skin.nodes.new('ShaderNodeGroup');new.name='AFN73_MAP_'+kind;new.node_tree=lookup(kind);links=[l for l in skin.links if l.from_node==node];assert links
        for link in links:
            assert link.from_socket.name=='Color';target=link.to_socket;skin.links.remove(link);skin.links.new(new.outputs['Color'],target)
        replacements.append({'sourcePlaceholder':leaf,'kind':kind,'replacement':new.node_tree.name,'sourceTextureControlsUnchanged':True})
    assignments=[]
    for n in m.native_names():
        o=bpy.data.objects[n]
        for i,old in enumerate(o.data.materials):
            if old and old.name=='AFN57_CANONICAL_SKIN':o.data.materials[i]=mat;assignments.append({'object':n,'slot':i})
    assert assignments and mat.displacement_method=='BUMP' and render.lights()==lights
    s=bpy.context.scene;m.shade.settings();m.k.b.camera('face');s.camera.data.lens=85;s['AFN73_scope']='Complete source CC0 material with exact native source masks and verified flat-map UV leaves, author settings unchanged; inactive pigment/age placeholders not qualified. BUMP only, no geometry displacement. Appearance/contact/runtime unaccepted.';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    save(TAG+'-build-summary.json',{'source':str(SRC),'sourceSha256':sha(SRC),'output':str(OUT),'outputSha256':sha(OUT),'outputBytes':OUT.stat().st_size,'originalMaterialSource':str(D/'char.blend'),'originalMaterialSourceSha256':sha(D/'char.blend'),'material':mat.name,'displacementMethod':mat.displacement_method,'restoredMasks':list(MASKS),'leafReplacements':replacements,'original4kSourceBytesUsed':HIGH_SOURCE,'sourceTextures':RAW_TEXTURES,'sourceControlOrShaderParameterRetuning':False,'geometryOrHairEyeLightingExposureChanges':False,'assignments':assignments,'scope':'Complete source shader semantics at its fixed supplied controls, with original native masks and three effective flat-image leaves. Missing dark/age placeholder branches remain inactive and unqualified; view-dependent source approximations are retained, not asserted as physical ground truth.','secondsBeforePilot':time.time()-tick})
    pilot('face');pilot('body-face');print('R73_COMPLETE_SKIN_PILOTS_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
