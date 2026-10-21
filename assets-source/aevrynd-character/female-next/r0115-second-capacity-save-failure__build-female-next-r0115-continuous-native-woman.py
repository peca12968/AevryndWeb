"""One connected native adult skin through head/neck/shoulders, not another neck loft."""
from pathlib import Path
import bpy,numpy as np,json,time,datetime,hashlib,shutil,importlib.util
from mathutils import Vector
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0115-native-continuous-neck';S=R/'engine/assets/characters/female-next/source'
SRC=S/'aevrynd-female-next-r0113-b-native-neck-skin.blend';OUT=S/'aevrynd-female-next-r0115-a-continuous-native-woman.blend'
sp=importlib.util.spec_from_file_location('r115buildbase',Path(__file__).with_name('build-female-next-r0113-native-neck-character.py'));b=importlib.util.module_from_spec(sp);sp.loader.exec_module(b);q=b.q;b.u.v.E=E
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda v:v.tolist() if isinstance(v,np.ndarray) else v.item())+'\n',encoding='utf-8',newline='\n')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    tick=time.time();assert not OUT.exists()
    if not (E/'continuous-authoring-start.json').exists():save('continuous-authoring-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'action':'Replace failed cut-and-loft skin by original connected adult native head-neck-shoulder-body construction; preserve actual existing head/fibres by checked matching surface IDs, no pose-field transfer.'})
    bpy.ops.wm.open_mainfile(filepath=str(SRC));b.deliver(0);skin=bpy.data.objects['AFN113_COMPLETE_WOMAN_COHERENT_HEAD'];d,oldWorld,oldT=b.u.b.geom(skin);oldWorld=oldWorld.copy();oldT=oldT.copy();oldMesh=skin.data
    oldFibres={n:q.hair(bpy.data.objects[n]).copy() for n in ['AFN97_TUCKED_ARTIST_BOB_CHILDREN','AFN57_NATIVE_BROWS','AFN57_NATIVE_LASHES']}
    oldRadii={n:q.arr(bpy.data.objects[n].data.attributes['radius'].data,'value',len(bpy.data.objects[n].data.attributes['radius'].data)).copy() for n in oldFibres}
    oldLashHelper=q.geom(bpy.data.objects['AFN59_LASHES_NATIVE_POINT_POSES'])[1].copy()
    # The same pinned adult morphology and world transform as the retained head.
    info=json.loads((E.parent/'r0113-coherent-head-foundation/coherent-native-head-b.json').read_text(encoding='utf-8'));V,UV,F,FUV,groups=b.author.load_mesh();V+=b.author.target('macrodetails/caucasian-female-young.target.gz',len(V))
    cv=lambda P:P[:,[0,2,1]]*np.array([1,-1,1]);world=cv(V)*info['uniformScale']+np.array(info['translation']);faces=[f for f,g in zip(F,groups) if g=='body'];uvFaces=[f for f,g in zip(FUV,groups) if g=='body'];used=np.unique(np.concatenate(faces));assert np.array_equal(used,np.arange(len(used)))
    A=np.array(skin.matrix_world);AI=np.linalg.inv(A);local=lambda P:(P-A[:3,3])@AI[:3,:3].T
    raw=bpy.data.meshes.new('AFN115_ORIGINAL_CONNECTED_NATIVE_ADULT_SKIN');raw.from_pydata(local(world[used]).tolist(),[],faces);raw.update();raw.uv_layers.new(name='MakeHumanOriginalUV').data.foreach_set('uv',UV[np.concatenate(uvFaces)].astype('f4').ravel());raw.polygons.foreach_set('use_smooth',np.ones(len(raw.polygons),bool))
    source=bpy.data.objects.new('AFN115_EDITABLE_CONNECTED_NATIVE_ADULT_SOURCE',raw);bpy.context.scene.collection.objects.link(source);source.matrix_world=skin.matrix_world.copy();basis=source.shape_key_add(name='Basis')
    for side,label in [('L','left'),('R','right')]:
        delta=cv(b.author.target('expression/units/caucasian/eye-'+label+'-closure.target.gz',len(V)))*info['uniformScale'];key=source.shape_key_add(name='AFN115_NATIVE_CLOSED_'+side);key.relative_key=basis;key.data.foreach_set('co',local(world[used]+delta[used]).astype('f4').ravel())
    sub=source.modifiers.new('AFN115_ORIGINAL_CONNECTED_SKIN_SUBDIVISION','SUBSURF');sub.levels=sub.render_levels=2;bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();ev=source.evaluated_get(deps)
    mesh=bpy.data.meshes.new_from_object(ev,preserve_all_data_layers=True,depsgraph=deps);neutral=q.arr(mesh.vertices,'co',len(mesh.vertices),3).copy();newWorld=neutral@A[:3,:3].T+A[:3,3];poses={}
    for side in ['L','R']:
        key=source.data.shape_keys.key_blocks['AFN115_NATIVE_CLOSED_'+side];key.value=1.;source.data.shape_keys.update_tag();source.update_tag();bpy.context.view_layer.update();pd,P,PT=b.u.b.geom(source);poses[side]=local(P.copy());key.value=0.;source.data.shape_keys.update_tag();source.update_tag();bpy.context.view_layer.update()
    # Preserve the current physically authored material, use its already accepted
    # native UV branch everywhere. No pigment, exposure or normal simplification.
    for mat in oldMesh.materials:mesh.materials.append(mat)
    mesh.polygons.foreach_set('material_index',np.full(len(mesh.polygons),8,dtype='i4'))
    attr=mesh.attributes.get('AFN113_NATIVE_COLOR_WEIGHT') or mesh.attributes.new(name='AFN113_NATIVE_COLOR_WEIGHT',type='FLOAT',domain='POINT');attr.data.foreach_set('value',np.ones(len(mesh.vertices),'f4'))
    # Existing non-native UV consumers keep a named chart, now consistently the
    # same original native UV rather than a nearest projected old-body chart.
    nativeUV=q.arr(mesh.uv_layers['MakeHumanOriginalUV'].data,'uv',len(mesh.loops),2).copy()
    for layer in oldMesh.uv_layers:
        if layer.name not in mesh.uv_layers:mesh.uv_layers.new(name=layer.name).data.foreach_set('uv',nativeUV.ravel())
    mesh.uv_layers.active=mesh.uv_layers['MakeHumanOriginalUV'];mesh.uv_layers['MakeHumanOriginalUV'].active_render=True
    # Keep the same object/matrix targeted by the existing real fibre modifiers.
    skin.data=mesh;basis=skin.shape_key_add(name='Basis');face=bpy.data.objects['AFN59_FACE_CONTROLS']
    for side,prop in [('L','blink_left'),('R','blink_right')]:
        key=skin.shape_key_add(name='AFN113_CLOSED_'+side);key.relative_key=basis;key.data.foreach_set('co',poses[side].astype('f4').ravel());b.oldbuild.drive(key,face,prop,'v')
    b.deliver(0);nd,N,NT=b.u.b.geom(skin);N=N.copy();NT=NT.copy()
    # Coordinate matching is restricted to the same source head after original
    # topology subdivision. It is an identity reindex, not new follicle proof.
    tree=KDTree(len(N))
    for i,p in enumerate(N):tree.insert(Vector(p),i)
    tree.balance();requested=set();bindings=[]
    for name in ['AFN97_TUCKED_ARTIST_BOB_CHILDREN','AFN57_NATIVE_BROWS']:
        ob=bpy.data.objects[name]
        for j in range(3):
            at=ob.data.attributes['AFN97_ScalpVertex'+str(j)];ids=q.arr(at.data,'value',len(at.data),dtype='i4');requested.update(map(int,ids));bindings.append((ob,at,ids.copy()))
    lash=bpy.data.objects['AFN59_LASHES_NATIVE_POINT_POSES']
    for j in range(3):
        at=lash.data.attributes['AFN101_LashVertex'+str(j)];ids=q.arr(at.data,'value',len(at.data),dtype='i4');requested.update(map(int,ids));bindings.append((lash,at,ids.copy()))
    mapping={};errors=[]
    for i in sorted(requested):
        hit,j,dist=tree.find(Vector(oldWorld[i]));mapping[i]=j;errors.append(dist)
    # Stop only a genuinely failed identity premise; retain its evidence instead
    # of silently fitting roots or deleting fibres.
    save('source-identity-reindex.json',{'actualOldSourceVertices':len(requested),'maximumCoordinateMatchErrorM':max(errors),'quantilesM':np.quantile(errors,[0,.5,.95,1]),'samePinnedHeadAndWorldTransform':True,'notAnatomicalFolliclesOrContactProof':True})
    # The first run disproved total identity near the old cut. Explicitly bind
    # to actual new triangles and author new rest frames, retaining every shaft.
    centres=N[NT].mean(1);headIDs=np.flatnonzero(centres[:,2]>1.39);surface=BVHTree.FromPolygons(N.tolist(),NT[headIDs].tolist(),all_triangles=True,epsilon=0.)
    expected={};rootChanges={}
    for name in ['AFN97_TUCKED_ARTIST_BOB_CHILDREN','AFN57_NATIVE_BROWS']:
        ob=bpy.data.objects[name];data=ob.data;previous=oldFibres[name];counts=np.array([c.points_length for c in data.curves],dtype='i4');starts=np.r_[0,np.cumsum(counts)[:-1]];HA=np.array(ob.matrix_world);HI=np.linalg.inv(HA[:3,:3]);inLocal=lambda P:(P-HA[:3,3])@HI.T;Vlocal=inLocal(N);points=inLocal(previous);newPoints=points.copy();radii=q.arr(data.attributes['radius'].data,'value',len(points));ids=[];weights=[];roots=[];frames=[];changes=[]
        for start,count in zip(starts,counts):
            hit,no,fi,dist=surface.find_nearest(Vector(previous[start]));tri=NT[headIDs[fi]];w=b.u.a.bary(np.array(hit),N[tri]);p=Vlocal[tri];t=p[1]-p[0];t/=np.linalg.norm(t);n=np.cross(p[1]-p[0],p[2]-p[0]);n/=np.linalg.norm(n);root=w@p+n*radii[start];newPoints[start:start+count]+=root-points[start];ids.append(tri);weights.append(w);roots.append(root);frames.append([t,np.cross(n,t),n]);changes.append(np.linalg.norm((root-points[start])@HA[:3,:3].T))
        ids=np.array(ids,dtype='i4');frames=np.array(frames);data.attributes['position'].data.foreach_set('vector',newPoints.astype('f4').ravel())
        for j in range(3):data.attributes['AFN97_ScalpVertex'+str(j)].data.foreach_set('value',ids[:,j])
        for n,val in [('RootBarycentric',weights),('RestRoot',roots),('RestT',frames[:,0]),('RestB',frames[:,1]),('RestN',frames[:,2])]:data.attributes['AFN97_'+n].data.foreach_set('vector',np.array(val,dtype='f4').ravel())
        data.attributes['AFN97_RootRadiusNative'].data.foreach_set('value',radii[starts]);data.update_tag();ob.update_tag();expected[name]=newPoints@HA[:3,:3].T+HA[:3,3];rootChanges[name]=np.quantile(changes,[0,.5,.95,1])
    LA=np.array(lash.matrix_world);LI=np.linalg.inv(LA[:3,:3]);VL=(N-LA[:3,3])@LI.T;LP=(oldLashHelper-LA[:3,3])@LI.T;rows=json.loads((E.parent/'r0113-coherent-head-foundation/b-mobile-lash-bindings.json').read_text(encoding='utf-8'));ids=np.empty((len(LP),3),'i4');weights=np.empty_like(LP);offset=np.empty_like(LP);lashChanges=[]
    for row in rows:
        start=row['pointStart'];end=start+row['points'];hit,no,fi,dist=surface.find_nearest(Vector(oldLashHelper[start]));tri=NT[headIDs[fi]];w=b.u.a.bary(np.array(hit),N[tri]);p=VL[tri];t=p[1]-p[0];t/=np.linalg.norm(t);n=np.cross(p[1]-p[0],p[2]-p[0]);n/=np.linalg.norm(n);frame=np.column_stack((t,np.cross(n,t),n));ids[start:end]=tri;weights[start:end]=w;offset[start:end]=(LP[start:end]-LP[start])@frame;lashChanges.append(dist);row.update(actualR115Triangle=tri.tolist(),actualR115Barycentric=w.tolist(),sourceRootReattachmentDistanceM=dist)
    for j in range(3):lash.data.attributes['AFN101_LashVertex'+str(j)].data.foreach_set('value',ids[:,j])
    lash.data.attributes['AFN101_LashBarycentric'].data.foreach_set('vector',weights.astype('f4').ravel());lash.data.attributes['AFN101_LashLocalFrameOffset'].data.foreach_set('vector',offset.astype('f4').ravel());lash.data.update_tag();lash.update_tag();rootChanges['AFN57_NATIVE_LASHES']=np.quantile(lashChanges,[0,.5,.95,1]);save('actual-lash-rebindings.json',rows)
    source.hide_render=True;source.hide_set(True);b.deliver(0);fibres={}
    for n,previous in oldFibres.items():
        ob=bpy.data.objects[n];actual=q.hair(ob);err=float(np.linalg.norm(actual-previous,axis=1).max());rad=q.arr(ob.data.attributes['radius'].data,'value',len(oldRadii[n]));assert np.array_equal(rad,oldRadii[n]);targetError=None if n not in expected else float(np.linalg.norm(actual-expected[n],axis=1).max());fibres[n]={'curves':len(ob.data.curves),'points':len(actual),'maximumWorldChangeM':err,'newRootTranslationQuantilesM':rootChanges[n],'actualAgainstNewAuthoredRestMaxErrorM':targetError,'allRadiiByteExact':True,'noFibreDeleted':True}
        if targetError is not None:assert targetError<8e-6
    # Inspect the original connected construction as a source reference, then
    # the complete textured woman, without a detached proxy serving as output.
    save('a-build-summary.json',{'source':str(SRC),'output':str(OUT),'foundation':'Same MakeHuman adult female-young native topology/own blink and same whole-head world staging, now original connected whole body including uninterrupted neck and shoulders. No cuts, zipper, interpolated neck annulus or independent collar.','bodyShapeChangedAndRequiresWholeBodyReview':True,'rawSourceVertices':len(raw.vertices),'actualCompleteVertices':len(N),'actualCompleteTriangles':len(NT),'renderSkin':skin.name,'editableSource':source.name,'nativeMaterial':mesh.materials[8].name,'nativeColourWeightAllOne':True,'oldPhysicalShaderCopiedUnchangedNoPigmentOrExposureAdjustment':True,'allFibres':fibres,'originalSourceIdentityMaxErrorM':max(errors),'bodyRigOralGuideFolliclesFiniteContactRuntimeUnaccepted':True,'secondsBeforePreview':time.time()-tick})
    np.savez_compressed(E/'continuous-source-lineage.npz',oldRequestedVertexIDs=np.array(sorted(requested),dtype='i4'),newCorrespondingVertexIDs=np.array([mapping[i] for i in sorted(requested)],dtype='i4'),oldRequestedWorld=oldWorld[sorted(requested)],newCorrespondingWorld=N[[mapping[i] for i in sorted(requested)]],sourceUniformScale=np.array(info['uniformScale']),sourceTranslation=np.array(info['translation']))
    skin['AFN115_scope']='One continuous native adult skin through head-neck-body, same working woman head and all fibres. No complete function/contact/runtime acceptance. Original r113 B remains immutable rollback.'
    # Drop only now-unused mesh data; original full scene files remain intact.
    if oldMesh.users==0:bpy.data.meshes.remove(oldMesh)
    b.deliver(0);bpy.context.preferences.filepaths.save_version=0
    temp=Path('C:/Users/USER/AppData/Local/Temp')/OUT.name;assert not temp.exists();bpy.ops.wm.save_as_mainfile(filepath=str(temp),compress=True,copy=True,relative_remap=False)
    free=shutil.disk_usage(S).free;assert free>temp.stat().st_size+18000000,('Keep full temporary source; canonical capacity insufficient',free,temp.stat().st_size)
    shutil.copyfile(temp,OUT);assert sha(temp)==sha(OUT);save('complete-source-save.json',{'canonicalSource':str(OUT),'temporaryVerifiedFullCopy':str(temp),'bytes':OUT.stat().st_size,'sha256':sha(OUT),'byteIdentical':True,'canonicalSourceContextForRelativeTexturesPreserved':True})
    views=[]
    for view in ['face','body-face','profile','back']:
        views.append(b.u.v.image('a-continuous-native-woman',view));save('a-view-controls.json',views)
    for label,value in [('half',.5),('closed',1.),('restored',0.)]:
        b.deliver(value);views.append(b.u.v.image('a-continuous-native-woman-'+label,'face'));save('a-view-controls.json',views)
    print('R115_CONTINUOUS_NATIVE_COMPLETE_WOMAN_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
