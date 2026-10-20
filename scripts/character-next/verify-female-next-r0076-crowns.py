"""Saved crown geometry, all same-arch tooth pairs and exact inherited motion premises."""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
from mathutils.bvhtree import BVHTree
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0076-proximal-crowns';OLD=E.parent/'r0075-occlusion-authoring'
def module(n,file):
    s=importlib.util.spec_from_file_location(n,Path(__file__).with_name(file));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
q=module('verify76data','qualify-female-next-r0075-dental-motion.py');cross=module('verify76surface','screen-female-next-r0074-oral-contact.py')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def signature(o):
    h=hashlib.sha256(q.signature(o).encode());d=o.data
    for key in d.shape_keys.key_blocks:h.update(key.name.encode());h.update(q.arr(key.data,'co',len(key.data),3).tobytes())
    for fc in d.shape_keys.animation_data.drivers if d.shape_keys.animation_data else []:h.update((fc.data_path+fc.driver.expression).encode())
    h.update(q.arr(d.polygons,'material_index',len(d.polygons),dtype='i4').tobytes());return h.hexdigest()
def main():
    tick=time.time();ref=q.read(E/'a-build-summary.json');assert sha(Path(ref['source']))==ref['sourceSha256'];bpy.ops.wm.open_mainfile(filepath=ref['source']);s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();names=list(q.read(E.parent/'r0060-ocular-assembly/b-build-summary.json')['visibleComponents'].values());native={n:signature(bpy.data.objects[n]) for n in names};old={};motion={};hn=['AFN68_MAIN_RENDER_CURVES','AFN68_FLYAWAY_RENDER_CURVES']
    for arch in ('upper','lower'):
        o=bpy.data.objects['AFN74_'+arch.upper()+'_TEETH_RIGID'];old[arch]={'local':q.arr(o.data.vertices,'co',len(o.data.vertices),3).copy(),'world':q.geom(o)[1].copy(),'UV':q.arr(o.data.uv_layers['VitruvianUV.UDIM'].data,'uv',len(o.data.loops),2).copy(),'loops':q.arr(o.data.loops,'vertex_index',len(o.data.loops),dtype='i4').copy()}
    for f in (1,7,13,25,31,37):
        s.frame_set(f);bpy.context.view_layer.update();motion[f]={'matrices':{a:np.array(bpy.data.objects['AFN74_'+a.upper()+'_TEETH_RIGID'].matrix_world) for a in ('upper','lower')},'skin':q.geom(bpy.data.objects['AFN74_SKIN_AND_EXISTING_OCULAR_LINING'])[1].copy(),'hair':{n:q.hair(bpy.data.objects[n]).copy() for n in hn}}
    assert sha(Path(ref['output']))==ref['outputSha256'];bpy.ops.wm.open_mainfile(filepath=ref['output']);s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();assert {n:signature(bpy.data.objects[n]) for n in names}==native;assert not bpy.data.libraries;arches={};plane_rows=[];actual_crossings=[]
    for arch in ('upper','lower'):
        o=bpy.data.objects['AFN74_'+arch.upper()+'_TEETH_RIGID'];d,p=q.geom(o);lineage=np.load(E/(arch+'-sculpt-lineage.npz'),allow_pickle=False);owner=lineage['vertexTooth'];centers=np.array([old[arch]['world'][owner==i].mean(0) for i in range(16)]);assert np.max(np.abs(centers-lineage['centers']))<1e-7;assert np.max(np.abs(old[arch]['world']-lineage['oldWorld']))<1e-7;lam=lineage['radialLambda'];assert np.all((lam>0)&(lam<=1));expected=centers[owner]+lam[:,None]*(old[arch]['world']-centers[owner]);error=float(np.linalg.norm(p-expected,axis=1).max());assert error<1e-6
        raw=q.arr(o.data.vertices,'co',len(o.data.vertices),3);protected=lineage['protected'];assert np.array_equal(raw[protected],old[arch]['local'][protected]);assert np.array_equal(q.arr(d.loops,'vertex_index',len(d.loops),dtype='i4'),old[arch]['loops']);assert np.array_equal(q.arr(d.uv_layers['VitruvianUV.UDIM'].data,'uv',len(d.loops),2),old[arch]['UV']);assert not o.modifiers and not o.data.shape_keys
        d.calc_loop_triangles();tri=np.array([t.vertices[:] for t in d.loop_triangles]);tree=BVHTree.FromPolygons(p.tolist(),tri.tolist(),all_triangles=True);witness=None;checked=0
        for a,b in tree.overlap(tree):
            if a>=b:continue
            checked+=1;point=cross.proper_cross(p[tri[a]],p[tri[b]])
            if point is not None:witness={'triangleA':int(a),'triangleB':int(b),'worldPointM':point,'sameTooth':bool(owner[tri[a,0]]==owner[tri[b,0]])};break
        actual_crossings.append({'arch':arch,'examinedActualTriangleCandidates':checked,'properCrossingWitness':witness});normals={};explicit={(v['toothA'],v['toothB']):np.array(v['normal']) for v in next(v['planes'] for v in ref['sculpt'] if v['arch']==arch)}
        for i in range(16):
            a=p[owner==i]
            for j in range(i+1,16):
                b=p[owner==j];gap=max(float((b.min(0)-a.max(0)).max()),float((a.min(0)-b.max(0)).max()));method='coordinate-axis'
                if (i,j) in explicit:
                    n=explicit[(i,j)];gap=max(gap,float((b@n).min()-(a@n).max()));method='independently remeasured authored direction'
                if gap<=2e-6:
                    normals.setdefault(i,q.directions(a));n=normals[i];gap=max(gap,float(((b@n.T).min(0)-(a@n.T).max(0)).max()));method='remeasured finite-vertex supports'
                plane_rows.append({'arch':arch,'toothA':i,'toothB':j,'passed':gap>2e-6,'conservativeDistanceLowerBoundM':gap-2e-6,'method':method})
        arches[arch]={'maximumConvexCombinationSavedResidualM':error,'protectedVerticesExact':int(protected.sum()),'oldSameToothHullInclusionVerifiedWith1MicrometreAllowance':True,'hasCustomNormals':bool(d.has_custom_normals),'world':p.copy(),'edges':q.arr(d.edges,'vertices',len(d.edges),2,'i4')}
        print('R76_ARCH_CHECK',arch,'pairs',120,'witness',witness,'customNormals',arches[arch]['hasCustomNormals'],flush=True)
    poses=[]
    for f in (1,7,13,25,31,37):
        s.frame_set(f);bpy.context.view_layer.update();assert abs(bpy.data.objects['AFN74_ORAL_CONTROLS']['jaw_open']-((f-1)/12 if f<=13 else (1 if f==25 else (37-f)/12)))<1e-6;row={'frame':f,'dental':{}}
        for arch in ('upper','lower'):
            o=bpy.data.objects['AFN74_'+arch.upper()+'_TEETH_RIGID'];assert np.max(np.abs(np.array(o.matrix_world)-motion[f]['matrices'][arch]))<1e-7;_,p=q.geom(o);edges=arches[arch]['edges'];rest=arches[arch]['world'];length=np.linalg.norm(rest[edges[:,1]]-rest[edges[:,0]],axis=1);strain=float(np.abs(np.linalg.norm(p[edges[:,1]]-p[edges[:,0]],axis=1)/length-1).max());assert strain<1e-5;row['dental'][arch]={'maximumRelativeTemporalEdgeStrain':strain}
        row['skinErrorM']=float(np.linalg.norm(q.geom(bpy.data.objects['AFN74_SKIN_AND_EXISTING_OCULAR_LINING'])[1]-motion[f]['skin'],axis=1).max());assert row['skinErrorM']<1e-6;row['hairErrorsM']={n:float(np.linalg.norm(q.hair(bpy.data.objects[n])-motion[f]['hair'][n],axis=1).max()) for n in hn};assert max(row['hairErrorsM'].values())<1e-6;poses.append(row)
    previous=q.read(OLD/'c-independent-operation-and-interarch.json');assert previous['sha256']==ref['sourceSha256'] and previous['status']=='PASS_SCOPED_SAVED_OPERATION_AND_ANALYTIC_INTERARCH_CLEARANCE';inherited=min(v['conservativeDistanceLowerBoundAfterMarginM'] for v in previous['interarchProof'])-2e-6;assert inherited>0;images=[]
    for im in bpy.data.images:
        if im.packed_file or im.source!='FILE':continue
        p=Path(bpy.path.abspath(im.filepath));assert p.is_file();images.append({'relative':im.filepath,'sha256':sha(p)})
    ok=all(v['passed'] for v in plane_rows) and all(v['properCrossingWitness'] is None for v in actual_crossings);result={'status':'PASS_SCOPED_ALL_DIFFERENT_TOOTH_PAIRS_AND_SAVED_OPERATION' if ok else 'UNACCEPTED_TOOTH_PAIR_OR_ACTUAL_SURFACE_FAILURE','source':ref['output'],'sha256':ref['outputSha256'],'originalNativeCagesAllKeysWeightsUVAndDriversExact':True,'sameArch240PairCertificates':plane_rows,'actualSurfaceScreens':actual_crossings,'sculptReadback':{a:{k:v for k,v in x.items() if k not in ('world','edges')} for a,x in arches.items()},'sixActualPoses':poses,'sourceInterarchProof':str(OLD/'c-independent-operation-and-interarch.json'),'inheritedInterarchLowerBoundAfterAdditional2MicrometreAllowanceM':inherited,'inheritanceBasis':'Each new saved vertex is within1micrometre of an explicit convex combination of its original same-tooth vertex and original tooth centroid. Both centroid and vertex are in the original same-tooth convex hull. Topology, UV, root/tip local coordinates and sampled dental parent matrices retained. Original fixed-Head rigid jaw analytic scope only.','sameArchScope':'120 pairs per arch, actual finite vertices/surfaces, invariant under the common rigid arch parent. Not a true global minimum or signed distance.','trueGlobalSignedMinimumM':None,'stillUnaccepted':['Full continuous tooth/gum/tongue/skin volumes and contacts.','Other head/body actions, natural hair/cloth, independent soft cages and engine.','Whole-character realism and user female approval.'],'externalTextures':images,'seconds':time.time()-tick};(E/'a-independent-readback.json').write_text(json.dumps(result,indent=2),encoding='utf8');print('R76_SAVED_CROWNS_QUALIFIED',result['status'],time.time()-tick,flush=True)
if __name__=='__main__':main()
