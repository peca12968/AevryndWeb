"""Private artist-groom transfer feasibility. No public asset promotion.
Source: Daniel Bystedt Hair Styles demo, in-file CC BY-SA (version unspecified).
Keep generated donor data, images and derived blend PRIVATE until exact terms
are resolved. Current owned working source and public history stay unchanged.
"""
import bpy,importlib.util,json,time,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sp=importlib.util.spec_from_file_location('a39artist',Path(__file__).with_name('build-female-next-r0039-complete-guides.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a)
m=a.m;f=a.f;b=a.b;v=a.v;E=a.E;PRIVATE=E/'private';PRIVATE.mkdir(exist_ok=True)
REF=f.R/'Reference/character/blender-hair-styles/hair_nodes-female_hair_styles.blend'
OUT=PRIVATE/'aevrynd-female-next-r0039-c-artist-transfer-study.blend'
def write(n,x):(PRIVATE/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def resample(P,count=128):
    arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(P,axis=0),axis=1))]
    assert arc[-1]>1e-8
    return np.column_stack([np.interp(np.linspace(0,arc[-1],count),arc,P[:,j]) for j in range(3)])
def extract():
    assert b.sha(REF)=='1ad6202095c1793678fee7d69a7e9f8b5fdb6e5c293d300eb1062d2d437e8d48'
    bpy.ops.wm.open_mainfile(filepath=str(REF));s=bpy.context.scene
    targets=['long hair main','long hair strands'];keep=set(targets+['long hair growth mesh','head'])
    def unexclude(lc):
        lc.exclude=False;lc.hide_viewport=False
        for c in lc.children:unexclude(c)
    unexclude(bpy.context.view_layer.layer_collection)
    for o in s.objects:
        if o.name not in keep:
            for mm in o.modifiers:mm.show_viewport=False;mm.show_render=False
        o.hide_set(o.name not in keep)
    for name in targets:
        o=bpy.data.objects[name];ng=bpy.data.node_groups.new('PRIVATE_NATIVE_RESAMPLE_'+name,'GeometryNodeTree')
        ng.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');ng.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
        inp=ng.nodes.new('NodeGroupInput');out=ng.nodes.new('NodeGroupOutput');res=ng.nodes.new('GeometryNodeResampleCurve');res.inputs['Mode'].default_value='Count';res.inputs['Count'].default_value=128
        ng.links.new(inp.outputs[0],res.inputs[0]);ng.links.new(res.outputs[0],out.inputs[0]);mm=o.modifiers.new('PRIVATE_EVALUATE_ACTUAL_CURVE_SHAPE','NODES');mm.node_group=ng
    bpy.context.view_layer.update();dep=bpy.context.evaluated_depsgraph_get();records=[];curves=[]
    for name in targets:
        o=bpy.data.objects[name];eo=o.evaluated_get(dep);d=eo.data
        assert isinstance(d,bpy.types.Curves),(name,type(d).__name__)
        print('ARTIST_EVALUATED',name,len(d.curves),len(d.points),flush=True)
        assert len(d.points)<50000000
        p=np.empty(len(d.points)*3,dtype='f4');d.position_data.foreach_get('vector',p);p=p.reshape(-1,3)
        records.append({'name':name,'curves':len(d.curves),'points':len(d.points)})
        for curve in d.curves:
            points=p[curve.first_point_index:curve.first_point_index+curve.points_length]
            assert len(points)==128
            curves.append(points.copy())
    assert len(curves)>=10000,('not enough evaluated curves',len(curves))
    selected=np.linspace(0,len(curves)-1,min(12000,len(curves)),dtype='i4')
    P=np.array([curves[i] for i in selected],dtype='f4')
    np.savez_compressed(PRIVATE/'artist-render-12k-reference-only.npz',positions=P,selectedSourceCurves=selected)
    write('artist-evaluation.json',{'source':str(REF),'sourceSha256':b.sha(REF),'author':'Daniel Bystedt',
        'license':'CC BY-SA exact version not identified; private study only','evaluated':records,
        'selected':len(P),'resampledPoints':128,'resampling':'Actual native Blender curve resampling after original artist modifiers; not control polygons','pointBounds':[P.min((0,1)).tolist(),P.max((0,1)).tolist()],
        'modifiersUsed':'Original Blender authoring graph evaluated locally to study actual artist groom. No source/node code imported into Aevrynd or exported as runtime.'})
    return P
def main():
    start=time.time();P=extract()
    bpy.ops.wm.open_mainfile(filepath=str(a.SRC));s=bpy.context.scene;b.setup(s,b.config(s));before=f.state()
    old=bpy.data.objects[f.OLD];base,rad=m.eval_arrays(old);mx=np.array(old.matrix_world);inv=np.linalg.inv(mx);count=len(P)
    bd=old.data.copy();bd.name='AFN39_C_PRIVATE_MATCHED_BEFORE';bd.remove_curves(indices=list(range(count,len(bd.curves))))
    before_object=old.copy();before_object.data=bd;before_object.name=bd.name
    for mm in list(before_object.modifiers):before_object.modifiers.remove(mm)
    s.collection.objects.link(before_object);before_object.hide_render=False;old.hide_render=True;f.E=PRIVATE;f.render('c-private-before');before_object.hide_render=True
    # Own coarse anatomical affine alignment, independently recorded. Exact
    # real body roots are rebound below; this is not captured correspondence.
    scale=np.array((.094,.085,.081));offset=np.array((0,.005,.234));world=P.astype('f8')*scale+offset
    V,T=b.evaluated(bpy.data.objects[b.BODY],True);tree=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True);tri=V[T]
    maxshift=0.;roots=[];barys=[];normals=[];source_roots=world[:,0].copy();length=.030
    for ci,q in enumerate(world):
        hit,n,tid,d=tree.find_nearest(Vector(q[0]));hit=np.array(hit);normal=a.norm(np.array(n));root=hit+normal*.00018
        delta=root-q[0];maxshift=max(maxshift,float(np.linalg.norm(delta)))
        arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(q,axis=0),axis=1))]
        weight=(1-np.clip(arc/length,0,1))**2;q+=weight[:,None]*delta;q[0]=root
        A,B,C=tri[tid];st=np.linalg.lstsq(np.column_stack((B-A,C-A)),hit-A,rcond=None)[0];bc=np.r_[1-st.sum(),st]
        assert bc.min()>-1e-4
        roots.append(int(tid));barys.append(bc);normals.append(normal)
    local=((world-mx[:3,3])@inv[:3,:3].T).astype('f4')
    d=old.data.copy();d.name='AFN39_C_PRIVATE_ARTIST_FIBRES';d.remove_curves(indices=list(range(count,len(d.curves))));d.position_data.foreach_set('vector',local.ravel())
    o=old.copy();o.data=d;o.name=d.name
    for mm in list(o.modifiers):o.modifiers.remove(mm)
    for key in list(o.keys()):del o[key]
    o['aevrynd_layer']='PRIVATE_ARTIST_GROOM_TRANSFER_STUDY';o['author']='Daniel Bystedt; coarse retarget/bind by Aevrynd'
    o['license']='Upstream CC BY-SA, exact version unresolved. Private feasibility study; not an owned formal runtime asset.'
    s.collection.objects.link(o);o.hide_render=True;o.hide_set(True);old.hide_render=True;old.hide_set(True)
    assert f.state()==before
    o.hide_render=False;bpy.context.view_layer.update();actual,rr=v.hair_arrays(o)
    assert np.array_equal(actual,local) and np.array_equal(rr,rad[:count])
    actual_world=actual.astype('f8')@mx[:3,:3].T+mx[:3,3];r=rr.astype('f8')*np.linalg.norm(mx[:3,:3],ord=2)
    ids=np.linspace(0,count-1,256,dtype='i4');audit=f.flowcheck.check(actual_world[ids],r[ids],tree,tri)
    write('c-representative-body-contact.json',audit)
    f.E=PRIVATE;f.render('c-private')
    np.savez_compressed(PRIVATE/'c-private-root-bindings.npz',rootTriangles=np.array(roots,dtype='i4'),rootBarycentric=np.array(barys),rootNormals=np.array(normals),sourceRoots=source_roots)
    b.camera('face');s.camera.data.lens=85;s['AFN39_status']='PRIVATE_ARTIST_RETARGET_FEASIBILITY_NOT_LICENSED_FOR_PROMOTION'
    bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    write('c-private-build.json',{'source':str(a.SRC),'sourceSha256':b.sha(a.SRC),'donor':str(REF),'donorSha256':b.sha(REF),
      'author':'Daniel Bystedt','declaredLicense':'CC BY-SA (version unresolved)','decision':'PRIVATE_RESEARCH_ONLY_NOT_ADOPTED',
      'output':str(OUT),'outputSha256':b.sha(OUT),'count':count,'beforeMatchedCount':count,'workingSourceStillHas12000':True,'pointsPerFibre':128,
      'sourceBodyEyeTissuesLashesBrowsSkinLightsExposureExact':True,'originalPhysicalRadiiAndMaterialsExact':True,
      'rootSetIntentionallyDifferent':'All roots actually rebound to current body; not old root-set preservation.',
      'affineScale':scale.tolist(),'affineOffset':offset.tolist(),'rootBlendLengthM':length,'maximumRootRebindDisplacementM':maxshift,
      'pilot':audit,'fullChildrenSelfMotionRuntime':'NOT_QUALIFIED','sourceNodeCodeOrDonorHeadInOutput':False,
      'noPublicRedistributionOrFormalAssetPromotion':True,'seconds':time.time()-start})
    print('R39_C_PRIVATE_DONE',audit['status'],maxshift,time.time()-start,flush=True)
if __name__=='__main__':main()
