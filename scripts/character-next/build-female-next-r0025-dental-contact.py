"""Bounded local dental contact repair, with closed crown solids.

Original CC0 crown surfaces are preserved except where a neighbouring tooth's
contact cell cuts an actual overlap. This is a geometric repair approximation,
not a claim of clinically calibrated dentition or new tooth sculpt quality.
"""
import bpy,bmesh,importlib.util,json,math,time,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
spec=importlib.util.spec_from_file_location('prior25',Path(__file__).with_name('build-female-next-r0024-oral-layers.py'));prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
R,S=prior.R,prior.S;E=R/'Evidence/character-female-next/r0025-dental-contact';E.mkdir(exist_ok=True)
DST=S/'aevrynd-female-next-r0025-a-dental-contact-study.blend'
GAP=.000020;MAX_CUT=.0015;MIN_VOLUME=.70
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(name,data):(E/name).write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf8')

def fill_boundaries(bm,cap_kind=1):
    edges=[e for e in bm.edges if e.is_boundary]
    if edges:
        cap=bm.faces.layers.int.get('AFN25_CAP') or bm.faces.layers.int.new('AFN25_CAP')
        result=bmesh.ops.holes_fill(bm,edges=edges,sides=0)
        for face in result['faces']:face[cap]=cap_kind
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    return len(edges)

def tooth_mesh(name,Q,uv,F,FUV,group,planes,material):
    ids=set(group);selected=[i for i,f in enumerate(F) if set(f).issubset(ids)]
    index={old:new for new,old in enumerate(group)}
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(Q[group].tolist(),[],[[index[v] for v in F[i]] for i in selected]);mesh.update()
    layer=mesh.uv_layers.new(name='OralUV')
    for poly,i in zip(mesh.polygons,selected):
        for li,ui in zip(poly.loop_indices,FUV[i]):layer.data[li].uv=uv[ui]
    mesh.calc_loop_triangles();sourceP=np.array([v.co for v in mesh.vertices],np.float64);sourceT=np.array([tuple(t.vertices) for t in mesh.loop_triangles],np.int32);sourceUV=np.array([[tuple(layer.data[li].uv) for li in t.loops] for t in mesh.loop_triangles]);sourceTree=BVHTree.FromPolygons(sourceP.tolist(),sourceT.tolist(),all_triangles=True)
    bm=bmesh.new();bm.from_mesh(mesh);root_edges=fill_boundaries(bm);original_volume=bm.calc_volume(signed=False)
    assert root_edges==12 and original_volume>1.e-12
    applied=[]
    for other,n,h in planes:
        distances=np.array([np.dot(n,v.co)-h for v in bm.verts])
        if distances.max()<=1.e-9:continue
        assert distances.min()<0,'Contact plane removed the entire tooth'
        bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1.e-9,plane_co=Vector(n*h),plane_no=Vector(n),use_snap_center=False,clear_outer=True,clear_inner=False)
        fill_boundaries(bm,cap_kind=2);applied.append(int(other))
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    volume=bm.calc_volume(signed=False);boundary=sum(e.is_boundary for e in bm.edges);nonmanifold=sum(not e.is_manifold for e in bm.edges)
    assert boundary==nonmanifold==0
    bm.to_mesh(mesh);bm.free();mesh.update();mesh.materials.append(material)
    # New contact/closure faces need enamel UVs as well as geometry. Leaving
    # Blender's (0,0) default would sample the black atlas background.
    projected=0;cap=mesh.attributes['AFN25_CAP'];uvlayer=mesh.uv_layers['OralUV']
    for poly in mesh.polygons:
        if not cap.data[poly.index].value:continue
        projected+=1
        for li,vi in zip(poly.loop_indices,poly.vertices):
            point=mesh.vertices[vi].co;hit,normal,ti,distance=sourceTree.find_nearest(point);a,c,d=sourceP[sourceT[ti]]
            bc=np.linalg.lstsq(np.column_stack((c-a,d-a)),np.array(hit)-a,rcond=None)[0];weights=np.array((1-bc.sum(),bc[0],bc[1]));uvlayer.data[li].uv=weights@sourceUV[ti]
    for poly in mesh.polygons:poly.use_smooth=True
    return mesh,{'originalRootBoundaryEdges':root_edges,'rootCapMeaning':'Closed crown-base collision solid, not a complete anatomical root.','capFaceAttribute':'AFN25_CAP: 0 original crown, 1 original root-end closure, 2 new contact-plane face. These tags are provenance, not automatic collision exclusions.','rootCapFaces':sum(x.value==1 for x in cap.data),'contactCapFaces':sum(x.value==2 for x in cap.data),'capFacesWithNearestSourceEnamelUV':projected,'originalCappedVolumeM3':original_volume,'repairedVolumeM3':volume,'volumeRatio':volume/original_volume,'boundaryEdges':boundary,'nonManifoldEdges':nonmanifold,'appliedContactNeighbours':applied,'vertices':len(mesh.vertices),'polygons':len(mesh.polygons)}

def main():
    start=time.time();manifest=json.loads((S.parent/'female-next.asset.json').read_text(encoding='utf8'));source_report=json.loads((prior.E/'b-build-verification.json').read_text(encoding='utf8'));source=Path(source_report['output']);assert sha(source)==source_report['outputSha256']
    save('iteration-contract.json',{'previousGoalTurnClassification':'progress: r24 real oral layers and rigid controls built/rendered; contact failures and inherited original dental intersections established; no adoption.','stage':'B_COMPLETE_HEAD_IN_PROGRESS','source':str(source),'sourceSha256':sha(source),'workingHead':manifest['workingReviewSource'],'primaryDefect':'Adapted CC0 crowns have open root ends and 1466 raw inter-tooth triangle pairs at neutral, including neighbours and opposing arches.','hypothesis':'Close the existing crown bases and trim only geometric overlap into paired contact cells. This preserves placement, jaw motion, material and most tooth surfaces, unlike global scaling/refitting.','design':'Euclidean contact-cell bisectors between original crown centres, 20um numerical separation. This is a bounded geometric approximation; rendered shape and topology decide whether it is usable.','rejectIf':['Any closed-crown boundary/nonmanifold/self intersection or tooth-to-tooth intersection after repair.','Original-vertex plane cut depth over 1.5mm or capped volume ratio below 0.70.','Flattened visible crowns, visible gaps or whole-face regression.'],'budget':{'candidates':1,'threads':4,'teeth':32,'planesPerToothMaximum':31,'diagnosticMinutes':10,'roundCheckpointMinutes':45},'scope':'Dental contact/crown-solid repair only. Existing gingival/tongue/body failures remain unless separately proven; no runtime or full-mouth acceptance.'})
    bpy.ops.wm.open_mainfile(filepath=str(source));rig=bpy.data.objects['AFN_R0005_Rig'];prior.solid.stage.set_pose(rig,'neutral')
    master=bpy.data.objects['AFN24_MouthControl'];master['open']=0.;master.update_tag(refresh={'OBJECT'});bpy.context.view_layer.update()
    unchanged={o.name:prior.solid.geom(o) for o in bpy.data.objects if o.type=='MESH' and o.name not in ('AFN24_UpperTeeth','AFN24_LowerTeeth')}
    folder=S/'oral/makehuman-system-cc0/teeth/teeth_base';V,uv,F,FUV=prior.proxy.obj(folder/'teeth_base.obj');groups=prior.proxy.components(len(V),F)[1:]
    cache=np.load(S/'aevrynd-female-next-r0024-oral-fit-data.npz');mapping=prior.proxy.proxy(folder/'teeth_base.mhclo');fitted,scales=prior.proxy.fit(mapping,prior.proxy.to_mh(cache['nativeNeutral']));Q=prior.proxy.to_blender(fitted);C=np.array([Q[g].mean(0) for g in groups])
    topo=json.loads((E/'topology-inspection.json').read_text(encoding='utf8'));jaws=[row['jaw'] for row in topo['teeth']]
    allplanes=[];preflight=[]
    for i,g in enumerate(groups):
        planes=[]
        for j in range(32):
            if i==j:continue
            n=C[j]-C[i];n/=np.linalg.norm(n);h=float(n@((C[i]+C[j])*.5)-GAP*.5);planes.append((j,n,h))
        maxcut=max(float((Q[g]@n-h).max()) for j,n,h in planes);preflight.append(maxcut);allplanes.append(planes)
    save('contact-cell-preflight.json',{'maximumPlaneCutDepthM':max(preflight),'perToothM':preflight,'maximumAllowedM':MAX_CUT,'status':'PASS_BOUNDED_INPUT_CUT_DEPTH' if max(preflight)<=MAX_CUT else 'REJECT_TOO_MUCH_CROWN_REMOVAL'})
    assert max(preflight)<=MAX_CUT
    material=bpy.data.objects['AFN24_UpperTeeth'].data.materials[0];collection=bpy.data.collections.new('AFN25_DENTITION');bpy.context.scene.collection.children.link(collection);rows=[]
    for i,g in enumerate(groups):
        jaw=jaws[i];name='AFN25_'+jaw.title()+'_%02d'%(i+1);mesh,stats=tooth_mesh(name,Q,uv,F,FUV,g,allplanes[i],material);obj=bpy.data.objects.new(name,mesh);collection.objects.link(obj)
        parent=bpy.data.objects['AFN24_'+jaw.title()+'RigidControl'];pivot=np.array(parent.location,np.float64)
        points=prior.positions(obj);obj.data.vertices.foreach_set('co',(points-pivot).astype(np.float32).ravel());obj.parent=parent;obj.matrix_parent_inverse=Matrix.Identity(4);obj.matrix_basis=Matrix.Identity(4)
        obj['aevrynd_layer']='TEETH_'+jaw.upper();obj['aevrynd_status']='DENTAL_CONTACT_REPAIR_PENDING_SURFACE_VISUAL_GATES';obj['aevrynd_original_component']=i+1;obj['aevrynd_original_vertex_indices']=g;obj['aevrynd_license']='Derived from MakeHuman CC0 graphical crown data; own contact clipping/caps'
        stats.update({'name':name,'jaw':jaw,'sourceComponent':i+1,'sourceCentreM':C[i].tolist(),'sourceMaximumPlaneCutDepthM':preflight[i],'planes':[{'other':j+1,'normal':n.tolist(),'offsetM':h} for j,n,h in allplanes[i]]});rows.append(stats)
    for name in ('AFN24_UpperTeeth','AFN24_LowerTeeth'):bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
    assert unchanged=={n:prior.solid.geom(bpy.data.objects[n]) for n in unchanged}
    quality=all(row['volumeRatio']>=MIN_VOLUME for row in rows)
    bpy.context.scene['aevrynd_revision']='female-next-r0025-a';bpy.context.scene['aevrynd_release_state']='DENTAL_CONTACT_REPAIR_PENDING_FULL_MOUTH_GATES';bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(DST),compress=True)
    save('a-build-verification.json',{'source':str(source),'sourceSha256':sha(source),'output':str(DST),'outputSha256':sha(DST),'status':'PASS_BOUNDED_BUILD_CONTACT_VISUAL_PENDING' if quality else 'REJECT_CROWN_VOLUME_CHANGE','designSeparationM':GAP,'minimumVolumeRatioRequired':MIN_VOLUME,'minimumActualVolumeRatio':min(row['volumeRatio'] for row in rows),'sourceNonDentalMeshGeometryUnchanged':True,'teeth':rows,'wallSeconds':time.time()-start,'limits':['Contact-cell crowns are a geometric repair, not clinically calibrated anatomy.','Existing gingival/lingual motion and contacts have not been repaired.','No continuous body/tissue, hair or runtime acceptance.']})
    print('R0025_BUILD',json.dumps({'teeth':32,'minimumVolumeRatio':min(row['volumeRatio'] for row in rows),'maximumCutM':max(preflight),'qualityGate':quality}),flush=True)
if __name__=='__main__':main()
