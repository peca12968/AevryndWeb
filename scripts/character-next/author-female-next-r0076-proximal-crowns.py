"""Local smooth proximal crown sculpt, with root/tip pins and old-hull inclusion."""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time,heapq
from mathutils.bvhtree import BVHTree
R=Path(r'D:\Download\Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0076-proximal-crowns';OLD=E.parent/'r0075-occlusion-authoring';SRC=S/'aevrynd-female-next-r0075-c-coordinated-oral-arc-study.blend';SHA='367198d2448a401715f09174c5587e092f5ea9b53c0de2544eb59d6c5cf4cc59';OUT=S/'aevrynd-female-next-r0076-a-proximal-crown-sculpt-study.blend';GAP=.00002
def module(name,file):
    s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
q=module('crown76data','qualify-female-next-r0075-dental-motion.py');screen=module('crown76cross','screen-female-next-r0074-oral-contact.py');render=module('crown76render','build-female-next-r0074-oral-controls.py');render.E=E;render.m.shade.g.E=E
def save(n,v):(E/n).write_text(json.dumps(v,indent=2)+'\n',encoding='utf8',newline='\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def constraints(points,owner,protected,ia,ib):
    ai=np.flatnonzero(owner==ia);bi=np.flatnonzero(owner==ib);a=points[ai];b=points[bi];ca=a.mean(0);cb=b.mean(0);axis=(cb-ca)/np.linalg.norm(cb-ca);pa=points[(owner==ia)&protected];pb=points[(owner==ib)&protected];normals=np.r_[axis[None,:],q.directions(pa),-q.directions(pb)];normals=normals[(normals@axis)>.75];best=None
    for n in normals:
        lo=float((pa@n).max())+GAP*.5+2e-6;hi=float((pb@n).min())-GAP*.5-2e-6
        if lo>=hi:continue
        d=float(np.clip(((a@n).max()+(b@n).min())*.5,lo,hi));bounds=(d-GAP*.5,-d-GAP*.5);largest=0.;proposal=[];valid=True
        for ids,p,c,normal,bound in ((ai,a,ca,n,bounds[0]),(bi,b,cb,-n,bounds[1])):
            if bound-c@normal<.00015:valid=False;break
            protected_gap=float((bound-p[protected[ids]]@normal).min());sigma=min(.00008,protected_gap/12);assert sigma>0;v=p@normal-bound;rproj=(p-c)@normal;active=(v>-8*sigma)&(rproj>0)&~protected[ids];lam=np.ones(len(ids));delta=sigma*np.logaddexp(0,v[active]/sigma);lam[active]=1-delta/rproj[active]
            if lam.min()<.75:valid=False;break
            change=np.linalg.norm((1-lam)[:,None]*(p-c),axis=1);largest=max(largest,float(change.max()));proposal.append((ids,lam))
        if not valid or largest>.00075:continue
        score=largest+0.00005*(1-float(n@axis))
        if best is None or score<best[0]:best=(score,n,d,proposal,largest)
    if best is None:raise AssertionError(('No bounded root/tip-preserving proximal sculpt plane',ia,ib))
    return best
def sculpt(o,arch):
    d,p=q.geom(o);p=p.copy();d.calc_loop_triangles();tri=np.array([t.vertices[:] for t in d.loop_triangles],dtype='i4');charts=q.read(E.parent/'r0074-oral-controls/source-oral-uv-islands.json')[3:];charts=[c for c in charts if (c['jawAffected']==0)==(arch=='upper')];owner=q.tooth_ids(o,charts);tooth=owner[tri[:,0]];assert np.all(owner[tri]==tooth[:,None]);tree=BVHTree.FromPolygons(p.tolist(),tri.tolist(),all_triangles=True);pairs={}
    for a,b in tree.overlap(tree):
        i,j=int(tooth[a]),int(tooth[b])
        if a>=b or i==j:continue
        witness=screen.proper_cross(p[tri[a]],p[tri[b]])
        if witness is None:continue
        key=tuple(sorted((i,j)));row=pairs.setdefault(key,{'properCrossings':0,'firstWorldPointM':witness});row['properCrossings']+=1
    edge=np.array([v.vertices[:] for v in d.edges],dtype='i4');counts=np.zeros(len(edge),'i4')
    for loop in d.loops:counts[loop.edge_index]+=1
    boundary=np.unique(edge[counts==1]);adj=[[] for _ in p]
    for a,b in edge:
        length=float(np.linalg.norm(p[a]-p[b]));adj[a].append((int(b),length));adj[b].append((int(a),length))
    distance=np.full(len(p),np.inf);distance[boundary]=0;heap=[(0.,int(v)) for v in boundary];heapq.heapify(heap)
    while heap:
        dist,i=heapq.heappop(heap)
        if dist!=distance[i] or dist>.00035:continue
        for j,length in adj[i]:
            value=dist+length
            if value<distance[j] and value<=.00035:distance[j]=value;heapq.heappush(heap,(value,j))
    protected=distance<=.00035
    for i in range(16):
        ids=np.flatnonzero(owner==i);tip=int(ids[np.argmin(p[ids,2]) if arch=='upper' else np.argmax(p[ids,2])]);protected[tip]=True
        for v,_ in adj[tip]:protected[v]=True
    centers=np.array([p[owner==i].mean(0) for i in range(16)]);lam=np.ones(len(p));planes=[]
    for (i,j),witness in sorted(pairs.items()):
        current=centers[owner]+lam[:,None]*(p-centers[owner]);_,n,distance0,proposal,largest=constraints(current,owner,protected,i,j)
        for ids,factor in proposal:lam[ids]*=factor
        planes.append({'toothA':i,'toothB':j,'normal':n.tolist(),'offset':distance0,'guardM':GAP,'sourceWitness':witness,'singleStepMaximumWorldDeltaM':largest});print('R76_SCULPT_PAIR',arch,i,j,largest,flush=True)
    new=centers[owner]+lam[:,None]*(p-centers[owner]);delta=np.linalg.norm(new-p,axis=1);assert not np.any(delta[protected]>1e-12) and float(delta.max())<.00075
    for row in planes:
        n=np.array(row['normal']);gap=float((new[owner==row['toothB']]@n).min()-(new[owner==row['toothA']]@n).max());assert gap>=GAP-1e-10;row['actualVertexSupportGapM']=gap
    n0=np.cross(p[tri[:,1]]-p[tri[:,0]],p[tri[:,2]]-p[tri[:,0]]);n1=np.cross(new[tri[:,1]]-new[tri[:,0]],new[tri[:,2]]-new[tri[:,0]]);length0=np.linalg.norm(n0,axis=1);length1=np.linalg.norm(n1,axis=1);cos=np.sum(n0*n1,axis=1)/np.maximum(length0*length1,1e-24);assert cos.min()>0 and (length1/np.maximum(length0,1e-24)).min()>.02,('Fold or severe collapse',arch,float(cos.min()))
    inv=np.linalg.inv(np.array(o.matrix_world));local=new@inv[:3,:3].T+inv[:3,3];original=q.arr(o.data.vertices,'co',len(o.data.vertices),3).copy();local=local.astype('f4');local[protected]=original[protected];o.data.vertices.foreach_set('co',local.ravel());o.data.update();np.savez_compressed(E/(arch+'-sculpt-lineage.npz'),oldWorld=p,newWorld=new,centers=centers,vertexTooth=owner,radialLambda=lam,protected=protected,boundary=boundary,triangles=tri)
    return {'arch':arch,'actualCrossingToothPairsBefore':len(pairs),'originalActualTriangleCrossings':sum(v['properCrossings'] for v in pairs.values()),'planes':planes,'rootAndTipProtectedVertices':int(protected.sum()),'changedVerticesOver1Micrometre':int((delta>1e-6).sum()),'maximumWorldSculptM':float(delta.max()),'minimumLambda':float(lam.min()),'minimumTriangleNormalCosine':float(cos.min()),'allNewVerticesConvexCombinationsOfOldSameToothVertices':True,'rootBoundaryOriginalLocalCoordinatesExact':True}
def main():
    assert not OUT.exists() and sha(SRC)==SHA;bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();rows=[]
    for arch in ('lower','upper'):rows.append(sculpt(bpy.data.objects['AFN74_'+arch.upper()+'_TEETH_RIGID'],arch))
    s['AFN76_scope']='Local smooth proximal crown contact sculpt only; roots/tips pinned, tooth identities and parent motion retained. New crown vertices stay in the old corresponding tooth convex hull. Full-mouth/engine acceptance remains unproven.';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True);save('a-build-summary.json',{'source':str(SRC),'sourceSha256':SHA,'output':str(OUT),'outputSha256':sha(OUT),'outputBytes':OUT.stat().st_size,'sculpt':rows,'method':'Smooth local radial contact contour correction; not tooth translation, global scaling, Boolean fusion or hidden clipping.','appearanceFunctionContactRuntimeAccepted':False})
    controls=[]
    for f,tag in ((1,'a-neutral'),(13,'a-open')):
        s.frame_set(f);bpy.context.view_layer.update();controls +=[render.render(tag,'face'),render.render(tag,'body-face')]
    save('a-pilot-controls.json',controls);print('R76_COMPLETE_LOCAL_CROWN_SCULPT_AND_PILOTS_DONE',flush=True)
if __name__=='__main__':main()
