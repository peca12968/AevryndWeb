"""Artist-image-informed brow pilot, followed by spatial hair fibres.

The CC0 artist texture supplies silhouette and local flow evidence. A pilot
conforming card is explicitly diagnostic only, never accepted as 3D fibres.
The body, eye, skin, light and actual-width scalp groom remain untouched.
"""
import bpy,importlib.util,json,math,time,sys,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
spec=importlib.util.spec_from_file_location('v35',Path(__file__).with_name('verify-female-next-r0035-lid-rest.py'));v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
b=v.b;R=b.R;S=b.S;E=R/'Evidence/character-female-next/r0036-data-informed-brows'
SRC=S/'aevrynd-female-next-r0035-b-neutral-rest-review.blend'
TEX=S/'brows/makehuman-system-cc0/eyebrow001.png'
def save(n,x):(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def read(n):return json.loads((E/n).read_text(encoding='utf8'))
def state():
    names=[o.name for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render and not o.name.startswith('AFN36_')]
    hair=next(o for o in bpy.context.scene.objects if o.type=='CURVES' and not o.hide_render and not o.name.startswith('AFN36_'))
    p,r=v.hair_arrays(hair)
    return {'meshes':{n:v.g.signature(bpy.data.objects[n]) for n in names},'materials':v.materials(names),'skinFields':v.fields(bpy.data.objects[b.BODY]),'stage':v.stage(),
      'hair':{'name':hair.name,'positions':hashlib.sha256(p.tobytes()).hexdigest(),'radii':hashlib.sha256(r.tobytes()).hexdigest(),'matrix':b.matrix(hair.matrix_world),'materials':[v.v32.material_signature(m) for m in hair.data.materials]}}
def camera(view):b.camera(view);bpy.context.scene.camera.data.lens=85
def render(label,views=('face','oblique','profile')):
    s=bpy.context.scene;rows=[];s.render.resolution_x=s.render.resolution_y=800
    for view in views:
        camera(view);s.render.filepath=str(E/f'{label}-{view}.png');bpy.ops.render.render(write_still=True)
        rows.append({'view':view,'path':s.render.filepath,'cameraMatrix':b.matrix(s.camera.matrix_world),'lens':s.camera.data.lens,'resolution':[800,800],'stage':v.stage()})
    save(label+'-renders.json',rows)
def sample(bt,V,T,x,z):
    h,n,ti,d=bt.ray_cast(Vector((x,-.35,z)),Vector((0,1,0)),.5)
    if h is None or n.y>-.15:raise ValueError(('brow misses front skin',x,z))
    tri=V[T[ti]];co=np.linalg.lstsq(np.column_stack((tri[1]-tri[0],tri[2]-tri[0])),np.array(h)-tri[0],rcond=None)[0];bc=np.array((1-co.sum(),co[0],co[1]));assert bc.min()>-1e-4
    bc=np.maximum(0,bc);bc/=bc.sum();normal=np.array(n);normal/=np.linalg.norm(normal)
    return bc@tri,normal,int(ti),bc
def world_xz(px,py,side):
    # Top artist brow: medial x17 -> lateral x480; image y158..255.
    # Bottom donor kept separate for documentation, not blindly mirrored UVs.
    return side*(.0128+(px-17)*(.0495/463)),1.4910-(py-158)*(.0150/97)+(-.0004 if side<0 else 0.)
def pilot():
    start=time.time();assert b.sha(SRC)=='e522f587e7f9d5e5df7564b1ff0c38f75575dda3e6e6b1806ae2eee662b0c168'
    bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;b.setup(s,b.config(s));before=state();render('before')
    V,T=b.evaluated(bpy.data.objects[b.BODY],True);bt=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True,epsilon=0.)
    image=bpy.data.images.load(str(TEX),check_existing=True);image.pack();mat=bpy.data.materials.new('AFN36_DIAGNOSTIC_ArtistSilhouette');mat.use_nodes=True
    p=mat.node_tree.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.5;p.inputs['Specular IOR Level'].default_value=.25
    tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image;mat.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color']);mat.node_tree.links.new(tex.outputs['Alpha'],p.inputs['Alpha'])
    mat.surface_render_method='DITHERED';rows=[]
    for label,side in [('L',1),('R',-1)]:
        nx,ny=79,25;P=[];UV=[];bindings=[]
        for py in np.linspace(148,264,ny):
            for px in np.linspace(8,490,nx):
                x,z=world_xz(px,py,side);pt,n,ti,bc=sample(bt,V,T,x,z);P.append(pt+n*.00012);UV.append((px/512,1-py/512));bindings.append({'triangle':ti,'barycentric':bc.tolist()})
        faces=[]
        for j in range(ny-1):
            for k in range(nx-1):a=j*nx+k;faces.append((a,a+1,a+nx+1,a+nx))
        mesh=bpy.data.meshes.new('AFN36_'+label+'_DiagnosticSilhouette');mesh.from_pydata(P,[],faces);mesh.update();uv=mesh.uv_layers.new(name='ArtistUV');ids=np.empty(len(mesh.loops),dtype='i4');mesh.loops.foreach_get('vertex_index',ids);uv.data.foreach_set('uv',np.array(UV,dtype='f4')[ids].ravel());mesh.materials.append(mat)
        o=bpy.data.objects.new(mesh.name,mesh);s.collection.objects.link(o);o['AFN36_pilot']='Diagnostic conforming alpha layer, not 3D fibres or accepted hair';o['source']='CC0 MakeHuman eyebrow001'
        for poly in mesh.polygons:poly.use_smooth=True
        rows.append({'name':o.name,'vertices':len(P),'faces':len(faces),'bindings':bindings})
    assert state()==before;camera('face');out=S/'aevrynd-female-next-r0036-p-silhouette-pilot.blend';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out),compress=True);render('pilot')
    save('pilot-build.json',{'source':str(SRC),'sourceSha256':b.sha(SRC),'output':str(out),'outputSha256':b.sha(out),'texture':str(TEX),'textureSha256':b.sha(TEX),'originalState':before,'originalStateExact':True,'brows':rows,'scope':'Diagnostic alpha-card silhouette feasibility only, not fibre depth/motion/contact/runtime qualification.','seconds':time.time()-start});print('R36_PILOT_DONE',flush=True)
def fibres():
    start=time.time();assert b.sha(SRC)=='e522f587e7f9d5e5df7564b1ff0c38f75575dda3e6e6b1806ae2eee662b0c168'
    flow=np.load(S/'aevrynd-female-next-r0036-image-flow.npz');pixels=flow['pixelPaths'];base_r=flow['radii'];colors=flow['linearColors'];NPT=24
    solve_spec=importlib.util.spec_from_file_location('contact36',Path(__file__).with_name('solve-female-next-r0036-brow-contacts.py'));solver=importlib.util.module_from_spec(solve_spec);solve_spec.loader.exec_module(solver)
    bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;before=state();body=bpy.data.objects[b.BODY];V,T=b.evaluated(body,True);bt=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True,epsilon=0.)
    P=[];N=[];surface=[];bindings=[];radii=[];u=np.linspace(0,1,NPT)
    for side in (1,-1):
        for ci,xy in enumerate(pixels):
            pts=[];nn=[];skin=[];root=None
            for j,(px,py) in enumerate(xy):
                x,z=world_xz(float(px),float(py),side);pt,n,ti,bc=sample(bt,V,T,x,z);skin.append(pt);nn.append(n)
                height=.00018+.00010*(.5+.5*math.sin(ci*2.399963))
                gap=base_r[ci,j]+.000025+height*math.sin(math.pi*u[j]*.87)
                pts.append(pt+n*gap)
                if j==0:root={'bodyTriangle':ti,'bodyVertices':T[ti].tolist(),'barycentric':bc.tolist(),'surfacePointM':pt.tolist(),'normal':n.tolist(),'rootNormalOffsetM':float(gap),'sourcePixel':xy[0].tolist(),'side':side,'imagePathIndex':ci}
            P.append(pts);N.append(nn);surface.append(skin);bindings.append(root);radii.append(base_r[ci])
    P=np.array(P,dtype='f8');radii=np.array(radii,dtype='f8');N=np.array(N);surface=np.array(surface)
    initial_ids,initial_gap,_,_=solver.contacts(P,radii,1e-6)
    save('a-initial-contact.json',{'candidatePairs':len(initial_ids),'overlappingConservativeCapsules':int((initial_gap<=1e-6).sum()),'minimumPairCapsuleGapM':float(initial_gap.min()),'allFollicles':len(P),'solver':'Simultaneous free-point relaxation, all roots fixed, no greedy per-fibre removal or lift choices.'})
    print('R36_INITIAL',len(initial_ids),int((initial_gap<=1e-6).sum()),flush=True)
    P,solved=solver.solve(P,radii,N,surface);save('a-relaxation.json',solved);print('R36_RELAXED',json.dumps({k:w for k,w in solved.items() if k!='iterations'}),flush=True)
    if solved['remainingConservativeCapsuleOverlaps'] or solved['maximumDisplacementM']>solved['maximumAllowedDisplacementM']:
        # Preserve the actual failed complete-head candidate for visual review.
        decision='UNQUALIFIED_STATIC_CONTACT_DIAGNOSTIC'
    else:decision='PENDING_SAVED_CONTACT_AND_APPEARANCE'
    collection=bpy.data.collections.new('AFN36_ARTIST_INFORMED_BROWS');s.collection.children.link(collection)
    scalp=next(o for o in s.objects if o.type=='CURVES' and not o.hide_render)
    base=np.median(colors,axis=0);mats=[]
    for k in range(6):
        m=bpy.data.materials.new(f'AFN36_ArtistBrown_{k}');m.use_nodes=True;sh=m.node_tree.nodes.get('Principled BSDF');rgb=base*(.78+.088*k);sh.inputs['Base Color'].default_value=(*rgb,1.);sh.inputs['Roughness'].default_value=.46;sh.inputs['Specular IOR Level'].default_value=.30;sh.inputs['IOR'].default_value=1.55;m.diffuse_color=(*rgb,1);mats.append(m)
    # Source container is known valid native Curves; replace all original data.
    objects=[]
    for index,side in enumerate(('L','R')):
        d=scalp.data.copy();d.name=f'AFN36_{side}_BrowFibres';d.surface=None;d.materials.clear()
        for attr in list(d.attributes):
            if attr.name not in ('position','radius','curve_type','material_index'):d.attributes.remove(attr)
        d.remove_curves(indices=list(range(450,len(d.curves))));d.resize_curves([NPT]*450)
        pp=P[index*450:(index+1)*450].astype('f4');rr=radii[index*450:(index+1)*450].astype('f4')
        d.position_data.foreach_set('vector',pp.ravel());d.attributes['radius'].data.foreach_set('value',rr.ravel());d.attributes['curve_type'].data.foreach_set('value',[1]*450)
        for mat in mats:d.materials.append(mat)
        d.attributes['material_index'].data.foreach_set('value',[k%6 for k in range(450)])
        o=bpy.data.objects.new(d.name,d);collection.objects.link(o);o.parent=body;o.matrix_world=Matrix.Identity(4);o['aevrynd_layer']='EYEBROW_FIBRES';o['AFN36_binding_cache']='aevrynd-female-next-r0036-a-brow-fibres.npz';o['AFN36_static_only']=True;o['AFN36_artist_source']='MakeHuman system CC0 eyebrow001 silhouette and image-local tangent evidence';objects.append(o.name)
        # Separate actual-skin attachment study, never an opaque rendered cap.
        bounds=surface[index*450:(index+1)*450].reshape(-1,3);lo=bounds.min(0)-.001;hi=bounds.max(0)+.001
        tri_min=V[T].min(1);tri_max=V[T].max(1);keep=np.all(tri_max>=lo,axis=1)&np.all(tri_min<=hi,axis=1);ids=np.flatnonzero(keep);used,remap=np.unique(T[ids],return_inverse=True)
        me=bpy.data.meshes.new(f'AFN36_{side}_ActualSkinAttachment');me.from_pydata(V[used],[],remap.reshape(-1,3));me.update();em=bpy.data.objects.new(me.name,me);collection.objects.link(em);em.hide_render=True;em.hide_set(True);em['AFN36_scope']='Editable extracted neutral skin patch; bindings reference exact body triangle cache, no live deform modifier.'
    bpy.context.view_layer.update();assert state()==before
    # Store saved precision for the independent verifier, including all roots.
    paths=[];actual_r=[]
    for name in objects:
        pp,rr=v.hair_arrays(bpy.data.objects[name]);paths.append(pp);actual_r.append(rr)
    np.savez_compressed(S/'aevrynd-female-next-r0036-a-brow-fibres.npz',positions=np.concatenate(paths),radii=np.concatenate(actual_r),rootTriangles=np.array([r['bodyTriangle'] for r in bindings],dtype='i4'),rootVertices=np.array([r['bodyVertices'] for r in bindings],dtype='i4'),rootBarycentric=np.array([r['barycentric'] for r in bindings]),rootNormals=np.array([r['normal'] for r in bindings]),rootSurface=np.array([r['surfacePointM'] for r in bindings]),rootStandOff=np.array([r['rootNormalOffsetM'] for r in bindings]),sourcePixelPaths=np.tile(pixels,(2,1,1)))
    camera('face');out=S/'aevrynd-female-next-r0036-a-artist-informed-brows.blend';s['AFN36_status']=decision;s['AFN36_scope']='Native actual-radius brows; static authoring, not facial rig/dynamics/runtime';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out),compress=True)
    save('a-build.json',{'source':str(SRC),'sourceSha256':b.sha(SRC),'output':str(out),'outputSha256':b.sha(out),'originalState':before,'originalStateExact':True,'objects':objects,'fibres':900,'pointsPerFibre':NPT,'segments':900*(NPT-1),'cache':str(S/'aevrynd-female-next-r0036-a-brow-fibres.npz'),'cacheSha256':b.sha(S/'aevrynd-female-next-r0036-a-brow-fibres.npz'),'texture':str(TEX),'textureSha256':b.sha(TEX),'relaxation':solved,'curveType':'POLY','primitive':s.render.hair_type,'hairSubdivision':s.render.hair_subdiv,'decision':decision,'materialBaseLinearRGB':base.tolist(),'seconds':time.time()-start,'limits':['Artist 2D local-flow inference, not captured individual follicles','No body rig/deforming attachment/blink/gaze or dynamic/self qualification until separate stated proof','Existing scalp groom remains visually rejected; no whole-character or runtime acceptance']})
    render('a-after');print('R36_FIBRES_DONE',time.time()-start,flush=True)
if __name__=='__main__':
    if '--fibres' in sys.argv:fibres()
    else:pilot()
