"""Native card/atlas readback and early actual-surface contact falsification.

0-thickness textured surfaces only; never a physical micro-fibre proof.
No sampled-pair minimum or first witnesses are reported as a global total.
"""
import bpy,numpy as np,json,time,importlib.util
from pathlib import Path
from mathutils.bvhtree import BVHTree
def module(n,p):
    s=importlib.util.spec_from_file_location(n,Path(__file__).with_name(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
m=module('read64texture','texture-female-next-r0064-cards.py');base=m.m;g=base.g;k=g.k;v=module('signature64','verify-female-next-r0061-complete-groom.py');E=m.E
def read(p):return json.loads(p.read_text(encoding='utf8'))
def mesh(o):
    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());d=ev.to_mesh();d.calc_loop_triangles();P=np.array([p.co[:] for p in d.vertices],'f8');M=np.array(o.matrix_world);P=P@M[:3,:3].T+M[:3,3];T=np.array([t.vertices[:] for t in d.loop_triangles],'i4');ev.to_mesh_clear();return P,T
def contacts(V,T,BV,BT,label,same=False):
    tree=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True);other=tree if same else BVHTree.FromPolygons(BV.tolist(),BT.tolist(),all_triangles=True);pairs=tree.overlap(other);tested=0;legal=0;bad=[]
    for i,j in pairs:
        if same and i>=j:continue
        points=k.exact.intersections(V[T[i]],BV[BT[j]])
        tested+=1
        if not points:continue
        shared=sorted(set(T[i])&set(BT[j])) if same else [];expected=V[shared] if shared else []
        if shared and k.exact.on_expected(points,expected,1e-6):legal+=1;continue
        bad.append({'triangles':[int(i),int(j)],'pointsM':[p.tolist() for p in points[:4]]})
        if len(bad)>=16:break
    return {'pair':label,'status':'REJECT_ACTUAL_SURFACE_INTERSECTIONS' if bad else 'NO_WITNESS_IN_TESTED_SURFACE_SCOPE_VOLUME_THICKNESS_UNACCEPTED','broadPhasePairs':len(pairs),'refinedPairs':tested,'topologicalSharedJoins':legal,'witnesses':bad,'earlyStopped':bool(bad),'failureCountIsGlobalTotal':False,'surfaceNumericalAllowanceM':1e-6,'exactGlobalSignedMinimumM':None,'scope':'Actual evaluated mesh triangle intersections,0-thickness representation. Alpha masks do not excuse actual surface failures. Not finite3-D micro-fibres or continuous motion.'}
def main():
    tick=time.time();ref=read(E/'c-build-summary.json');assert base.sha(m.OUT)==ref['outputSha256'];names=list(read(E.parent/'r0060-ocular-assembly/b-build-summary.json')['visibleComponents'].values())
    bpy.ops.wm.open_mainfile(filepath=str(base.SRC));native={n:v.mesh_signature(bpy.data.objects[n]) for n in names};stage=k.f.v.stage();v.raise_subdivision();poses={}
    for frame in (1,21):
        bpy.context.scene.frame_set(frame);bpy.context.view_layer.update();poses[frame]={n:v.digest(k.mesh(bpy.data.objects[n])['V']) for n in names}
    bpy.ops.wm.open_mainfile(filepath=str(m.OUT));assert native=={n:v.mesh_signature(bpy.data.objects[n]) for n in names};now=k.f.v.stage();assert now['lights']==stage['lights']
    for key in ('transform','look','exposure','gamma','world'):assert now['config'][key]==stage['config'][key]
    v.raise_subdivision()
    for frame in (1,21):
        bpy.context.scene.frame_set(frame);bpy.context.view_layer.update();assert poses[frame]=={n:v.digest(k.mesh(bpy.data.objects[n])['V']) for n in names}
    bpy.context.scene.frame_set(1);bpy.context.view_layer.update();images=[]
    for im in bpy.data.images:
        if im.source=='FILE':
            p=Path(bpy.path.abspath(im.filepath));assert im.filepath.startswith('//') and p.exists();im.reload();images.append({'relative':im.filepath,'sha256':base.sha(p),'packed':bool(im.packed_file)})
    # The shader uses albedo/coverage and normals. UV-flow is a separate own
    # engine-data PNG; Blender drops its unreferenced datablock on save.
    # Verify the actual17 saved images AND all3 authored files, rather than
    # pretending the in-memory18-image construction list was a saved readback.
    assert len(images)==17 and sum(x['packed'] for x in images)==2
    external=[]
    for item in ref['textures']:
        p=Path(bpy.path.abspath(item['relative']));assert p.exists() and base.sha(p)==item['sha256'];external.append({'relative':item['relative'],'sha256':base.sha(p),'savedInBlend':any(x['sha256']==item['sha256'] for x in images)})
    assert not bpy.data.libraries and not bpy.app.handlers.frame_change_pre and not bpy.app.handlers.frame_change_post
    author=read(E/'b-guide-authoring.json');cards=[];guides=[];sourcebody=k.mesh(bpy.data.objects[names[4]]);rooterror=[]
    for rec in author['guides']:
        guide=bpy.data.objects[rec['guideObject']];points=np.array([p.co[:] for p in guide.data.splines[0].bezier_points]);assert np.max(np.abs(points-np.array(rec['points'])))<1e-6;guides.append(guide.name);o=bpy.data.objects[rec['cardObject']];P,T=mesh(o);assert np.isfinite(P).all() and len(P)==rec['vertices'];assert len(o.data.uv_layers['AFN64_CardUV'].data)==len(o.data.loops)
        for j,rr in enumerate(rec['rootRows']):
            tri=sourcebody['V'][sourcebody['T'][int(rr[0])]];normal=base.unit(np.cross(tri[1]-tri[0],tri[2]-tri[0]));target=np.array(rr[2:])@tri+normal*.0008;rooterror.append(float(np.linalg.norm(P[j]-target)))
        cards.append((P,T))
    assert max(rooterror)<1e-6;cap=bpy.data.objects['AFN64_SCALP_UNDERCOAT'];CP,CT=mesh(cap);assert np.isfinite(CP).all()
    function={'status':'PASS_REOPENED_EDITABLE_STATIC_CARD_DATA_ONLY','source':str(m.OUT),'sha256':base.sha(m.OUT),'cards':len(cards),'explicitBezierGuides':len(guides),'guidesLiveDeformCards':False,'cardVertices':sum(len(p) for p,t in cards),'cardTriangles':sum(len(t) for p,t in cards),'scalpVertices':len(CP),'scalpTriangles':len(CT),'maximumDeclaredUndercoatRootErrorM':max(rooterror),'originalFiveComponentsNativeUVKeysMaterialsAndNeutralClosedPositionsExact':True,'lightsExposureSkinExact':True,'relativeTextures':images,'ownAtlasFiles':external,'savedPackedTextureCount':2,'flowPNGIsSeparateUnusedNativeShaderData':True,'constructionListIsNotSavedImageCount':True,'automaticHandlersOrLibraries':False,'individualFolliclesRigDynamicsOrRuntimeAccepted':False,'seconds':time.time()-tick};base.save('c-native-readback.json',function);print('R64_NATIVE_CARD_READBACK_PASS',len(cards),time.time()-tick,flush=True)
    V=[];T=[];off=0
    for p,t in cards:V.append(p);T.append(t+off);off+=len(p)
    V=np.concatenate(V);T=np.concatenate(T);bodyparts=[k.mesh(bpy.data.objects[n]) for n in names];BV,BT,mi,fi=k.join(bodyparts)
    body=contacts(V,T,BV,BT,'all32actualCardsVsAllFiveBodyOpticSurfaces');base.save('c-card-body-falsification.json',body);print('R64_CARD_BODY',body['status'],time.time()-tick,flush=True)
    selftest=contacts(V,T,V,T,'all32actualCardsSelf',True);base.save('c-card-self-falsification.json',selftest);print('R64_CARD_SELF',selftest['status'],time.time()-tick,flush=True)
    captest=contacts(CP,CT,BV,BT,'actualScalpUndercoatVsAllFiveBodyOpticSurfaces');base.save('c-scalp-body-falsification.json',captest);print('R64_SCALP_BODY',captest['status'],time.time()-tick,flush=True)
    base.save('c-contact-scope.json',{'source':str(m.OUT),'sha256':base.sha(m.OUT),'status':'UNACCEPTED','body':body['status'],'cardSelf':selftest['status'],'scalpBody':captest['status'],'notTested':['Card/scalp joins and cap self','Body containment and nonzero thickness','Alpha-conditioned virtual fibres','Head-follow or cloth interactions','All continuous motion','Engine runtime performance'],'noGlobalSignedMinimumOrZeroPenetrationClaim':True,'seconds':time.time()-tick})
if __name__=='__main__':main()
