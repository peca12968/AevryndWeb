"""Realize the same C hairstyle field as native editable Blender POLY fibres.

Use a known valid native Curves block only as a format container. All points,
radii, materials and root lineage are replaced by the current actual scalp
groom. No old hair routing/geometry, node system or head coordinates survive.
"""
import bpy,importlib.util,json,sys,time,hashlib,math
from pathlib import Path
import numpy as np
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
spec=importlib.util.spec_from_file_location('c33',Path(__file__).with_name('build-female-next-r0033-volume-bob.py'));c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c);g=c.g
COUNT=12000;OUT=g.b.S/'aevrynd-female-next-r0033-c-parted-bob-fibres.blend'
CONTAINER=g.b.S/'aevrynd-female-next-r0013-b-safe-io-native-envelope-hair-study.blend'

def arrays(d):
    p=np.empty(len(d.points)*3,dtype='f4');d.position_data.foreach_get('vector',p)
    r=np.empty(len(d.points),dtype='f4');d.attributes['radius'].data.foreach_get('value',r)
    return p.reshape(-1,g.N,3),r.reshape(-1,g.N)

def write(d,P,rr):
    d.position_data.foreach_set('vector',np.asarray(P,dtype='f4').ravel())
    d.attributes['radius'].data.foreach_set('value',np.asarray(rr,dtype='f4').ravel())
    d.attributes['curve_type'].data.foreach_set('value',[1]*len(P))
    d.attributes['material_index'].data.foreach_set('value',[k%6 for k in range(len(P))])

def native_container():
    with bpy.data.libraries.load(str(CONTAINER),link=False) as (a,b):
        names=list(a.hair_curves);assert 'AFN13_PRIMARY_MASS' in names,names;b.hair_curves=['AFN13_PRIMARY_MASS']
    d=b.hair_curves[0];d.surface=None;d.materials.clear();d.name='AFN33_C_BODY_BOUND_FIBRES'
    for attr in list(d.attributes):
        if attr.name not in ('position','radius','curve_type','material_index'):d.attributes.remove(attr)
    old_size=len(d.curves);assert old_size>=4;d.remove_curves(indices=list(range(4,old_size)));d.resize_curves([g.N]*4)
    o=bpy.data.objects.new(d.name,d);bpy.context.scene.collection.objects.link(o);o.parent=bpy.data.objects[g.b.BODY];o.matrix_world=Matrix.Identity(4)
    mats=[]
    for k in range(6):
        m=g.material();m.name='AFN33_C_Chestnut_'+str(k);p=m.node_tree.nodes.get('Principled BSDF');factor=.76+.09*k
        p.inputs['Base Color'].default_value=(.038*factor,.016*factor,.008*factor,1);m.diffuse_color=(.038*factor,.016*factor,.008*factor,1);mats.append(m);d.materials.append(m)
    return o

def main():
    start=time.time();c.configure();proof=json.loads((g.E/'c-build-verification.json').read_text());assert proof['expansionAllowed'];guide_source=Path(proof['output']);assert g.b.sha(guide_source)==proof['outputSha256']
    bpy.ops.wm.open_mainfile(filepath=str(guide_source));s=bpy.context.scene;g.b.E=g.E
    for o in s.objects:
        if o.type=='CURVE' and o.name.startswith('AFN33_'):o.hide_render=True
    visible={n:g.signature(bpy.data.objects[n]) for n in proof['preservedVisibleMeshes']};cfg=g.b.config(s)
    V,T=g.b.evaluated(bpy.data.objects[g.b.BODY],True);tree=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True);tri=V[T]
    o=native_container();d=o.data
    # Bounded format test before large authoring; round-trip an actual native
    # block. Avoid the previously crashing new-data/operator/library deletion.
    pilot=np.load(g.b.S/'aevrynd-female-next-r0033-c-volume-bob-guides.npz')['positions'][:4]
    pilot_rr=np.broadcast_to(np.linspace(.00004,.000002,g.N),(4,g.N)).copy();write(d,pilot,pilot_rr)
    pilot_path=g.E/'c-native-format-pilot.blend';g.b.camera('face');bpy.ops.wm.save_as_mainfile(filepath=str(pilot_path),compress=True)
    bpy.ops.wm.open_mainfile(filepath=str(pilot_path));o=bpy.data.objects['AFN33_C_BODY_BOUND_FIBRES'];d=o.data
    pp,pr=arrays(d);assert np.array_equal(pp,pilot.astype('f4')) and np.array_equal(pr,pilot_rr.astype('f4'));assert not o.modifiers
    g.save('c-native-format-pilot.json',{'container':str(CONTAINER),'containerSha256':g.b.sha(CONTAINER),'scope':'Data-format container only; all original curve geometry/materials removed','fourRealCurvesReopened':True,'positionsAndRadiiExact':True,'curveType':'POLY / INT8 value1 through RNA int32 list','newContainerConstructorOrOperatorUsed':False})
    print('R33_NATIVE_FORMAT_ROUNDTRIP_PASS',flush=True)
    rng=np.random.default_rng(330033);paths=[];radii=[];bindings=[];guideids=[];weights=[];params=[];parts=[]
    guides=np.load(g.b.S/'aevrynd-female-next-r0033-c-volume-bob-guides.npz')['positions'].astype('f8')
    ugrid=g.U;agrid=g.AZ
    for ci in range(COUNT):
        side=-1 if ci<COUNT//2 else 1;a=float(rng.uniform(.004,math.pi-.004));lo=g.theta_min(a)
        theta=math.asin(float(rng.uniform(math.sin(lo),math.sin(1.54))));u=(theta-lo)/(1.54-lo)
        P,root=c.volume_path(tree,tri,side,a,u)
        # Bilinear lineage within this part. Re-evaluate actual scalp root and
        # proximal path instead of averaging points through a convex scalp.
        ia=int(np.clip(np.searchsorted(agrid,a)-1,0,len(agrid)-2));iu=int(np.clip(np.searchsorted(ugrid,u)-1,0,len(ugrid)-2))
        fa=float(np.clip((a-agrid[ia])/(agrid[ia+1]-agrid[ia]),0,1));fu=float((u-ugrid[iu])/(ugrid[iu+1]-ugrid[iu]));base=0 if side<0 else len(ugrid)*len(agrid)
        ids=np.array((base+iu*len(agrid)+ia,base+iu*len(agrid)+ia+1,base+(iu+1)*len(agrid)+ia,base+(iu+1)*len(agrid)+ia+1));w=np.array(((1-fu)*(1-fa),(1-fu)*fa,fu*(1-fa),fu*fa))
        # Primary bundle attraction only in the free half; it fades at the
        # root, preserving the independent scalp domain and follicle exit.
        nearest=int(ids[np.argmax(w)]);Q=guides[nearest];t=np.linspace(0,1,g.N);pull=.30*np.clip((t-.30)/.70,0,1)**1.5
        P+=(Q-P)*pull[:,None]
        # Strand-scale variation and feathered tips, not a density mask or cap.
        phase=float(rng.uniform(0,math.tau));amplitude=float(rng.uniform(.00004,.00016))
        P+=amplitude*(np.sin(math.pi*t)**2*np.sin(10*math.pi*t+phase))[:,None]*np.array((math.sin(a),math.cos(a),.15))
        P[:,2]+=float(rng.uniform(-.006,.006))*t**6
        radius=float(rng.uniform(.000032,.000046));rr=radius*(.28+.72*(1-t)**.25);rr[-1]=.000002
        paths.append(P);radii.append(rr);bindings.append(root);guideids.append(ids);weights.append(w);params.append((a,u));parts.append(side)
        if ci%2000==0:print('R33_FIBRES_AUTHORED',ci,COUNT,time.time()-start,flush=True)
    P=np.array(paths,dtype='f4');rr=np.array(radii,dtype='f4');del paths,radii
    d.add_curves([g.N]*(COUNT-4));write(d,P,rr);bpy.context.view_layer.update()
    actual,ar=arrays(d);assert np.array_equal(actual,P) and np.array_equal(ar,rr);assert np.isfinite(actual).all() and (ar>0).all();assert all(x.value==1 for x in d.attributes['curve_type'].data)
    # Read saved precision and actual world matrix before testing all children.
    mx=np.array(o.matrix_world);world=actual.astype('f8')@mx[:3,:3].T+mx[:3,3]
    radius_scale=float(np.linalg.norm(mx[:3,:3],ord=2));actual_r=ar.astype('f8')*radius_scale
    g.save('c-fibre-generation.json',{'curves':COUNT,'pointsPerCurve':g.N,'sourceGuides':str(guide_source),'sourceGuideSha256':g.b.sha(guide_source),'sourceHead':str(g.SRC),'sourceHeadSha256':g.b.sha(g.SRC),'generator':'Own actual-surface analytic scalp path + same-part free guide-bundle attraction; all roots from actual evaluated body triangle barycentrics','surfaceSampling':'Uniform azimuth and sine-elevation; approximate ellipsoidal area distribution, not measured follicle density','guideLineage':'Four same-part parametric neighbors, normalized bilinear weights; closest group attracts only free half','layers':'Native fibre object, hidden editable guides, hidden separate scalp chart meshes; no opaque scalp cap','containerOnly':str(CONTAINER),'containerGeometryRetained':False,'radiiRangeM':[float(ar.min()),float(ar.max())],'curveType':'POLY','selfCollision':'NOT_TESTED','dynamicMotion':'NOT_IMPLEMENTED','runtime':'NOT_IMPLEMENTED'})
    audit=g.check(world,actual_r,tree,tri);g.save('c-all-fibre-body-contact.json',audit)
    optics={}
    for name in visible:
        if name==g.b.BODY:continue
        vv,tt=g.b.evaluated(bpy.data.objects[name],True);ot=BVHTree.FromPolygons(vv.tolist(),tt.tolist(),all_triangles=True)
        # Most are separated by an AABB; compute exact positive box separation
        # as a broadphase proof for the complete fibre capsule, not CV-only.
        hair_min=world.min((0,1))-actual_r.max();hair_max=world.max((0,1))+actual_r.max()
        sep=np.maximum(vv.min(0)-hair_max,hair_min-vv.max(0));gap=float(np.maximum(sep,0).max())
        if gap>1e-6:optics[name]={'status':'PASS_AABB_SEPARATION','minimumCertifiedAxisGapM':gap}
        else:optics[name]=g.check(world,actual_r,ot,vv[tt],roots=False)
    g.save('c-all-fibre-optical-contact.json',optics)
    assert {n:g.signature(bpy.data.objects[n]) for n in visible}==visible
    assert g.b.config(bpy.context.scene)==cfg
    o['aevrynd_layer']='SCALP_HAIR_FIBRES';o['AFN33_status']='STATIC_HAIRSTYLE_APPEARANCE_CANDIDATE_NOT_DYNAMICS_RUNTIME';o['AFN33_root_binding_cache']='aevrynd-female-next-r0033-c-bob-fibres.npz'
    np.savez_compressed(g.b.S/'aevrynd-female-next-r0033-c-bob-fibres.npz',positions=actual,radii=ar,parts=np.array(parts,dtype='i4'),scalpParams=np.array(params,dtype='f4'),rootTriangles=np.array([x['triangle'] for x in bindings],dtype='i4'),rootBarycentric=np.array([x['barycentric'] for x in bindings]),guideIndices=np.array(guideids,dtype='i4'),guideWeights=np.array(weights,dtype='f4'))
    # Remove only true orphans, leaving no runtime/linked library dependency.
    bpy.data.orphans_purge(do_local_ids=True,do_linked_ids=True,do_recursive=True)
    assert not bpy.data.libraries and not bpy.data.texts
    g.b.camera('face');bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    g.save('c-fibre-build-verification.json',{'source':str(g.SRC),'sourceSha256':g.b.sha(g.SRC),'output':str(OUT),'outputSha256':g.b.sha(OUT),'originalVisibleMeshesExact':visible,'stageExact':True,'curves':COUNT,'pointsPerCurve':g.N,'allChildrenBodyContact':audit,'opticalContact':optics,'bodyPass':audit['status']=='PASS_TESTED_STATIC_CAPSULES','runtimePromotion':False,'externalLibraries':0,'seconds':time.time()-start})
    g.q.render('c-fibres');print('R33_FIBRES_DONE',audit['status'],time.time()-start,flush=True)

if __name__=='__main__':main()
