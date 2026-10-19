"""Realize independent cage locks as actual scalp-bound volume fibres.

Preview is a deterministic subset of the full12000 existing follicles. Native
container/materials are reused, but all shape points are regenerated from own
independent cages; no old angular free-length field or guide attraction.
"""
import bpy,importlib.util,json,sys,time,hashlib,math
from pathlib import Path
import numpy as np
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
spec=importlib.util.spec_from_file_location('c34',Path(__file__).with_name('build-female-next-r0034-descending-locks.py'));c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c);a=c.a;g=a.g
CONTAINER=a.S/'aevrynd-female-next-r0033-c-parted-bob-fibres.blend'

def arrays(d):
    p=np.empty(len(d.points)*3,dtype='f4');d.position_data.foreach_get('vector',p);r=np.empty(len(d.points),dtype='f4');d.attributes['radius'].data.foreach_get('value',r);return p.reshape(-1,a.N,3),r.reshape(-1,a.N)

def optics(P,r,names):
    rows={};hair_min=P.min(1)-r.max(1)[:,None];hair_max=P.max(1)+r.max(1)[:,None]
    for name in names:
        if name==g.b.BODY:continue
        v,t=g.b.evaluated(bpy.data.objects[name],True);sep=np.maximum(v.min(0)-hair_max,hair_min-v.max(0));separated=np.maximum(sep,0).max(1)>1e-6;ids=np.flatnonzero(~separated)
        rootsep=np.maximum(v.min(0)-P[:,0]-r[:,0,None],P[:,0]-r[:,0,None]-v.max(0));root_outside=np.maximum(rootsep,0).max(1)>1e-6;assert root_outside.all()
        row={'completeCurveAABBSeparated':int(separated.sum()),'remainingCurves':len(ids),'allRootsOutsideOpticalAABB':True}
        if len(ids):row['remainingCapsules']=g.check(P[ids],r[ids],BVHTree.FromPolygons(v.tolist(),t.tolist(),all_triangles=True),v[t],roots=False)
        rows[name]=row
    return rows

def main():
    start=time.time();c.configure();preview='--preview' in sys.argv;label='c-preview' if preview else 'c-fibres';E=a.E;g.b.E=E
    proof=a.read('c-build-verification.json');assert proof['expansionAllowed'];guide_source=Path(proof['output']);assert g.b.sha(guide_source)==proof['outputSha256']
    if not preview:
        prior=a.read('c-preview-build.json');assert prior['bodyContact']['status']=='PASS_TESTED_STATIC_CAPSULES' and prior['visualExpansionApproved'] is True
        bpy.ops.wm.open_mainfile(filepath=str(CONTAINER));g.b.setup(bpy.context.scene,g.b.config(bpy.context.scene));bpy.context.scene.render.hair_type='STRIP';bpy.context.scene.render.hair_subdiv=0;g.q.render('r33-physical-wide')
    if not (E/'r33-wide-renders.json').exists() or len(json.loads((E/'r33-wide-renders.json').read_text())['rows'])!=6:
        assert g.b.sha(CONTAINER)=='7f959bb5dd6f04c347ae4f78cb9eac7f1cbbf2a7d91dd24e994c05e6817aaae1';bpy.ops.wm.open_mainfile(filepath=str(CONTAINER));g.b.setup(bpy.context.scene,g.b.config(bpy.context.scene));g.q.render('r33-wide')
    bpy.ops.wm.open_mainfile(filepath=str(guide_source));scene=bpy.context.scene;scene.render.hair_type='STRIP';scene.render.hair_subdiv=0;originals={n:g.signature(bpy.data.objects[n]) for n in proof['originalVisibleMeshesExact']};cfg=g.b.config(scene)
    for o in scene.objects:
        if o.type=='CURVE' and o.name.startswith('AFN34_'):o.hide_render=True
    body=bpy.data.objects[g.b.BODY];V,T=g.b.evaluated(body,True);tri=V[T];tree=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True)
    data,roots,params,parts,owners,centers=a.root_data();source_ids=np.arange(0,len(roots),10 if preview else 1,dtype='i4');count=len(source_ids)
    paths=[];radii=[];scatters=[];trims=[]
    existing_cache=a.S/f'aevrynd-female-next-r0034-{label}-hair.npz'
    reuse='--reuse-cache' in sys.argv
    if reuse:
        cached_report=a.read(label+'-build.json');assert cached_report['sourceSha256']==g.b.sha(guide_source) and cached_report['cacheSha256']==g.b.sha(existing_cache),'Reuse requires a prior verified authored-cache report matching this exact guide source'
        cached=np.load(existing_cache);assert np.array_equal(cached['sourceRootIds'],source_ids);positions=cached['positions'].copy();rr=cached['radii'].copy();scatters=cached['scatterUV'].tolist();trims=cached['freeTrim'].tolist();print('R34_REUSE_AUTHORED_CACHE',g.b.sha(existing_cache),flush=True)
    for k,ri in enumerate([] if reuse else source_ids):
        rng=np.random.default_rng(340034+int(ri));rho=math.sqrt(float(rng.random()));angle=float(rng.uniform(0,math.tau));scatter=(rho*math.cos(angle),rho*math.sin(angle));trim=float(rng.uniform(.73,1.))
        P,*_=a.groom_path(tree,tri,roots[ri],params[ri],a.MASTERS[owners[ri]],scatter,trim)
        arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(P,axis=0),axis=1))];remain=arc[-1]-arc
        # Fibre radius tapers over a physical terminal length, not a repeated
        # CV cutoff. Counts, material and root positions do not hide the form.
        radius=float(data['radii'][ri,0]);r=radius*(.04+.96*np.clip(remain/.026,0,1)**.65);r[-1]=.000001
        paths.append(P);radii.append(r);scatters.append(scatter);trims.append(trim)
        if k%2000==0:print('R34_CHILDREN',label,k,count,time.time()-start,flush=True)
    if not reuse:positions=np.asarray(paths,dtype='f4');rr=np.asarray(radii,dtype='f4')
    del paths,radii
    with bpy.data.libraries.load(str(CONTAINER),link=False) as (src,dst):
        assert 'AFN33_C_BODY_BOUND_FIBRES' in src.hair_curves;dst.hair_curves=['AFN33_C_BODY_BOUND_FIBRES']
    d=dst.hair_curves[0];d.surface=None;d.name='AFN34_C_INDEPENDENT_LOCK_FIBRES'
    if count<len(d.curves):d.remove_curves(indices=list(range(count,len(d.curves))))
    assert len(d.curves)==count;d.resize_curves([a.N]*count);d.position_data.foreach_set('vector',positions.ravel());d.attributes['radius'].data.foreach_set('value',rr.ravel());d.attributes['curve_type'].data.foreach_set('value',[1]*count);d.attributes['material_index'].data.foreach_set('value',[int(i)%6 for i in source_ids])
    o=bpy.data.objects.new(d.name,d);scene.collection.objects.link(o);o.parent=body;o.matrix_world=Matrix.Identity(4);o['aevrynd_layer']='INDEPENDENT_MASTER_LOCK_FIBRES';o['aevrynd_static_only']=True;bpy.context.view_layer.update()
    local,ar=arrays(d);assert np.array_equal(local,positions) and np.array_equal(ar,rr) and np.isfinite(local).all() and (ar>0).all();mx=np.array(o.matrix_world);world=local.astype('f8')@mx[:3,:3].T+mx[:3,3];r=ar.astype('f8')*np.linalg.norm(mx[:3,:3],ord=2)
    audit=g.check(world,r,tree,tri);a.save(label+'-body-contact.json',audit);optical=optics(world,r,originals);a.save(label+'-optical-contact.json',optical)
    assert {n:g.signature(bpy.data.objects[n]) for n in originals}==originals and g.b.config(scene)==cfg
    cache=a.S/f'aevrynd-female-next-r0034-{label}-hair.npz';np.savez_compressed(cache,positions=local,radii=ar,sourceRootIds=source_ids,masterIds=owners[source_ids],scatterUV=np.array(scatters,dtype='f4'),freeTrim=np.array(trims,dtype='f4'),rootTriangles=data['rootTriangles'][source_ids],rootBarycentric=data['rootBarycentric'][source_ids],parts=parts[source_ids],scalpParams=params[source_ids])
    g.b.camera('face');scene['AFN34_status']='INDEPENDENT_CAGE_VOLUME_PREVIEW' if preview else 'INDEPENDENT_CAGE_VOLUME_STATIC_CANDIDATE';bpy.data.orphans_purge(do_local_ids=True,do_linked_ids=True,do_recursive=True)
    linked=[{'name':i.name_full,'type':type(i).__name__,'library':i.library.filepath} for i in bpy.data.user_map() if i.library]
    a.save(label+'-dependency-inspection.json',{'linkedIDs':linked,'libraryIdentifiers':[{'name':l.name,'filepath':l.filepath,'users':l.users} for l in bpy.data.libraries],'texts':[t.name for t in bpy.data.texts],'scope':'Inspect identifiers after local append before removing only unreferenced library identifiers; never batch-delete live linked data/node groups.'})
    assert not linked and not bpy.data.texts
    for library in list(bpy.data.libraries):bpy.data.libraries.remove(library)
    assert not bpy.data.libraries
    out=a.S/f'aevrynd-female-next-r0034-{label}.blend';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out),compress=True)
    crosssections=[];scatter_arr=np.array(scatters)
    for mi,m in enumerate(a.MASTERS):
        members=owners[source_ids]==mi;coords=scatter_arr[members]*np.array((m[7],m[8]));eig=np.linalg.eigvalsh(np.cov(coords.T));crosssections.append({'master':mi,'name':m[0],'fibres':int(members.sum()),'ellipseHalfAxesM':[m[7],m[8]],'scatterCovarianceEigenvaluesM2':eig.tolist(),'minorMajorRatio':float(eig[0]/eig[1]),'scope':'Generation-plane scatter has two nonzero axes; this is not a hair self/contact or full swept-volume proof'})
    report={'source':str(guide_source),'sourceSha256':g.b.sha(guide_source),'headSource':str(a.SRC),'headSourceSha256':g.b.sha(a.SRC),'output':str(out),'outputSha256':g.b.sha(out),'cache':str(cache),'cacheSha256':g.b.sha(cache),'curves':count,'pointsPerCurve':a.N,'masterLocks':len(a.MASTERS),'previewSubsetOfFullRoots':preview,'same12000RootSetAsR33':not preview,'originalNineMeshesExact':originals,'sourceStageExactExceptMatched85mmHeadCamera':True,'curvePrimitive':'STRIP','hairSubdivision':0,'primitiveReason':'STRAND ignores diameter; STRIP is required to respect tested physical radius. Matched r33-physical-wide comparison separates this functional fix from geometry change.','nativeMatrixWorld':mx.tolist(),'positionsSha256':hashlib.sha256(local.tobytes()).hexdigest(),'radiiSha256':hashlib.sha256(ar.tobytes()).hexdigest(),'materials':'Original same6 r33 chestnut fibre materials; no density/material change used to judge full final shape','bodyContact':audit,'opticalContact':optical,'crosssectionDiagnostics':crosssections,'visualExpansionApproved':False,'seconds':time.time()-start,'limits':['Representative guides and preview are not all-child proof.','Final body/optic static proof does not imply hair/hair self, motion, wind, cloth, rig, engine, LOD or performance.','Control cages are editable offline; changes require explicit cache regeneration.','Appearance judged separately from geometry/contact; no whole-character or runtime promotion.']};a.save(label+'-build.json',report)
    report.pop('sourceStageExactExceptMatched85mmHeadCamera',None);report['sourceGeometryMaterialsLightsExposureExact']=True;report['controlledStageChanges']=['Same85mm complete-head framing for both actual paired grooms','STRAND->STRIP with subdivision0 to respect physical radii'];a.save(label+'-build.json',report)
    g.q.render(label);print('R34_FIBRES_DONE',label,audit['status'],time.time()-start,flush=True)

if __name__=='__main__':main()
