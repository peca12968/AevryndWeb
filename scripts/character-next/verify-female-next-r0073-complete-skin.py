"""Independent geometry, source mask, shader semantics and flat-leaf readback."""
from pathlib import Path
import bpy,numpy as np,json,hashlib,sys,time,importlib.util
def module(n,p):
    s=importlib.util.spec_from_file_location(n,Path(__file__).with_name(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
q=module('verify73build','build-female-next-r0073-complete-skin.py');v=module('verify73mesh','verify-female-next-r0061-complete-groom.py')
HAIR=('AFN68_MAIN_RENDER_CURVES','AFN68_FLYAWAY_RENDER_CURVES','AFN57_NATIVE_BROWS','AFN57_NATIVE_LASHES')
def digest(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def value(v):
    if isinstance(v,(str,int,float,bool)):return v
    try:return list(v)
    except:return str(v)
def props(n):
    out={}
    for p in n.bl_rna.properties:
        if p.is_readonly or p.type not in ('BOOLEAN','INT','FLOAT','ENUM','STRING') or p.identifier in ('name','label','location','width','height','dimensions','color','select','hide','show_options','show_preview','show_texture','use_custom_color'):continue
        out[p.identifier]=value(getattr(n,p.identifier))
    return out
def tree(t):
    nodes={}
    for n in t.nodes:
        a={'type':n.bl_idname,'properties':props(n),'inputs':[(s.name,value(s.default_value)) for s in n.inputs if hasattr(s,'default_value')],'outputs':[(s.name,value(s.default_value)) for s in n.outputs if hasattr(s,'default_value')]}
        if n.type=='GROUP':a['group']=tree(n.node_tree)
        if n.type=='VALTORGB':a['ramp']={'mode':n.color_ramp.color_mode,'interpolation':n.color_ramp.interpolation,'hue':n.color_ramp.hue_interpolation,'elements':[(e.position,list(e.color)) for e in n.color_ramp.elements]}
        if n.type=='CURVE_RGB':a['curves']={'points':[[(list(p.location),p.handle_type) for p in c.points] for c in n.mapping.curves],'black':list(n.mapping.black_level),'white':list(n.mapping.white_level),'extend':n.mapping.extend}
        if n.type=='TEX_IMAGE':a['image']=n.image.filepath if n.image else None
        assert n.bl_idname!='ShaderNodeScript'
        nodes[n.name]=a
    assert not t.animation_data or not t.animation_data.drivers
    return {'nodes':nodes,'links':sorted([(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in t.links])}
REPLACEMENTS={'tex_Skin_Height.<UDIM>':'AFN73_MAP_Skin_Height','tex_Skin_Roughness.<UDIM>':'AFN73_MAP_Skin_Roughness','tex_Light_Skin_Color.<UDIM>':'AFN73_MAP_Light_Skin_Color'}
def compare_tree(a,b,path='root'):
    extras=set(b['nodes'])-set(a['nodes']);assert extras==(set(REPLACEMENTS.values()) if path=='root/Group' else set()),(path,extras)
    for name,row in a['nodes'].items():
        current=b['nodes'][name];left={k:x for k,x in row.items() if k!='group'};right={k:x for k,x in current.items() if k!='group'};assert left==right,(path,name)
        if 'group' in row:compare_tree(row['group'],current['group'],path+'/'+name)
    links=a['links']
    if path=='root/Group':links=sorted([(REPLACEMENTS.get(f,f),fs,t,ts) for f,fs,t,ts in links])
    assert links==b['links'],path
def input_expr(s):
    return output_expr(s.links[0].from_socket) if s.is_linked else value(s.default_value)
def output_expr(s):
    n=s.node
    if n.type=='GROUP':
        out=next(x for x in n.node_tree.nodes if x.type=='GROUP_OUTPUT' and x.is_active_output);return input_expr(out.inputs[s.name])
    if n.type=='TEX_IMAGE':return ['IMAGE',n.image.filepath.replace('\\','/').rsplit('/',1)[-1],n.image.colorspace_settings.name,n.interpolation,n.extension,s.name,input_expr(n.inputs['Vector'])]
    if n.type=='UVMAP':return ['UV',n.uv_map]
    if n.type=='SEPXYZ':return ['SEP',s.name,input_expr(n.inputs[0])]
    if n.type=='MATH':return ['MATH',n.operation,n.use_clamp,[input_expr(x) for x in n.inputs]]
    if n.type=='MIX_RGB':return ['MIX_RGB',n.blend_type,n.use_clamp,n.use_alpha,[input_expr(x) for x in n.inputs]]
    raise AssertionError(('Unexpected leaf sampling expression',n.bl_idname,n.name))
def mesh_native(o):
    x=v.mesh_signature(o);x.pop('materials');return x
def world(o):
    d=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;P=q.m.base.array3(d.position_data,'vector').astype('f8');A=np.array(o.matrix_world);return P@A[:3,:3].T+A[:3,3]
def posed():
    out={};v.raise_subdivision()
    for f in (1,13,49):
        bpy.context.scene.frame_set(f);bpy.context.view_layer.update();row={}
        for n in q.m.native_names():
            m=q.m.k.mesh(bpy.data.objects[n]);assert np.isfinite(m['V']).all();row[n]={'V':digest(m['V']),'T':digest(m['T']),'vertices':len(m['V']),'triangles':len(m['T'])}
        for n in HAIR:row[n]={'positions':digest(world(bpy.data.objects[n]))}
        out[str(f)]=row
    return out
def rig():
    o=bpy.data.objects['AFN69_BODY_CONTROLS'];return {'bones':[(b.name,b.parent.name if b.parent else None,np.array(b.matrix_local).tolist()) for b in o.data.bones],'weights':{n:digest(np.array([(i,g.group,g.weight) for i,p in enumerate(bpy.data.objects[n].data.vertices) for g in p.groups],dtype='f8')) for n in q.m.native_names()}}
def verify_masks():
    ref=json.loads((q.E.parent/'r0057-coherent-foundation/canonical-library.json').read_text());assert q.sha(Path(ref['output']))==ref['sha256']
    with bpy.data.libraries.load(ref['output'],link=False) as (src,dst):dst.objects=['cm_vitruvian']
    source=dst.objects[0];me=source.data;native_corners={(p.index,int(me.loops[i].vertex_index)):i for p in me.polygons for i in p.loop_indices};arrays={};rows=[]
    for name in q.MASKS:
        a=me.color_attributes[name];x=np.empty((len(a.data),4),'f4');a.data.foreach_get('color',x.ravel());arrays[name]=(a.domain,x)
    for n in q.m.native_names():
        d=bpy.data.objects[n].data;ids=np.empty(len(d.vertices),'i4');d.attributes['AFN60_NativeVertexID'].data.foreach_get('value',ids);faces=np.empty(len(d.polygons),'i4');d.attributes['AFN60_NativeFaceID'].data.foreach_get('value',faces);corners=[native_corners[(int(faces[p.index]),int(ids[d.loops[i].vertex_index]))] for p in d.polygons for i in p.loop_indices]
        for name,(domain,x) in arrays.items():
            a=d.color_attributes[name];actual=np.empty((len(a.data),4),'f4');a.data.foreach_get('color',actual.ravel());expected=x[ids if domain=='POINT' else corners];assert np.array_equal(actual,expected)
            rows.append({'object':n,'mask':name,'domain':domain,'count':len(actual),'exactSourceNativeCorrespondence':True,'sha256':digest(actual)})
    bpy.data.objects.remove(source,do_unlink=True)
    return rows
def main():
    tick=time.time();assert q.sha(q.SRC)==q.SOURCE_SHA;bpy.ops.wm.open_mainfile(filepath=str(q.SRC));bpy.context.scene.frame_set(1);names=q.m.native_names();native={n:mesh_native(bpy.data.objects[n]) for n in names};hair={n:q.m.k.v59.native_curves(bpy.data.objects[n]) for n in HAIR};materials={x.name:q.m.k.f.v.v32.material_signature(x) for x in bpy.data.materials if x.use_nodes};rigstate=rig();lights=q.render.lights();view=[bpy.context.scene.view_settings.exposure,bpy.context.scene.view_settings.view_transform,bpy.context.scene.view_settings.look]
    original=bpy.data.materials['AFN57_CANONICAL_SKIN'].node_tree;p=original.nodes['Principled BSDF'];leaf_expr={'Light_Skin_Color':input_expr(p.inputs['Base Color']),'Skin_Roughness':input_expr(p.inputs['Roughness']),'Skin_Height':input_expr(original.nodes['Bump'].inputs['Height'])};baseposed=posed()
    with bpy.data.libraries.load(str(q.D/'char.blend'),link=False) as (src,dst):dst.materials=['UDIM.Skin']
    source_tree=tree(dst.materials[0].node_tree);ref=json.loads((q.E/(q.TAG+'-build-summary.json')).read_text());path=Path(ref['output'])
    if '--history' in sys.argv:path=q.R/'sites-engine-journey/assets-source/aevrynd-character/female-next'/path.name
    assert q.sha(path)==ref['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(path));bpy.context.scene.frame_set(1)
    assert native=={n:mesh_native(bpy.data.objects[n]) for n in names};assert hair=={n:q.m.k.v59.native_curves(bpy.data.objects[n]) for n in HAIR};assert materials=={n:q.m.k.f.v.v32.material_signature(bpy.data.materials[n]) for n in materials};assert rig()==rigstate and q.render.lights()==lights;assert view==[bpy.context.scene.view_settings.exposure,bpy.context.scene.view_settings.view_transform,bpy.context.scene.view_settings.look]
    assert posed()==baseposed;mat=bpy.data.materials[ref['material']];assert mat.displacement_method=='BUMP';compare_tree(source_tree,tree(mat.node_tree));skin=mat.node_tree.nodes['Group'].node_tree
    source_map_checks=[]
    for kind,expected in leaf_expr.items():
        assert output_expr(skin.nodes['AFN73_MAP_'+kind].outputs['Color'])==expected,kind
        if q.HIGH_SOURCE:
            original={x['file']:x for x in json.loads((q.E.parent/'r0057-coherent-foundation/texture-derivatives.json').read_text())['files']}
            for node in skin.nodes['AFN73_MAP_'+kind].node_tree.nodes:
                if node.type!='TEX_IMAGE':continue
                image=node.image;normalized=image.filepath.replace('\\','/');filename=normalized.rsplit('/',1)[-1];assert filename in original and normalized=='//study-vitruvian-textures-source4k/'+filename and list(image.size)==original[filename]['sourceSize']==[4096,4096];p=Path(bpy.path.abspath(image.filepath));assert q.sha(p)==original[filename]['sourceSHA256'];source_map_checks.append({'file':filename,'actualSize':list(image.size),'sha256':q.sha(p),'exactOriginalPublishedSourceBytes':True,'workingDerivativeSize':original[filename]['size']})
    # Inspect the saved asset before the checker appends its reference object.
    # That append can retain temporary library IDs which are not in the asset.
    external=[];packed=0
    for im in bpy.data.images:
        if im.packed_file:packed+=1
        elif im.source=='FILE':
            p=Path(bpy.path.abspath(im.filepath));assert im.filepath.startswith('//') and p.exists();external.append({'relative':im.filepath,'sha256':q.sha(p)})
    assert len(external)==(27 if q.HIGH_SOURCE else 15) and not bpy.data.libraries and not bpy.app.handlers.frame_change_pre and not bpy.app.handlers.frame_change_post
    saved_dependencies={'externalImages':len(external),'linkedLibraries':[],'frameChangeHandlers':[]};masks=verify_masks();reference_import={'libraries':[(x.name,x.filepath) for x in bpy.data.libraries],'externalFileImageCount':sum(1 for x in bpy.data.images if x.source=='FILE' and not x.packed_file)}
    q.save(q.TAG+('-history-readback.json' if '--history' in sys.argv else '-independent-readback.json'),{'status':'PASS_SAVED_SOURCE_MASKS_SHADER_SEMANTICS_AND_UNCHANGED_GEOMETRY_SCOPE','source':str(path),'sha256':q.sha(path),'originalNativeMeshKeysUVAndAllOldMaterialsExact':True,'actualFiveMeshAndFourCurveGeometriesExactAtFrames':[1,13,49],'baselinePosedGeometry':baseposed,'rigBonesWeightsLightsExposureExact':True,'sourceShaderAllOriginalNodesParametersSettingsAndLinksExactExceptDocumentedThreeLeafConnections':True,'threeLeafUVSelectionFilteringColorSpaceExpressionsEqualCanonical':True,'textureSampleDataEqualCanonicalWorkingMaps':not q.HIGH_SOURCE,'original4kSourceBytesChecked':source_map_checks,'displacementMethod':'BUMP','sourceMasksIndependentlyReconstructed':masks,'externalTextures':external,'packedImages':packed,'savedAssetDependenciesBeforeCheckerReferenceAppend':saved_dependencies,'temporaryCheckerReferenceImportStateNotSavedAssetDependencies':reference_import,'inactiveSourceDarkAgeBranchesNotCertified':True,'wholeAppearanceOrNaturalMotionOrContactOrRuntimeAccepted':False,'seconds':time.time()-tick});print('R73_SOURCE_SKIN_READBACK_PASS',q.TAG,time.time()-tick,reference_import,flush=True)
if __name__=='__main__':main()
