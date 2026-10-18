"""Interpolate compatible verified guides, then route every final child on the global envelope."""
import bpy,bmesh,json,math,importlib.util,time,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
spec=importlib.util.spec_from_file_location('route',Path(__file__).with_name('build-female-next-r0013-envelope-hair.py'));route=importlib.util.module_from_spec(spec);spec.loader.exec_module(route)
R,S,E=route.R,route.S,route.E;solid=route.solid;rng=np.random.default_rng(1313)

def graph(roots,normals,G,prefix=''):
    triangles=[]
    tangent=G[:,10]-G[:,2];tangent/=np.maximum(np.linalg.norm(tangent,axis=1,keepdims=True),1e-12)
    for side in (-1,1):
        bm=bmesh.new();layer=bm.verts.layers.int.new('guide')
        for i,p in enumerate(roots):
            if p[0]*side<0:continue
            v=bm.verts.new(p);v[layer]=i
        result=bmesh.ops.convex_hull(bm,input=list(bm.verts),use_existing_faces=False);bm.normal_update()
        faces=[f for f in result['geom'] if isinstance(f,bmesh.types.BMFace)]
        bmesh.ops.triangulate(bm,faces=faces);bm.normal_update()
        for f in bm.faces:
            ids=[v[layer] for v in f.verts]
            if len(ids)!=3:continue
            P=roots[ids];n=np.cross(P[1]-P[0],P[2]-P[0]);area=np.linalg.norm(n)*.5
            if area<1e-8:continue
            n/=np.linalg.norm(n)
            if abs(n@normals[ids].mean(axis=0))<.45:continue
            if max(np.linalg.norm(P[i]-P[j]) for i in range(3) for j in range(i))>.042:continue
            if min(tangent[ids[i]]@tangent[ids[j]] for i in range(3) for j in range(i))<.1:continue
            triangles.append(ids)
        bm.free()
    ids=np.array(triangles,dtype=np.int32);P=roots[ids];areas=np.linalg.norm(np.cross(P[:,1]-P[:,0],P[:,2]-P[:,0]),axis=1)*.5
    assert len(ids)>50,len(ids)
    (E/(prefix+'root-connectivity.json')).write_text(json.dumps({'triangles':ids.tolist(),'areasM2':areas.tolist(),'separatePartSides':True,'maxTriangleEdgeM':.042,'minGuideTangentDot':.1,'uniformAreaSampling':True},indent=2)+'\n')
    return ids,areas/areas.sum()

def fibre_materials():
    mats=[]
    for i in range(6):
        m=bpy.data.materials.new('AFN13_ChestnutKeratin_'+str(i));m.use_nodes=True
        bs=next(n for n in m.node_tree.nodes if n.bl_idname=='ShaderNodeBsdfPrincipled');factor=.72+i*.12
        bs.inputs['Base Color'].default_value=(.040*factor,.019*factor,.009*factor,1);bs.inputs['Roughness'].default_value=.43;bs.inputs['Specular IOR Level'].default_value=.28;bs.inputs['Anisotropic'].default_value=.65;mats.append(m)
    return mats

def native(name,P,radii,rig,mats,use_operator=False,copied_data=None):
    if copied_data is not None:
        d=copied_data;d.name=name;o=None;d.materials.clear()
        assert len(d.curves)==len(P) and len(d.points)==sum(len(p) for p in P)
    elif use_operator:
        groups=set(bpy.data.node_groups);libs=set(bpy.data.libraries)
        bpy.ops.object.select_all(action='DESELECT');body=bpy.data.objects['AFN_R0008_Body'];body.select_set(True);bpy.context.view_layer.objects.active=body
        bpy.ops.object.curves_empty_hair_add();o=bpy.context.object;d=o.data;o.modifiers.clear();d.surface=None
        # Discard operator-added stock Hair Dynamics graphs and linked libraries.
        # The saved asset contains only our explicit fibre arrays and materials.
        discarded=list(set(bpy.data.node_groups)-groups)+list(set(bpy.data.libraries)-libs)
        if discarded:bpy.data.batch_remove(ids=discarded)
        o.name=name;d.name=name;d.materials.clear()
    else:d=bpy.data.hair_curves.new(name);o=None
    if copied_data is None:d.add_curves([len(p) for p in P])
    flat=np.concatenate(P).astype(np.float32);rr=np.concatenate(radii).astype(np.float32)
    d.position_data.foreach_set('vector',flat.ravel());radius=d.attributes.get('radius') or d.attributes.new('radius','FLOAT','POINT');radius.data.foreach_set('value',rr)
    # Blender's installed spline enum: 0 Catmull-Rom, 1 Poly, 2 Bezier, 3 NURBS.
    # POLY avoids unverified interpolation overshoot between tested capsules.
    # RNA exposes the INT8 attribute's `value` as a 32-bit integer property.
    # Match RNA buffer width, not the attribute's compact storage width.
    typ=d.attributes.get('curve_type') or d.attributes.new('curve_type','INT8','CURVE');typ.data.foreach_set('value',[1]*len(P))
    mat=d.attributes.get('material_index') or d.attributes.new('material_index','INT','CURVE');mat.data.foreach_set('value',[i%len(mats) for i in range(len(P))])
    for m in mats:d.materials.append(m)
    if o is None:o=bpy.data.objects.new(name,d);bpy.context.scene.collection.objects.link(o)
    route.parent_head(o,rig)
    o['aevrynd_layer']=name;o['aevrynd_revision']='female-next-r0013';o['aevrynd_static_only']=True;o['aevrynd_curve_type']='POLY'
    return o

def main():
    start=time.time();soft='--soft-roots' in sys.argv;label='b' if soft else 'a';prefix='b-' if soft else '';prior=json.loads((E/(prefix+'guide-envelope-verification.json')).read_text());assert prior['nextStageAllowed']
    src=S/f'aevrynd-female-next-r0013-{label}-envelope-guides.blend';assert route.sha(src)==prior['outputSha256']
    bpy.ops.wm.open_mainfile(filepath=str(src));rig=bpy.data.objects['AFN_R0005_Rig'];solid.stage.set_pose(rig,'neutral');body=bpy.data.objects['AFN_R0008_Body'];body.data.calc_loop_triangles()
    V,T,tree=solid.data(body);V=np.array(V,dtype=np.float64);T=np.array(T,dtype=np.int32);tri=V[T]
    data=np.load(S/f'aevrynd-female-next-r0013-{label}-envelope-guides.npz');G=np.array([data['positions'][a:b] for a,b in zip(data['offsets'][:-1],data['offsets'][1:])],dtype=np.float64);A=data['planeNormals'];b=data['planeOffsets'];roots=G[:,0]
    normals=np.array([tree.find_nearest(Vector(p))[1] for p in roots]);connect,prob=graph(roots,normals,G,prefix)
    mats=fibre_materials();allP=[];allR=[];allLayer=[];bind=[];layers=[]
    for li,(name,count) in enumerate((('AFN13_PRIMARY_MASS',14000),('AFN13_SECONDARY_CLUMPS',7000),('AFN13_HAIRLINE_FINE',500),('AFN13_FLYAWAYS',80))):
        paths=[];radii=[]
        for ci in range(count):
            ids=connect[int(rng.choice(len(connect),p=prob))];s=math.sqrt(float(rng.random()));v=float(rng.random());w=np.array((1-s,s*(1-v),s*v))
            seed=np.einsum('i,ij->j',w,roots[ids]);hit,n,ti,d=tree.find_nearest(Vector(seed));root=np.array(hit+n*.00020)
            if soft and root[2]<1.485 and root[1]<-.012:continue
            if li==2 and root[1]>-.065:continue
            sourcePaths=G[ids] if soft else G[ids,2:];N=sourcePaths.shape[1];u=np.linspace(0,1,N);clump=(.15 if li==0 else .5)*u**1.8;one=np.eye(3)[np.argmax(w)];weights=(1-clump[:,None])*w+clump[:,None]*one
            raw=np.einsum('ji,ijk->jk',weights,sourcePaths);raw+=(root-np.einsum('i,ij->j',w,roots[ids]))[None,:]*(1-u[:,None])**2
            wave=np.array((float(n[1]),-float(n[0]),0.));wave/=max(np.linalg.norm(wave),1e-12);phase=float(rng.uniform(0,math.tau))
            raw+=wave[None,:]*(.00018*np.sin(u*math.pi)*np.sin(u*math.pi*6+phase))[:,None]
            raw[:,2]+=float(rng.uniform(-.004,.004))*u**5
            if li==2 and ci%3==0:raw=raw[:24]
            if li==3:raw+=np.array(n)[None,:]*(.002*np.sin(np.linspace(0,math.pi,len(raw))))[:,None]
            if soft:
                ramp=np.clip(np.linspace(0,1,len(raw))/.15,0,1);ramp=ramp*ramp*(3-2*ramp)
                routed=route.shell_batch(raw[1:],A,b,.00015+.00185*ramp[1:],.00005+.00095*ramp[1:]);P=np.vstack((root,routed))
            else:P=np.vstack((root,root+np.array(n)*.001,route.shell_batch(raw,A,b,np.full(len(raw),.002),np.full(len(raw),.001))))
            r=float(rng.uniform(.000027,.000038))*(.67 if li>=2 else 1.);u=np.linspace(0,1,len(P));rr=r*(.23+.77*(1-u)**.23);rr[-1]=r*.08
            paths.append(P);radii.append(rr);allLayer.append(li)
            triangle=tri[ti];u1=triangle[1]-triangle[0];u2=triangle[2]-triangle[0];delta=np.array(hit)-triangle[0];bc=np.linalg.lstsq(np.column_stack((u1,u2)),delta,rcond=None)[0]
            bind.append({'layer':li,'curve':len(paths)-1,'bodyTriangle':int(ti),'bodyVertices':T[ti].tolist(),'barycentric':[float(1-bc.sum()),float(bc[0]),float(bc[1])],'normal':list(n),'guideIndices':ids.tolist(),'guideWeights':w.tolist()})
        print('AFN13_NATIVE_BEGIN='+json.dumps({'layer':name,'curves':len(paths),'elapsedSeconds':time.time()-start}),flush=True)
        o=native(name,paths,radii,rig,mats);allP.extend(paths);allR.extend(radii);layers.append({'name':name,'curves':len(paths),'points':sum(len(p) for p in paths)})
        print('AFN13_CHILD_LAYER='+json.dumps(layers[-1]),flush=True)
    assert len(allP)<=24000
    if '--safe-io' in sys.argv:label+='-safe-io';prefix=label+'-'
    offsets=np.cumsum([0]+[len(p) for p in allP]);dest=S/f'aevrynd-female-next-r0013-{label}-native-envelope-hair-study.blend'
    np.savez_compressed(S/f'aevrynd-female-next-r0013-{label}-native-hair-data.npz',positions=np.concatenate(allP).astype(np.float32),radii=np.concatenate(allR).astype(np.float32),offsets=offsets,layers=np.array(allLayer,dtype=np.int8))
    (E/(prefix+'child-root-bindings.json')).write_text(json.dumps(bind,separators=(',',':'))+'\n')
    scene=bpy.context.scene;scene['aevrynd_revision']=f'female-next-r0013-{label}-native-envelope-hair';scene['aevrynd_release_state']='STATIC_HAIR_STUDY_PENDING_SAVED_COLLISION_AND_VISUAL_REVIEW';scene.render.threads_mode='FIXED';scene.render.threads=8
    bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(dest))
    (E/(prefix+'native-groom-build.json')).write_text(json.dumps({'source':str(src),'sourceSha256':route.sha(src),'output':str(dest),'outputSha256':route.sha(dest),'layers':layers,'hairCurves':len(allP),'hairPoints':int(offsets[-1]),'fileBytes':dest.stat().st_size,'routing':'Global expanded support envelope, compatible guide interpolation, actual skin-bound root corridor. Final saved capsules require independent verification.','material':'Same six Principled BSDF parameters as r0012 for controlled Eevee comparison. Native strand representation differs.','overallScore':None,'dynamicStatus':'NOT_IMPLEMENTED','wallSeconds':time.time()-start},indent=2)+'\n')
    print('AFN13_CHILDREN_DONE',flush=True)

if __name__=='__main__':main()
