"""Bounded source hierarchy check before structural eye-wall repair."""
import bpy, importlib.util, json, time, gc
from pathlib import Path
import numpy as np

sp=importlib.util.spec_from_file_location('r50base',Path(__file__).with_name('verify-female-next-r0050-neutral-rest.py'))
a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a)
b=a.b;f=a.f;E=b.R/'Evidence/character-female-next/r0051-eye-wall';E.mkdir(parents=True,exist_ok=True)
SRC=a.a.SRC

def save(name,x):
    (E/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def roi(P):
    return (abs(abs(P[:,0])-.0313)<.019)&(P[:,1]>-.135)&(P[:,1]<-.087)&(P[:,2]>1.443)&(P[:,2]<1.479)

def check(P,T):
    full=a.selfcheck.tree(P,T)
    broad,pairs=a.selfcheck.changed_self(P,T,roi(P),full)
    actual=[]
    for x,y in sorted(pairs):
        hits=a.exact.intersections(P[T[x]],P[T[y]])
        if hits:
            actual.append((x,y))
    ids=np.unique(T[np.array(actual,dtype='i4')].ravel()) if actual else np.array([],dtype='i4')
    result={'regionTriangles':broad['affectedTriangleCount'],'broadPairs':len(pairs),
            'actualSelfPairs':len(actual),'allActualPairs':actual,
            'intersectingVertexIds':ids.tolist(),
            'badBoundsM':[P[ids].min(0).tolist(),P[ids].max(0).tolist()] if len(ids) else None,
            'witnesses':[{'triangles':[x,y],'vertices':P[T[[x,y]]].tolist()} for x,y in actual[:5]],
            'scope':'Both complete ocular regions against full body; exact nonadjacent triangle intersections; neutral pose only.'}
    del full;gc.collect()
    return result

def main():
    tick=time.time();assert b.sha(SRC)=='49f76186981a7244444e37b950eab6acd24e34be15a65d855cee527422405c67'
    bpy.ops.wm.open_mainfile(filepath=str(SRC));body=bpy.data.objects[b.BODY]
    mult=next(m for m in body.modifiers if m.type=='MULTIRES')
    report={'source':str(SRC),'sourceSha256':b.sha(SRC),
            'modifiers':[{'name':m.name,'type':m.type} for m in body.modifiers], 'levels':{}}
    original=(mult.levels,mult.render_levels)
    for level in (0,1,2,3):
        mult.levels=mult.render_levels=level;bpy.context.view_layer.update();P,T=b.evaluated(body,True)
        row=check(P,T);row.update(vertices=len(P),triangles=len(T));report['levels'][str(level)]=row
        if level==0:
            native=P.copy();nativeTri=T.copy()
        if level==3:np.savez_compressed(E/'local-source-cache.npz',source=P,triangles=T,native=native,nativeTriangles=nativeTri)
        save('source-hierarchy.json',report);print('R51_SOURCE_LEVEL',level,row['actualSelfPairs'],row['badBoundsM'],flush=True)
    mult.levels,mult.render_levels=original
    # One independent undisplaced surface from exactly the same native cage.
    mult.show_viewport=mult.show_render=False
    sub=body.modifiers.new('AFN51_DIAGNOSTIC_UNDISPLACED','SUBSURF');sub.levels=sub.render_levels=3
    sub.subdivision_type='CATMULL_CLARK';bpy.context.view_layer.update();Q,U=b.evaluated(body,True)
    cache=np.load(E/'local-source-cache.npz');P,T=cache['source'],cache['triangles']
    row=check(Q,U);report['undisplacedSameCageLevel3']=row
    report['undisplacedTrianglesEqualSource']=bool(np.array_equal(T,U))
    report['undisplacedComparisonLimit']='Independent self test only; different evaluated triangulation is not a point correspondence.'
    body.modifiers.remove(sub);mult.show_viewport=mult.show_render=True;bpy.context.view_layer.update()
    old=b.S/'aevrynd-female-next-r0028-a-cc0-female-foundation.blend'
    assert b.sha(old)=='68aa031b5ef4ad3353129eeb9ac881ef7237ed840928e05bd0c4a6b6e32cba6c'
    bpy.ops.wm.open_mainfile(filepath=str(old));oldBody=bpy.data.objects[b.BODY]
    oldMult=next(m for m in oldBody.modifiers if m.type=='MULTIRES');oldMult.levels=0;oldMult.render_levels=0
    bpy.context.view_layer.update();oldP,oldT=b.evaluated(oldBody,True)
    oldRow=check(oldP,oldT);report['originalR28Native']=oldRow
    report['originalR28NativeTrianglesEqualSource']=bool(np.array_equal(oldT,nativeTri))
    report['originalR28Source']=str(old);report['originalR28Sha256']=b.sha(old)
    # Index lineage is validated separately from geometry-dependent triangle diagonals.
    np.savez_compressed(E/'local-source-cache.npz',source=P,triangles=T,native=native,nativeTriangles=nativeTri,oldNative=oldP,oldNativeTriangles=oldT)
    report['seconds']=time.time()-tick;report['status']='DIAGNOSED_NOT_REPAIRED'
    save('source-hierarchy.json',report);print('R51_UNDISPLACED',row['actualSelfPairs'],time.time()-tick,flush=True)

if __name__=='__main__':main()
