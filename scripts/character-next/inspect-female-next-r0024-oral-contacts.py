"""Bounded provenance check: inherited contacts versus adapter-introduced ones."""
import bpy,importlib.util,json
from pathlib import Path
import numpy as np
from mathutils.bvhtree import BVHTree
spec=importlib.util.spec_from_file_location('b24',Path(__file__).with_name('build-female-next-r0024-oral-layers.py'));b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
def analysis(P,F,components):
    owner={i:ci for ci,g in enumerate(components) for i in g}
    # Use Blender's same explicit loop triangulation for original/fitted data.
    m=bpy.data.meshes.new('AFN24_CONTACT_PROVENANCE_TEMP');m.from_pydata(P.tolist(),[],F);m.update();m.calc_loop_triangles();T=[tuple(t.vertices) for t in m.loop_triangles]
    tree=BVHTree.FromPolygons(P.tolist(),T,all_triangles=True);pairs=[(i,j) for i,j in tree.overlap(tree) if i<j and set(T[i]).isdisjoint(T[j])]
    result={'triangles':len(T),'nonAdjacentPairs':len(pairs),'withinSameComponent':0,'betweenDifferentTeeth':0,'gingivalToTooth':0,'componentPairs':{}}
    for i,j in pairs:
        a,c=owner[T[i][0]],owner[T[j][0]]
        label=','.join(map(str,sorted((a,c))));result['componentPairs'][label]=result['componentPairs'].get(label,0)+1
        if a==c:result['withinSameComponent']+=1
        elif a and c:result['betweenDifferentTeeth']+=1
        else:result['gingivalToTooth']+=1
    bpy.data.meshes.remove(m);return result
def main():
    folder=b.S/'oral/makehuman-system-cc0/teeth/teeth_base';V,uv,F,FUV=b.proxy.obj(folder/'teeth_base.obj');groups=b.proxy.components(len(V),F)
    cache=np.load(b.S/'aevrynd-female-next-r0024-oral-fit-data.npz');mapping=b.proxy.proxy(folder/'teeth_base.mhclo');fitted,scales=b.proxy.fit(mapping,b.proxy.to_mh(cache['nativeNeutral']));Q=b.proxy.to_blender(fitted)
    original=analysis(b.proxy.to_blender(V),F,groups);adapted=analysis(Q,F,groups)
    # Translate the body/oral hits to named world-space regions, no exclusion.
    static=json.loads((b.E/'b-static-verification.json').read_text(encoding='utf8'))
    hits=static['results'][1]['parts']['AFN24_ContinuousGingivalLining']['bodyPairSamples']
    b.save('contact-provenance.json',{'originalCC0Asset':original,'adaptedNeutralAsset':adapted,'adaptationScales':scales.tolist(),'openGingivalBodyExamples':hits,'decision':'Original/fitted differences guide the next architecture. Neither source provenance nor anatomical naming automatically makes intersections acceptable.','scope':'Same Blender triangulation/BVH predicate on raw CC0 original and actual fitted neutral mesh. No continuous motion proof.'})
    print('R0024_PROVENANCE',json.dumps({k:{a:c for a,c in v.items() if a!='componentPairs'} for k,v in (('original',original),('adapted',adapted))}),flush=True)
if __name__=='__main__':main()
