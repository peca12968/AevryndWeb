"""One bounded authored-guide registration test, not an accepted groom.

Pinned CC0 Bob data only. No donor tool code, cards, atlas, root-frame
transport, private donor data, image hull or old Aevrynd path template.
The single whole-head affine transform is design registration, not fitting
or root/collision evidence. A failed pilot is never densified.
"""
from pathlib import Path
import bpy,importlib.util,numpy as np,json,time,sys
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
sp=importlib.util.spec_from_file_location('bob55',Path(__file__).with_name('build-female-next-r0054-clump-volume.py'))
k=importlib.util.module_from_spec(sp);sp.loader.exec_module(k)
b=k.b;f=k.f;E=b.R/'Evidence/character-female-next/r0055-authored-cc0-bob';D=b.R/'Reference/character/charmorph-vitruvian-cc0'
SRC=k.SRC;OUT=b.S/'aevrynd-female-next-r0055-a-authored-bob-registration.blend'
LANDMARK='--landmark-registration' in sys.argv
TAG='b' if LANDMARK else 'a'
if LANDMARK:OUT=b.S/'aevrynd-female-next-r0055-b-landmark-bob-registration.blend'

def save(n,x):
    if n.startswith('a-'):n=TAG+n[1:]
    (E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def main():
    tick=time.time();E.mkdir(parents=True,exist_ok=True)
    assert b.sha(D/'Bob.npz')=='9f85d124b9014e12a968ed99a211590b6fe14c27fb464adf2362a8de89174cea'
    assert b.sha(SRC)=='c293976b2745e372565eb990f2e844a8255f2cdaad8e004563643d0f51c9f537'
    a=np.load(D/'Bob.npz',allow_pickle=False);assert np.all(a['cnt']==16)
    P=a['data'].reshape(-1,16,3).astype('f8');scale=np.array([.88,.85,.80]);shift=np.array([0,-.062,1.5615-.80*1.74643874168396])
    bpy.ops.wm.open_mainfile(filepath=str(SRC));before=f.state();old=bpy.data.objects[k.k.OLD]
    if LANDMARK:
        landmarks=json.loads((E/'donor-inspection.json').read_text())['objects'][0]['registrationLandmarks']
        srcEyes=np.array([landmarks['eyeCenterNegativeX'],landmarks['eyeCenterPositiveX']]);targetEyes=[]
        for ob in bpy.data.objects:
            if ob.type=='MESH' and 'AFN30_' in ob.name and 'Sclera' in ob.name:
                V,_=b.evaluated(ob,True);targetEyes.append(V.mean(0))
        assert len(targetEyes)==2,('Target ocular region names',[(o.name,o.type) for o in bpy.data.objects if 'Sclera' in o.name])
        targetEyes=np.array(sorted(targetEyes,key=lambda x:x[0]));sourceCentre=srcEyes.mean(0);targetCentre=targetEyes.mean(0)
        V,_=b.evaluated(bpy.data.objects[b.BODY],True)
        sx=(targetEyes[1,0]-targetEyes[0,0])/(srcEyes[1,0]-srcEyes[0,0]);sz=(V[:,2].max()-targetCentre[2])/(landmarks['top']-sourceCentre[2])
        scale=np.array([sx,(sx+sz)*.5,sz]);shift=targetCentre-sourceCentre*scale
        save('b-registration-landmarks.json',{'sourceEyes':srcEyes.tolist(),'targetEyes':targetEyes.tolist(),'sourceTop':landmarks['top'],'targetTop':float(V[:,2].max()),'scope':'Whole-style affine design alignment. Not root fitting or contact proof.'})
    Q=(P*scale+shift).astype('f4');assert np.isfinite(Q).all()
    d=old.data.copy();d.name='AFN55_CC0_AUTHORED_BOB_GUIDES';d.remove_curves(indices=list(range(1,len(d.curves))));d.resize_curves([16]);d.add_curves([16]*(len(Q)-1))
    for attr in list(d.attributes):
        if attr.name.startswith('AFN38') or attr.name.startswith('.selection') or attr.name=='surface_uv_coordinate':d.attributes.remove(attr)
    d.surface=None;d.position_data.foreach_set('vector',Q.ravel());d.attributes['curve_type'].data.foreach_set('value',[1]*len(Q))
    radii=np.broadcast_to(np.linspace(.000055,.000009,16),(len(Q),16)).astype('f4').copy()
    d.attributes['radius'].data.foreach_set('value',radii.ravel());d.attributes['material_index'].data.foreach_set('value',np.arange(len(Q))%len(d.materials))
    ob=bpy.data.objects.new(d.name,d);bpy.context.scene.collection.objects.link(ob);ob.matrix_world=Matrix.Identity(4)
    ob['scope']='CC0 Bob full shape pilot. Affine registration only; physical follicles and full contact unqualified. Do not generate children before actual form/contact decision.'
    ob['aevrynd_layer']='UNQUALIFIED_AUTHORED_GUIDE_PILOT'
    old.hide_render=True;old.hide_set(True)
    V,T=b.evaluated(bpy.data.objects[b.BODY],True);tree=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True)
    rootErrors=[float(tree.find_nearest(Vector(p))[3]) for p in Q[:,0]]
    # Root distance is diagnostic only. Do not silently snap, trim or exclude roots.
    save(TAG+'-round-contract.json',{'revision':'female-next-r0055','previousGoalTurnClassification':'progress: v15 prompt/entry changes completed and pushed5dc7d3c; no appearance gain. Unregisteredr54E now reviewed and rejected for bands, holes and helmet form.',
        'source':str(SRC),'sourceSha256':b.sha(SRC),'mainDefect':'Complete naturally flowing hair shape absent',
        'reference':'Pinned author-defined CC0 Vitruvian Bob248guides. Single anatomical scale registration of the entire style; no old guide routes.',
        'expectedVisibleChange':'Natural authored crown-to-side/back flow rather than synthetic scaffold/tubes/hull bands',
        'minimumTest':'Actual248guide whole-head/body and multiangle render; thick path view explicitly diagnostic; root distance and full finite static body capsules before any children',
        'reject':['Unnatural complete shape','Root registration cannot be justified','Full finite paths fail actual body contact'],
        'candidateCount':1,'resourceLimit':'One pilot,4Blender threads, one heavy job; no density or parameter sweep'})
    after=f.state();assert all(after[x]==before[x] for x in ('meshes','materials','skinFields','stage'))
    assert all(after['curves'][name]==row for name,row in before['curves'].items())
    save('a-build-summary.json',{'source':str(SRC),'sourceSha256':b.sha(SRC),'output':str(OUT),
        'guideSourceSHA256':b.sha(D/'Bob.npz'),'guideCount':len(Q),'pointsPerGuide':16,'wholeHeadScale':scale.tolist(),'wholeHeadTranslationM':shift.tolist(),
        'rootUnsignedDistanceRangeM':[min(rootErrors),max(rootErrors)],'rootUnsignedDistanceP50M':float(np.median(rootErrors)),
        'rootBinding':'NOT_BOUND_NOT_QUALIFIED','originalCharacterStateUnchanged':True,'status':'AFFINE_AUTHORED_GUIDE_PILOT_PENDING_REVIEW'})
    b.camera('face');bpy.context.scene.camera.data.lens=85;bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    np.savez_compressed(E/(TAG+'-actual-guide-data.npz'),positions=Q,radii=radii)
    report=json.loads((E/(TAG+'-build-summary.json')).read_text());report['outputSha256']=b.sha(OUT);save('a-build-summary.json',report)
    f.E=E;f.render(TAG+'-actual-fibres',('face','oblique','profile'));k.k.k.k.a.i.ch.review.extras(TAG+'-actual-fibres',E)
    d.attributes['radius'].data.foreach_set('value',np.full((len(Q),16),.0005,dtype='f4').ravel());bpy.context.view_layer.update()
    f.render(TAG+'-path-diagnostic',('face','oblique','profile'));k.k.k.k.a.i.ch.review.extras(TAG+'-path-diagnostic',E)
    d.attributes['radius'].data.foreach_set('value',radii.ravel());bpy.context.view_layer.update()
    contact=f.flowcheck.check(Q.astype('f8'),radii.astype('f8'),tree,V[T],roots=True)
    save('a-static-body-capsules.json',contact)
    print('R55_AUTHORED_BOB_PILOT_READY',contact['status'],time.time()-tick,flush=True)

if __name__=='__main__':main()
