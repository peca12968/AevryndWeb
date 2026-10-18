"""Actual affected surfaces in named static states; never a continuous proof."""
import bpy,json,importlib.util,time,sys
import numpy as np
from pathlib import Path
from mathutils.bvhtree import BVHTree
spec=importlib.util.spec_from_file_location('build',Path(__file__).with_name('build-female-next-r0020-pinned-blink.py'));b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
a,solid,E=b.a,b.solid,b.E
PREFIX='b' if '--b' in sys.argv else 'a'
if PREFIX=='b':b.DST=b.S/'aevrynd-female-next-r0020-b-visible-rim-blink-study.blend'

def main():
    report=json.loads((E/f'{PREFIX}-build-verification.json').read_text());assert a.sha(b.DST)==report['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(b.DST));rig=bpy.data.objects['AFN_R0005_Rig'];solid.stage.set_pose(rig,'neutral');body=bpy.data.objects['AFN_R0008_Body'];base=a.positions(body);changed=np.zeros(len(base),bool)
    for key in body.data.shape_keys.key_blocks[1:]:
        p=np.empty_like(base);key.data.foreach_get('co',p.ravel());changed|=np.any(p!=base,axis=1)
    attachments=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(('AFN10_','AFN11_'))];eyes=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('AFN6_')];rows=[]
    states=[('neutral',w,w) for w in (0.,.125,.25,.375,.5,.625,.75,.875,1.)]+[('neutral',1.,0.),('neutral',0.,1.),('neutral',.5,0.),('neutral',0.,.5)]+[(pose,1.,1.) for pose in ('gaze-left','gaze-right','turn-left','turn-right')]
    for pose,left,right in states:
        started=time.time();solid.stage.set_pose(rig,pose);a.set_blink(left,right);V,T,bodytree=solid.data(body);indices=np.array(T,np.int32);active=np.flatnonzero(changed[indices].any(axis=1));local=BVHTree.FromPolygons(V,indices[active].tolist(),all_triangles=True);overlap=local.overlap(bodytree);pairs=[(int(active[i]),j) for i,j in overlap if int(active[i])<j and set(T[int(active[i])]).isdisjoint(T[j])];activeSet=set(active.tolist());pairs.extend((j,int(active[i])) for i,j in overlap if j<int(active[i]) and j not in activeSet and set(T[int(active[i])]).isdisjoint(T[j]));pairs=sorted(set(pairs));optics={o.name:solid.data(o) for o in eyes};optical={name:len(bodytree.overlap(d[2])) for name,d in optics.items()};parts={o.name:solid.data(o) for o in attachments};attachmentRows={}
        for o in attachments:
            P,PT,tree=parts[o.name];selfPairs=[(i,j) for i,j in tree.overlap(tree) if i<j and set(PT[i]).isdisjoint(PT[j])];cross={n:len(tree.overlap(d[2])) for n,d in parts.items() if n>o.name};bodyPairs=tree.overlap(bodytree);eyePairs={name:len(tree.overlap(d[2])) for name,d in optics.items()};attachmentRows[o.name]={'bodyTriangleIntersectionPairs':len(bodyPairs),'bodyPairSamples':bodyPairs[:10],'selfNonAdjacentTrianglePairs':len(selfPairs),'selfPairSamples':selfPairs[:10],'otherAttachmentPairs':cross,'opticalSurfacePairs':eyePairs,'minimumSampledVertexBodyGapM':min(bodytree.find_nearest(p)[3] for p in P)}
        failures=len(pairs)+sum(optical.values())+sum(x['bodyTriangleIntersectionPairs']+x['selfNonAdjacentTrianglePairs']+sum(x['otherAttachmentPairs'].values())+sum(x['opticalSurfacePairs'].values()) for x in attachmentRows.values());rows.append({'pose':pose,'left':left,'right':right,'changedBodyTriangles':len(active),'changedBodyNonAdjacentSelfPairs':len(pairs),'bodySelfPairSamples':pairs[:20],'bodyOpticsPairs':optical,'attachments':attachmentRows,'surfaceFailurePairs':failures,'wallSeconds':time.time()-started});b.save(f'{PREFIX}-blink-sampled-surface-verification.json',{'asset':str(b.DST),'assetSha256':a.sha(b.DST),'status':'PASS_TESTED_SURFACE_STATES_ONLY' if all(x['surfaceFailurePairs']==0 for x in rows) else 'FAIL_OR_UNRESOLVED','samples':rows,'scope':'Complete affected body triangles vs all body; complete optical/lash/brow surfaces in named discrete states. No continuous or swept contact proof, no complete scalp hair or clothing collision check. Distances are sampled attachment vertices to body triangles, not global minimum or signed distance. Zero surface intersection alone does not prove closure.'});print(f'R0020_SAMPLE {pose} {left} {right} FAILURES {failures}',flush=True)
        # Fail the cheap synchronized feasibility test before expanding states.
        if failures and len(rows)<=5:break
    solid.stage.set_pose(rig,'neutral');a.set_blink(0.,0.)
if __name__=='__main__':main()
