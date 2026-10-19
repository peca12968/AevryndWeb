"""One coherent CC0 female foundation preview under the existing review stage.

Canonical topology, supplied female morph and its own UV/texture set are kept
together. Hair follows the exact same-topology female surface delta, never a
nearest-point fit onto the old Aevrynd head. No addon/embedded code is imported.
This is a complete-body look-development study, not an adopted runtime asset.
"""
from pathlib import Path
import bpy,importlib.util,numpy as np,json,time,sys
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
sp=importlib.util.spec_from_file_location('coherent57',Path(__file__).with_name('build-female-next-r0054-clump-volume.py'))
k=importlib.util.module_from_spec(sp);sp.loader.exec_module(k)
b=k.b;f=k.f;R=b.R;D=R/'Reference/character/charmorph-vitruvian-cc0';TEX=b.S/'study-vitruvian-textures';E=R/'Evidence/character-female-next/r0057-coherent-foundation'
OUT=b.S/'aevrynd-female-next-r0057-a-coherent-female-foundation.blend'
PORTABLE='--portable-native' in sys.argv
CLEAN='--clean-native' in sys.argv or PORTABLE;TAG='d' if PORTABLE else ('c' if CLEAN else 'a')
if CLEAN:OUT=b.S/'aevrynd-female-next-r0057-c-clean-native-foundation.blend'
if PORTABLE:OUT=b.S/'aevrynd-female-next-r0057-d-portable-native-foundation.blend'
CURVE_TEMPLATE=None
def save(n,x):(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def attr(d,name,kind,domain):return d.attributes.get(name) or d.attributes.new(name,kind,domain)
def curve_data(name,counts):
    if not PORTABLE:
        d=bpy.data.hair_curves.new(name);d.add_curves(counts);return d
    d=CURVE_TEMPLATE.copy();d.name=name;d.use_fake_user=False;d.resize_curves([int(counts[0])]);d.add_curves([int(x) for x in counts[1:]]);return d

def texture(tree,name,kind,tile,uv,tiled=False):
    if tiled and PORTABLE:
        previous=None;coord=tree.nodes.new('ShaderNodeSeparateXYZ');tree.links.new(uv.outputs['UV'],coord.inputs['Vector']);floor=tree.nodes.new('ShaderNodeMath');floor.operation='FLOOR';tree.links.new(coord.outputs['X'],floor.inputs[0])
        for number in range(1001,1005):
            im=bpy.data.images.load(str(TEX/f'{kind}.{number}.exr'),check_existing=True)
            if kind in ('Skin_Roughness','Skin_Height'):im.colorspace_settings.name='Non-Color'
            n=tree.nodes.new('ShaderNodeTexImage');n.name=name+'_'+str(number);n.image=im;n.extension='REPEAT';tree.links.new(uv.outputs['UV'],n.inputs['Vector'])
            if previous is None:previous=n.outputs['Color'];last=n
            else:
                select=tree.nodes.new('ShaderNodeMath');select.operation='GREATER_THAN';select.inputs[1].default_value=number-1001-.5;tree.links.new(floor.outputs[0],select.inputs[0]);mix=tree.nodes.new('ShaderNodeMixRGB');tree.links.new(select.outputs[0],mix.inputs[0]);tree.links.new(previous,mix.inputs[1]);tree.links.new(n.outputs['Color'],mix.inputs[2]);previous=mix.outputs['Color'];last=mix
        return last
    p=TEX/f'{kind}.{tile}.exr';im=bpy.data.images.load(str(p),check_existing=True)
    if tiled:
        im.source='TILED';im.filepath=str(TEX/(kind+'.<UDIM>.exr'))
        for number in range(1002,1005):
            if number not in [t.number for t in im.tiles]:im.tiles.new(number)
        im.reload()
    if kind in ('Skin_Roughness','Skin_Height'):im.colorspace_settings.name='Non-Color'
    n=tree.nodes.new('ShaderNodeTexImage');n.name=name;n.image=im;n.interpolation='Linear'
    if tiled:tree.links.new(uv.outputs['UV'],n.inputs['Vector'])
    else:
        offset=tree.nodes.new('ShaderNodeVectorMath');offset.operation='SUBTRACT';offset.inputs[1].default_value=(tile-1001,0,0);tree.links.new(uv.outputs['UV'],offset.inputs[0]);tree.links.new(offset.outputs['Vector'],n.inputs['Vector'])
    return n

def principled(name,color,rough):
    m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough
    uv=m.node_tree.nodes.new('ShaderNodeUVMap');uv.uv_map='VitruvianUV.UDIM';return m,p,uv

def materials(cap):
    skin,p,uv=principled('AFN57_CANONICAL_SKIN',(.5,.3,.23),.45);t=skin.node_tree
    colour=texture(t,'SuppliedSkinColour','Light_Skin_Color',1001,uv,True);rough=texture(t,'SuppliedSkinRoughness','Skin_Roughness',1001,uv,True);height=texture(t,'SuppliedSkinHeight','Skin_Height',1001,uv,True)
    t.links.new(colour.outputs['Color'],p.inputs['Base Color']);t.links.new(rough.outputs['Color'],p.inputs['Roughness']);bump=t.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.20;bump.inputs['Distance'].default_value=.0003;t.links.new(height.outputs['Color'],bump.inputs['Height']);t.links.new(bump.outputs['Normal'],p.inputs['Normal'])
    p.inputs['IOR'].default_value=1.4;p.inputs['Subsurface Weight'].default_value=.12;p.inputs['Subsurface Scale'].default_value=.001
    mouth,p,uv=principled('AFN57_CANONICAL_MOUTH',(.4,.1,.1),.28);tex=texture(mouth.node_tree,'SuppliedMouthColour','Mouth_Color',1008,uv);mouth.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color']);p.inputs['Subsurface Weight'].default_value=.04
    iris,p,uv=principled('AFN57_CANONICAL_IRIS',(.14,.07,.02),.30);tex=texture(iris.node_tree,'SuppliedIrisColour','Iris_Color',1007,uv);iris.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color'])
    pupil,_,_=principled('AFN57_CANONICAL_PUPIL',(.001,.001,.001),.30)
    # Reuse our existing refracting-interface material only as a look-dev
    # approximation on the original combined sclera/cornea component.
    eye=cap;eye.name='AFN57_COMBINED_SCLERA_CORNEA_APPROXIMATION';tree=eye.node_tree;out=next(n for n in tree.nodes if n.type=='OUTPUT_MATERIAL');capSocket=out.inputs['Surface'].links[0].from_socket
    sclera=tree.nodes.new('ShaderNodeBsdfPrincipled');sclera.inputs['Roughness'].default_value=.25;uv=tree.nodes.new('ShaderNodeUVMap');uv.uv_map='VitruvianUV.UDIM';tex=texture(tree,'SuppliedScleraColour','Sclera_Color',1005,uv);tree.links.new(tex.outputs['Color'],sclera.inputs['Base Color'])
    geo=tree.nodes.new('ShaderNodeNewGeometry');normal=tree.nodes.new('ShaderNodeVectorTransform');normal.vector_type='NORMAL';normal.convert_from='WORLD';normal.convert_to='OBJECT';tree.links.new(geo.outputs['Normal'],normal.inputs['Vector']);split=tree.nodes.new('ShaderNodeSeparateXYZ');tree.links.new(normal.outputs['Vector'],split.inputs['Vector'])
    mask=tree.nodes.new('ShaderNodeMath');mask.operation='LESS_THAN';mask.inputs[1].default_value=-.78;tree.links.new(split.outputs['Y'],mask.inputs[0]);mix=tree.nodes.new('ShaderNodeMixShader');tree.links.new(mask.outputs[0],mix.inputs[0]);tree.links.new(sclera.outputs['BSDF'],mix.inputs[1]);tree.links.new(capSocket,mix.inputs[2]);tree.links.new(mix.outputs[0],out.inputs['Surface'])
    if CLEAN:
        mask=tree.nodes.new('ShaderNodeMath');mask.operation='SUBTRACT';mask.name='AFN57_SOURCE_CORNEA_ALPHA';mask.inputs[0].default_value=1;tree.links.new(tex.outputs['Alpha'],mask.inputs[1]);tree.links.new(mask.outputs[0],mix.inputs[0])
    hair,_,_=principled('AFN57_CANONICAL_BROW_LASH_AND_HAIR',(.055,.023,.010),.38)
    wet,p,_=principled('AFN57_CANONICAL_WETLINE',(.40,.15,.12),.11);p.inputs['Coat Weight'].default_value=1.
    return [iris,mouth,pupil,eye,skin,skin,hair,wet]

def main():
    global CURVE_TEMPLATE
    tick=time.time();library=json.loads((E/'canonical-library.json').read_text());assert b.sha(Path(library['output']))==library['sha256']
    deriv=json.loads((E/'texture-derivatives.json').read_text())
    for row in deriv['files']:assert b.sha(TEX/row['file'])==row['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(k.SRC));stage=f.v.stage();cap=bpy.data.objects['AFN30_L_Cornea'].data.materials[0].copy();cap.use_fake_user=True
    if PORTABLE:
        CURVE_TEMPLATE=bpy.data.objects[k.k.OLD].data.copy();CURVE_TEMPLATE.name='AFN57_NATIVE_CURVE_FORMAT_TEMPLATE';CURVE_TEMPLATE.remove_curves(indices=list(range(1,len(CURVE_TEMPLATE.curves))));CURVE_TEMPLATE.surface=None;CURVE_TEMPLATE.materials.clear();CURVE_TEMPLATE.use_fake_user=True
        for attribute in list(CURVE_TEMPLATE.attributes):
            if attribute.name not in ('position','radius','curve_type','material_index') and not attribute.is_required:CURVE_TEMPLATE.attributes.remove(attribute)
    # Keep exactly the same camera/lights/world; construct a separate complete
    # candidate instead of silently replacing any current working character.
    for o in list(bpy.context.scene.objects):
        if o.type not in ('CAMERA','LIGHT'):bpy.data.objects.remove(o,do_unlink=True)
    bpy.data.orphans_purge(do_recursive=True)
    if CLEAN:
        raw=np.load(E/'canonical-mesh-data.npz');offset=np.r_[0,np.cumsum(raw['polygonCounts'])];faces=[raw['corners'][offset[i]:offset[i+1]].tolist() for i in range(len(offset)-1)]
        mesh=bpy.data.meshes.new('AFN57_PURE_CANONICAL_BODY');mesh.from_pydata(raw['canonical'].tolist(),[],faces);mesh.update();uv=mesh.uv_layers.new(name='VitruvianUV.UDIM');uv.data.foreach_set('uv',raw['uv'].ravel());body=bpy.data.objects.new('AFN57_CC0_COHERENT_FEMALE_BODY',mesh);bpy.context.scene.collection.objects.link(body)
        body.shape_key_add(name='Basis');femaleKey=body.shape_key_add(name='AFN57_Supplied_Female_Morph');femaleKey.data.foreach_set('co',raw['female'].astype('f4').ravel());femaleKey.value=1;beforeIndices=raw['materials']
        assert np.array_equal(np.array([v for p in mesh.polygons for v in p.vertices]),raw['corners']) and np.array_equal(np.array([u.uv[:] for u in uv.data],dtype='f4'),raw['uv'])
    else:
        with bpy.data.libraries.load(library['output'],link=False) as (source,target):target.objects=['cm_vitruvian']
        body=target.objects[0];bpy.context.scene.collection.objects.link(body);body.name='AFN57_CC0_COHERENT_FEMALE_BODY';beforeIndices=np.array([p.material_index for p in body.data.polygons],dtype='i4')
    body.hide_render=False;body.hide_set(False);mats=materials(cap);body.data.materials.clear()
    for mat in mats:body.data.materials.append(mat)
    body.data.polygons.foreach_set('material_index',beforeIndices)
    for poly in body.data.polygons:poly.use_smooth=True
    for ps in body.particle_systems:ps.settings.material=7
    P=np.load(D/'Default.npy');morph=np.load(D/'Gender_Female.npz');F=P.copy();F[morph['idx']]+=morph['delta']
    eyes=np.array([vi for p in body.data.polygons if p.material_index==3 for vi in p.vertices]);eyes=np.unique(eyes);eyeCentre=F[eyes].mean(0)
    reference=json.loads((R/'Evidence/character-female-next/r0055-authored-cc0-bob/b-registration-landmarks.json').read_text());targetEye=np.array(reference['targetEyes']).mean(0)
    scale=reference['targetTop']/float(F[:,2].max());matrix=Matrix.Diagonal((scale,scale,scale,1));matrix.translation=(0,float(targetEye[1]-eyeCentre[1]*scale),0);body.matrix_world=matrix
    sub=body.modifiers.new('AFN57_NATIVE_SUBDIVISION','SUBSURF');sub.levels=1;sub.render_levels=2
    # Canonical hair deformation uses exact source vertex correspondence.
    body.data.calc_loop_triangles();tri=np.array([list(t.vertices) for t in body.data.loop_triangles if t.material_index in (4,5) and P[list(t.vertices),2].min()>1.40],dtype='i4');used,inv=np.unique(tri,return_inverse=True)
    cm=bpy.data.meshes.new('AFN57_CANONICAL_SKIN_MORPH_CAGE');cm.from_pydata(P[used].tolist(),[],inv.reshape(-1,3).tolist());cm.update();cage=bpy.data.objects.new(cm.name,cm);bpy.context.scene.collection.objects.link(cage)
    raw=np.load(D/'Bob.npz',allow_pickle=False);assert np.all(raw['cnt']==16);guides=raw['data'].reshape(-1,16,3)
    sourceRootDistances=[]
    if PORTABLE:
        tree=BVHTree.FromPolygons(P.tolist(),tri.tolist(),all_triangles=True);Q=guides.copy()
        for i,root in enumerate(guides[:,0]):
            foot,normal,index,distance=tree.find_nearest(Vector(root));A=P[tri[index]];bc2=np.linalg.lstsq(np.column_stack((A[1]-A[0],A[2]-A[0])),np.array(foot)-A[0],rcond=None)[0];bc=np.clip(np.r_[1-bc2.sum(),bc2],0,1);bc/=bc.sum()
            Q[i]+=bc@(F[tri[index]]-A);sourceRootDistances.append(float(distance))
        carrier=None;Q=Q.astype('f4')
    else:
        hm=bpy.data.meshes.new('AFN57_CANONICAL_GUIDE_MORPH_CARRIER');hm.from_pydata(guides.reshape(-1,3).tolist(),[],[]);hm.update();carrier=bpy.data.objects.new(hm.name,hm);bpy.context.scene.collection.objects.link(carrier);mod=carrier.modifiers.new('AFN57_SAME_TOPOLOGY_FEMALE_MORPH','SURFACE_DEFORM');mod.target=cage
        bpy.context.view_layer.objects.active=carrier;carrier.select_set(True);bpy.ops.object.surfacedeform_bind(modifier=mod.name);assert mod.is_bound
        cm.vertices.foreach_set('co',F[used].astype('f4').ravel());cm.update();bpy.context.view_layer.update();ev=carrier.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();Q=np.array([v.co[:] for v in me.vertices],dtype='f4').reshape(guides.shape);ev.to_mesh_clear()
    d=curve_data('AFN57_CANONICAL_BOB_GUIDES',[16]*len(Q));d.position_data.foreach_set('vector',Q.ravel());attr(d,'radius','FLOAT','POINT').data.foreach_set('value',np.broadcast_to(np.linspace(.000055,.000009,16),(len(Q),16)).astype('f4').ravel());attr(d,'curve_type','INT8','CURVE').data.foreach_set('value',[1]*len(Q));attr(d,'material_index','INT','CURVE').data.foreach_set('value',[0]*len(Q));d.materials.append(mats[6])
    hair=bpy.data.objects.new(d.name,d);bpy.context.scene.collection.objects.link(hair);hair.matrix_world=matrix.copy();hair['scope']='Original canonical Bob248guides with exact same-topology female surface deformation. No child hairs, actual follicle/finite contacts, dynamics or runtime qualification.'
    facial=[];facialArrays={}
    if PORTABLE:
        for label in ('lashes','brows'):
            raw=np.load(E/('female-object-space-'+label+'.npz'));fq=raw['positions'];counts=raw['counts'];info=json.loads((E/('female-object-space-'+label+'.json')).read_text());assert info['suppliedFemaleMorphValue']==1
            fd=curve_data('AFN57_NATIVE_'+label.upper(),counts.tolist());fd.position_data.foreach_set('vector',fq.ravel());attr(fd,'radius','FLOAT','POINT').data.foreach_set('value',np.full(len(fq),info['sourceRadiusM'],dtype='f4'));attr(fd,'curve_type','INT8','CURVE').data.foreach_set('value',[1]*len(counts));attr(fd,'material_index','INT','CURVE').data.foreach_set('value',[0]*len(counts));fd.materials.append(mats[6]);face=bpy.data.objects.new(fd.name,fd);bpy.context.scene.collection.objects.link(face);face.matrix_world=matrix.copy()
            canonicalFace=np.load(E/('canonical-object-space-'+label+'.npz'))['positions'];facial.append({'object':face.name,'curves':len(counts),'points':len(fq),'radiusLocalM':info['sourceRadiusM'],'nativeFemalePoseShiftM':float(np.linalg.norm(fq-canonicalFace,axis=1).max()),'source':'Evaluated original ParticleHairKey.co_object at supplied female1; baked data only, no legacy system or SurfaceDeform in rendered scene.'});facialArrays[label+'Positions']=fq;facialArrays[label+'Counts']=counts;facialArrays[label+'Radii']=np.full(len(fq),info['sourceRadiusM'],dtype='f4')
        np.savez_compressed(E/'d-native-facial-hair.npz',**facialArrays)
    elif CLEAN:
        for label in ('lashes','brows'):
            raw=np.load(E/('canonical-object-space-'+label+'.npz'));q=raw['positions'];counts=raw['counts'];info=json.loads((E/('canonical-object-space-'+label+'.json')).read_text())
            cm.vertices.foreach_set('co',P[used].astype('f4').ravel());cm.update();fm=bpy.data.meshes.new('AFN57_TEMP_'+label);fm.from_pydata(q.tolist(),[],[]);fm.update();fo=bpy.data.objects.new(fm.name,fm);bpy.context.scene.collection.objects.link(fo);md=fo.modifiers.new('AFN57_CANONICAL_FEMALE_DELTA','SURFACE_DEFORM');md.target=cage;bpy.context.view_layer.objects.active=fo;fo.select_set(True);bpy.ops.object.surfacedeform_bind(modifier=md.name);assert md.is_bound
            cm.vertices.foreach_set('co',F[used].astype('f4').ravel());cm.update();bpy.context.view_layer.update();fe=fo.evaluated_get(bpy.context.evaluated_depsgraph_get());mm=fe.to_mesh();fq=np.array([v.co[:] for v in mm.vertices],dtype='f4');fe.to_mesh_clear()
            fd=bpy.data.hair_curves.new('AFN57_NATIVE_'+label.upper());fd.add_curves(counts.tolist());fd.position_data.foreach_set('vector',fq.ravel());fd.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',np.full(len(fq),info['sourceRadiusM'],dtype='f4'));fd.attributes.new('curve_type','INT8','CURVE').data.foreach_set('value',[1]*len(counts));fd.attributes.new('material_index','INT','CURVE').data.foreach_set('value',[0]*len(counts));fd.materials.append(mats[6]);face=bpy.data.objects.new(fd.name,fd);bpy.context.scene.collection.objects.link(face);face.matrix_world=matrix.copy();face['scope']='Original authored facial hair baked through exact canonical female surface delta. Static editable source data only; eyelid contact and blink not accepted.'
            facial.append({'object':face.name,'curves':len(counts),'points':len(fq),'radiusLocalM':info['sourceRadiusM'],'maximumFemaleDeltaM':float(np.linalg.norm(fq-q,axis=1).max())});facialArrays[label+'Positions']=fq;facialArrays[label+'Counts']=counts;facialArrays[label+'Radii']=np.full(len(fq),info['sourceRadiusM'],dtype='f4')
            bpy.data.objects.remove(fo,do_unlink=True);bpy.data.meshes.remove(fm)
        np.savez_compressed(E/'c-native-facial-hair.npz',**facialArrays)
    for o in (cage,carrier):
        if o:o.hide_render=True;o.hide_set(True);o['scope']='Hidden exact-source morph authoring data, not runtime or collision representation.'
    # Match the stage after normal scene-placement work; no light/exposure edit.
    assert f.v.stage()==stage
    for image in bpy.data.images:
        if image.filepath and str(TEX) in bpy.path.abspath(image.filepath):image.filepath=bpy.path.relpath(image.filepath,start=str(b.S))
    cap.use_fake_user=False
    if CURVE_TEMPLATE:CURVE_TEMPLATE.use_fake_user=False
    b.camera('face');bpy.context.scene.camera.data.lens=85;bpy.context.preferences.filepaths.save_version=0
    body['scope']='Coherent CC0 female foundation look-dev only. Source eyes/oral/body still combined; no accepted full rig, articulation, contacts or runtime.'
    bpy.context.scene['AFN57_status']='COMPLETE_BODY_FOUNDATION_LOOKDEV_STUDY_NOT_ADOPTED'
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    save(TAG+'-build-summary.json',{'revision':'female-next-r0057','output':str(OUT),'outputSha256':b.sha(OUT),'sourceCanonical':library,
        'previousGoalTurnClassification':'progress: r56target-native local/full-curve Comb pilots rejected; root/body integrity preserved but no natural full hair form.',
        'mainHypothesis':'A character whose head, female morph, eye/oral geometry, UV/skin data and hair share one canonical source is a more useful complete foundation than repeated incompatible fitting.',
        'sourceBodyVertices':len(P),'sourceBodyPolygons':len(body.data.polygons),'uniformSceneScale':scale,'sceneTranslationM':list(matrix.translation),
        'suppliedFemaleMorphValue':1,'nativeBrowAndLashSystems':library['particleSystems'],'hairGuides':len(Q),'hairPointsPerGuide':16,
        'hairFemaleMorphMaximumPointShiftM':float(np.linalg.norm(Q-guides,axis=2).max()),'bodyUV':'VitruvianUV.UDIM',
        'legacyParticleSystemsAbsent':len(body.particle_systems)==0,'pureSourceTopologyAndLoopUVReconstructed':CLEAN,'nativeFacialHair':facial,'sourceEyeAlphaMaskUsed':CLEAN,
        'portableNativeDataPath':PORTABLE,'tiledImageIDsAvoided':PORTABLE,'sourceBobRootDistanceRangeM':[min(sourceRootDistances),max(sourceRootDistances)] if sourceRootDistances else None,'headHairMorphScope':'Same canonical-source triangle female displacement, uniform per guide; preserves each original path, no cross-body target projection. Static study, not qualified binding.' if PORTABLE else 'Native same-topology surface morph',
        'shaderScope':'Own PBR/SSS nodes from source linear colour/roughness/height data. Existing owned one-interface cornea reused on a normal-defined cap of original combined eye geometry; approximate look-dev, not complete eye optical acceptance.',
        'stageUnchanged':True,'textureDerivatives':str(E/'texture-derivatives.json'),'textureExternalRelativePaths':True,
        'contact':'NOT_TESTED_PENDING_COMPLETE_APPEARANCE_REVIEW','rigClothesDynamicsRuntime':'NOT_QUALIFIED','status':'COHERENT_COMPLETE_BODY_FOUNDATION_PENDING_VISUAL_REVIEW','seconds':time.time()-tick})
    np.savez_compressed(E/(TAG+'-canonical-female-data.npz'),canonical=P,female=F,sourceMorphIndices=morph['idx'],sourceMorphDelta=morph['delta'],hairCanonical=guides,hairFemale=Q,bodyMatrix=np.array(matrix))
    f.E=E;f.render(TAG+'-coherent',('face','oblique','profile'));k.k.k.k.a.i.ch.review.extras(TAG+'-coherent',E)
    print('R57_COHERENT_PREVIEW_READY',len(P),len(Q),time.time()-tick,flush=True)

if __name__=='__main__':main()
