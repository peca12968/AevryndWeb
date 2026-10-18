"""Reopened soft tissue, with inherited dental evidence kept exactly scoped."""
import bpy,importlib.util,json,time
from pathlib import Path
import numpy as np
from mathutils import Vector
spec=importlib.util.spec_from_file_location('b26',Path(__file__).with_name('build-female-next-r0026-oral-interface.py'));b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
def weight(w):
    master=bpy.data.objects['AFN24_MouthControl'];master['open']=float(w);master.update_tag(refresh={'OBJECT'});bpy.context.scene.frame_set(bpy.context.scene.frame_current+1);bpy.context.view_layer.update()
def main():
    report=json.loads((b.E/'c-build-verification.json').read_text(encoding='utf8'));path=Path(report['output']);assert b.b.sha(path)==report['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(path));rig=bpy.data.objects['AFN_R0005_Rig'];b.b.prior.solid.stage.set_pose(rig,'neutral');weight(0.)
    old=json.loads((b.b.E/'a-saved-motion-verification.json').read_text(encoding='utf8'));teeth=[bpy.data.objects[name] for name in old['teethGeometry']]
    for name,data in old['teethGeometry'].items():
        o=bpy.data.objects[name];assert b.b.prior.solid.geom(o)==data['geometrySha256'] and o.parent.name==data['parent'] and [v for row in o.matrix_basis for v in row]==data['matrixBasis']
    for name,prior in old['jawControls'].items():
        o=bpy.data.objects[name];now={'parent':o.parent.name,'parentType':o.parent_type,'parentBone':o.parent_bone,'matrixParentInverse':[v for row in o.matrix_parent_inverse for v in row],'location':list(o.location),'scale':list(o.scale),'rotationAxisAngle':list(o.rotation_axis_angle),'drivers':[{'path':c.data_path,'index':c.array_index,'expression':c.driver.expression,'targets':[(var.name,var.targets[0].id.name,var.targets[0].data_path) for var in c.driver.variables]} for c in o.animation_data.drivers]}
        assert json.loads(json.dumps(now))==prior
    tongue=bpy.data.objects['AFN26_Tongue'];gum=bpy.data.objects['AFN26_GingivalLining'];structure=[]
    for o in (tongue,gum):
        P,T,tree=b.b.prior.solid.data(o);p=np.array(P,np.float64);tri=p[np.array(T)];areas=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)/2;edges={}
        for face in o.data.polygons:
            ids=list(face.vertices)
            for a,c in zip(ids,ids[1:]+ids[:1]):key=tuple(sorted((a,c)));edges.setdefault(key,[]).append(1 if a<c else -1)
        components=b.b.prior.proxy.components(len(P),T)
        structure.append({'object':o.name,'vertices':len(P),'triangles':len(T),'components':len(components),'boundaryEdges':sum(len(v)==1 for v in edges.values()),'nonManifoldOrInconsistentEdges':sum(len(v)>2 or (len(v)==2 and sum(v)!=0) for v in edges.values()),'degenerateTriangles':int((areas<1.e-14).sum()),'minimumTriangleAreaM2':float(areas.min())})
    rows=[];neutral=b.b.prior.evaluate(tongue)
    for w in (0.,.05,.1,.15,.2):
        start=time.time();weight(w);P,T,tree=b.b.prior.solid.data(tongue);G,GT,gtree=b.b.prior.solid.data(gum);V,VT,body=b.b.prior.solid.data(bpy.data.objects['AFN_R0008_Body']);p=np.array(P,np.float64);tri=p[np.array(T)];dental=[]
        for o in teeth:
            Q,F,own=b.b.prior.solid.data(o);q=np.array(Q,np.float64);hits=tree.overlap(own);a=b.b.prior.solid.classify(tree,tri,Vector(q[0]));c=b.b.prior.solid.classify(own,q[np.array(F)],Vector(p[0]));dental.append({'tooth':o.name,'trianglePairs':len(hits),'toothAnchorVsTongue':a,'tongueAnchorVsTooth':c,'sampledVertexDistanceM':min(float(own.find_nearest(point)[3]) for point in P),'samples':hits[:6]})
        ts=[(i,j) for i,j in tree.overlap(tree) if i<j and set(T[i]).isdisjoint(T[j])];gs=[(i,j) for i,j in gtree.overlap(gtree) if i<j and set(GT[i]).isdisjoint(GT[j])];tg=tree.overlap(gtree);tb=tree.overlap(body);gb=gtree.overlap(body)
        rows.append({'weight':w,'tongueDental':dental,'tongueBodyTrianglePairs':len(tb),'tongueSelfNonAdjacentPairs':len(ts),'tongueGingivaTrianglePairs':len(tg),'gingivaBodyTrianglePairs':len(gb),'gingivaSelfNonAdjacentPairs':len(gs),'tongueBodyAnchor':b.b.prior.solid.classify(body,np.array(V)[np.array(VT)],Vector(p[0])),'tongueSelfSamples':ts[:8],'gingivaBodySamples':gb[:8],'wallSeconds':time.time()-start})
        b.save('c-static-verification.json',{'asset':str(path),'assetSha256':b.b.sha(path),'inheritedExactDentalGeometryAndControls':True,'inheritedDentalProof':str(b.b.E/'a-dental-sweep-verification.json'),'structure':structure,'poses':rows,'scope':'Changed actual soft-tissue surfaces in five static mouth weights. Raw anatomical interface contacts retained. Closed dental geometry/control fingerprints checked before reusing only the r25 dental-pair evidence.'})
        print('R0026_STATIC',w,'TONGUE_DENTAL',sum(r['trianglePairs'] for r in dental),'TONGUE_SELF',len(ts),'TONGUE_BODY',len(tb),'TONGUE_GUM',len(tg),'GUM_BODY',len(gb),'GUM_SELF',len(gs),flush=True)
    tongue_structure=next(r for r in structure if r['object']==tongue.name);tongue_good=tongue_structure['components']==1 and tongue_structure['boundaryEdges']==tongue_structure['nonManifoldOrInconsistentEdges']==tongue_structure['degenerateTriangles']==0 and all(r['tongueBodyTrianglePairs']==r['tongueSelfNonAdjacentPairs']==0 and r['tongueBodyAnchor']=='outside' and all(c['trianglePairs']==0 and c['toothAnchorVsTongue']=='outside' and c['tongueAnchorVsTooth']=='outside' for c in r['tongueDental']) for r in rows)
    b.save('c-verification-summary.json',{'asset':str(path),'assetSha256':b.b.sha(path),'tongueStructureAndFiveStateDentalBodyPass':tongue_good,'inheritedDentalPairSweepUnchanged':True,'wholeMouthAccepted':False,'gingivalMotionAccepted':all(r['gingivaBodyTrianglePairs']==r['gingivaSelfNonAdjacentPairs']==0 for r in rows),'scope':'Five sampled soft-tissue states only. Lower tongue and lower teeth share one rigid control; their unchanged relative geometry is separable throughout the same range if the neutral surface/containment tests pass. No upper-tooth/body/gingival/tongue continuous proof or whole-mouth acceptance.'});print('R0026_TONGUE_PASS',tongue_good,flush=True)
if __name__=='__main__':main()
