"""One attributed artist-guide study, rebound by an explicit growth surface.

Preserve two growth islands, UV/parting fields and authored guide hierarchy.
Warp the dense growth surface by first exits from inside the actual head;
bind guides by source triangle/barycentric frames, then evaluate/bake once.
The source notice remains CC BY-SA; this is not an exclusive original groom.
"""
from pathlib import Path
import bpy,numpy as np,json,time,sys,importlib.util
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
def module(n,p):
    s=importlib.util.spec_from_file_location(n,Path(__file__).with_name(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
m=module('guide68source','inspect-female-next-r0068-guide-structure.py');base=module('guide68authorstage','inspect-female-next-r0065-eye-shading.py');k=base.k;shade=base.shade;R=m.R;E=m.E;S=R/'engine/assets/characters/female-next/source';SRC=S/'aevrynd-female-next-r0065-a-inner-eye-diffuse-study.blend';SOURCE_SHA='4d0e3f67735ae68c5c1fa3c933f7cabb03cb547928e778f7067a8e699620b708';OUT=S/'aevrynd-female-next-r0068-a-guide-surface-study.blend'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def array3(data,field):
    out=np.empty(len(data)*3,dtype='f4');data.foreach_get(field,out);return out.reshape(-1,3)
def bary(q,t):
    a,b,c=t;v=b-a;w=c-a;p=q-a;aa=v@v;ab=v@w;bb=w@w;pa=p@v;pb=p@w;den=aa*bb-ab*ab;assert abs(den)>1e-18;u=(bb*pa-ab*pb)/den;v2=(aa*pb-ab*pa)/den;return np.array([1-u-v2,u,v2])
def frame(t):
    x=t[1]-t[0];x=x/np.linalg.norm(x);z=np.cross(x,t[2]-t[0]);assert np.linalg.norm(z)>1e-10;z=z/np.linalg.norm(z);y=np.cross(z,x);return np.stack((x,y,z),axis=1)
def mesh_data(name,V,T):
    d=bpy.data.meshes.new(name);d.vertices.add(len(V));d.vertices.foreach_set('co',np.asarray(V,dtype='f4').ravel());d.loops.add(T.size);d.loops.foreach_set('vertex_index',np.asarray(T,dtype='i4').ravel());d.polygons.add(len(T));d.polygons.foreach_set('loop_start',np.arange(len(T),dtype='i4')*3);d.polygons.foreach_set('loop_total',np.full(len(T),3,dtype='i4'));d.update(calc_edges=True);return d
def attr(d,name,kind,domain,values):
    a=d.attributes.get(name) or d.attributes.new(name,kind,domain);a.data.foreach_set('vector' if kind=='FLOAT_VECTOR' else 'value',np.asarray(values).ravel())
def parity(tree,p,d):
    direction=Vector(d).normalized();origin=Vector(p);hits=0
    for _ in range(96):
        co,_,_,_=tree.ray_cast(origin,direction,4.)
        if co is None:return hits%2==1
        hits+=1;origin=co+direction*1e-7
    raise AssertionError('Parity ray did not terminate')
def preview(tag='a-guide'):
    shade.settings();k.b.camera('face');s=bpy.context.scene;s.camera.data.lens=85;s.render.resolution_x=s.render.resolution_y=640;s.cycles.samples=16;s.render.filepath=str(E/(tag+'-preview-face.png'));camera=np.array(s.camera.matrix_world).tolist();bpy.ops.render.render(write_still=True);return {'file':s.render.filepath,'camera':camera,'resolution':640,'samples':16,'seed':s.cycles.seed,'exposure':s.view_settings.exposure}
def main():
    tick=time.time();shade.g.E=E
    if '--views' in sys.argv:
        ref=read(E/'a-build-summary.json');assert m.sha(OUT)==ref['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(OUT));shade.settings();m.save('a-full-view-controls.json',shade.render('a-guide',('face','body-face','oblique','profile','back','alternate-oblique')));return
    assert not OUT.exists() and m.sha(SRC)==SOURCE_SHA and m.sha(m.SRC)==m.SHA;bpy.ops.wm.open_mainfile(filepath=str(SRC));bpy.context.scene.frame_set(1);stage=k.f.v.stage();body=bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING'];savedLevels=[]
    for o in bpy.data.objects:
        if o.type=='MESH':
            for md in o.modifiers:
                if md.type=='SUBSURF':savedLevels.append((md,md.levels));md.levels=md.render_levels
    bpy.context.view_layer.update();bodyRow=k.mesh(body);V,T=bodyRow['V'],bodyRow['T'];tree=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True);eyes=[]
    for name in ('AFN60_L_EYE_OUTER_SHELL_APPROX','AFN60_R_EYE_OUTER_SHELL_APPROX'):
        q=k.mesh(bpy.data.objects[name])['V'];eyes.append((q.min(0)+q.max(0))*.5)
    eye=np.mean(eyes,axis=0);eyeX=abs(eyes[0][0]);sx=eyeX/.305877685546875;sz=(V[:,2].max()-eye[2])/(16.410877227783203-15.30112361907959);sy=(sx+sz)*.5;M=Matrix.Diagonal((sx,sy,sz,1.));M.translation=(0.,float(eye[1]+1.3379756212234497*sy),float(eye[2]-15.30112361907959*sz));A=np.array(M);inv=np.linalg.inv(A)
    origin=np.array([0.,0.,eye[2]+.015]);assert all(parity(tree,origin,d) for d in ((1.,.321,.173),(-.137,1.,.297),(.311,-.197,1.)))
    for md,level in savedLevels:md.levels=level
    with bpy.data.libraries.load(str(m.SRC),link=False) as (src,dst):dst.objects=['head','long hair growth mesh','long hair main','long hair strands']
    objects={o.name:o for o in dst.objects};growth=objects['long hair growth mesh'];guides=[objects['long hair main'],objects['long hair strands']]
    for o in objects.values():o.parent=None;bpy.context.scene.collection.objects.link(o);o.matrix_world=M;o.hide_render=True;o.hide_set(False)
    bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();old=bpy.data.meshes.new_from_object(growth.evaluated_get(dg),preserve_all_data_layers=True,depsgraph=dg);old.calc_loop_triangles();G0=array3(old.vertices,'co').astype('f8');GT=np.array([t.vertices[:] for t in old.loop_triangles],dtype='i4');sourceTree=BVHTree.FromPolygons(G0.tolist(),GT.tolist(),all_triangles=True)
    sourceMaxRadius=read(E/'original-style-evaluation.json')['objects'][0]['localRadiusRange'][1];maxWorldRadius=sourceMaxRadius*np.linalg.norm(A[:3,:3],ord=2);world=G0@A[:3,:3].T+A[:3,3];hit=np.empty_like(world);faceIDs=np.empty(len(G0),dtype='i4');bodyBary=np.empty_like(world)
    for i,q in enumerate(world):
        direction=Vector(q-origin).normalized();co,normal,face,distance=tree.ray_cast(Vector(origin),direction,1.);assert co is not None,(i,q);hit[i]=np.array(co)+np.array(normal)*maxWorldRadius;faceIDs[i]=face;bodyBary[i]=bary(np.array(co),V[T[face]])
    G1=hit@inv[:3,:3].T+inv[:3,3];registration=np.linalg.norm(hit-world,axis=1);assert registration.max()<.035,('Growth surface registration requires redesign',float(registration.max()))
    new=old.copy();new.name='AFN68_TWO_ISLAND_GROWTH_SURFACE';new.vertices.foreach_set('co',G1.astype('f4').ravel());new.update();growth.data=new
    for md in list(growth.modifiers):growth.modifiers.remove(md)
    attr(new,'AFN68_RestBodyTriangle','INT','POINT',faceIDs);attr(new,'AFN68_RestBodyBarycentric','FLOAT_VECTOR','POINT',bodyBary.astype('f4'));attr(new,'AFN68_OriginalGrowthPosition','FLOAT_VECTOR','POINT',G0.astype('f4'))
    bindings=[]
    for o in guides:
        P=array3(o.data.position_data,'vector').astype('f8');counts=np.array([c.points_length for c in o.data.curves],dtype='i4');starts=np.r_[0,np.cumsum(counts)[:-1]];Q=P.copy();sourceFaces=[];barys=[];gaps=[]
        for ci,(start,count) in enumerate(zip(starts,counts)):
            root=P[start];near,_,face,distance=sourceTree.find_nearest(Vector(root));assert distance<.05,(o.name,ci,distance);weights=bary(np.array(near),G0[GT[face]]);newRoot=weights@G1[GT[face]];rotation=frame(G1[GT[face]])@frame(G0[GT[face]]).T;Q[start:start+count]=(P[start:start+count]-root)@rotation.T+newRoot;sourceFaces.append(face);barys.append(weights);gaps.append(distance)
        o.data.position_data.foreach_set('vector',Q.astype('f4').ravel());attr(o.data,'AFN68_SourceGrowthTriangle','INT','CURVE',np.array(sourceFaces,dtype='i4'));attr(o.data,'AFN68_SourceGrowthBarycentric','FLOAT_VECTOR','CURVE',np.array(barys,dtype='f4'))
        for md in o.modifiers:
            if md.type=='NODES' and md.node_group and md.node_group.name.startswith('Surface Deform'):md.show_viewport=md.show_render=False
        bindings.append({'object':o.name,'nativeGuides':len(counts),'nativePoints':len(P),'maximumOriginalRootGrowthDistanceLocal':max(gaps),'binding':'Source growth triangle/barycentric and orthonormal rest frame, not a failed-path root clamp.'})
    localV=V@inv[:3,:3].T+inv[:3,3];collider=bpy.data.objects.new('AFN68_RENDER_BODY_CONTACT_REFERENCE',mesh_data('AFN68_RENDER_BODY_CONTACT_REFERENCE',localV,T));bpy.context.scene.collection.objects.link(collider);collider.matrix_world=M;collider.hide_render=True;collider.hide_set(True);reconstructed=localV.astype('f4').astype('f8')@A[:3,:3].T+A[:3,3];collisionError=float(np.linalg.norm(reconstructed-V,axis=1).max());assert collisionError<1e-6
    sourceChanges=[]
    for o in guides:
        for md in o.modifiers:
            if md.type!='NODES' or not md.node_group:continue
            for node in md.node_group.nodes:
                if node.bl_idname=='GeometryNodeGroup' and node.node_tree and node.node_tree.name.startswith('Shrinkwrap Hair Curves'):
                    surface=next(i for i in node.inputs if i.name=='Surface' and i.type=='OBJECT');surface.default_value=collider;node.inputs['Offset Distance'].default_value=sourceMaxRadius;node.inputs['Above Surface'].default_value=sourceMaxRadius;sourceChanges.append({'object':o.name,'node':node.name,'surface':collider.name,'offsetAndActivationLocal':sourceMaxRadius,'basis':'Actual maximum rendered source radius, not a tuned collision allowance.'})
    bpy.context.view_layer.update();visible=[];arrays={}
    for i,o in enumerate(guides):
        d=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;assert len(d.curves)<250000 and len(d.position_data)<15000000;copy=d.copy();copy.name='AFN68_MAIN_RENDER_CURVES' if i==0 else 'AFN68_FLYAWAY_RENDER_CURVES';ob=bpy.data.objects.new(copy.name,copy);bpy.context.scene.collection.objects.link(ob);ob.matrix_world=M;ob.hide_render=False;o.hide_render=True;o.name='AFN68_EDITABLE_MAIN_GUIDES' if i==0 else 'AFN68_EDITABLE_FLYAWAY_GUIDES';P=array3(copy.position_data,'vector');counts=np.array([c.points_length for c in copy.curves],dtype='i4');rr=np.empty(len(P),dtype='f4');assert copy.attributes.get('radius');copy.attributes['radius'].data.foreach_get('value',rr);assert np.isfinite(P).all() and np.isfinite(rr).all() and (rr>=0).all();visible.append({'object':ob.name,'curves':len(counts),'points':len(P),'curvePointCounts':sorted(set(counts.tolist())),'localRadiusRangeM':[float(rr.min()),float(rr.max())]});arrays[str(i)+'positions']=P;arrays[str(i)+'counts']=counts;arrays[str(i)+'radii']=rr
    growth.name='AFN68_TWO_ISLAND_GROWTH_SURFACE';objects['head'].name='AFN68_ORIGINAL_REFERENCE_HEAD_HIDDEN';objects['head'].hide_set(True);bpy.data.objects['AFN57_CANONICAL_BOB_GUIDES'].hide_render=True;bpy.data.objects['AFN57_CANONICAL_BOB_GUIDES'].hide_set(True);assert k.f.v.stage()==stage
    arrays['matrix']=A;np.savez_compressed(E/'a-render-curve-data.npz',**arrays);shade.settings();k.b.camera('face');bpy.context.preferences.filepaths.save_version=0;bpy.context.scene['AFN68_status']='ATTRIBUTED_GUIDE_SURFACE_STUDY_UNACCEPTED';bpy.context.scene['AFN68_source_credit']='Daniel Bystedt, Hair Styles Demo, CC BY-SA as author/publisher declares; version not supplied. Source-derived study, not exclusive Aevrynd groom.';bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    m.save('a-build-summary.json',{'source':str(SRC),'sourceSha256':SOURCE_SHA,'publisherSource':str(m.SRC),'publisherSourceSha256':m.SHA,'sourceCredit':bpy.context.scene['AFN68_source_credit'],'output':str(OUT),'outputSha256':m.sha(OUT),'anatomicalAlignmentMatrix':A.tolist(),'alignmentBasis':'Eye separation/centre and head top; one fit, no parameter sweep.','growthVertices':len(G0),'growthTriangles':len(GT),'maximumGrowthRegistrationWorldM':float(registration.max()),'growthRegistrationMethod':'First exit rays from a three-parity-confirmed head-interior origin onto actual closed render tissue, retaining source growth topology/UV/islands/parting.','growthVertexStandOffWorldM':maxWorldRadius,'guideBindings':bindings,'sourceNodeChanges':sourceChanges,'visibleComponents':visible,'bodyRenderCollisionReferenceMaximumReconstructionErrorM':collisionError,'bodySkinEyesStageUnchanged':True,'sourceSurfaceDeformModifiersDisabledAfterExplicitBind':True,'newHairDynamicsOrEngineAcceptance':False,'sourceRights':'CC BY-SA notice retained; author did not state version. Original body remains separately sourced CC0; engine code licensing is not asserted or changed.','secondsBeforePreview':time.time()-tick})
    m.save('a-preview-control.json',preview());print('R68_GUIDE_SURFACE_PREVIEW',visible,time.time()-tick,flush=True)
if __name__=='__main__':main()
