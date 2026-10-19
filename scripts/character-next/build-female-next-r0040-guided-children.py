"""Private full-character C review from repaired complete guide paths.
Own explicit same-source-scalp-island three-guide delta lineage, actual native
variable POLY fibres. Artist groom remains private; no runtime promotion.
"""
import bpy,importlib.util,time,json
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
sp=importlib.util.spec_from_file_location('routes40',Path(__file__).with_name('build-female-next-r0040-surface-routes.py'));rt=importlib.util.module_from_spec(sp);sp.loader.exec_module(rt)
ad=rt.ad;rod=rt.rod;a=rt.a;m=rt.m;f=rt.f;b=rt.b;v=rt.v;E=rt.E;PVT=rt.PVT
review=f.flowcheck.module('review40','render-female-next-r0039-review.py')
OUT=PVT/'aevrynd-female-next-r0040-c-complete-contact-review.blend'

def components(V,T):
    parent=np.arange(len(V))
    def root(j):
        while parent[j]!=j:parent[j]=parent[parent[j]];j=parent[j]
        return j
    for t in T:
        j=root(int(t[0]))
        for k in t[1:]:parent[root(int(k))]=j
    return np.array([root(j) for j in range(len(V))])

def main():
    start=time.time();guideproof=json.loads((E/'c-refined-guide-surface-routes.json').read_text());assert guideproof['status']=='PASS_TESTED_STATIC_CAPSULES'
    guides,parameters=rt.unpack(PVT/'c-refined-surface-guide-paths.npz');rest=np.load(PVT/'a-rebuilt-guide-paths.npz')['restPositionsWorld'].astype('f8')
    original=np.load(PVT/'raw-artist-guides-reference-only.npz');donor=np.load(rod.c.PRIVATE/'artist-render-12k-reference-only.npz')['positions'].astype('f8');assert len(donor)==11223
    G=original['growthVertices'];GT=original['growthTriangles'];labels=components(G,GT);gTree=BVHTree.FromPolygons(G.tolist(),GT.tolist(),all_triangles=True)
    def part(point):
        _,_,tid,dist=gTree.find_nearest(Vector(point));return int(labels[GT[tid,0]]),float(dist)
    guideparts=np.array([part(p[0])[0] for p in original['allRawPositions'][:346]])
    trees={};domains={}
    for k in np.unique(guideparts):
        ids=np.flatnonzero(guideparts==k);assert len(ids)>=3;tree=KDTree(len(ids))
        for j in ids:tree.insert(Vector(original['allRawPositions'][j,0]),int(j))
        tree.balance();trees[int(k)]=tree;domains[int(k)]=len(ids)
    childparts=[];indices=[];weights=[];growthDistances=[]
    for ci,p in enumerate(donor):
        if ci>=11193:ids=[346+ci-11193]*3;w=np.array([1.,0.,0.]);k=-1;dist=0.
        else:
            k,dist=part(p[0]);assert k in trees
            near=trees[k].find_n(Vector(p[0]),3);ids=[q[1] for q in near];ds=np.array([q[2] for q in near]);w=1/np.maximum(ds,1e-7)**2;w/=w.sum()
        childparts.append(k);indices.append(ids);weights.append(w);growthDistances.append(dist)
    indices=np.array(indices,dtype='i4');weights=np.array(weights);assert np.max(np.abs(weights.sum(1)-1))<1e-12
    src=rod.c.PRIVATE/'aevrynd-female-next-r0039-c1-surface-transfer-study.blend';bpy.ops.wm.open_mainfile(filepath=str(src));s=bpy.context.scene
    old=bpy.data.objects['AFN39_C1_PRIVATE_SURFACE_TRANSFER'];base,rad=v.hair_arrays(old);mx=np.array(old.matrix_world);base=base.astype('f8')@mx[:3,:3].T+mx[:3,3];rad=rad.astype('f8')
    old.hide_render=True;retained=f.state();old.hide_render=False
    for o in s.objects:
        if o.type=='CURVES' and o!=old and o.name not in ('AFN36_L_BrowFibres','AFN36_R_BrowFibres'):o.hide_set(True)
    old.hide_set(False);f.E=PVT
    beforeviews=f.render('c-before');beforeextra=review.extras('c-before',PVT)
    old.hide_render=True;old.hide_set(True);paths=[];radii=[];grid=np.linspace(0,1,128);rootError=0.
    for ci,(ids,w) in enumerate(zip(indices,weights)):
        t=np.unique(np.concatenate([grid]+[parameters[k] for k in ids if len(parameters[k])>128]))
        P=np.column_stack([np.interp(t,grid,base[ci,:,j]) for j in range(3)])
        for k,weight in zip(ids,w):
            if weight==0:continue
            change=np.column_stack([np.interp(t,parameters[k],guides[k][:,j])-np.interp(t,grid,rest[k,:,j]) for j in range(3)])
            P+=weight*change
        P[0]=base[ci,0];rootError=max(rootError,float(np.linalg.norm(P[0]-base[ci,0])));paths.append(P);radii.append(np.interp(t,grid,rad[ci]))
    obj=ad.make_native(old,paths,radii,'AFN40_C_PRIVATE_GUIDED_CHILDREN');actual,rr=ad.read_native(obj)
    assert max(float(np.linalg.norm(x[0]-base[ci,0])) for ci,x in enumerate(actual))<1.5e-7
    obj.hide_render=True;assert f.state()==retained;obj.hide_render=False
    V,T=b.evaluated(bpy.data.objects[b.BODY],True);tree=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True)
    ids=np.linspace(0,len(actual)-1,256,dtype='i4');pilot=f.flowcheck.check([actual[k] for k in ids],[rr[k] for k in ids],tree,V[T])
    ad.save('c-child-pilot.json',pilot);f.render('c-after');afterextra=review.extras('c-after',PVT);assert beforeextra==afterextra
    controls=ad.make_native(old,guides,[np.full(len(x),.000046) for x in guides],'AFN40_C_PRIVATE_EDITABLE_GUIDES');controls.hide_render=True;controls.hide_set(True)
    b.camera('face');s.camera.data.lens=85;obj.hide_set(False);bpy.context.view_layer.objects.active=obj;obj.select_set(True)
    s['AFN40_scope']='PRIVATE_STATIC_GROOM_CONTACT_REVIEW; NOT adopted, all-child/self/dynamics/runtime unqualified'
    bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    np.savez_compressed(PVT/'c-child-guide-lineage.npz',indices=indices,weights=weights,guideParts=guideparts,childParts=np.array(childparts),growthDistances=np.array(growthDistances))
    ad.save('c-complete-build.json',{'source':str(src),'output':str(OUT),'outputSha256':b.sha(OUT),'workingSource':str(rod.SRC),'workingSourceSha256':b.sha(rod.SRC),'sourceArtist':'Daniel Bystedt','license':'Upstream CC BY-SA exact version unresolved, PRIVATE ONLY','count':len(actual),'points':sum(map(len,actual)),'sourceCountPreserved':True,'physicalRadiiPreservedPiecewiseLinearly':True,'sourceMaterialPreserved':True,'originalC1RootsPreservedWithinFloat32':True,'rootErrorM':rootError,'retainedBodyEyeSkinLashBrowStageExact':True,'guideDomains':domains,'lineage':'3 inverse-distance native source-root neighbors on actual source-growth connected island; last30 direct secondary guides; piecewise-linear correction uses union of guide breakpoints and original child samples','pilot':pilot,'fullChildSelfDynamicsRuntime':'NOT_QUALIFIED','matchedAdditionalViews':beforeextra,'seconds':time.time()-start})
    print('R40_CHILDREN_DONE',len(actual),sum(map(len,actual)),pilot['unqualifiedSegments'],time.time()-start,flush=True)

if __name__=='__main__':main()
