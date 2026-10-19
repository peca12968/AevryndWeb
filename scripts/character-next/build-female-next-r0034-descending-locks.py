"""C: artist edit of each cage's upper fall, following complete-head evidence.

B's first free controls stay at nearly scalp-exit height, leaving lateral
bridges. Re-author those first two controls per lock to descend immediately;
preserve independent lower curves/ends and root attachment. Final candidate.
"""
import bpy,importlib.util,json
from pathlib import Path
import numpy as np
spec=importlib.util.spec_from_file_location('b34',Path(__file__).with_name('build-female-next-r0034-cage-locks.py'));b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b);a=b.a;g=a.g
UPPER=[
[(-.085,-.120,1.490),(-.099,-.120,1.455)],
[(-.075,-.123,1.515),(-.095,-.127,1.478)],
[(-.085,-.095,1.510),(-.101,-.092,1.472)],
[(-.096,-.052,1.470),(-.107,-.052,1.438)],
[(-.096,-.040,1.505),(-.111,-.033,1.465)],
[(-.096,.001,1.470),(-.109,.008,1.438)],
[(-.098,.008,1.505),(-.108,.018,1.465)],
[(-.091,.044,1.460),(-.103,.062,1.425)],
[(-.092,.053,1.505),(-.105,.072,1.465)],
[(-.059,.076,1.450),(-.070,.090,1.418)],
[(-.060,.078,1.505),(-.074,.099,1.460)],
[(-.024,.078,1.480),(-.037,.096,1.442)],
[(.074,-.125,1.520),(.094,-.139,1.490)],
[(.078,-.117,1.490),(.091,-.127,1.458)],
[(.089,-.073,1.510),(.105,-.077,1.475)],
[(.094,-.052,1.470),(.103,-.061,1.438)],
[(.099,-.016,1.510),(.112,-.015,1.470)],
[(.096,.001,1.470),(.109,.010,1.443)],
[(.094,.047,1.510),(.107,.067,1.475)],
[(.089,.043,1.460),(.104,.061,1.428)],
[(.062,.074,1.510),(.078,.096,1.470)],
[(.057,.074,1.450),(.073,.090,1.423)],
[(.020,.078,1.480),(.036,.099,1.442)],
[(.081,-.095,1.525),(.104,-.103,1.492)],
]

def configure():
    b.configure()
    a.MASTERS=[tuple(list(m[:6])+[UPPER[i]+m[6][2:]]+list(m[7:])) for i,m in enumerate(a.MASTERS)]
    original_render=g.q.render
    def audited_render(label):
        primitive=bpy.context.scene.render.hair_type;subdiv=bpy.context.scene.render.hair_subdiv
        original_render(label)
        p=a.E/(label+'-renders.json');report=json.loads(p.read_text())
        for row in report['rows']:row['curvePrimitive']=primitive;row['hairSubdivision']=subdiv
        report['curveAudit']='Render primitive explicitly captured; STRAND ignores diameter and cannot establish physical-width display.';p.write_text(json.dumps(report,indent=2)+'\n')
    g.q.render=audited_render

def main():
    configure();a.OUT=a.S/'aevrynd-female-next-r0034-c-descending-cage-locks.blend'
    original_save=a.save
    a.save=lambda n,x:original_save(('c-'+n[2:]) if n.startswith('a-') else ('c-'+n if n in ('round-contract.json','baseline-state.json') else n),x)
    original_render=g.q.render;g.q.render=lambda label:original_render('c-guides' if label=='a-guides' else label)
    original_legacy=a.legacy_paths
    a.legacy_paths=lambda name,*args,**kwargs:original_legacy(name.replace('AFN34_A_','AFN34_C_'),*args,**kwargs)
    original_np_save=np.savez_compressed
    def cache(path,*args,**kwargs):
        path=Path(path)
        if path.name=='aevrynd-female-next-r0034-a-master-guides.npz':path=path.with_name('aevrynd-female-next-r0034-c-master-guides.npz')
        return original_np_save(path,*args,**kwargs)
    np.savez_compressed=cache;a.main()
    p=a.E/'c-round-contract.json';contract=json.loads(p.read_text());contract.update({'candidate':'C / final bounded edit','candidateCount':3,'reason':'A/B full-head pilots show first free controls at scalp-exit height, causing lateral shelves. No child expansion from those shapes.','methodDifference':'Keep B independent cubic cages, re-author the first two free controls of every lock to descend immediately; preserve root bindings and independent lower3Dcurves/ends. This is an artist cage edit, not body pushing or density/mat/tolerance change.','camera':'Same85mm complete-hair cameras as before-wide; source head/skin/optics/light/exposure unchanged.'});p.write_text(json.dumps(contract,indent=2)+'\n')

if __name__=='__main__':main()
