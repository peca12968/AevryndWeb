"""Explicit native boundary-to-posterior lining; no automatic cavity subdivision."""
from pathlib import Path
import bpy,numpy as np,json,datetime,time,importlib.util,collections
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0146-connected-palpebral-lining';SRC=R/'engine/assets/characters/female-next/source/r0144-source/aevrynd-female-next-r0144-a-current-skin-blink.blend'
sp=importlib.util.spec_from_file_location('r146patchbase',Path(__file__).with_name('build-female-next-r0144-current-skin-blink.py'));h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h);a=h.a
def save(n,x):h.save.__globals__['E']=E;h.save(n,x)
def main():
    tick=time.time();assert not (E/'posterior-patch-geometry.npz').exists();bpy.ops.wm.open_mainfile(filepath=str(SRC));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update();skin=bpy.data.objects[h.h.SKIN];A=np.array(skin.matrix_world);raw=np.empty((len(skin.data.vertices),3),dtype='f4');skin.data.vertices.foreach_get('co',raw.ravel());W=(np.c_[raw,np.ones(len(raw))]@A.T)[:,:3];polys=[tuple(p.vertices) for p in skin.data.polygons];angles={s:np.array([x.value for x in skin.data.attributes['AFN144_Angle_'+s].data]) for s in ['L','R']};old=json.loads((E.parent/'r0144-current-skin-blink/current-skin-blink-construction.json').read_text('utf-8'));output={};reports={}
    for side in ['L','R']:
        C=np.array(old['actualNativeDomains'][side]['actualOpticalCentreWorld']);V,F=a.geometry(bpy.data.objects['AFN138_'+side+'_ANATOMICAL_SOCKET_CONSTRUCTION']);tree=BVHTree.FromPolygons([Vector(p) for p in V],F.tolist(),all_triangles=True);near=np.linalg.norm(W-C,axis=1)<.025;on=np.zeros(len(W),bool)
        for i in np.flatnonzero(near):on[i]=tree.find_nearest(Vector(W[i]))[3]<3e-6
        selected=[]
        for i,p in enumerate(polys):
            if all(on[j] for j in p) and tree.find_nearest(Vector(W[list(p)].mean(0)))[3]<3e-6:selected.append(i)
        counts=collections.Counter();oriented={}
        for i in selected:
            p=polys[i]
            for x,y in zip(p,p[1:]+p[:1]):edge=tuple(sorted((x,y)));counts[edge]+=1;oriented[edge]=(x,y)
        boundary=[edge for edge,count in counts.items() if count==1];graph=collections.defaultdict(list)
        for x,y in boundary:graph[x].append(y);graph[y].append(x)
        degree={k:len(v) for k,v in graph.items()};report={'side':side,'originalInnerFaceCount':len(selected),'actualBoundaryEdges':len(boundary),'boundaryVertexDegrees':dict(collections.Counter(degree.values())),'constructionMembershipDistanceM':3e-6,'membershipToleranceNotContactAcceptance':True};reports[side]=report;save('native-posterior-boundary-authoring-observation.json',reports)
        assert selected and boundary and all(d==2 for d in degree.values()),('Need explicit closed source lining boundary',report)
        loops=[];unseen=set(graph)
        while unseen:
            start=min(unseen);loop=[start];previous=None;current=start
            while True:
                choices=[j for j in graph[current] if j!=previous];nxt=choices[0]
                if nxt==start:break
                assert nxt not in loop;loop.append(nxt);previous,current=current,nxt
            unseen.difference_update(loop);loops.append(loop)
        report['boundaryLoopSizes']=[len(x) for x in loops];save('native-posterior-boundary-authoring-observation.json',reports);assert len(loops)==1,('Multiple lining boundaries need explicit anatomical pairing',report)
        loop=loops[0];P=W[loop];rel=P-C;u=rel/np.linalg.norm(rel,axis=1)[:,None];back=np.array([0.,1.,0.]);theta=np.arccos(np.clip(u@back,-1,1));tangent=u-(u@back)[:,None]*back;tangent/=np.linalg.norm(tangent,axis=1)[:,None];assert (theta>1).all() and (theta<np.pi-.01).all()
        # The actual source rim is the shared first ring. Fourteen explicit rows
        # span posterior lid support/fold and posterior orbital lining to one pole.
        rows=14;points=[P];rowAngle=[angles[side][loop]];sourceParameters=[np.c_[np.arange(len(loop)),np.zeros(len(loop))]]
        for k in range(1,rows+1):
            t=k/(rows+1);direction=np.cos(theta*(1-t))[:,None]*back+np.sin(theta*(1-t))[:,None]*tangent;hit=[]
            for q in direction:
                p=tree.ray_cast(Vector(C),Vector(q),.1)[0];assert p is not None;hit.append(tuple(p))
            points.append(np.asarray(hit));distance=t*theta*np.linalg.norm(rel,axis=1);band=np.where(angles[side][loop]>=0,.010,.005);fade=np.clip(1-distance/band,0,1);fade=fade*fade*(3-2*fade);rowAngle.append(angles[side][loop]*fade);sourceParameters.append(np.c_[np.arange(len(loop)),np.full(len(loop),t)])
        pole=tree.ray_cast(Vector(C),Vector(back),.1)[0];assert pole is not None;Pnew=np.concatenate(points+[np.array([tuple(pole)])]);angle=np.r_[np.concatenate(rowAngle),0.];parameters=np.concatenate(sourceParameters+[np.array([[0.,1.]])]);N=len(loop);faces=[]
        for k in range(rows):
            for i in range(N):
                j=(i+1)%N;a0=k*N+i;b0=k*N+j;c0=(k+1)*N+j;d0=(k+1)*N+i;faces.extend([(a0,b0,c0),(a0,c0,d0)])
        for i in range(N):faces.append((rows*N+i,rows*N+(i+1)%N,len(Pnew)-1))
        faces=np.asarray(faces,dtype='i4');tri=Pnew[faces];normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);length=np.linalg.norm(normal,axis=1);orientation=np.einsum('ij,ij->i',normal,tri.mean(1)-C);faces[orientation>0]=faces[orientation>0][:,[0,2,1]]
        # Validate the actual stored float32 world mesh before any complete save.
        stored=Pnew.astype('f4').astype('f8');area=np.linalg.norm(np.cross(stored[faces[:,1]]-stored[faces[:,0]],stored[faces[:,2]]-stored[faces[:,0]]),axis=1);report.update(explicitPosteriorRows=rows,newPoints=len(Pnew),newTriangles=len(faces),minimumStoredTwiceAreaM2=float(area.min()),zeroAreaTriangles=int((area==0).sum()),originalBoundaryPositionsExact=True)
        save('native-posterior-boundary-authoring-observation.json',reports);assert (area>0).all(),('Explicit lining has a stored degenerate face',report)
        if not (E/'direct-palpebral-patch-authoring-start.json').exists():save('direct-palpebral-patch-authoring-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'originalStartedUTC':'2026-10-22T02:06:15+00:00','action':'Author explicit positive-area posterior lining from complete actual source boundary to posterior pole; connected boundary lineage retained, no automatic subdivision or bad-face removal.'})
        mesh=bpy.data.meshes.new('AFN146_'+side+'_AUTHORED_CONNECTED_POSTERIOR_PATCH');mesh.from_pydata(Pnew.tolist(),[],faces.tolist());mesh.update();ob=bpy.data.objects.new(mesh.name,mesh);scene.collection.objects.link(ob);ob.hide_render=True
        output.update({side+'-boundaryOriginalIds':np.array(loop,dtype='i4'),side+'-replacedOriginalPolygons':np.array(selected,dtype='i4'),side+'-world':Pnew,side+'-triangles':faces,side+'-angles':angle,side+'-parameters':parameters})
    np.savez_compressed(E/'posterior-patch-geometry.npz',**output);save('posterior-patch-authoring.json',{'source':str(SRC),'actualSourceSkin':skin.name,'sides':reports,'scope':'Authored component topology only, not a complete woman or improvement. Must reconnect actual Skin, author visible boundary/lining and native motion, judge full head/body, independently reopen/restore and test actual geometry.','originalAllFacesRemainInImmutableSource':True,'noCompleteSourceSaved':True,'seconds':time.time()-tick});print('R146_EXPLICIT_POSTERIOR_LINING_PATCH_AUTHORED',reports,time.time()-tick,flush=True)
if __name__=='__main__':main()
