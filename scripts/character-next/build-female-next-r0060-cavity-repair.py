"""One topology-aware socket repair; actual optical geometry stays unchanged.

Replace a nonmanifold duplicate disk with one continuous conjunctival lining.
The two real skin socket disks are mapped around supporting planes of the
original optical convex hull. Boundary cage vertices stay fixed. Subdivision
effects and finite contact remain independent acceptance tests, not assumptions.
"""
from pathlib import Path
from collections import defaultdict
import bpy,numpy as np,json,time,importlib.util,sys
sp=importlib.util.spec_from_file_location('blink60',Path(__file__).with_name('build-female-next-r0059-authored-blink.py'));k=importlib.util.module_from_spec(sp);sp.loader.exec_module(k)
b=k.b;f=k.f;E=b.R/'Evidence/character-female-next/r0060-ocular-assembly';PREV=E.parent/'r0059-authored-blink';OUT=b.S/'aevrynd-female-next-r0060-a-cavity-assembly-study.blend'
def save(n,x):(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2,default=lambda v:v.item() if isinstance(v,np.generic) else (_ for _ in ()).throw(TypeError(type(v).__name__)))+'\n',encoding='utf8')
def harmonic(inside,boundary,adj,bvals):
    index={v:i for i,v in enumerate(inside)};L=np.zeros((len(inside),len(inside)));rhs=np.zeros((len(inside),bvals.shape[1]));B={v:i for i,v in enumerate(boundary)}
    for v,ii in index.items():
        L[ii,ii]=len(adj[v])
        for n in adj[v]:
            if n in index:L[ii,index[n]]-=1
            else:rhs[ii]+=bvals[B[n]]
    return np.linalg.solve(L,rhs)
def patch_info(group,faces,P,C):
    fs=group['faces'];es=defaultdict(list);adj=defaultdict(set)
    for fi in fs:
        face=faces[fi]
        for x,y in zip(face,face[1:]+face[:1]):es[tuple(sorted((x,y)))].append(fi);adj[x].add(y);adj[y].add(x)
    boundaryEdges=[e for e,ff in es.items() if len(ff)==1];boundary=sorted(set(x for edge in boundaryEdges for x in edge));inside=sorted(set(adj)-set(boundary));assert len(adj)-len(es)+len(fs)==1 and len(boundary)==28
    direction=P[boundary]-C;angle=np.arctan2(direction[:,2],direction[:,0]);buv=np.column_stack((np.cos(angle),np.sin(angle)));iuv=harmonic(inside,boundary,adj,buv);uv={v:p for v,p in zip(boundary,buv)};uv.update({v:p for v,p in zip(inside,iuv)});assert max(np.linalg.norm(x) for x in iuv)<1
    return {'faces':fs,'boundary':boundary,'inside':inside,'adj':adj,'uv':uv,'firstRing':sorted(set(fi for e in boundaryEdges for fi in es[e]))}
def repair(P,patch,optic,gap):
    C=(optic.min(0)+optic.max(0))*.5;B=patch['boundary'];I=patch['inside'];dB=P[B]-C;dB/=np.linalg.norm(dB,axis=1)[:,None];H=harmonic(I,B,patch['adj'],dB);directions={v:q for v,q in zip(B,dB)}
    # Stereographic disk-to-sphere coordinates keep the entire cup distributed
    # smoothly. A previous linear pole blend failed a positive-plane guard and
    # was stopped before saving a candidate; it is not tuned further.
    kapB=np.sqrt(np.maximum(1-dB[:,1],1e-12)/np.maximum(1+dB[:,1],1e-12))[:,None];kapI=harmonic(I,B,patch['adj'],kapB)
    for v,kap in zip(I,kapI[:,0]):
        u,w=patch['uv'][v];r2=kap*kap*(u*u+w*w);directions[v]=np.array((2*kap*u,1-r2,2*kap*w))/(1+r2)
    radius={v:0. for v in I};boundaryBad=[];planeRows=[];Bset=set(B)
    for fi in patch['faces']:
        face=FACES[fi];D=np.array([directions[v] for v in face]);n=D.mean(0);n/=np.linalg.norm(n);fixed=[v for v in face if v in Bset];options=[n]
        if fixed:options += [directions[v] for v in fixed]
        def plane(nn):return float(((optic-C)@nn).max()+gap)
        free=[v for v in face if v not in Bset];options=[nn for nn in options if all(directions[v]@nn>.01 for v in free)];assert options,('No common forward support plane',fi)
        if fixed:
            n=max(options,key=lambda nn:float(np.min((P[fixed]-C)@nn)-plane(nn)))
        else:n=options[0]
        support=plane(n);slack=float(np.min((P[fixed]-C)@n)-support) if fixed else None
        if fixed and slack<0:boundaryBad.append({'sourceFace':fi,'fixedBoundarySlackM':slack,'fixedVertices':fixed})
        for v in face:
            if v in Bset:continue
            den=float(directions[v]@n);assert den>.01,('Folded spherical patch mapping',fi,v,den);radius[v]=max(radius[v],support/den)
        planeRows.append({'sourceFace':fi,'normal':n.tolist(),'supportRelativeToCentreM':support})
    Q=P.copy()
    for v,r in radius.items():Q[v]=C+directions[v]*r
    originalRadius=np.linalg.norm(optic-C,axis=1).max();assert max(radius.values())<originalRadius*3
    return Q,{'centreLocalM':C.tolist(),'physicalStandOffLocalM':gap,'fixedBoundaryVertices':len(B),'changedInteriorVertices':len(I),'infeasibleFixedBoundaryFaces':boundaryBad,'supportPlanes':planeRows,'maximumInteriorDisplacementLocalM':float(np.linalg.norm(Q[I]-P[I],axis=1).max()),'scope':'Native control-cage construction only. Not a proof for the subdivided rendered surface; actual neutral/closed finite surfaces must be retested.'}
FACES=[]
def make_component(old,raw,ci,name,faces,corrections,firstRing):
    used=np.flatnonzero(raw['components']==ci);fi=np.flatnonzero(raw['faceComponents']==ci);index=np.full(len(raw['positions']),-1,dtype='i4');index[used]=np.arange(len(used));mesh=bpy.data.meshes.new(name+'_NATIVE_MESH');mesh.from_pydata(raw['positions'][used].tolist(),[],[index[faces[i]].tolist() for i in fi]);mesh.update();uv=mesh.uv_layers.new(name='VitruvianUV.UDIM');starts=np.r_[0,np.cumsum(raw['polygonCounts'])];loops=np.concatenate([np.arange(starts[i],starts[i+1]) for i in fi]);uv.data.foreach_set('uv',raw['uv'][loops].ravel())
    for mat in old.data.materials:mesh.materials.append(mat)
    materials=raw['materials'][fi].copy()
    if ci==4:materials[np.isin(fi,list(firstRing))]=7
    mesh.polygons.foreach_set('material_index',materials)
    for p in mesh.polygons:p.use_smooth=True
    mesh.attributes.new('AFN60_NativeVertexID','INT','POINT').data.foreach_set('value',used.astype('i4'));mesh.attributes.new('AFN60_NativeFaceID','INT','FACE').data.foreach_set('value',fi.astype('i4'))
    flag=mesh.attributes.new('AFN60_ReplaceOldBranchDisk','BOOLEAN','FACE');flag.data.foreach_set('value',(raw['materials'][fi]==7).tolist())
    obj=bpy.data.objects.new(name,mesh);bpy.context.scene.collection.objects.link(obj);obj.matrix_world=old.matrix_world.copy();obj.shape_key_add(name='Basis');female=obj.shape_key_add(name='AFN57_Supplied_Female_Morph');female.data.foreach_set('co',raw['AFN57_Supplied_Female_Morph'][used].ravel());female.value=1
    for side in ('Left','Right'):
        key=obj.shape_key_add(name='AFN59_Blink_'+side);positions=raw['AFN59_Blink_'+side].astype('f8').copy()
        if ci==4:positions+=corrections[side]-corrections['Neutral']
        key.data.foreach_set('co',positions[used].astype('f4').ravel());k.driver(key,bpy.data.objects[k.CTRL],side,'v')
    if ci==4:
        key=obj.shape_key_add(name='AFN60_Cavity_Repair');key.data.foreach_set('co',(raw['positions'][used]+corrections['Neutral'][used]).astype('f4').ravel());key.value=1
    sub=obj.modifiers.new('AFN60_NATIVE_SUBDIVISION','SUBSURF');sub.levels=1;sub.render_levels=2
    if ci==4:
        ng=bpy.data.node_groups.new('AFN60_SINGLE_CONTINUOUS_LINING','GeometryNodeTree');ng.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');ng.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry');inp=ng.nodes.new('NodeGroupInput');out=ng.nodes.new('NodeGroupOutput');attr=ng.nodes.new('GeometryNodeInputNamedAttribute');attr.data_type='BOOLEAN';attr.inputs['Name'].default_value='AFN60_ReplaceOldBranchDisk';delete=ng.nodes.new('GeometryNodeDeleteGeometry');delete.domain='FACE';delete.mode='ALL';ng.links.new(inp.outputs['Geometry'],delete.inputs['Geometry']);ng.links.new(attr.outputs['Attribute'],delete.inputs['Selection']);ng.links.new(delete.outputs['Geometry'],out.inputs['Geometry']);md=obj.modifiers.new('AFN60_REPLACE_DUPLICATE_BRANCH_WITH_REAL_LINING','NODES');md.node_group=ng
    obj['sourceComponent']=ci;obj['scope']='Original whole connected component with exact source vertex/face IDs, UV and controls. Eye outer shells remain combined sclera/cornea approximations; iris/pupil remain one connected surface, not complete anatomical separation.'
    return obj
def main():
    global FACES
    tick=time.time();recovery='--recover-saved' in sys.argv;originalOutputHash=b.sha(OUT) if recovery else None
    if not recovery:assert not OUT.exists(),'Do not overwrite an existing model snapshot.'
    a=json.loads((PREV/'a-build-summary.json').read_text());source=Path(a['output']);assert b.sha(source)==a['outputSha256'];raw=np.load(E/'native-component-lineage.npz');data={key:raw[key] for key in raw.files};raw=data;corners=raw['corners'];starts=np.r_[0,np.cumsum(raw['polygonCounts'])];FACES=[corners[starts[i]:starts[i+1]].tolist() for i in range(len(starts)-1)];groups=json.loads((E/'native-socket-patches.json').read_text())['groups'];sockets=[g for g in groups if len(g['faces'])<1000];assert len(sockets)==2
    bpy.ops.wm.open_mainfile(filepath=str(source));old=bpy.data.objects[k.BODY];stage=f.v.stage();F=raw['AFN57_Supplied_Female_Morph'].astype('f8');base=raw['positions'].astype('f8');D={side:raw['AFN59_Blink_'+side].astype('f8')-base for side in ('Left','Right')};neutral=np.zeros_like(F);closed={side:np.zeros_like(F) for side in ('Left','Right')};reports={};firstRing=set();scale=np.linalg.norm(np.array(old.matrix_world)[:3,:3],ord=2)
    for g in sockets:
        positive=np.mean(F[g['vertices'],0])>0;side='Left' if positive else 'Right';opticIDs=np.flatnonzero(np.isin(raw['components'],(0,2) if positive else (1,3)));optic=F[opticIDs];C=(optic.min(0)+optic.max(0))*.5;patch=patch_info(g,FACES,F,C);firstRing.update(patch['firstRing']);opticEnvelope=np.concatenate((optic,(F+D[side])[opticIDs]));Q,info=repair(F,patch,opticEnvelope,.00008/scale);neutral[patch['inside']]=Q[patch['inside']]-F[patch['inside']];pose=F+D[side];closed[side][patch['inside']]=Q[patch['inside']]-pose[patch['inside']];reports[side]={'neutral':info,'closed':{'method':'Posterior native cup remains fixed while the original aperture boundary follows the authored blink. Supporting planes enclose both original neutral/closed optical vertices. Actual subdivided transition still needs testing.'},'originalPatchFaces':patch['faces'],'fixedBoundarySourceVertexIDs':patch['boundary'],'interiorSourceVertexIDs':patch['inside']}
    corrections={'Neutral':neutral,'Left':neutral.copy(),'Right':neutral.copy()}
    for side,report in reports.items():corrections[side][report['interiorSourceVertexIDs']]=closed[side][report['interiorSourceVertexIDs']]
    names={0:'AFN60_L_EYE_OUTER_SHELL_APPROX',1:'AFN60_R_EYE_OUTER_SHELL_APPROX',2:'AFN60_L_IRIS_PUPIL_SURFACE',3:'AFN60_R_IRIS_PUPIL_SURFACE',4:'AFN60_BODY_ORAL_AND_OCULAR_LINING'}
    if recovery:
        saved=np.load(E/'a-native-cavity-corrections.npz');assert all(np.array_equal(saved[key],value) for key,value in corrections.items());bpy.ops.wm.open_mainfile(filepath=str(OUT));assert all(name in bpy.data.objects for name in names.values());assert b.sha(OUT)==originalOutputHash
        save('a-recovery-receipt.json',{'reason':'Original model saved successfully, then JSON metadata serialization rejected a numpy.float32. Recompute identical metadata and render saved source; no geometry rebuild or source overwrite.','source':str(OUT),'originalSha256':originalOutputHash,'sourceWrittenByRecovery':False})
    else:
        np.savez_compressed(E/'a-native-cavity-corrections.npz',**corrections);objects=[make_component(old,raw,ci,name,FACES,corrections,firstRing) for ci,name in names.items()];old.name='AFN60_ORIGINAL_SOURCE_CAGE';old.hide_render=True;old.hide_set(True);old['scope']='Unmodified original full source/control cage retained for comparison, not rendered. Visible components replace it exactly once; duplicate sourceTearline disk replaced by one corrected continuous skin/conjunctival lining.'
        bpy.context.scene.frame_set(1);bpy.context.view_layer.update();assert f.v.stage()==stage;b.camera('face');bpy.context.scene.camera.data.lens=85;bpy.context.preferences.filepaths.save_version=0;bpy.context.scene['AFN60_status']='PARTITIONED_OCULAR_CAVITY_REPAIR_STUDY_NOT_ACCEPTED';bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    save('a-build-summary.json',{'revision':'female-next-r0060','source':str(source),'sourceSha256':b.sha(source),'output':str(OUT),'outputSha256':b.sha(OUT),'method':'Exact connected-component partition plus original topological socket disk repair around finite optical supporting planes, fixed native cage rim. Replace nonmanifold duplicate membrane with single continuous conjunctival lining and wet rim material.','visibleComponents':names,'originalBodyCageRetainedHidden':True,'originalOpticsNativeGeometryNotRescaledOrTranslated':True,'physicalStandOffWorldM':.00008,'nativeInteriorCorrections':reports,'replacementLiningNativeFaces':sorted(firstRing),'sourceGhostDiskNativeFaces':584,'geometryRemovalReason':'56source edges had three incident faces4/4/7. Original duplicated disk is replaced by real repaired native skin cavity; first interior lining ring uses wet material. It is not an accepted separate tear-film volume.','subdivisionWarning':'Native rim cage positions fixed; their evaluated positions may change as neighbouring interior faces are rebuilt. Surface contacts/appearance require actual testing.','nativeBlinkControlsRetained':True,'scalpHairNativeFacialHairDataUnchanged':True,'facialHairAttachmentWarning':'Source curves still follow r59native poses. If evaluated skin rim moves, exact follicle coupling must be revalidated/rebuilt before adoption.','stageUnchanged':True,'status':'PENDING_ACTUAL_APPEARANCE_AND_CONTACT','seconds':time.time()-tick})
    for frame,label in ((1,'a-neutral'),(21,'a-closed')):
        k.set_frame(frame);f.E=E;f.render(label,('face','profile','oblique'));k.k.k.k.k.k.a.i.ch.review.extras(label,E)
    k.set_frame(1);print('R60_CAVITY_ASSEMBLY_PREVIEW',str(OUT),time.time()-tick,flush=True)
if __name__=='__main__':main()
