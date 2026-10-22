"""Reconstruct moving cavity tessellation and aspherical lamellar sliding path.
The existing actual eye assembly and original cavity define a construction surface,
never collision proof. No failure faces are removed or optical geometry rescaled.
"""
from pathlib import Path
import bpy,bmesh,numpy as np,json,time,datetime,importlib.util
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0145-aspherical-lid-wall';S=R/'engine/assets/characters/female-next/source';SRC=S/'r0144-source/aevrynd-female-next-r0144-a-current-skin-blink.blend';OUT=S/'r0145-source/aevrynd-female-next-r0145-a-aspherical-lid-wall.blend'
sp=importlib.util.spec_from_file_location('r145base',Path(__file__).with_name('build-female-next-r0144-current-skin-blink.py'));h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h);a=h.a;a.b.u.v.E=E
PROPS=h.PROPS
def save(n,x):(E/n).write_bytes((json.dumps(x,indent=2,default=lambda q:q.tolist() if isinstance(q,np.ndarray) else q.item() if isinstance(q,np.generic) else str(q))+'\n').encode())
def attr_array(mesh,name):
    p=mesh.attributes[name];x=np.empty(len(p.data),dtype='i4' if p.data_type=='INT' else 'f4');p.data.foreach_get('value',x);return x
def add_slide(ob,centres,rig):
    md=ob.modifiers[0];assert md.type=='NODES';ng=md.node_group;N=ng.nodes;L=ng.links;setp=next(n for n in N if n.bl_idname=='GeometryNodeSetPosition');pos=next(n for n in N if n.bl_idname=='GeometryNodeInputPosition').outputs['Position'];current=setp.inputs['Position'].links[0].from_socket
    def vector(op,x,y=None):
        n=N.new('ShaderNodeVectorMath');n.operation=op
        if hasattr(x,'node'):L.new(x,n.inputs[0])
        else:n.inputs[0].default_value=x
        if y is not None:
            if hasattr(y,'node'):L.new(y,n.inputs[1])
            else:n.inputs[1].default_value=y
        return n.outputs['Value' if op=='LENGTH' else 'Vector']
    def math(op,x,y=None):
        n=N.new('ShaderNodeMath');n.operation=op
        for i,v in enumerate([x,y]):
            if v is None:continue
            if hasattr(v,'node'):L.new(v,n.inputs[i])
            else:n.inputs[i].default_value=v
        return n.outputs[0]
    def boolean(op,x,y=None):
        n=N.new('FunctionNodeBooleanMath');n.operation=op;L.new(x,n.inputs[0])
        if y is not None:L.new(y,n.inputs[1])
        return n.outputs[0]
    A=np.array(ob.matrix_world);inv=np.linalg.inv(A);scale=np.linalg.norm(A[:3,0]);activeControls=[];reports=[]
    for side in ['L','R']:
        C=(inv@np.r_[centres[side],1])[:3];target=bpy.data.objects['AFN138_'+side+'_ANATOMICAL_SOCKET_CONSTRUCTION'];info=N.new('GeometryNodeObjectInfo');info.name='AFN145_ASPHERICAL_INNER_SURFACE_'+side;info.transform_space='RELATIVE';info.inputs['Object'].default_value=target
        def ray(direction):
            node=N.new('GeometryNodeRaycast');node.data_type='FLOAT';L.new(info.outputs['Geometry'],node.inputs['Target Geometry']);node.inputs['Source Position'].default_value=C;L.new(direction,node.inputs['Ray Direction']);node.inputs['Ray Length'].default_value=.1/scale;return node
        oldDirection=vector('SUBTRACT',pos,C);direction=vector('SUBTRACT',current,C);restHit=ray(oldDirection);newHit=ray(direction)
        originalGap=math('SUBTRACT',vector('LENGTH',oldDirection),vector('LENGTH',vector('SUBTRACT',restHit.outputs['Hit Position'],C)))
        radius=math('ADD',vector('LENGTH',vector('SUBTRACT',newHit.outputs['Hit Position'],C)),originalGap);unit=vector('NORMALIZE',direction);mul=N.new('ShaderNodeVectorMath');mul.operation='SCALE';L.new(unit,mul.inputs[0]);L.new(radius,mul.inputs['Scale']);mapped=vector('ADD',C,mul.outputs['Vector'])
        angle=N.new('GeometryNodeInputNamedAttribute');angle.data_type='FLOAT';angle.inputs['Name'].default_value='AFN144_Angle_'+side;value=N['AFN144_NATIVE_BLINK_VALUE_'+side].outputs[0];selected=math('GREATER_THAN',math('ABSOLUTE',math('MULTIPLY',angle.outputs['Attribute'],value)),0.);hits=boolean('AND',restHit.outputs['Is Hit'],newHit.outputs['Is Hit']);use=boolean('AND',selected,hits)
        switch=N.new('GeometryNodeSwitch');switch.input_type='VECTOR';L.new(use,switch.inputs['Switch']);L.new(current,switch.inputs['False']);L.new(mapped,switch.inputs['True']);current=switch.outputs[0]
        # Keep hit failures inspectable on actual evaluated geometry. No silent fallback acceptance.
        bad=boolean('AND',selected,boolean('NOT',hits));store=N.new('GeometryNodeStoreNamedAttribute');store.data_type='BOOLEAN';store.domain='POINT';store.inputs['Name'].default_value='AFN145_SlideRayFailure_'+side;L.new(bad,store.inputs['Value']);geometry=setp.inputs['Geometry'].links[0].from_socket;L.new(geometry,store.inputs['Geometry']);L.new(store.outputs['Geometry'],setp.inputs['Geometry'])
        activeControls.append(math('GREATER_THAN',value,0.));reports.append({'side':side,'actualConstructionSurface':target.name,'originalNativeRadialInnerOuterGapPreserved':True,'extraClearanceOrInflationAdded':0.,'rayLengthLocal':.1/scale,'objectSpaceOpticalCentre':C})
    L.new(current,setp.inputs['Position'])
    # Preserve the zero-blink source evaluation exactly, including all original gaze poses.
    inp=next(n for n in N if n.bl_idname=='NodeGroupInput');out=next(n for n in N if n.bl_idname=='NodeGroupOutput');bypass=N.new('GeometryNodeSwitch');bypass.input_type='GEOMETRY';L.new(boolean('OR',*activeControls),bypass.inputs['Switch']);L.new(inp.outputs['Geometry'],bypass.inputs['False']);L.new(setp.outputs['Geometry'],bypass.inputs['True']);L.new(bypass.outputs[0],out.inputs['Geometry']);ng.name='AFN145_ASPHERICAL_LAMELLAR_SLIDE_'+ob.name
    return reports
def main():
    tick=time.time();assert not OUT.exists();bpy.ops.wm.open_mainfile(filepath=str(SRC));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update();skin=bpy.data.objects[h.h.SKIN];rig=bpy.data.objects['AFN138_ACTUAL_CURRENT_GAZE_RIG'];names=a.FIXED+a.MOVING;baseline={n:a.geometry(bpy.data.objects[n]) for n in names};protected=a.a.protected();raw={n:a.rawsig(bpy.data.objects[n]) for n in names};W,T=baseline[h.h.SKIN]
    save('direct-aspherical-wall-authoring-start.json' if not (E/'direct-aspherical-wall-authoring-start.json').exists() else 'lineage-repair-authoring-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'originalStartedUTC':'2026-10-22T01:14:55+00:00','action':'Directly reconstruct actual moving cavity tessellation and a shared aspherical lamellar sliding path. Original angular closure field retained, ocular meshes unchanged, no failure faces removed or cap added.'})
    prior=json.loads((E.parent/'r0144-current-skin-blink/current-skin-blink-construction.json').read_text('utf-8'));centres={s:np.array(prior['actualNativeDomains'][s]['actualOpticalCentreWorld']) for s in ['L','R']};trees={}
    for side in ['L','R']:
        V,F=a.geometry(bpy.data.objects['AFN138_'+side+'_ANATOMICAL_SOCKET_CONSTRUCTION']);trees[side]=BVHTree.FromPolygons([Vector(p) for p in V],F.tolist(),all_triangles=True)
    A=np.array(skin.matrix_world);near=np.min(np.linalg.norm(W[:,None,:]-np.array(list(centres.values()))[None,:,:],axis=2),axis=1)<.025;wall=np.zeros(len(W),bool)
    for i in np.flatnonzero(near):
        side='L' if W[i,0]>0 else 'R';wall[i]=trees[side].find_nearest(Vector(W[i]))[3]<3e-6
    rawBefore=np.empty((len(skin.data.vertices),3),dtype='f4');skin.data.vertices.foreach_get('co',rawBefore.ravel());assert len(rawBefore)==len(W)
    bm=bmesh.new();bm.from_mesh(skin.data);bm.verts.ensure_lookup_table();originalVerts=set(bm.verts);ids=bm.verts.layers.int.new('AFN145_ORIGINAL_VERTEX_ID');domain=bm.verts.layers.float.new('AFN145_ORIGINAL_CAVITY_DOMAIN')
    for i,v in enumerate(bm.verts):v[ids]=i;v[domain]=float(wall[i])
    faces=[f for f in bm.faces if all(v[domain]>.999 for v in f.verts)];oldWallFaces=len(faces);assert oldWallFaces>20;bmesh.ops.triangulate(bm,faces=faces)
    lengths=[]
    for iteration in range(6):
        edges=[e for e in bm.edges if all(v[domain]>.999 for v in e.verts) and any(all(v[domain]>.999 for v in f.verts) for f in e.link_faces) and np.linalg.norm(A[:3,:3]@np.array(e.verts[1].co-e.verts[0].co))>.0012]
        lengths.append(len(edges))
        if not edges:break
        bmesh.ops.subdivide_edges(bm,edges=edges,cuts=1,use_grid_fill=True,use_only_quads=False)
        for v in bm.verts:
            if v not in originalVerts:v[ids]=-1
    bm.normal_update();bm.to_mesh(skin.data);bm.free();skin.data.update();candidateIds=attr_array(skin.data,'AFN145_ORIGINAL_VERTEX_ID');rawAfter=np.empty((len(skin.data.vertices),3),dtype='f4');skin.data.vertices.foreach_get('co',rawAfter.ravel());mapping=np.full(len(rawAfter),-1,dtype='i4');used=set();byCoordinate={}
    for i,p in enumerate(rawBefore):byCoordinate.setdefault(tuple(p),[]).append(i)
    for j,oldId in enumerate(candidateIds):
        if 0<=oldId<len(rawBefore) and int(oldId) not in used and np.array_equal(rawAfter[j],rawBefore[oldId]):mapping[j]=oldId;used.add(int(oldId))
    for j in np.flatnonzero(mapping<0):
        choices=byCoordinate.get(tuple(rawAfter[j]),[])
        for oldId in choices:
            if oldId not in used:mapping[j]=oldId;used.add(oldId);break
    save('native-subdivision-lineage-readback.json',{'originalHandle75524FailedBeforeAnyFullSource':'Original BMesh wrapper-set birth tracking did not establish a unique original ID mapping. Original failure/source retained.','originalVertexCount':len(rawBefore),'afterVertexCount':len(rawAfter),'initialNonnegativeCustomIds':int((candidateIds>=0).sum()),'initialUniqueNonnegativeCustomIds':len(np.unique(candidateIds[candidateIds>=0])),'originalExactCoordinateMultisetRecoveredCount':len(used),'originalPositionsMovedOrRemoved':len(used)!=len(rawBefore),'identityMethod':'Retain valid original custom IDs only when exact raw coordinates agree and unused; resolve remaining unchanged vertices by exact coordinate multiset without tolerance, preserving duplicate counts. New inserted points retain-1.','noCollisionBoundChanged':True})
    assert len(used)==len(rawBefore),'Native subdivision changed/removed original coordinate multiset';skin.data.attributes['AFN145_ORIGINAL_VERTEX_ID'].data.foreach_set('value',mapping);original=np.flatnonzero(mapping>=0);assert len(original)==len(W) and len(np.unique(mapping[original]))==len(W)
    reports={}
    for name in [h.h.SKIN]+h.h.ATTACH:reports[name]=add_slide(bpy.data.objects[name],centres,rig)
    scene.frame_set(1);rig.update_tag();bpy.context.view_layer.update();now={n:a.geometry(bpy.data.objects[n]) for n in names};skinError=float(np.linalg.norm(now[h.h.SKIN][0][original]-W[mapping[original]],axis=1).max());assert skinError<2e-6
    for n in names:
        if n!=h.h.SKIN:assert a.rawsig(bpy.data.objects[n])==raw[n] and np.linalg.norm(now[n][0]-baseline[n][0],axis=1).max()<2e-6,n
    assert a.a.protected()==protected
    rig['AFN145_scope']='Actual moving inner wall tessellation and original radial lamellar gap on retained aspherical cavity construction. Construction only; original source clearance is not collision proof, actual evaluated surfaces must be independently tested. No physiology/natural timing/full finite-contact acceptance.'
    bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=False)
    np.savez_compressed(E/'native-wall-topology-lineage.npz',originalSkinWorld=W,originalSkinTriangles=T,originalVertexId=mapping,originalCavityDomain=wall)
    save('aspherical-lid-wall-construction.json',{'source':str(SRC),'actualSkin':skin.name,'actualRig':rig.name,'actualControllers':PROPS,'originalSkinVertices':len(W),'newSkinVertices':len(now[h.h.SKIN][0]),'originalSkinTriangles':len(T),'newSkinTriangles':len(now[h.h.SKIN][1]),'originalCavityPointDomainCount':int(wall.sum()),'originalCavityFaceCount':oldWallFaces,'subdivisionSelectedEdgesEachIteration':lengths,'fixedWallEdgeTargetM':.0012,'targetIsConstructionResolutionNotContactTolerance':True,'originalPointPositionDeviationM':skinError,'oldVerticesAndAllOriginalFacesRetainedThroughConformingSubdivision':True,'originalUVAndDeformWeightsInterpolatedByNativeBMesh':True,'layerPath':'At each native angular position, use original aspherical cavity radial surface plus original point-to-inner-surface radial gap. Both original outer lid and posterior cavity wall share the same surface map; no new outward guard, eye scaling, face deletion or caps. Native ray failures remain recorded as actual point attributes.','reports':reports,'retainedCavityIsConstructionNotCollisionProof':True,'contactPredicateUnchangedM':1e-12,'allChangedSkinContactClaimsRequireRetest':True,'completeAppearanceOperationContactRuntimeAccepted':False,'secondsBeforePreview':time.time()-tick})
    save('a-build-summary.json',{'source':str(SRC),'comparisonBaseline':str(h.SRC),'output':str(OUT),'sha256':a.a.sha(OUT),'bytes':OUT.stat().st_size,'actualSkin':skin.name,'actualRig':rig.name,'actualControllers':PROPS,'originalGazeAction':'AFN138_NATIVE_CURRENT_GAZE_DEMO','newBlinkDemoAction':'AFN144_ACTUAL_CURRENT_SKIN_BLINK_DEMO','oneCompleteCandidate':True,'completeAppearanceOperationContactRuntimeUnaccepted':True,'secondsBeforePreview':time.time()-tick});views=[]
    for v in ['face','body-face','profile','oblique','back']:views.append(a.b.u.v.image('a-aspherical-lid-wall',v));save('a-view-controls.json',views)
    motion=[]
    for f in [5,9,13,17]:
        scene.frame_set(f);bpy.context.view_layer.update()
        for v in ['face','body-face']:
            row=a.b.u.v.image('blink-%03d'%f,v);row['actualBlink']={s:float(rig[p]) for s,p in PROPS.items()};motion.append(row);save('actual-blink-motion-controls.json',motion)
    scene.frame_set(9);bpy.context.view_layer.update();save('actual-closed-profile-control.json',a.b.u.v.image('closed-blink','profile'));scene.frame_set(1);bpy.context.view_layer.update();assert a.a.protected()==protected;print('R145_ACTUAL_ASPHERICAL_LID_WALL_COMPLETE_HEAD_BODY_BLINK_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
