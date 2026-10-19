"""One topology-aware posterior socket repair; neutral source, not a blink.

Keep native connectivity/UV/sculpt; redistribute only disk interior coordinates
with fixed boundary, then respect the actual posterior optical surface.
"""
from pathlib import Path
from collections import defaultdict
import bpy, importlib.util, numpy as np, time, json
from mathutils import Vector
sp=importlib.util.spec_from_file_location('eye51',Path(__file__).with_name('inspect-female-next-r0051-eye-source.py'))
k=importlib.util.module_from_spec(sp);sp.loader.exec_module(k)
a=k.a;b=k.b;f=k.f;E=k.E;SRC=k.SRC
OUT=b.S/'aevrynd-female-next-r0051-a-posterior-eye-wall.blend'

def save(n,x):k.save(n,x)

def main():
    tick=time.time();assert b.sha(SRC)=='49f76186981a7244444e37b950eab6acd24e34be15a65d855cee527422405c67'
    bpy.ops.wm.open_mainfile(filepath=str(SRC));before=f.state();body=bpy.data.objects[b.BODY]
    nativeSignature=b.mesh_signature(body.data);mult=next(m for m in body.modifiers if m.type=='MULTIRES')
    mult.levels=mult.render_levels=0;bpy.context.view_layer.update();P,T=b.evaluated(body,True)
    polys=[list(p.vertices) for p in body.data.polygons];centres=np.array([P[p].mean(0) for p in polys]);Q=P.copy();regions={}
    for side in ('L','R'):
        C=np.array(a.i.i.FITS[side]['centerM']);q=centres-C
        fs=np.flatnonzero((q[:,1]>.006)&(np.linalg.norm(q,axis=1)<.024))
        es=defaultdict(list);adj=defaultdict(set)
        for fi in fs:
            pp=polys[fi]
            for x,y in zip(pp,pp[1:]+pp[:1]):
                es[tuple(sorted((x,y)))].append(int(fi));adj[x].add(y);adj[y].add(x)
        boundary=[e for e,faces in es.items() if len(faces)==1];vs=sorted(adj);bvs=sorted(set(x for e in boundary for x in e));inside=sorted(set(vs)-set(bvs))
        degree=defaultdict(int)
        for x,y in boundary:degree[x]+=1;degree[y]+=1
        assert len(vs)-len(es)+len(fs)==1 and all(d==2 for d in degree.values()),'Posterior patch is not a simple disk'
        assert inside
        # Uniform positive native-edge weights; leave physical boundary exact.
        index={v:i for i,v in enumerate(inside)};L=np.zeros((len(inside),len(inside)));rhs=np.zeros((len(inside),3))
        for v,ii in index.items():
            L[ii,ii]=len(adj[v])
            for n in adj[v]:
                if n in index:L[ii,index[n]]-=1
                else:rhs[ii]+=P[n]
        Q[inside]=np.linalg.solve(L,rhs)
        ev=[];et=[];offset=0
        for part in ('Sclera','Cornea','Iris','Pupil'):
            vv,tt=b.evaluated(bpy.data.objects[f'AFN30_{side}_{part}'],True);ev.append(vv);et.append(tt+offset);offset+=len(vv)
        V,U=np.concatenate(ev),np.concatenate(et);tree=a.selfcheck.tree(V,U)
        # One supporting plane per whole quad, not vertex-only ray clearance.
        # X/Z disk coordinates stay fixed; solve only free Y lower bounds.
        supported=0;planes=[];free=set(inside);boundarySet=set(bvs)
        for fi in fs:
            face=polys[fi];fixed=[v for v in face if v in boundarySet]
            probes=[Q[face].mean(0),P[face].mean(0)]
            if fixed:probes+=[P[fixed].mean(0)]+[P[v] for v in fixed]
            options=[]
            for probe in probes:
                n=probe-C;n/=np.linalg.norm(n)
                if n[1]<.05:continue
                h=float((V@n).max()+.00008)
                slack=float((P[fixed]@n-h).min()) if fixed else 1.
                options.append((slack,n,h))
            assert options,'No posterior support direction'
            slack,n,h=max(options,key=lambda row:row[0])
            assert slack>=-1e-10,('No separating plane at fixed disk boundary',side,int(fi),slack)
            for vi in face:
                if vi in free:
                    Q[vi,1]=max(Q[vi,1],(h-n[0]*Q[vi,0]-n[2]*Q[vi,2])/n[1]);supported+=1
            planes.append({'polygon':int(fi),'normal':n.tolist(),'offset':h,'fixedBoundaryMinimumSlackM':slack if fixed else None})
        for row in planes:
            assert np.min(Q[polys[row['polygon']]]@row['normal']-row['offset'])>=-1e-9
        ids=np.array(vs);regions[side]={'nativePolygons':fs.tolist(),'vertices':vs,'fixedBoundary':bvs,'interior':inside,
            'euler':1,'boundaryEdges':len(boundary),'posteriorOpticalSupportedVertices':supported,
            'wholeQuadSupportStandOffM':.00008,'wholeQuadPlanes':planes,'maximumNativeMovementM':float(np.linalg.norm(Q[ids]-P[ids],axis=1).max()),
            'sourcePatchBoundsM':[P[ids].min(0).tolist(),P[ids].max(0).tolist()]}
    moved=np.linalg.norm(Q-P,axis=1)>1e-10
    assert not np.any(moved & (P[:,1]<-.109)),'Unexpected external rim movement'
    inv=body.matrix_world.inverted()
    for vi in np.flatnonzero(moved):body.data.vertices[int(vi)].co=inv@Vector(Q[vi])
    body.data.update();bpy.context.view_layer.update();coarse,ct=b.evaluated(body,True);coarseSelf=k.check(coarse,ct)
    optics={};baselineOptics={};affectedOptics={}
    bodyTree=a.selfcheck.tree(coarse,ct);sourceTree=a.selfcheck.tree(P,T)
    for side in ('L','R'):
        for part in ('Sclera','Cornea','Iris','Pupil'):
            name=f'AFN30_{side}_{part}';V,U=b.evaluated(bpy.data.objects[name],True);tree=a.selfcheck.tree(V,U)
            optics[name]=a.actual_pairs(coarse,ct,V,U,bodyTree.overlap(tree))
            baselineOptics[name]=a.actual_pairs(P,T,V,U,sourceTree.overlap(tree))
            affectedPairs=[(x,y) for x,y in bodyTree.overlap(tree) if np.any(moved[ct[x]])]
            affectedOptics[name]=a.actual_pairs(coarse,ct,V,U,affectedPairs)
    report={'source':str(SRC),'sourceSha256':b.sha(SRC),'method':'Fixed-boundary native posterior disk fairing with positive graph weights; separating planes for whole quads against all actual optical vertices. Same topology/UV, no hidden geometry or tolerance change.',
            'regions':regions,'nativeChangedVertices':np.flatnonzero(moved).tolist(),
            'coarseSelf':coarseSelf,'coarseFixedOptics':optics,'coarseSourceFixedOptics':baselineOptics,
            'coarseAffectedFixedOptics':affectedOptics,'status':'COARSE_CHECKED',
            'reference':'https://doc.cgal.org/latest/Surface_mesh_parameterization/index.html',
            'referenceLimit':'Convex-boundary planar injectivity does not certify our physical boundary, optical support modification or sculpted 3D mesh; actual self/optics tests decide.'}
    save('a-coarse-feasibility.json',report)
    if coarseSelf['actualSelfPairs'] or any(r['actualSurfaceIntersectionPairs'] for r in affectedOptics.values()):
        report['status']='REJECT_COARSE_STRUCTURAL_CONSTRUCTION';save('a-coarse-feasibility.json',report)
        print('R51_COARSE_REJECT',coarseSelf['actualSelfPairs'],sum(r['actualSurfaceIntersectionPairs'] for r in affectedOptics.values()),'baseline',sum(r['actualSurfaceIntersectionPairs'] for r in baselineOptics.values()),flush=True);return
    mult.levels=mult.render_levels=mult.sculpt_levels=3;bpy.context.view_layer.update()
    after=f.state();assert all(after[key]==before[key] for key in ('materials','skinFields','curves','stage'))
    assert all(after['meshes'][n]==row for n,row in before['meshes'].items() if n!=b.BODY)
    assert b.mesh_signature(body.data)['uv']==nativeSignature['uv']
    bpy.context.scene['AFN51_status']='POSTERIOR_WALL_REPAIR_CANDIDATE_FULL_SCULPT_UNVERIFIED'
    b.camera('face');bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    report.update(status='SAVED_FULL_CHARACTER_CANDIDATE_NOT_CONTACT_ACCEPTED',output=str(OUT),outputSha256=b.sha(OUT),seconds=time.time()-tick)
    save('a-build-summary.json',report)
    f.E=E;f.render('a-after',('face','oblique','profile'));a.i.i.E=E;a.i.i.closeup('a-after');a.i.ch.review.extras('a-after',E)
    print('R51_CANDIDATE_READY',int(moved.sum()),time.time()-tick,flush=True)

if __name__=='__main__':main()
