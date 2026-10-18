"""Reopen and check actual oral/body surfaces; no exclusion of failed regions."""
import bpy, importlib.util, json, time
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
spec=importlib.util.spec_from_file_location('oral24',Path(__file__).with_name('build-female-next-r0024-oral-layers.py'))
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)

def weight(value):
    master=bpy.data.objects['AFN24_MouthControl'];master['open']=float(value)
    master.update_tag(refresh={'OBJECT'});bpy.context.scene.frame_set(bpy.context.scene.frame_current+1);bpy.context.view_layer.update()

def main():
    report=json.loads((b.E/'b-build-verification.json').read_text(encoding='utf8'))
    path=Path(report['output']);assert b.sha(path)==report['outputSha256']
    bpy.ops.wm.open_mainfile(filepath=str(path));rig=bpy.data.objects['AFN_R0005_Rig'];b.solid.stage.set_pose(rig,'neutral')
    body=bpy.data.objects['AFN_R0008_Body'];parts=[bpy.data.objects[n] for n in ('AFN24_UpperTeeth','AFN24_LowerTeeth','AFN24_ContinuousGingivalLining','AFN24_Tongue')]
    cache=np.load(b.S/'aevrynd-female-next-r0024-oral-fit-data.npz');delta=cache['bodyDeltaOpen']
    changed=np.linalg.norm(delta,axis=1)>1.e-7;results=[]
    for w in (0.,.2):
        start=time.time();weight(w);V,T,tree=b.solid.data(body);P=np.array(V,np.float64);tri=P[np.array(T)]
        evaluatorError=float(np.linalg.norm(P-(cache['bodyNeutral']+delta*w),axis=1).max());assert evaluatorError<5.e-7
        snapshots={o.name:b.solid.data(o) for o in parts};rows={}
        for o in parts:
            Q,F,own=snapshots[o.name];q=np.array(Q,np.float64);hits=tree.overlap(own)
            pairs=[(i,j) for i,j in own.overlap(own) if i<j and set(F[i]).isdisjoint(F[j])]
            original_ids=o['aevrynd_original_vertex_indices']
            # Report every actual crossing. Gingival joins may be anatomical but
            # are not silently excluded from the raw results.
            rows[o.name]={'vertices':len(Q),'triangles':len(F),'bodyTrianglePairs':len(hits),'bodyPairSamples':[{'bodyTriangle':int(i),'oralTriangle':int(j),'bodyCentreM':tri[i].mean(0).tolist(),'oralCentreM':q[list(F[j])].mean(0).tolist()} for i,j in hits[:12]],'bodyVertexSampleMinimumDistanceM':min(float(tree.find_nearest(v)[3]) for v in Q),'nonAdjacentSelfPairs':len(pairs),'selfPairSamples':pairs[:12], 'boundsM':[q.min(0).tolist(),q.max(0).tolist()]}
            if o.name.endswith('Teeth'):
                groups=b.proxy.components(len(Q),F)
                states=[b.solid.classify(tree,tri,Vector(q[g].mean(0))) for g in groups]
                neutral=cache[o.name+'_neutral'];expectedD=np.linalg.norm(neutral[:,None,:]-neutral[None,:,:],axis=2)
                actualD=np.linalg.norm(q[:,None,:]-q[None,:,:],axis=2)
                rows[o.name]['rigidPairwiseDistanceMaximumErrorM']=float(abs(expectedD-actualD).max())
                rows[o.name]['toothCentroidBodyClassification']={s:states.count(s) for s in set(states)}
        cross=[]
        for i,o in enumerate(parts):
            for p in parts[i+1:]:
                a=snapshots[o.name];c=snapshots[p.name];pairs=a[2].overlap(c[2])
                cross.append({'pair':[o.name,p.name],'trianglePairs':len(pairs),'samples':pairs[:12],'anatomicalJoin':'Tooth root/gingival embedding needs provenance comparison; raw intersections remain reported.' if 'Gingival' in o.name+p.name and 'Teeth' in o.name+p.name else None})
        active=np.flatnonzero(changed[np.array(T)].any(axis=1));local=BVHTree.FromPolygons(V,[T[i] for i in active],all_triangles=True)
        self_pairs=sorted({tuple(sorted((int(active[i]),j))) for i,j in local.overlap(tree) if int(active[i])!=j and set(T[int(active[i])]).isdisjoint(T[j])})
        existing={o.name:len(local.overlap(b.solid.data(o)[2])) for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(('AFN6_','AFN10_','AFN11_'))}
        results.append({'weight':w,'evaluatorMaximumErrorM':evaluatorError,'parts':rows,'oralComponentRawIntersections':cross,'changedBodyNonAdjacentSelfPairs':len(self_pairs),'bodySelfSamples':self_pairs[:16],'changedBodyVsExistingOpticalBrowLash':existing,'wallSeconds':time.time()-start})
        b.save('b-static-verification.json',{'asset':str(path),'assetSha256':b.sha(path),'results':results,'status':'REVIEW_RAW_CONTACT_RESULTS','method':'Reopened file, exact full triangle intersection tests; nonadjacent self tests; per-tooth centroid closed-body classification; vertex-sampled distance explicitly not full surface minimum.','limits':['Two static endpoints only; no continuous proof.','Anatomical joins not automatically excluded.','No complete scalp hair/self-motion or engine qualification.']})
        print('R0024_STATIC',w,json.dumps({n:{k:v for k,v in r.items() if k in ('bodyTrianglePairs','nonAdjacentSelfPairs','toothCentroidBodyClassification')} for n,r in rows.items()}), 'BODYSELF',len(self_pairs),flush=True)
    b.save('b-layer-inventory.json',{'packedImages':[(i.name,bool(i.packed_file)) for i in bpy.data.images if i.source=='FILE'],'externalLibraries':len(bpy.data.libraries),'objects':[{'name':o.name,'parent':o.parent.name if o.parent else None,'layer':o.get('aevrynd_layer'),'verts':len(o.data.vertices),'polygons':len(o.data.polygons)} for o in parts],'attachmentSupportMaximumMoveM':report['attachmentBoundSkinMaximumMoveM']})
if __name__=='__main__':main()
