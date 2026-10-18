"""Retarget CC0 hand-authored guides and bake an independent layered fibre groom.

Reference guide geometry: Tomas Klecer, MakeHuman Hair Editor functional CC0 pack.
No upstream Geometry Nodes or program code are retained in the output.
"""
import bpy,bmesh,math,json,hashlib,random,importlib.util,sys
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0012-layered-hair';E.mkdir(parents=True,exist_ok=True);S=R/'engine/assets/characters/female-next/source'
SRC=S/'aevrynd-female-next-r0011-b-ridge-skin-brows-study.blend';REF=R/'sites-engine-journey/assets-source/reference/cc0/makehuman-haireditor/unpacked/hair/haireditor/hair.blend'
spec=importlib.util.spec_from_file_location('solid',Path(__file__).with_name('verify-female-next-r0010-eye-rim.py'));solid=importlib.util.module_from_spec(spec);spec.loader.exec_module(solid);solid.stage.eyes.E=E
N=32; rng=np.random.default_rng(1212)

def mixed(o):
    if not o.data.shape_keys:return np.array([tuple(v.co) for v in o.data.vertices],dtype=np.float64)
    keys=o.data.shape_keys.key_blocks;P=np.array([tuple(v.co) for v in keys[0].data],dtype=np.float64)
    for k in keys[1:]:
        if k.value and not k.mute:P+=k.value*(np.array([tuple(v.co) for v in k.data])-np.array([tuple(v.co) for v in k.relative_key.data]))
    return P

def resample(P,n=N):
    out=[]
    for t in np.linspace(0,len(P)-1,n):
        i=min(len(P)-2,int(t));u=t-i;p0=P[max(0,i-1)];p1=P[i];p2=P[i+1];p3=P[min(len(P)-1,i+2)]
        out.append(.5*((2*p1)+(-p0+p2)*u+(2*p0-5*p1+4*p2-p3)*u*u+(-p0+3*p1-3*p2+p3)*u*u*u))
    return np.array(out)

def bary(p,a,b,c):
    u=b-a;v=c-a;w=p-a;d=u.dot(u)*v.dot(v)-u.dot(v)**2;t=(v.dot(v)*w.dot(u)-u.dot(v)*w.dot(v))/d;q=(u.dot(u)*w.dot(v)-u.dot(v)*w.dot(u))/d;return (1-t-q,t,q)

def transfer(body,tree,tri,volume=False):
    containers=('objects','meshes','hair_curves','node_groups','materials','images');before={c:{x.name for x in getattr(bpy.data,c)} for c in containers}
    target=mixed(bpy.data.objects['AFN_R0005_EditableNativeCC0'])[:13380]
    with bpy.data.libraries.load(str(REF),link=False) as (f,t):t.objects=['Human','straight_hair_to_shoulder']
    human,hair=t.objects;source=mixed(human)[:13380];basis=np.array([tuple(v.co) for v in human.data.vertices[:13380]],dtype=np.float64)
    guides=[np.array([tuple(p.position) for p in c.points],dtype=np.float64) for c in hair.data.curves]
    coarse=[tuple(p.vertices) for p in human.data.polygons if all(i<13380 for i in p.vertices)]
    target_raw=bpy.data.objects['AFN_R0005_EditableNativeCC0'];target_faces=[tuple(p.vertices) for p in target_raw.data.polygons if all(i<13380 for i in p.vertices)]
    assert coarse==target_faces, 'Native body vertex correspondence is not established'
    options=[]
    for name,P in [('mixed',source),('basis',basis)]:
        bt=BVHTree.FromPolygons([Vector(p) for p in P],coarse);ds=[bt.find_nearest(Vector(g[0]))[3] for g in guides];options.append((np.median(ds),name,P,ds))
    _,mode,source,root_errors=min(options,key=lambda x:x[0]);mask=source[:,2]>source[:,2].max()-.18
    design=np.column_stack((source[mask],np.ones(np.count_nonzero(mask))));A=np.linalg.lstsq(design,target[mask],rcond=None)[0];fit=design@A;err=np.linalg.norm(fit-target[mask],axis=1)
    G=[];bindings=[];edits=[]
    for gi,guide in enumerate(guides):
        mapped=np.column_stack((guide,np.ones(len(guide))))@A;hit,n,ti,d=tree.find_nearest(Vector(mapped[0]));root=np.array(hit+n*.00020);mapped+=root-mapped[0]
        tipz=1.360+.012*np.clip((root[1]+.12)/.17,0,1);drop=root[2]-mapped[-1,2]
        if drop>.025:mapped[:,2]=root[2]+(mapped[:,2]-root[2])*np.clip((root[2]-tipz)/drop,.25,1.25)
        P=resample(mapped)
        if volume:
            for j,p in enumerate(P):
                u=j/(N-1);v=min(1.,u/.65);out=p-np.array((0.,-.036,1.475));out/=max(np.linalg.norm(out),1e-9)
                P[j]+=out*((.004+.0015*math.sin(gi*1.17))*math.sin(math.pi*v))
        for j in range(N):
            p=Vector(P[j]);h,normal,face,dist=tree.find_nearest(p);signed=(p-h).dot(normal);margin=.00020 if j==0 else .00040
            inside=signed<0 and solid.classify(tree,tri,p)=='inside'
            if inside or dist<margin:
                q=h+normal*margin;edits.append({'guide':gi,'point':j,'deltaM':(q-p).length,'wasInside':bool(inside)});P[j]=q
        hit,n,ti,d=tree.find_nearest(Vector(P[0]));ids=list(body.data.loop_triangles[ti].vertices);bc=bary(hit,*[body.matrix_world@body.data.vertices[i].co for i in ids]);G.append(P)
        bindings.append({'guide':gi,'bodyTriangle':ti,'bodyVertices':ids,'barycentric':bc,'root':P[0].tolist(),'normal':list(n),'skinGapM':d})
    # Keep only the original character and Aevrynd-authored data; imported node graphs are discarded.
    for o in list(bpy.data.objects):
        if o.name not in before['objects']:bpy.data.objects.remove(o,do_unlink=True)
    for c in ('hair_curves','meshes','node_groups','materials','images'):
        for x in list(getattr(bpy.data,c)):
            if x.name not in before[c]:getattr(bpy.data,c).remove(x,do_unlink=True)
    record={'reference':str(REF),'referenceSha256':hashlib.sha256(REF.read_bytes()).hexdigest(),'author':'Tomas Klecer','license':'CC0-1.0','nativeBodyTopologyMatches':True,'sourceShapeState':mode,'sourceGuideRootDistanceMedianM':float(np.median(root_errors)),'sourceGuideRootDistanceMaxM':float(max(root_errors)),'headAffine':A.tolist(),'fitRmsM':float(np.sqrt(np.mean(err**2))),'fitMaxM':float(err.max()),'headAnchorVertices':int(mask.sum()),'guideCount':len(G),'pointsPerGuide':N,'projectionEdits':edits,'bindings':bindings,'upstreamNodeGraphsRetained':False}
    (E/(('b-volume-' if volume else '')+'guide-transfer.json')).write_text(json.dumps(record,indent=2)+'\n');return np.array(G),bindings,record

def connectivity(roots,normals,rig):
    triangles=[]
    for sign in (-1,1):
        bm=bmesh.new();layer=bm.verts.layers.int.new('guide_index');vertices=[]
        for i,p in enumerate(roots):
            if p[0]*sign<0:continue
            v=bm.verts.new(p);v[layer]=i;vertices.append(v)
        bmesh.ops.convex_hull(bm,input=vertices,use_existing_faces=False);bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.normal_update()
        for face in bm.faces:
            ids=[v[layer] for v in face.verts];normal=normals[ids].mean(axis=0)
            if face.normal.dot(Vector(normal))>.35 and face.calc_area()>1e-8:triangles.append(ids)
        bm.free()
    triangles=np.array(triangles,dtype=np.int32);p=roots[triangles];areas=np.linalg.norm(np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0]),axis=1)*.5
    mesh=bpy.data.meshes.new('AFN12_SCALP_ROOT_CONNECTIVITY');mesh.from_pydata(roots.tolist(),[],triangles.tolist());mesh.update();o=bpy.data.objects.new(mesh.name,mesh);bpy.context.scene.collection.objects.link(o);o.hide_render=True;o.hide_viewport=True;o['aevrynd_layer']='SCALP_EMITTER_GUIDE_CONNECTIVITY';o['aevrynd_not_surface_cap']=True
    (E/'b-volume-root-connectivity.json').write_text(json.dumps({'guideTriangles':triangles.tolist(),'triangleAreasM2':areas.tolist(),'method':'Separate left/right root convex hull; retain only faces aligned with actual skin normals. Uniform area sampling followed by projection to original body. Hidden emitter, no rendered scalp cap.'},indent=2)+'\n')
    return triangles,areas/areas.sum()

def materials():
    mats=[]
    for i in range(6):
        m=bpy.data.materials.new('AFN12_ChestnutKeratin_'+str(i));m.use_nodes=True;bs=next(n for n in m.node_tree.nodes if n.bl_idname=='ShaderNodeBsdfPrincipled');factor=.72+i*.12
        bs.inputs['Base Color'].default_value=(.040*factor,.019*factor,.009*factor,1);bs.inputs['Roughness'].default_value=.43;bs.inputs['Specular IOR Level'].default_value=.28;bs.inputs['Anisotropic'].default_value=.65;mats.append(m)
    return mats

def curves(name,paths,radii,rig,mats,hidden=False):
    collection=bpy.data.collections.new(name);bpy.context.scene.collection.children.link(collection);data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D';data.resolution_u=1;data.bevel_depth=.000032;data.bevel_resolution=0;data.use_fill_caps=True;data.twist_mode='MINIMUM'
    for m in mats:data.materials.append(m)
    for i,(P,r) in enumerate(zip(paths,radii)):
        spline=data.splines.new('POLY');spline.points.add(len(P)-1);coords=np.column_stack((P,np.ones(len(P)))).astype(np.float32);spline.points.foreach_set('co',coords.ravel());spline.points.foreach_set('radius',(r/.000032).astype(np.float32));spline.material_index=i%len(mats)
    obj=bpy.data.objects.new(name,data);collection.objects.link(obj);obj.parent=rig;obj.parent_type='BONE';obj.parent_bone='head';obj.matrix_basis=Matrix.Identity(4);obj.matrix_parent_inverse=Matrix.Identity(4);bpy.context.view_layer.update();obj.matrix_parent_inverse=obj.matrix_world.inverted();bpy.context.view_layer.update()
    assert max(abs(obj.matrix_world[i][j]-(1 if i==j else 0)) for i in range(4) for j in range(4))<1e-5
    obj.hide_render=hidden;obj['aevrynd_layer']=name;obj['aevrynd_revision']='female-next-r0012';obj['aevrynd_source']='252 retargeted CC0 guides; Aevrynd interpolation, root binding and geometry.';return obj

def main(volume=False):
    label='b-volume-hair' if volume else 'a-layered-hair'
    bpy.ops.wm.open_mainfile(filepath=str(SRC));rig=bpy.data.objects['AFN_R0005_Rig'];solid.stage.set_pose(rig,'neutral');body=bpy.data.objects['AFN_R0008_Body'];body.data.calc_loop_triangles();V,T,tree=solid.data(body);tri=np.asarray([tuple(v) for v in V],dtype=np.float64)[np.asarray(T,dtype=np.int32)]
    G,guide_bindings,transfer_info=transfer(body,tree,tri,volume);mats=materials();curves('AFN12_GUIDES',G,np.full((len(G),N),.00006),rig,mats,True)
    roots=G[:,0];normals=np.array([b['normal'] for b in guide_bindings]);layers=[];allP=[];allR=[];allIds=[];allWeights=[];allOffsets=[];allLayers=[];corrections=[]
    graph,probabilities=connectivity(roots,normals,rig) if volume else (None,None)
    configs=[('AFN12_PRIMARY_MASS',56 if volume else 24,.0035),('AFN12_SECONDARY_CLUMPS',32 if volume else 24,.0060),('AFN12_HAIRLINE_FINE',3,.0015),('AFN12_FLYAWAYS',1,.0020)]
    for li,(name,count,jitter) in enumerate(configs):
        paths=[];radii=[]
        for gi in range(len(G)):
            if li==2 and not(roots[gi,1]<-.065):continue
            if li==3 and gi%4:continue
            normal=Vector(normals[gi]);axis=normal.cross(Vector((0,0,1)))
            if axis.length<.1:axis=normal.cross(Vector((1,0,0)))
            axis.normalize();other=normal.cross(axis).normalized()
            for child in range(count):
                if volume and li<2:
                    ids=graph[int(rng.choice(len(graph),p=probabilities))];s=math.sqrt(float(rng.random()));v=float(rng.random());weights=np.array((1-s,s*(1-v),s*v));seed=Vector(np.einsum('i,ij->j',weights,roots[ids]));normal=Vector(np.einsum('i,ij->j',weights,normals[ids])).normalized()
                else:
                    offset=axis*float(rng.normal(0,jitter*.55))+other*float(rng.normal(0,jitter*.55));seed=Vector(roots[gi])+offset
                hit,n,face,d=tree.find_nearest(seed)
                if n.dot(normal)<.4:continue
                root=np.array(hit+n*.00020)
                if not(volume and li<2):
                    dist=np.linalg.norm(roots-root,axis=1);eligible=np.where(roots[:,0]*roots[gi,0]>=0)[0];ids=eligible[np.argsort(dist[eligible])[:3]];weights=1/np.maximum(dist[ids],.0007)**2;weights/=weights.sum()
                u=np.linspace(0,1,N)
                if volume:
                    clump=(.08 if li==0 else .55)*u**1.8;one=np.eye(3)[np.argmax(weights)];wv=(1-clump[:,None])*weights+clump[:,None]*one;P=np.einsum('ji,ijk->jk',wv,G[ids])
                else:P=np.einsum('i,ijk->jk',weights,G[ids])
                delta=root-P[0];profile=.4+.6*(1-u)**2;P+=profile[:,None]*delta
                if volume:P[:,2]+=float(rng.uniform(-.004,.004))*u**5
                tangent=P[-1]-P[0];wave_axis=np.cross(tangent,[0,0,1]);wave_axis/=max(np.linalg.norm(wave_axis),1e-9);phase=float(rng.uniform(0,math.tau));amp=.00012 if li<3 else .0012
                P+=wave_axis[None,:]*(amp*np.sin(u*math.pi)*np.sin(u*math.pi*8+phase))[:,None]
                if li==2 and child==0:P=resample(P[:12]) # a small number of short hairline transition hairs
                if li==3:P+=normals[gi][None,:]*(.0025*np.sin(u*math.pi))[:,None]
                for j in range(1,N):
                    p=Vector(P[j]);h,nn,ti,d=tree.find_nearest(p);signed=(p-h).dot(nn)
                    if d<.00017 or (signed<0 and solid.classify(tree,tri,p)=='inside'):
                        q=h+nn*.00035;corrections.append({'layer':li,'guide':gi,'child':child,'point':j,'deltaM':(q-p).length});P[j]=q
                radius=float(rng.uniform(.000027,.000038))*(.67 if li>=2 else 1.);r=radius*(.23+.77*(1-u)**.23);r[-1]=radius*.08
                paths.append(P);radii.append(r);allP.append(P);allR.append(r);allIds.append(ids);allWeights.append(weights);allOffsets.append(delta);allLayers.append(li)
        obj=curves(name,paths,radii,rig,mats);layers.append({'object':obj.name,'curves':len(paths),'points':len(paths)*N,'rootJitterSigmaM':jitter*.55,'baseRadiusM':.000032});print('AFN_R0012_LAYER='+json.dumps(layers[-1]),flush=True)
    P=np.array(allP,dtype=np.float32);rad=np.array(allR,dtype=np.float32);data_path=S/('aevrynd-female-next-r0012-'+('b' if volume else 'a')+'-hair-data.npz');np.savez_compressed(data_path,positions=P,radii=rad,guides=G.astype(np.float32),guideIndices=np.array(allIds,dtype=np.int32),guideWeights=np.array(allWeights,dtype=np.float32),rootOffsets=np.array(allOffsets,dtype=np.float32),layers=np.array(allLayers,dtype=np.int16),headRestMatrix=np.array(rig.data.bones['head'].matrix_local,dtype=np.float32))
    (E/(('b-volume-' if volume else '')+'child-corrections.json')).write_text(json.dumps(corrections,indent=2)+'\n');fits=solid.stage.eyes.helper_centres();images=[solid.stage.eyes.render(label,v,fits,'neutral') for v in ('face','oblique','profile')]
    scene=bpy.context.scene;scene['aevrynd_revision']='female-next-r0012-'+label;scene['aevrynd_release_state']='LAYERED_HAIR_STUDY_PENDING_COLLISION_AND_VISUAL_REVIEW';dest=S/('aevrynd-female-next-r0012-'+label+'-study.blend');bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(dest))
    (E/('female-next-r0012-'+label+'.report.json' if volume else 'female-next-r0012-layered-hair.report.json')).write_text(json.dumps({'revision':'female-next-r0012','variant':label,'source':str(SRC),'sourceSha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'output':str(dest),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'hairData':str(data_path),'hairDataSha256':hashlib.sha256(data_path.read_bytes()).hexdigest(),'hypothesis':'Retarget hand-authored coherent guide flow to the native head, then interpolate separated mass/detail/hairline layers to avoid a solid cap or unrelated wire strands.','guideSource':transfer_info['reference'],'guideLicense':'CC0-1.0','upstreamNodeGraphsRetained':False,'layers':layers,'hairCurves':len(P),'hairControlPoints':int(np.prod(P.shape[:2])),'renders':images,'status':'PENDING_TECHNICAL_VISUAL_REVIEW','enginePromotionApproved':False,'websitePromotionApproved':False,'overallCharacterScore':None,'remainingLimits':['Static head-bound groom, no physical simulation yet.','Body clearance and guide interpolation need independent saved-file segment verification.','Inter-strand continuous/self collision is not qualified.','Native scalp helper retained in editable source; no separate opaque cap is added.','No runtime LOD, shader baking or performance qualification.']},indent=2)+'\n');print('AFN_R0012_BUILD_DONE')

if __name__=='__main__':main('--volume' in sys.argv)
