"""Use source eye alpha and bake authored facial hair out of legacy systems.

The body/morph/UV/skin/light state is held fixed. Same-topology surface delta
maps canonical facial-hair data to the supplied female morph. No cross-model
closest-point retarget, new root placement or procedural replacement groom.
"""
from pathlib import Path
import bpy,importlib.util,numpy as np,json,time
sp=importlib.util.spec_from_file_location('repair57',Path(__file__).with_name('build-female-next-r0057-coherent-preview.py'))
k=importlib.util.module_from_spec(sp);sp.loader.exec_module(k)
b=k.b;f=k.f;E=k.E;SRC=b.S/'aevrynd-female-next-r0057-a-coherent-female-foundation.blend';OUT=b.S/'aevrynd-female-next-r0057-b-native-facial-hair-foundation.blend'
def save(n,x):(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def main():
    tick=time.time();a=json.loads((E/'a-build-summary.json').read_text());assert b.sha(SRC)==a['outputSha256']
    bpy.ops.wm.open_mainfile(filepath=str(SRC));body=bpy.data.objects['AFN57_CC0_COHERENT_FEMALE_BODY'];stage=f.v.stage();bodyVertices=np.array([v.co[:] for v in body.data.vertices]);bodyUV=np.array([x.uv[:] for x in body.data.uv_layers['VitruvianUV.UDIM'].data]);female=np.array([v.co[:] for v in body.data.shape_keys.key_blocks['AFN57_Supplied_Female_Morph'].data]);oldHair=bpy.data.objects['AFN57_CANONICAL_BOB_GUIDES'];oldPositions=np.array([p.vector[:] for p in oldHair.data.position_data]);oldRadii=np.array([p.value for p in oldHair.data.attributes['radius'].data])
    bpy.context.view_layer.objects.active=body;body.select_set(True)
    while len(body.particle_systems):body.particle_systems.active_index=0;bpy.ops.object.particle_system_remove()
    eye=bpy.data.materials['AFN57_COMBINED_SCLERA_CORNEA_APPROXIMATION'];tree=eye.node_tree;tex=tree.nodes['SuppliedScleraColour'];mix=next(n for n in tree.nodes if n.type=='MIX_SHADER');invert=tree.nodes.new('ShaderNodeMath');invert.operation='SUBTRACT';invert.name='AFN57_SourceAuthoredCorneaMask';invert.inputs[0].default_value=1;tree.links.new(tex.outputs['Alpha'],invert.inputs[1]);tree.links.new(invert.outputs[0],mix.inputs[0])
    data=np.load(E/'a-canonical-female-data.npz');P=data['canonical'];F=data['female'];body.data.calc_loop_triangles();tri=np.array([list(t.vertices) for t in body.data.loop_triangles if t.material_index in (4,5) and P[list(t.vertices),2].min()>1.40],dtype='i4');used,inv=np.unique(tri,return_inverse=True)
    cage=bpy.data.objects['AFN57_CANONICAL_SKIN_MORPH_CAGE'];assert len(cage.data.vertices)==len(used);cage.data.vertices.foreach_set('co',P[used].astype('f4').ravel());cage.data.update();rows=[];arrays={}
    for label in ('lashes','brows'):
        src=np.load(E/('canonical-object-space-'+label+'.npz'));q=src['positions'];counts=src['counts'];info=json.loads((E/('canonical-object-space-'+label+'.json')).read_text())
        hm=bpy.data.meshes.new('AFN57_'+label.upper()+'_MORPH_CARRIER');hm.from_pydata(q.tolist(),[],[]);hm.update();carrier=bpy.data.objects.new(hm.name,hm);bpy.context.scene.collection.objects.link(carrier);mod=carrier.modifiers.new('AFN57_EXACT_CANONICAL_MORPH','SURFACE_DEFORM');mod.target=cage
        bpy.context.view_layer.objects.active=carrier;carrier.select_set(True);bpy.ops.object.surfacedeform_bind(modifier=mod.name);assert mod.is_bound
        cage.data.vertices.foreach_set('co',F[used].astype('f4').ravel());cage.data.update();bpy.context.view_layer.update();ev=carrier.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();Q=np.array([v.co[:] for v in m.vertices],dtype='f4');ev.to_mesh_clear()
        d=bpy.data.hair_curves.new('AFN57_NATIVE_'+label.upper());d.add_curves(counts.tolist());d.position_data.foreach_set('vector',Q.ravel());d.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',np.full(len(Q),info['sourceRadiusM'],dtype='f4'));d.attributes.new('curve_type','INT8','CURVE').data.foreach_set('value',[1]*len(counts));d.attributes.new('material_index','INT','CURVE').data.foreach_set('value',[0]*len(counts));d.materials.append(bpy.data.materials['AFN57_CANONICAL_BROW_LASH_AND_HAIR'])
        ob=bpy.data.objects.new(d.name,d);bpy.context.scene.collection.objects.link(ob);ob.matrix_world=body.matrix_world.copy();ob['scope']='Baked original authored facial hair with same-canonical female surface delta. Independently editable, source radii retained. Contacts, blinking and dynamics not accepted.'
        arrays[label+'Positions']=Q;arrays[label+'Counts']=counts;arrays[label+'Radii']=np.full(len(Q),info['sourceRadiusM'],dtype='f4');rows.append({'object':ob.name,'curves':len(counts),'points':len(Q),'radiusLocalM':info['sourceRadiusM'],'maximumFemaleSurfaceShiftM':float(np.linalg.norm(Q-q,axis=1).max())})
        carrier.hide_render=True;carrier.hide_set(True);cage.data.vertices.foreach_set('co',P[used].astype('f4').ravel());cage.data.update()
    cage.data.vertices.foreach_set('co',F[used].astype('f4').ravel());cage.data.update();bpy.context.view_layer.update()
    assert np.array_equal(bodyVertices,np.array([v.co[:] for v in body.data.vertices])) and np.array_equal(female,np.array([v.co[:] for v in body.data.shape_keys.key_blocks['AFN57_Supplied_Female_Morph'].data]))
    assert np.array_equal(bodyUV,np.array([x.uv[:] for x in body.data.uv_layers['VitruvianUV.UDIM'].data])) and f.v.stage()==stage
    assert np.array_equal(oldPositions,np.array([p.vector[:] for p in oldHair.data.position_data])) and np.array_equal(oldRadii,np.array([p.value for p in oldHair.data.attributes['radius'].data]))
    np.savez_compressed(E/'b-native-facial-hair.npz',**arrays)
    b.camera('face');bpy.context.scene.camera.data.lens=85;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    save('b-build-summary.json',{'source':str(SRC),'sourceSha256':b.sha(SRC),'output':str(OUT),'outputSha256':b.sha(OUT),'nativeFacialHair':rows,
        'removedLegacyParticleSystems':True,'bodyNativeFemaleCoordinatesUVTransformAndBobGuidesExact':True,'skinAndStageUnchanged':True,
        'eyeMaterialRepair':'Original Sclera_Color alpha0..1 defines the corneal mix; guessed normal-angle mask disconnected. Existing one-interface optical approximation retained, no full eye acceptance.',
        'scope':'Candidate foundation function repair and appearance review only; no contacts, articulated rig, clothing, dynamics or runtime acceptance.','status':'PENDING_FULL_VISUAL_AND_REOPEN_REVIEW','seconds':time.time()-tick})
    f.E=E;f.render('b-coherent',('face','oblique','profile'));k.k.k.k.k.a.i.ch.review.extras('b-coherent',E)
    print('R57_NATIVE_FACIAL_HAIR_PREVIEW_READY',len(rows),time.time()-tick,flush=True)

if __name__=='__main__':main()
