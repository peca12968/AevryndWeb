"""Check true topology correspondence and clean subdivision before sculpt rebase."""
from pathlib import Path
import bpy,importlib.util,numpy as np,time
sp=importlib.util.spec_from_file_location('repair51',Path(__file__).with_name('build-female-next-r0051-eye-wall.py'))
k=importlib.util.module_from_spec(sp);sp.loader.exec_module(k)
a=k.a;b=k.b;E=k.E

def topology(o):
    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh()
    loops=np.empty(len(m.loops),dtype='i4');m.loops.foreach_get('vertex_index',loops)
    starts=np.empty(len(m.polygons),dtype='i4');m.polygons.foreach_get('loop_start',starts)
    totals=np.empty(len(m.polygons),dtype='i4');m.polygons.foreach_get('loop_total',totals)
    ev.to_mesh_clear();return loops,starts,totals

def main():
    tick=time.time();bpy.ops.wm.open_mainfile(filepath=str(k.OUT));body=bpy.data.objects[b.BODY]
    oldTopology=topology(body);P,T=b.evaluated(body,True);mult=next(m for m in body.modifiers if m.type=='MULTIRES')
    mult.show_viewport=mult.show_render=False
    sub=body.modifiers.new('AFN51_SAME_CAGE_SUBDIVISION','SUBSURF');sub.levels=sub.render_levels=3;sub.subdivision_type='CATMULL_CLARK'
    bpy.context.view_layer.update();newTopology=topology(body);Q,U=b.evaluated(body,True)
    same=all(np.array_equal(x,y) for x,y in zip(oldTopology,newTopology)) and P.shape==Q.shape
    row={'candidate':str(k.OUT),'sha256':b.sha(k.OUT),'sameFullPolygonLoopTopology':same,
         'triangulationEqual':bool(np.array_equal(T,U)),
         'note':'Geometric triangle diagonal choices may differ. Vertex/quad correspondence is proved only by full ordered loop/start/count equality.'}
    if same:
        row['undisplacedSelf']=k.k.check(Q,U);full=a.selfcheck.tree(Q,U);optics={}
        for side in ('L','R'):
            for part in ('Sclera','Cornea','Iris','Pupil'):
                name=f'AFN30_{side}_{part}';V,W=b.evaluated(bpy.data.objects[name],True);tree=a.selfcheck.tree(V,W)
                optics[name]=a.actual_pairs(Q,U,V,W,full.overlap(tree))
        row['undisplacedFixedOptics']=optics
    row['seconds']=time.time()-tick;k.save('b-rebase-feasibility.json',row)
    print('R51_REBASE_PROBE',same,row.get('undisplacedSelf',{}).get('actualSelfPairs'),sum(r['actualSurfaceIntersectionPairs'] for r in row.get('undisplacedFixedOptics',{}).values()),flush=True)

if __name__=='__main__':main()
