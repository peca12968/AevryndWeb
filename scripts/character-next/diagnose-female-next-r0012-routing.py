"""Classify unresolved strand points with closed-solid parity, not normal signs."""
import bpy,json,numpy as np,importlib.util
from pathlib import Path
from mathutils import Vector
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0012-layered-hair';S=R/'engine/assets/characters/female-next/source'
spec=importlib.util.spec_from_file_location('cert',Path(__file__).with_name('verify-female-next-r0012-hair-segments.py'));cert=importlib.util.module_from_spec(spec);spec.loader.exec_module(cert)
bpy.ops.wm.open_mainfile(filepath=str(S/'aevrynd-female-next-r0012-c-corrected-hair-study.blend'));body=bpy.data.objects['AFN_R0008_Body'];V,T,tree=cert.solid.data(body);tri=np.asarray([tuple(v) for v in V],dtype=np.float64)[np.asarray(T,dtype=np.int32)];routes=json.loads((E/'c-segment-routing.json').read_text());rows=[]
for item in routes['unresolved'][:20]:
    o=bpy.data.objects[item['object']];curve=o.data.splines[item['curve']];inside=[]
    for j,v in enumerate(curve.points):
        p=o.matrix_world@Vector(v.co[:3]);kind=cert.solid.classify(tree,tri,p)
        if kind!='outside':
            h,n,fi,d=tree.find_nearest(p);inside.append({'point':j,'classification':kind,'unsignedDistanceM':d,'nearestNormalDotM':(p-h).dot(n),'world':list(p)})
    rows.append({'object':o.name,'curve':item['curve'],'points':len(curve.points),'nonOutsidePoints':inside})
(E/'routing-containment-diagnosis.json').write_text(json.dumps({'scope':'First 20 unresolved curves only; full-solid per-point diagnostic.','rows':rows},indent=2)+'\n');print(json.dumps({'curves':len(rows),'nonOutsidePoints':sum(len(x['nonOutsidePoints']) for x in rows),'positiveNormalInside':sum(p['classification']=='inside' and p['nearestNormalDotM']>=0 for x in rows for p in x['nonOutsidePoints'])}))
