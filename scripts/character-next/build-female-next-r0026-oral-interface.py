"""One bounded oral soft-tissue candidate, with a fixed dentition.

Locally fit the closed tongue into actual lingual dental support planes,
preserving the posterior root and most bulk. Use the existing jaw angle for
both tongue and a two-bone gingival deformation. No global proportional shrink.
"""
import bpy,bmesh,importlib.util,json,math,time,sys
from pathlib import Path
import numpy as np
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
spec=importlib.util.spec_from_file_location('b25',Path(__file__).with_name('build-female-next-r0025-dental-contact.py'));b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
R,S=b.R,b.S;E=R/'Evidence/character-female-next/r0026-oral-interface';E.mkdir(exist_ok=True)
COLLECTION_SOLIDS='--collection-solids' in sys.argv
LOCAL_SOLIDS='--local-solids' in sys.argv or COLLECTION_SOLIDS;LABEL='c' if COLLECTION_SOLIDS else ('b' if LOCAL_SOLIDS else 'a')
DST=S/f'aevrynd-female-next-r0026-{LABEL}-oral-interface-study.blend';CLEARANCE=.00025;MAX_CUT=.005;MIN_VOLUME=.80
def save(name,obj):(E/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
def raw_copy(source,name,world):
    m=bpy.data.meshes.new(name);m.from_pydata(world.tolist(),[],[list(f.vertices) for f in source.data.polygons]);m.update()
    uv=m.uv_layers.new(name='OralUV')
    for i,loop in enumerate(source.data.uv_layers.active.data):uv.data[i].uv=loop.uv
    for material in source.data.materials:m.materials.append(material)
    for p in m.polygons:p.use_smooth=True
    return m
def cap(bm):
    edges=[e for e in bm.edges if e.is_boundary]
    if not edges:return
    attr=bm.faces.layers.int.get('AFN26_ARCH_CAP') or bm.faces.layers.int.new('AFN26_ARCH_CAP')
    for f in bmesh.ops.holes_fill(bm,edges=edges,sides=0)['faces']:f[attr]=1
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
def driver(target,path,index,master,factor):
    c=target.driver_add(path,index);d=c.driver;d.type='SCRIPTED'
    for var in list(d.variables):d.variables.remove(var)
    var=d.variables.new();var.name='w';var.type='SINGLE_PROP';var.targets[0].id=master;var.targets[0].data_path='["open"]';d.expression=repr(float(factor))+'*w'

def local_cutter(tooth,collection):
    Q=b.prior.evaluate(tooth);centre=Q.mean(0).astype(np.float32).astype(np.float64);local=Q-centre;bm=bmesh.new()
    # Small centre-relative coordinates avoid ill-conditioned sliver planes
    # after rounding an expanded hull at the world's ~1.4m head height.
    for p in local:bm.verts.new(p)
    bmesh.ops.convex_hull(bm,input=list(bm.verts),use_existing_faces=False)
    loose=[v for v in bm.verts if not v.link_faces]
    if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
    bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.normal_update();supports=[];ratios=[];raw_violation=[]
    def plane(face):
        p=np.array([v.co for v in face.verts],np.float64);n=np.cross(p[1]-p[0],p[2]-p[0]);n/=np.linalg.norm(n)
        if n@p[0]<0:n=-n
        return n,float(n@p[0])
    for f in bm.faces:
        n,h=plane(f);assert h>0;supports.append(h);actual=float((local@n).max());ratios.append((actual+CLEARANCE)/h);raw_violation.append(actual-h)
    # BMesh's approximate hull can miss a thin crown fragment by micrometres.
    # Solve the required scale from *actual* source support at every face,
    # rather than assuming its generated face offset already contains Q.
    scale=max(ratios)
    for v in bm.verts:v.co=Vector(scale*np.array(v.co))
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.normal_update();gaps=[]
    inward=[f for f in bm.faces if np.dot(np.array(f.normal,np.float64),np.array(f.verts[0].co))<0]
    if inward:bmesh.ops.reverse_faces(bm,faces=inward)
    bm.normal_update();assert all(e.is_manifold for e in bm.edges) and bm.calc_volume(signed=True)>0
    for f in bm.faces:
        n,h=plane(f);gaps.append(h-float((local@n).max()))
    assert min(gaps)>=CLEARANCE-1.e-6,(tooth.name,min(gaps),scale,min(supports))
    m=bpy.data.meshes.new('AFN26_TOOL_'+tooth.name);bm.to_mesh(m);bm.free();o=bpy.data.objects.new(m.name,m);collection.objects.link(o);o.location=centre;o.hide_render=True;o['aevrynd_layer']='OFFLINE_CONTACT_TOOL_NOT_RUNTIME';o['aevrynd_proxy_for']=tooth.name
    return o,{'tooth':tooth.name,'scaleOfToolHullOnly':scale,'correctedInwardFaces':len(inward),'rawHullMaximumSupportViolationM':max(raw_violation),'scaleConstruction':'max over faces of (actual source support + clearance) / positive generated face offset; no assumption that the approximate hull already contains all source vertices.','minimumActualCrownSupportGapM':min(gaps),'proof':'Every actual tooth vertex and its triangle convex combinations lies inside this closed convex cutter with at least the recorded face support margin. This is a local tool, not a changed tooth or a global tongue plane.'}

def main():
    start=time.time();prior= json.loads((b.E/'a-build-verification.json').read_text(encoding='utf8'));source=Path(prior['output']);assert b.sha(source)==prior['outputSha256']
    save(LABEL+'-iteration-contract.json',{'previousGoalTurnClassification':'progress: r25 dental solids/contact repair retained, all 496 dental pair sweep qualified in stated range; complete mouth and appearance not accepted.','stage':'B_COMPLETE_HEAD_IN_PROGRESS','source':str(source),'sourceSha256':b.sha(source),'primaryDefect':'Closed source tongue penetrates anterior/lateral crowns and oral lining; lower gingiva and tongue use independent native linear fields instead of the retained rigid jaw.','hypothesis':'Subtract only local conservative tooth solids from the existing tongue, then drive tongue and mapped lower gingiva from one jaw control.' if LOCAL_SOLIDS else 'Use lingual free-space support planes derived from fixed crowns and posterior tongue root.','alternativeReason':'A global support cage rejected before asset creation: a posterior crown plane would remove 22.5mm at the tongue tip. B uses local bounded convex cutter volumes instead of global halfspaces.' if LOCAL_SOLIDS else None,'design':'250um design clearance. B exact local solid subtraction and source UV projection; no global tongue scale or tooth change. A plane method and smoothing remain rejected. Gingival split uses original anatomical helper triplets.','rejectIf':['Source sampled tongue surface removal over 5mm or final solid volume retention below 80%.','New nonmanifold/self/body/dental intersections or distorted tongue shape.','Shared-jaw gingiva introduces worse body contact or unnatural bridge deformation.','Unrelated source geometry or dental control changes.'],'budget':{'candidatesMaximum':3,'candidate':LABEL,'threads':4,'sourceTongueVertices':226,'teeth':32,'maximumTongueVertices':10000,'initialContactWeights':[0,.2],'diagnosticMinutes':10,'roundCheckpointMinutes':45},'scope':'Soft-tissue interface candidate. Root/floor attachments remain raw contacts until geometrically accepted; no full-mouth or runtime claim.'})
    bpy.ops.wm.open_mainfile(filepath=str(source));rig=bpy.data.objects['AFN_R0005_Rig'];b.prior.solid.stage.set_pose(rig,'neutral');master=bpy.data.objects['AFN24_MouthControl'];master['open']=0.;master.update_tag(refresh={'OBJECT'});bpy.context.view_layer.update()
    tongue=bpy.data.objects['AFN24_Tongue'];gum=bpy.data.objects['AFN24_ContinuousGingivalLining'];teeth=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('AFN25_')]
    unchanged={o.name:b.prior.solid.geom(o) for o in bpy.data.objects if o.type=='MESH' and o not in (tongue,gum)}
    P=b.prior.evaluate(tongue);G=b.prior.evaluate(gum);back=P[P[:,1]>=P[:,1].max()-.002];seed=back.mean(0);planes=[]
    for o in teeth:
        q=b.prior.evaluate(o);n=q.mean(0)-seed;n[2]=0.;n/=np.linalg.norm(n);h=float((q@n).min()-CLEARANCE);planes.append({'tooth':o.name,'n':n,'h':h})
    maximum=max(float((P@r['n']-r['h']).max()) for r in planes)
    if not LOCAL_SOLIDS:
        save('lingual-space-preflight.json',{'source':str(source),'rootSeedM':seed.tolist(),'maximumSourcePlaneViolationM':maximum,'maximumAllowedM':MAX_CUT,'designClearanceM':CLEARANCE,'planes':[{'tooth':r['tooth'],'normal':r['n'].tolist(),'offsetM':r['h']} for r in planes],'status':'PASS_BOUNDED_LOCAL_CUT' if maximum<=MAX_CUT else 'REJECT_TOO_MUCH_SOURCE_CHANGE'})
        assert maximum<=MAX_CUT
    mesh=raw_copy(tongue,'AFN26_Tongue',P);mesh.calc_loop_triangles();T=np.array([tuple(t.vertices) for t in mesh.loop_triangles]);U=np.array([[tuple(mesh.uv_layers.active.data[li].uv) for li in t.loops] for t in mesh.loop_triangles]);tree=BVHTree.FromPolygons(P.tolist(),T.tolist(),all_triangles=True)
    bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
    volume=bm.calc_volume(signed=False);assert all(e.is_manifold for e in bm.edges)
    for row in ([] if LOCAL_SOLIDS else planes):
        n,h=row['n'],row['h'];distance=np.array([np.array(v.co)@n-h for v in bm.verts])
        if distance.max()<=1.e-9:continue
        assert distance.min()<0
        bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1.e-9,plane_co=Vector(n*h),plane_no=Vector(n),clear_outer=True,clear_inner=False);cap(bm)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));cut_volume=bm.calc_volume(signed=False);bm.to_mesh(mesh);bm.free();mesh.update();uv=mesh.uv_layers.active;tag=mesh.attributes.get('AFN26_ARCH_CAP');projected=0
    for poly in mesh.polygons:
        if not tag or not tag.data[poly.index].value:continue
        projected+=1
        for li,vi in zip(poly.loop_indices,poly.vertices):
            hit,normal,ti,dist=tree.find_nearest(mesh.vertices[vi].co);a,c,d=P[T[ti]];coord=np.linalg.lstsq(np.column_stack((c-a,d-a)),np.array(hit)-a,rcond=None)[0];weights=np.array((1-coord.sum(),coord[0],coord[1]));uv.data[li].uv=weights@U[ti]
    collection=bpy.data.collections.new('AFN26_ORAL_SOFT_TISSUE');bpy.context.scene.collection.children.link(collection);newtongue=bpy.data.objects.new('AFN26_Tongue',mesh);collection.objects.link(newtongue)
    bpy.context.view_layer.objects.active=newtongue;newtongue.select_set(True)
    cutters=[]
    if LOCAL_SOLIDS:
        tools=bpy.data.collections.new('AFN26_CONTACT_TOOLS');bpy.context.scene.collection.children.link(tools)
        for tooth in teeth:
            cutter,proof=local_cutter(tooth,tools);bpy.context.view_layer.update()
            if not COLLECTION_SOLIDS:
                modifier=newtongue.modifiers.new('AFN26_LOCAL_DIFFERENCE','BOOLEAN');modifier.operation='DIFFERENCE';modifier.solver='EXACT';modifier.object=cutter;bpy.ops.object.modifier_apply(modifier=modifier.name);cutter.hide_set(True);assert len(newtongue.data.vertices)<=10000
                temp=bmesh.new();temp.from_mesh(newtongue.data);proof['tongueVolumeRatioAfterThisDifference']=temp.calc_volume(signed=False)/volume;proof['resultSignedVolumeM3']=temp.calc_volume(signed=True);proof['resultVertices']=len(newtongue.data.vertices);temp.free()
            cutters.append(proof);save(LABEL+'-local-cutter-provenance.json',{'tools':cutters,'notRuntimeOrVisibleGeometry':True,'clearanceM':CLEARANCE,'operationArchitecture':'One collection difference with overlapping operands' if COLLECTION_SOLIDS else 'Sequential object differences'})
        if COLLECTION_SOLIDS:
            modifier=newtongue.modifiers.new('AFN26_LOCAL_COLLECTION_DIFFERENCE','BOOLEAN');modifier.operation='DIFFERENCE';modifier.solver='EXACT';modifier.operand_type='COLLECTION';modifier.collection=tools;modifier.use_self=True;bpy.context.view_layer.update();bpy.ops.object.modifier_apply(modifier=modifier.name)
            for cutter in tools.objects:cutter.hide_set(True)
            assert len(newtongue.data.vertices)<=10000
        uv=newtongue.data.uv_layers.active
        for poly in newtongue.data.polygons:
            poly.use_smooth=True
            for li,vi in zip(poly.loop_indices,poly.vertices):
                hit,normal,ti,dist=tree.find_nearest(newtongue.data.vertices[vi].co);a,c,d=P[T[ti]];coord=np.linalg.lstsq(np.column_stack((c-a,d-a)),np.array(hit)-a,rcond=None)[0];weights=np.array((1-coord.sum(),coord[0],coord[1]));uv.data[li].uv=weights@U[ti]
        save(LABEL+'-local-cutter-provenance.json',{'tools':cutters,'notRuntimeOrVisibleGeometry':True,'clearanceM':CLEARANCE,'operationArchitecture':'One collection difference with overlapping operands' if COLLECTION_SOLIDS else 'Sequential object differences','reference':'https://docs.blender.org/manual/en/latest/modeling/modifiers/generate/booleans.html','reasonForCollectionAlternative':'B failed at the 18th sequential cutter, collapsing the mesh after earlier cuts. C resolves the overlapping operand collection in one operation instead of repeatedly feeding modified topology into the solver.' if COLLECTION_SOLIDS else None})
    else:
        sub=newtongue.modifiers.new('AFN26_ContactEdgeRounding','SUBSURF');sub.levels=sub.render_levels=1;bpy.ops.object.modifier_apply(modifier=sub.name)
    newtongue.select_set(False)
    final=bmesh.new();final.from_mesh(newtongue.data);final_volume=final.calc_volume(signed=False);final.free();assert final_volume/volume>=MIN_VOLUME,('Tongue volume loss',final_volume/volume)
    Q=b.prior.positions(newtongue);newtongue.data.calc_loop_triangles();newT=[tuple(t.vertices) for t in newtongue.data.loop_triangles];newtree=BVHTree.FromPolygons(Q.tolist(),newT,all_triangles=True);sampled_removed=max(float(newtree.find_nearest(Vector(p))[3]) for p in P);assert sampled_removed<=MAX_CUT
    lower=bpy.data.objects['AFN24_LowerRigidControl'];pivot=np.array(lower.location,np.float64);local=b.prior.positions(newtongue)-pivot;newtongue.data.vertices.foreach_set('co',local.astype(np.float32).ravel());newtongue.parent=lower;newtongue.matrix_parent_inverse=Matrix.Identity(4);newtongue.matrix_basis=Matrix.Identity(4);newtongue['aevrynd_layer']='TONGUE';newtongue['aevrynd_license']='CC0 original graphical tongue; own local arch repair and rounding';newtongue['aevrynd_release_state']='ORAL_CONTACT_RESEARCH'
    # Build a separate oral armature; do not alter any existing head/jaw bone.
    arm=bpy.data.armatures.new('AFN26_OralRig');oralrig=bpy.data.objects.new('AFN26_OralRig',arm);collection.objects.link(oralrig);b.prior.route.parent_head(oralrig,rig)
    bpy.context.view_layer.objects.active=oralrig;oralrig.select_set(True);bpy.ops.object.mode_set(mode='EDIT');base=arm.edit_bones.new('AFN26_OralBase');base.head=(0,0,0);base.tail=(0,.02,0);jaw=arm.edit_bones.new('AFN26_OralJaw');jaw.head=pivot;jaw.tail=pivot+np.array((0,.02,0));jaw.parent=base;bpy.ops.object.mode_set(mode='OBJECT');oralrig.select_set(False)
    factor=float(lower.animation_data.drivers[0].driver.expression.split('*w')[0]);pb=oralrig.pose.bones['AFN26_OralJaw'];pb.rotation_mode='XYZ';driver(pb,'rotation_euler',0,master,factor)
    gm=raw_copy(gum,'AFN26_GingivalLining',G);newgum=bpy.data.objects.new('AFN26_GingivalLining',gm);collection.objects.link(newgum);newgum.parent=oralrig;newgum['aevrynd_layer']='ORAL_GINGIVAL_LINING'
    mapping=b.prior.proxy.proxy(S/'oral/makehuman-system-cc0/teeth/teeth_base/teeth_base.mhclo');indices=np.array(gum['aevrynd_original_vertex_indices'],np.int32);refs=mapping['ids'][indices];is_lower=np.isin(refs,(15006,15010,15041)).all(1);is_upper=np.isin(refs,(15069,15077,15111)).all(1);assert np.all(is_lower|is_upper) and not np.any(is_lower&is_upper)
    for name,ids in (('AFN26_OralBase',np.flatnonzero(is_upper)),('AFN26_OralJaw',np.flatnonzero(is_lower))):group=newgum.vertex_groups.new(name=name);group.add(ids.tolist(),1.,'REPLACE')
    mod=newgum.modifiers.new('AFN26_CoherentJawSkinning','ARMATURE');mod.object=oralrig;newgum['aevrynd_bind_reference']='Original CC0 proxy upper/lower helper triplets; all 1852 vertices bound, neutral geometry retained.'
    bpy.data.objects.remove(tongue,do_unlink=True);bpy.data.objects.remove(gum,do_unlink=True)
    assert unchanged=={n:b.prior.solid.geom(bpy.data.objects[n]) for n in unchanged}
    errors=[]
    for w in (0.,.2):
        master['open']=w;master.update_tag(refresh={'OBJECT'});bpy.context.scene.frame_set(bpy.context.scene.frame_current+1);bpy.context.view_layer.update();angle=factor*w;rot=np.array(((1,0,0),(0,math.cos(angle),-math.sin(angle)),(0,math.sin(angle),math.cos(angle))));expected=G.copy();expected[is_lower]=(G[is_lower]-pivot)@rot.T+pivot;error=float(np.linalg.norm(b.prior.evaluate(newgum)-expected,axis=1).max());errors.append(error);assert error<5.e-7,('Gingival jaw mismatch',error)
    master['open']=0.;master.update_tag(refresh={'OBJECT'});bpy.context.view_layer.update();bpy.context.scene['aevrynd_revision']='female-next-r0026-'+LABEL;bpy.context.scene['aevrynd_release_state']='SOFT_TISSUE_CONTACT_VISUAL_PENDING';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(DST),compress=True)
    save(LABEL+'-build-verification.json',{'source':str(source),'sourceSha256':b.sha(source),'output':str(DST),'outputSha256':b.sha(DST),'status':'BUILT_CONTACT_VISUAL_PENDING','sourceTongueVolumeM3':volume,'clippedTongueVolumeM3':cut_volume,'finalTongueVolumeM3':final_volume,'volumeRatioRetained':final_volume/volume,'maximumOriginalVertexToNewSurfaceSampleM':sampled_removed,'rejectedGlobalPlaneMaximumM':maximum,'rootSeedM':seed.tolist(),'designClearanceM':CLEARANCE,'newContactFacesWithSourceUV':projected,'tongueVertices':len(newtongue.data.vertices),'tonguePolygons':len(newtongue.data.polygons),'gingivalUpperVertices':int(is_upper.sum()),'gingivalLowerVertices':int(is_lower.sum()),'gingivalJawEvaluatorErrorsM':errors,'existingNonSoftTissueMeshGeometryUnchanged':True,'wallSeconds':time.time()-start,'limits':['Local cutter contact imprints require actual anatomy/appearance review.','Gingival/tongue root/floor contacts not automatically accepted or excluded.','No whole mouth, continuous soft-tissue/body, complete face, hair or runtime acceptance.']})
    print('R0026_BUILD',json.dumps({'tongueVolumeRatio':final_volume/volume,'sampledRemovalM':sampled_removed,'gumJawErrorsM':errors}),flush=True)
if __name__=='__main__':main()
