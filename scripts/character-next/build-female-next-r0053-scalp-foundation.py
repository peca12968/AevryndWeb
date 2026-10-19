"""Actual-skin geodesic hairline and a new normal-grown master cohort.

Anatomical boundary anchors are artist inputs, not a scan of follicles.
No old crown/free-fall paths or failed follower interpolation is reused.
"""
from pathlib import Path
from collections import defaultdict,deque
import bpy,importlib.util,numpy as np,json,time,heapq,math,sys
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
sp=importlib.util.spec_from_file_location('g52foundation53',Path(__file__).with_name('inspect-female-next-r0052-native-groom.py'))
k=importlib.util.module_from_spec(sp);sp.loader.exec_module(k)
b=k.b;f=k.f;SRC=k.SRC;E=b.R/'Evidence/character-female-next/r0053-new-primary-groom';E.mkdir(parents=True,exist_ok=True)
HIGH='--evaluated-boundary' in sys.argv
TAG='refined-' if HIGH else ''
OUT=b.S/('aevrynd-female-next-r0053-a-'+('refined-scalp-' if HIGH else '')+'normal-grown-foundation.blend')
OLD='AFN33_C_BODY_BOUND_FIBRES';NAME='AFN53_NEW_PRIMARY_CURVES';FACE='AFN53_TemporaryNativeFace'
COUNT=64;N=128

def save(n,x):(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def shortest(adj,P,start,end,blocked):
    distance={start:0.};previous={};queue=[(0.,start)]
    while queue:
        d,x=heapq.heappop(queue)
        if d!=distance[x]:continue
        if x==end:break
        for y in adj[x]:
            if y in blocked and y!=end:continue
            nd=d+float(np.linalg.norm(P[y]-P[x]))
            if nd<distance.get(y,math.inf):distance[y]=nd;previous[y]=x;heapq.heappush(queue,(nd,y))
    assert end in distance,'Hairline geodesic is disconnected'
    path=[end]
    while path[-1]!=start:path.append(previous[path[-1]])
    return path[::-1]

def main():
    tick=time.time();assert b.sha(SRC)=='b86f7eeedf6fd6a4d9a7f13ff42dc4051907516bc90be8261f02e7678242a3ff'
    bpy.ops.wm.open_mainfile(filepath=str(SRC));before=f.state();body=bpy.data.objects[b.BODY]
    V,T=b.evaluated(body,True);tree=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True)
    # Front rays define forehead/temple edges; lateral rays pass above the
    # pinnae; posterior rays place the nape boundary on actual skin.
    anchors=[('front_center',(0,-.3,1.533),(0,1,0)),
        ('R_front_inner',(.018,-.3,1.532),(0,1,0)),('R_front_corner',(.038,-.3,1.526),(0,1,0)),
        ('R_temple',(.055,-.3,1.510),(0,1,0)),('R_sideburn',(.062,-.3,1.477),(0,1,0)),
        ('R_above_ear',(.3,-.010,1.514),(-1,0,0)),('R_behind_ear',(.3,.3,1.482),(-.3,-.315,0)),
        ('R_nape_corner',(.040,.3,1.446),(0,-1,0)),('R_nape',(.020,.3,1.432),(0,-1,0)),
        ('nape_center',(0,.3,1.428),(0,-1,0)),
        ('L_nape',(-.020,.3,1.432),(0,-1,0)),('L_nape_corner',(-.040,.3,1.446),(0,-1,0)),
        ('L_behind_ear',(-.3,.3,1.482),(.3,-.315,0)),('L_above_ear',(-.3,-.010,1.514),(1,0,0)),
        ('L_sideburn',(-.062,-.3,1.477),(0,1,0)),('L_temple',(-.055,-.3,1.510),(0,1,0)),
        ('L_front_corner',(-.038,-.3,1.526),(0,1,0)),('L_front_inner',(-.018,-.3,1.532),(0,1,0))]
    hits=[]
    for name,origin,direction in anchors:
        hit=tree.ray_cast(Vector(origin),Vector(direction).normalized(),.6)[0]
        assert hit is not None,('Missing anatomical anchor',name)
        hits.append({'name':name,'worldM':list(hit),'rayOrigin':origin,'rayDirection':direction})
    mult=next(m for m in body.modifiers if m.type=='MULTIRES')
    if HIGH:
        P=V;headFaces=np.flatnonzero(V[T,2].min(1)>1.405);polys=T[headFaces].tolist()
    else:
        mult.levels=0;bpy.context.view_layer.update();P,NT=b.evaluated(body,True)
        polys=[list(poly.vertices) for poly in body.data.polygons]
    adj=defaultdict(set);edgeFaces=defaultdict(list)
    for fi,poly in enumerate(polys):
        for x,y in zip(poly,poly[1:]+poly[:1]):
            edgeFaces[tuple(sorted((x,y)))].append(fi)
            if min(P[x,2],P[y,2])>1.405:adj[x].add(y);adj[y].add(x)
    allowed=np.array(sorted(adj),dtype='i4');ids=[int(allowed[np.argmin(np.linalg.norm(P[allowed]-np.array(h['worldM']),axis=1))]) for h in hits]
    assert len(set(ids))==len(ids),'Anatomical anchors collapse on native topology'
    loop=[];blocked=set();segments=[]
    for j,(start,end) in enumerate(zip(ids,ids[1:]+ids[:1])):
        path=shortest(adj,P,start,end,(blocked|set(ids))-{start,end});segments.append(path)
        loop.extend(path[:-1]);blocked.update(path[:-1])
    assert len(loop)==len(set(loop)),'Hairline is not a simple mesh loop'
    barrier={tuple(sorted((x,y))) for x,y in zip(loop,loop[1:]+loop[:1])}
    faceAdj=defaultdict(set)
    for edge,faces in edgeFaces.items():
        if edge not in barrier:
            for fi in faces:faceAdj[fi].update(set(faces)-{fi})
    centres=np.array([P[p].mean(0) for p in polys]);seed=int(np.argmax(centres[:,2]));selected={seed};queue=deque([seed])
    while queue:
        for fi in faceAdj[queue.popleft()]:
            if fi not in selected:selected.add(fi);queue.append(fi)
    assert 40<len(selected)<(80000 if HIGH else 1200) and centres[sorted(selected),2].min()>1.405,('Invalid scalp flood',len(selected))
    if not HIGH:
        attribute=body.data.attributes.new(FACE,'INT','FACE');attribute.data.foreach_set('value',np.arange(len(polys),dtype='i4'))
        mult.levels=3;bpy.context.view_layer.update()
    ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh(preserve_all_data_layers=True,depsgraph=bpy.context.evaluated_depsgraph_get());mesh.calc_loop_triangles()
    if HIGH:chosen=headFaces[sorted(selected)]
    else:
        nativeFace=np.array([x.value for x in mesh.attributes[FACE].data],dtype='i4');triFace=np.array([t.polygon_index for t in mesh.loop_triangles],dtype='i4')
        chosen=np.flatnonzero(np.isin(nativeFace[triFace],list(selected)))
    loopIds=np.array([list(t.loops) for t in mesh.loop_triangles],dtype='i4');uvData=np.empty(len(mesh.uv_layers[0].data)*2,dtype='f4');mesh.uv_layers[0].data.foreach_get('uv',uvData);uvData=uvData.reshape(-1,2)
    surfaceUV=uvData[loopIds];ev.to_mesh_clear()
    if not HIGH:body.data.attributes.remove(body.data.attributes[FACE]);bpy.context.view_layer.update()
    VV,TT=b.evaluated(body,True);assert np.array_equal(V,VV) and np.array_equal(T,TT)
    sourceIds,inv=np.unique(T[chosen],return_inverse=True);scalpMesh=bpy.data.meshes.new('AFN53_ANATOMICAL_SCALP');scalpMesh.from_pydata(V[sourceIds].tolist(),[],inv.reshape(-1,3).tolist());scalpMesh.update()
    attr=scalpMesh.attributes.new('AFN53_BodyTriangle','INT','FACE');attr.data.foreach_set('value',chosen.astype('i4'))
    uv=scalpMesh.uv_layers.new(name='AFN53_SourceSkinUV')
    for li,coord in enumerate(surfaceUV[chosen].reshape(-1,2)):uv.data[li].uv=coord
    domain=bpy.data.objects.new(scalpMesh.name,scalpMesh);bpy.context.scene.collection.objects.link(domain);domain.hide_render=True;domain.hide_set(True)
    domain['scope']='Actual body triangle region from artist anatomical anchors/geodesic native boundary. Initial authoring region, not accepted final follicle truth or collision proxy.'
    area=np.linalg.norm(np.cross(V[T[chosen,1]]-V[T[chosen,0]],V[T[chosen,2]]-V[T[chosen,0]]),axis=1)*.5
    rng=np.random.default_rng(530053);prob=area/area.sum();roots=[];normals=[];binding=[];rootUV=[];attempts=0
    while len(roots)<COUNT and attempts<20000:
        attempts+=1;ti=int(rng.choice(chosen,p=prob));u=rng.random(2)
        if u.sum()>1:u=1-u
        bc=np.r_[1-u.sum(),u];p=bc@V[T[ti]];normal=np.cross(V[T[ti,1]]-V[T[ti,0]],V[T[ti,2]]-V[T[ti,0]]);normal/=np.linalg.norm(normal)
        if roots and np.min(np.linalg.norm(np.array(roots)-p,axis=1))<.012:continue
        roots.append(p);normals.append(normal);binding.append({'bodyTriangle':ti,'bodyVertices':T[ti].tolist(),'barycentric':bc.tolist(),'normal':normal.tolist(),'rootOffsetM':.00018});rootUV.append(bc@surfaceUV[ti])
    assert len(roots)==COUNT,('Insufficient separated roots',len(roots))
    roots=np.array(roots);normals=np.array(normals);guides=sorted([o for o in bpy.data.objects if o.name.startswith('AFN48_CTRL_')],key=lambda o:o.name)
    guideRoots=np.array([o.matrix_world@o.data.splines[0].bezier_points[0].co for o in guides]);D=np.linalg.norm(roots[:,None]-guideRoots[None],axis=2);D[roots[:,None,0]*guideRoots[None,:,0]<0]=1e3;section=np.argmin(D,axis=1)
    # Root/elevation-specific lengths; outward normal is only the initial seed.
    length=np.clip(.19+1.0*(roots[:,2]-1.43)+rng.uniform(-.015,.015,COUNT),.17,.32)
    start=roots+normals*.00018;paths=start[:,None]+normals[:,None]*length[:,None,None]*np.linspace(0,1,N)[None,:,None]
    d=bpy.data.objects[OLD].data.copy();d.name=NAME;d.remove_curves(indices=list(range(1,len(d.curves))));d.resize_curves([N]);d.add_curves([N]*(COUNT-1))
    for attr in list(d.attributes):
        if attr.name.startswith('AFN38') or attr.name.startswith('.selection'):d.attributes.remove(attr)
    d.position_data.foreach_set('vector',paths.astype('f4').ravel());radii=np.broadcast_to(np.linspace(.000055,.000009,N),(COUNT,N)).copy();d.attributes['radius'].data.foreach_set('value',radii.astype('f4').ravel());d.attributes['curve_type'].data.foreach_set('value',[1]*COUNT);d.attributes['material_index'].data.foreach_set('value',[int(x)%len(d.materials) for x in section])
    d.surface=body;d.surface_uv_map=body.data.uv_layers[0].name
    if 'surface_uv_coordinate' in d.attributes:d.attributes.remove(d.attributes['surface_uv_coordinate'])
    attr=d.attributes.new('surface_uv_coordinate','FLOAT_VECTOR','CURVE');attr.data.foreach_set('vector',np.column_stack((rootUV,np.zeros(COUNT))).astype('f4').ravel())
    o=bpy.data.objects.new(NAME,d);bpy.context.scene.collection.objects.link(o);o.matrix_world=Matrix.Identity(4)
    o['aevrynd_layer']='EDITABLE_NEW_PRIMARY_GROOM';o['scope']='New separated actual-surface roots and normal-grown initial native master curves, not a final hairstyle.'
    bpy.data.objects[OLD].hide_render=True
    after=f.state()
    report={'source':str(SRC),'sourceSha256':b.sha(SRC),'anatomicalAnchors':hits,
        'boundaryVertexSpace':'ACTUAL_EVALUATED_BODY' if HIGH else 'NATIVE_CAGE',
        'anchorVertexIds':ids,'anchorSnapErrorsM':np.linalg.norm(P[ids]-np.array([h['worldM'] for h in hits]),axis=1).tolist(),
        'boundaryLoop':loop,'selectedBoundaryFaces':sorted(selected),
        'actualScalpTriangles':len(chosen),'actualScalpAreaM2':float(area.sum()),'scalpBoundsM':[V[T[chosen]].reshape(-1,3).min(0).tolist(),V[T[chosen]].reshape(-1,3).max(0).tolist()],
        'rootCount':COUNT,'rootMinimumSpacingM':.012,'lengthRangeM':[float(length.min()),float(length.max())],
        'rootBindings':binding,'rootSection':section.tolist(),'sectionGuideNames':[g.name for g in guides],
        'bodyGeometryAndUVMaterialsSkinStageUnchanged':all(after[key]==before[key] for key in ('meshes','materials','skinFields','stage')),
        'status':'NORMAL_GROWN_PRIMARY_SEED_NOT_FINISHED_HAIR','seconds':time.time()-tick}
    b.camera('face');bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    report.update(output=str(OUT),outputSha256=b.sha(OUT));save(TAG+'foundation-build.json',report)
    np.savez_compressed(E/(TAG+'foundation-data.npz'),roots=roots,normals=normals,initialPaths=paths,radii=radii,section=section,scalpTriangles=chosen)
    # Clearly separate scalp-only anatomy visualization from production hair.
    o.hide_render=True;domain.hide_render=False;domain.hide_set(False)
    mat=bpy.data.materials.new('AFN53_SCALP_DIAGNOSTIC_CYAN');mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.015,.25,.32,1);bs.inputs['Roughness'].default_value=.8;domain.data.materials.clear();domain.data.materials.append(mat)
    for vertex in domain.data.vertices:vertex.co+=vertex.normal*.00025
    f.E=E;f.render(TAG+'scalp-diagnostic',('face','oblique','profile'));k.k.a.i.ch.review.extras(TAG+'scalp-diagnostic',E)
    print('R53_FOUNDATION',len(selected),len(chosen),len(roots),time.time()-tick,flush=True)

if __name__=='__main__':main()
