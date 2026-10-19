"""Actual-skin attached closed mucosal tissues and native eyelash fibres.

Each tissue base is a recorded tessellation of existing skin triangles. Its
boundary is welded to that base and its top lies outside the skin. This is an
explicit anatomical attachment, not an arbitrary body-contact exclusion.
No eyeball, body, skin material, lighting, brow or scalp geometry is modified.
"""
import bpy,importlib.util,json,math,time,hashlib
import numpy as np
from pathlib import Path
from collections import defaultdict,deque
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
spec=importlib.util.spec_from_file_location('i37',Path(__file__).with_name('inspect-female-next-r0037-eye-margin.py'));i=importlib.util.module_from_spec(spec);spec.loader.exec_module(i)
b=i.b;v=i.v;c=i.c;R=i.R;S=i.S;E=i.E;SRC=i.SRC;OUT=S/'aevrynd-female-next-r0037-a-attached-eye-margin.blend'
def save(n,x):i.save(n,x)
def read(n):return json.loads((E/n).read_text(encoding='utf8'))
def state():
    names=[o.name for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render and not o.name.startswith('AFN37_')]
    curves={}
    for o in bpy.context.scene.objects:
        if o.type=='CURVES' and not o.hide_render and not o.name.startswith('AFN37_'):
            p,r=v.hair_arrays(o);curves[o.name]={'pointsSha256':hashlib.sha256(p.tobytes()).hexdigest(),'radiusSha256':hashlib.sha256(r.tobytes()).hexdigest(),'matrix':b.matrix(o.matrix_world),'materials':[v.v32.material_signature(m) for m in o.data.materials],'materialIndices':[a.value for a in o.data.attributes['material_index'].data]}
    return {'meshes':{n:v.g.signature(bpy.data.objects[n]) for n in names},'materials':v.materials(names),'skinFields':v.fields(bpy.data.objects[b.BODY]),'curves':curves,'stage':v.stage()}
def render(label,views=('face','oblique','profile')):
    c.E=E;c.render(label,views)
def closeup(label):
    s=bpy.context.scene;cam=s.camera;cam.location=(0,-.48,1.468);cam.rotation_euler=(Vector((0,-.115,1.467))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=100;s.render.resolution_x=1400;s.render.resolution_y=650;s.render.filepath=str(E/(label+'-eyes.png'));bpy.context.view_layer.update();row={'camera':b.matrix(cam.matrix_world),'lens':100,'resolution':[1400,650],'stage':v.stage()};bpy.ops.render.render(write_still=True);s.render.resolution_x=s.render.resolution_y=800;c.camera('face');return row
def curve_distance(P,Q):
    out=[]
    for block in np.array_split(P,max(1,math.ceil(len(P)/1024))):out.append(np.sqrt(np.min(np.sum((block[:,None]-Q[None,:])**2,axis=2),axis=1)))
    return np.concatenate(out)
def connected_faces(tri):
    edge_faces=defaultdict(list)
    for k,t in enumerate(tri):
        for a,z in zip(t,np.roll(t,-1)):edge_faces[tuple(sorted((int(a),int(z))))].append(k)
    adjacency=defaultdict(set)
    for rows in edge_faces.values():
        for a in rows:adjacency[a].update(rows)
    left=set(range(len(tri)));parts=[]
    while left:
        seed=left.pop();part={seed};todo=[seed]
        while todo:
            p=todo.pop();new=adjacency[p]&left;left-=new;part|=new;todo.extend(new)
        parts.append(sorted(part))
    return sorted(parts,key=len,reverse=True)
def tissue_material(body,kind):
    m=body.data.materials[0].copy();m.name='AFN37_'+kind+'_WetMucosa';nt=m.node_tree;out=nt.nodes.get('Material Output');old=out.inputs['Surface'].links[0].from_socket
    wet=nt.nodes.new('ShaderNodeBsdfPrincipled');wet.name='AFN37_ActualMucosalResponse';wet.inputs['Base Color'].default_value=(.34,.135,.115,1);wet.inputs['Roughness'].default_value=.23;wet.inputs['Coat Weight'].default_value=.38;wet.inputs['Coat Roughness'].default_value=.065;wet.inputs['Subsurface Weight'].default_value=.06;wet.inputs['Subsurface Scale'].default_value=.0005
    attr=nt.nodes.new('ShaderNodeAttribute');attr.attribute_name='AFN37_WetWeight';mix=nt.nodes.new('ShaderNodeMixShader');nt.links.new(attr.outputs['Fac'],mix.inputs[0]);nt.links.new(old,mix.inputs[1]);nt.links.new(wet.outputs['BSDF'],mix.inputs[2]);nt.links.new(mix.outputs[0],out.inputs['Surface']);return m
def attached_patch(name,body,V,T,local,normals,fields,selected,metric,height,material,exact_boundary=False,weights_override=None):
    parts=connected_faces(T[selected]);largest=np.array(parts[0],dtype='i4');fraction=len(largest)/len(selected);assert fraction>.90,(name,'fragmented anatomical selection',fraction)
    selected=selected[largest];edges=defaultdict(int)
    for tri in T[selected]:
        for a,z in zip(tri,np.roll(tri,-1)):edges[tuple(sorted((int(a),int(z))))]+=1
    boundary_edges={e for e,k in edges.items() if k==1};boundary_vertices={a for e in boundary_edges for a in e};nodes=[];lookup={};child=[];ancestors=[]
    def node(key,indices,weights,boundary):
        if key in lookup:return lookup[key]
        idx=len(nodes);lookup[key]=idx;nodes.append({'indices':list(map(int,indices)),'weights':list(map(float,weights)),'boundary':bool(boundary)});return idx
    for tid in selected:
        a,z,d=map(int,T[tid]);ring=[node(('v',a),[a],[1],a in boundary_vertices),node(('e',*sorted((a,z))),[a,z],[.5,.5],tuple(sorted((a,z))) in boundary_edges),node(('v',z),[z],[1],z in boundary_vertices),node(('e',*sorted((z,d))),[z,d],[.5,.5],tuple(sorted((z,d))) in boundary_edges),node(('v',d),[d],[1],d in boundary_vertices),node(('e',*sorted((d,a))),[d,a],[.5,.5],tuple(sorted((d,a))) in boundary_edges)]
        if exact_boundary:ring=[idx for idx in ring if not (len(nodes[idx]['indices'])==2 and nodes[idx]['boundary'])]
        mid=node(('f',int(tid)),[a,z,d],[1/3]*3,False)
        for q in range(len(ring)):child.append((mid,ring[q],ring[(q+1)%len(ring)]));ancestors.append(int(tid))
    base=np.array([np.array(n['weights'])@local[n['indices']] for n in nodes],dtype='f4');world=base.astype('f8')@np.array(body.matrix_world)[:3,:3].T+np.array(body.matrix_world)[:3,3]
    nn=np.array([np.array(n['weights'])@normals[n['indices']] for n in nodes]);nn/=np.linalg.norm(nn,axis=1)[:,None];bound=np.array([n['boundary'] for n in nodes]);m=metric(world);w=np.clip(1-m,0,1);w=w*w*(3-2*w)
    if weights_override is not None:w=np.array([weights_override[tuple(sorted(zip(n['indices'],n['weights'])))] for n in nodes])
    offset=np.where(bound,0.,2e-6+height*w);world_top=world+nn*offset[:,None];inverse=np.linalg.inv(np.array(body.matrix_world));top=((world_top-np.array(body.matrix_world)[:3,3])@inverse[:3,:3].T).astype('f4')
    points=base.tolist();top_ids=np.arange(len(nodes));source_nodes=list(range(len(nodes)));roles=['base']*len(nodes);wet=[0.]*len(nodes)
    for j in np.flatnonzero(~bound):top_ids[j]=len(points);points.append(top[j].tolist());source_nodes.append(int(j));roles.append('top');wet.append(float(w[j]*(.9 if 'Caruncle' in name else .75)))
    faces=[];face_roles=[];face_source=[]
    for tri,tid in zip(child,ancestors):faces.append(tuple(reversed(tri)));face_roles.append('base');face_source.append(tid);faces.append(tuple(int(top_ids[j]) for j in tri));face_roles.append('top');face_source.append(tid)
    me=bpy.data.meshes.new(name);me.from_pydata(points,[],faces);me.update();o=bpy.data.objects.new(name,me);bpy.data.collections['AFN37_EYE_MARGIN'].objects.link(o);o.parent=body;o.matrix_parent_inverse=Matrix.Identity(4);o.matrix_basis=Matrix.Identity(4);me.materials.append(material)
    for field,values in fields.items():
        scalar=values.ndim==1;sampled=np.array([np.array(n['weights'])@values[n['indices']] for n in nodes],dtype='f4')[source_nodes];attr=me.attributes.new(field,'FLOAT' if scalar else 'FLOAT_VECTOR','POINT');attr.data.foreach_set('value' if scalar else 'vector',sampled.ravel())
    a=me.attributes.new('AFN37_WetWeight','FLOAT','POINT');a.data.foreach_set('value',wet)
    for p in me.polygons:p.use_smooth=True
    o['aevrynd_layer']='LACRIMAL_CARUNCLE' if 'Caruncle' in name else 'WET_LID_MARGIN';o['AFN37_attachment']='Closed external tissue volume with a recorded shared actual-skin base and welded boundary. Neutral authoring only.'
    return {'object':name,'sourceBodyTriangleIds':selected.tolist(),'selectionLargestComponentFraction':fraction,'baseNodeCount':len(nodes),'nodes':nodes,'vertexBaseNode':source_nodes,'vertexRole':roles,'facesRole':face_roles,'facesSourceBodyTriangle':face_source,'boundaryBaseNodes':np.flatnonzero(bound).tolist(),'topVertices':top_ids.tolist(),'maximumDesignedOffsetM':float(offset.max()),'maximumHeightM':height,'primitive':'Closed mesh, not a floating ring or face decal'}
def main():
    start=time.time();assert b.sha(SRC)=='d563918d780e6d86f52e8bd50562bc5beec427ccfc5ebb60ac88e3aa53185210';bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;before=state();render('before');before_close=closeup('before')
    save('round-contract.json',{'previousGoalTurnClassification':'progress: r36 integrated900actual-radius eyebrows, saved neutral contact proof and GitHub654ef68; full-face realism still incomplete','source':str(SRC),'sourceSha256':b.sha(SRC),'majorDefects':['Bare eyelid/inner-corner structures and artificial eye presentation','Rejected artificial full scalp groom','Incomplete skin/oral/rig/body/clothes/runtime'],'selectedDefect':'Missing coherent eyelid-margin anatomy: actual-skin attached wet mucosal rims, small inner-corner tissue and directed upper/lower3D lashes','expectedVisibleDifference':'More readable human lid/eye junction and natural lash framing in the complete head, without changing eye sizes/poses, body, skin color, lighting, brows or scalp.','pilot':'Actual native reference-loop/body/eye measurement disproved a simple native-loop tear tube: gap0.395..2.689mm. Use actual visible aperture to place the external margin and source-skin triangle footprints for attached tissue; full fluid meniscus continuity is NOT claimed.','candidates':1,'resources':{'threads':4,'heavyJobs':1,'checkpointMinutes':45,'initialDiagnosticMinutes':10,'lashes':340,'pointsPerLash':32,'tissueMaximumHeightM':.00018},'reject':['No visible multi-angle complete-head improvement or heavy makeup/inflamed/glued appearance','Unresolved finite lash/body/eye/tissue/hair/self contact','New closed tissues enter body outside the mathematically recorded shared skin base/welded seam','Original body/eye/nativeUV/skin/brow/scalp or stage changes'],'limits':'Neutral static authoring; not blink/gaze/face rig, fluid simulation, continuous contacts or runtime.'})
    body=bpy.data.objects[b.BODY];V,T=b.evaluated(body,True);bt=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True,epsilon=0.);eye_trees={};scans={};rim=read('rim-inspection.json')['sides'];curves={}
    for side in ('L','R'):
        ev,et=i.outer(side);eye_trees[side]=BVHTree.FromPolygons(ev.tolist(),et.tolist(),all_triangles=True);center=np.array(v.i.FITS[side]['centerM']);rows=v.i.aperture(bt,eye_trees[side],center,np.linspace(-.0104,.0104,151));rows=[r for r in rows if r.get('visible') and r['visibleSampleRuns']==1];assert len(rows)>120;scans[side]=rows
        for part,sgn in [('upper',1),('lower',-1)]:
            q=[]
            for r in rows[10:-10]:
                p,n,ti,d=bt.ray_cast(Vector((r['x'],-.35,r[part+'Z']+sgn*.00013)),Vector((0,1,0)),.5)
                if p is not None:q.append(list(p))
            curves[(side,part)]=np.array(q)
    evbody=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=evbody.to_mesh();local=np.empty(len(me.vertices)*3,dtype='f4');me.vertices.foreach_get('co',local);local=local.reshape(-1,3);normal_local=np.array([list(n.vector) for n in me.vertex_normals]);normal_matrix=np.linalg.inv(np.array(body.matrix_world)[:3,:3]).T;normals=normal_local@normal_matrix.T;normals/=np.linalg.norm(normals,axis=1)[:,None];fields={}
    for name in ('AFN32_RegisteredCC0UVW','AFN32_PigmentWeight','AFN32_Roughness'):
        attr=me.attributes[name];n=3 if attr.data_type=='FLOAT_VECTOR' else 1;data=np.empty(len(attr.data)*n,dtype='f4');attr.data.foreach_get('vector' if n==3 else 'value',data);fields[name]=data.reshape(-1,3) if n==3 else data
    evbody.to_mesh_clear();collection=bpy.data.collections.new('AFN37_EYE_MARGIN');s.collection.children.link(collection);mats={k:tissue_material(body,k) for k in ('Margin','Caruncle')};patches=[]
    for side in ('L','R'):
        for part in ('upper','lower'):
            Q=curves[(side,part)];lo=Q.min(0)-.001;hi=Q.max(0)+.001;inside=np.all(V>=lo,axis=1)&np.all(V<=hi,axis=1);candidates=np.flatnonzero(np.any(inside[T],axis=1));used=np.unique(T[candidates]);dist=curve_distance(V[used],Q);metric_all=np.full(len(V),np.inf);metric_all[used]=dist/.00046;keep=candidates[np.any(metric_all[T[candidates]]<1,axis=1)];assert len(keep)>20
            metric=lambda p,Q=Q:curve_distance(p,Q)/.00046
            patches.append(attached_patch(f'AFN37_{side}_{part}_WetMargin',body,V,T,local,normals,fields,keep,metric,.000035,mats['Margin']))
        sign=1 if side=='L' else -1;med=np.array(rim[side]['medialPointM']);px=med[0]+sign*.00045;p,_,_,_=bt.ray_cast(Vector((px,-.35,med[2]+.00010)),Vector((0,1,0)),.5);assert p is not None;centre=np.array(p);axes=np.array((.00072,.00075,.00051));mv=np.linalg.norm((V-centre)/axes,axis=1);keep=np.flatnonzero(np.any(mv[T]<1,axis=1));assert len(keep)>6
        metric=lambda p,centre=centre,axes=axes:np.linalg.norm((p-centre)/axes,axis=1)
        patches.append(attached_patch(f'AFN37_{side}_Caruncle',body,V,T,local,normals,fields,keep,metric,.00018,mats['Caruncle']))
    save('a-tissue-bindings.json',{'source':str(SRC),'sourceSha256':b.sha(SRC),'bodyObject':b.BODY,'bodyTriangles':len(T),'bodyTriangleHash':hashlib.sha256(T.tobytes()).hexdigest(),'coordinateSpace':'Tissue local = evaluated body local, parent body with identity basis/inverse. Base nodes are barycentric source-skin points; top boundary reuses exactly the base vertices.','numericalInterfaceAllowanceM':1e-6,'patches':patches})
    paths=[];radii=[];roots=[];names=[];rng=np.random.default_rng(3737);template=bpy.data.objects['AFN36_L_BrowFibres'];keratin=bpy.data.materials.new('AFN37_NaturalLashKeratin');keratin.use_nodes=True;sh=keratin.node_tree.nodes.get('Principled BSDF');sh.inputs['Base Color'].default_value=(.012,.006,.003,1);sh.inputs['Roughness'].default_value=.43;sh.inputs['Specular IOR Level'].default_value=.30
    for side in ('L','R'):
        sign=1 if side=='L' else -1;rows=sorted(scans[side],key=lambda r:sign*r['x']);rows=rows[8:-8]
        for part,count,zsign in [('upper',110,1),('lower',60,-1)]:
            object_paths=[];object_r=[]
            for ci in range(count):
                t=(ci+.5+rng.uniform(-.20,.20))/count;x=np.interp(t,np.linspace(0,1,len(rows)),[r['x'] for r in rows]);z=np.interp(t,np.linspace(0,1,len(rows)),[r[part+'Z'] for r in rows])+zsign*(.00029+(ci%3)*.00013)
                pt,nn,tid,bc=c.sample(bt,V,T,float(x),float(z));radius=float(rng.uniform(.000020,.000030)*(1 if part=='upper' else .72));root=pt+nn*(radius+.000025);length=(.0046+.0025*math.sin(math.pi*t))*rng.uniform(.85,1.10)*(1 if part=='upper' else .53);fan=sign*(t-.44)*.75;forward=np.array((fan,-1.,0.));forward/=np.linalg.norm(forward);up=np.array((0,0,zsign));d0=forward*.82+nn*.18+up*.06;d0/=np.linalg.norm(d0);p0=root;p1=root+d0*(length*.28);p2=root+forward*(length*.65)+up*(length*.045);p3=root+forward*(length*.90)+up*(length*.43);u=np.linspace(0,1,32);P=(1-u[:,None])**3*p0+3*(1-u[:,None])**2*u[:,None]*p1+3*(1-u[:,None])*u[:,None]**2*p2+u[:,None]**3*p3;rr=1e-6+(radius-1e-6)*(1-u)**.75
                roots.append({'object':f'AFN37_{side}_{part}_Lashes','bodyTriangle':int(tid),'bodyVertices':T[tid].tolist(),'barycentric':bc.tolist(),'surfaceM':pt.tolist(),'normal':nn.tolist(),'standOffM':radius+.000025,'side':side,'part':part,'t':t});object_paths.append(P);object_r.append(rr)
            d=template.data.copy();d.name=f'AFN37_{side}_{part}_Lashes';d.surface=None;d.materials.clear()
            for attr in list(d.attributes):
                if attr.name not in ('position','radius','curve_type','material_index'):d.attributes.remove(attr)
            d.remove_curves(indices=list(range(count,len(d.curves))));d.resize_curves([32]*count);d.position_data.foreach_set('vector',np.array(object_paths,dtype='f4').ravel());d.attributes['radius'].data.foreach_set('value',np.array(object_r,dtype='f4').ravel());d.attributes['curve_type'].data.foreach_set('value',[1]*count);d.attributes['material_index'].data.foreach_set('value',[0]*count);d.materials.append(keratin);o=bpy.data.objects.new(d.name,d);collection.objects.link(o);o.parent=body;o.matrix_world=Matrix.Identity(4);o['aevrynd_layer']='EYELASHES';o['AFN37_static_only']=True;names.append(o.name);paths.extend(object_paths);radii.extend(object_r)
    bpy.context.view_layer.update();assert state()==before;cache=S/'aevrynd-female-next-r0037-a-lashes.npz';np.savez_compressed(cache,positions=np.array(paths,dtype='f4'),radii=np.array(radii,dtype='f4'));save('a-lash-bindings.json',{'objects':names,'roots':roots,'cache':str(cache),'cacheSha256':b.sha(cache),'scope':'Actual neutral skin triangle/barycentric roots and native curve authoring only; no rig or live surface deformation.'});s['AFN37_status']='EYE_MARGIN_CANDIDATE_PENDING_SAVED_CONTACT_AND_VISUAL_REVIEW';c.camera('face');bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    save('a-build.json',{'source':str(SRC),'sourceSha256':b.sha(SRC),'output':str(OUT),'outputSha256':b.sha(OUT),'originalState':before,'originalStateExact':True,'tissues':[p['object'] for p in patches],'lashes':names,'lashCount':len(paths),'lashSegments':len(paths)*31,'primitive':'STRIP','hairSubdivision':0,'beforeCloseup':before_close,'seconds':time.time()-start,'limits':['Neutral attached tissues/lashes only, no blink/gaze/face rig or continuous contact proof','Wet mucosal response is not a simulated fluid meniscus bridging the body/globe gap','Optical geometry/materials unchanged; existing iris/catchlight appearance remains a separate problem','No full-head/character/runtime acceptance without stated further review']});render('a-after');after_close=closeup('a-after');assert before_close==after_close;save('a-closeup-controls.json',{'before':before_close,'after':after_close,'exact':True});print('R37_BUILD_DONE',time.time()-start,flush=True)
if __name__=='__main__':main()
