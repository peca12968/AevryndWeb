"""Scoped complete surfaces at blink samples; no continuum claim from samples."""
import bpy,json,importlib.util,time
import numpy as np
from pathlib import Path
from mathutils.bvhtree import BVHTree
spec=importlib.util.spec_from_file_location('build',Path(__file__).with_name('build-female-next-r0019-native-blink.py'));build=importlib.util.module_from_spec(spec);spec.loader.exec_module(build)
R,S,E,SRC,DST,solid=build.R,build.S,build.E,build.SRC,build.DST,build.solid
def main():
    prefix=build.VARIANT;report=json.loads((E/(prefix+'-build-verification.json')).read_text());assert build.sha(DST)==report['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(DST));solid.stage.set_pose(bpy.data.objects['AFN_R0005_Rig'],'neutral');body=bpy.data.objects['AFN_R0008_Body'];base=build.positions(body);changed=np.zeros(len(base),bool)
    for key in body.data.shape_keys.key_blocks[1:]:
        p=np.empty_like(base);key.data.foreach_get('co',p.ravel());changed|=np.any(p!=base,axis=1)
    attachments=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(('AFN10_','AFN11_'))];eyes=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('AFN6_')];optics={o.name:solid.data(o) for o in eyes};rows=[]
    for weight in (0.,.25,.5,.75,1.):
        started=time.time();build.set_blink(weight,weight);V,T,bodytree=solid.data(body);indices=np.array(T,np.int32);active=np.flatnonzero(changed[indices].any(axis=1));activeT=indices[active];local=BVHTree.FromPolygons(V,activeT.tolist(),all_triangles=True);pairs=[(int(active[a]),b) for a,b in local.overlap(bodytree) if int(active[a])<b and set(T[int(active[a])]).isdisjoint(T[b])]
        # A changed-vs-unchanged pair must not disappear due to index ordering.
        activeSet=set(active.tolist());pairs.extend((b,int(active[a])) for a,b in local.overlap(bodytree) if b<int(active[a]) and b not in activeSet and set(T[int(active[a])]).isdisjoint(T[b]));pairs=sorted(set(pairs))
        optical={name:len(bodytree.overlap(d[2])) for name,d in optics.items()};parts={o.name:solid.data(o) for o in attachments};attachmentRows={}
        for o in attachments:
            P,PT,tree=parts[o.name];selfPairs=[(a,b) for a,b in tree.overlap(tree) if a<b and set(PT[a]).isdisjoint(PT[b])];cross={n:len(tree.overlap(d[2])) for n,d in parts.items() if n>o.name};bodyPairs=tree.overlap(bodytree);eyePairs={name:len(tree.overlap(d[2])) for name,d in optics.items()}
            attachmentRows[o.name]={'bodyTriangleIntersectionPairs':len(bodyPairs),'bodyPairSamples':bodyPairs[:10],'selfNonAdjacentTrianglePairs':len(selfPairs),'selfPairSamples':selfPairs[:10],'otherAttachmentsPairs':cross,'opticalSurfacePairs':eyePairs,'minimumSampledVertexBodyGapM':min(bodytree.find_nearest(p)[3] for p in P)}
        failures=len(pairs)+sum(optical.values())+sum(x['bodyTriangleIntersectionPairs']+x['selfNonAdjacentTrianglePairs']+sum(x['otherAttachmentsPairs'].values())+sum(x['opticalSurfacePairs'].values()) for x in attachmentRows.values())
        rows.append({'weight':weight,'changedBodyTriangles':len(active),'changedBodyNonAdjacentSelfPairs':len(pairs),'bodySelfPairSamples':pairs[:20],'bodyOpticsPairs':optical,'attachments':attachmentRows,'surfaceFailurePairs':failures,'wallSeconds':time.time()-started});build.save(prefix+'-blink-sampled-surface-verification.json',{'asset':str(DST),'assetSha256':build.sha(DST),'status':'PASS_TESTED_BLINK_SAMPLES_ONLY' if all(x['surfaceFailurePairs']==0 for x in rows) else 'FAIL_OR_UNRESOLVED','samples':rows,'scope':'Complete affected body triangles vs all body triangles; full eye/attachment surfaces at five synchronized key values. No continuous proof, no independent asynchronous eye combination or full scalp-hair collision check. Distances are sampled attachment vertices to body triangles only, not global surface distances.'});print('R0019_SAMPLE '+str(weight)+' FAILURES '+str(failures),flush=True)
    build.set_blink(0.,0.);print('R0019_SAMPLED_SURFACES_DONE',flush=True)
if __name__=='__main__':main()
