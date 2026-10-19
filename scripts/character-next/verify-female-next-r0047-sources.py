"""Reopen exact rejected files and confirm actual contact witnesses."""
import bpy,importlib.util,numpy as np,time
from pathlib import Path
from mathutils import Vector
from mathutils.geometry import intersect_ray_tri
sp=importlib.util.spec_from_file_location('bob47verify',Path(__file__).with_name('build-female-next-r0047-authored-bob.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a)
b=a.b;f=a.f;E=a.E;S=a.S
def crossings(H,HT,V,T,pairs):
    confirmed=[]
    for hi,bi in pairs:
        A=H[HT[hi]];B=V[T[bi]];point=None
        for first,second in ((A,B),(B,A)):
            for k in range(3):
                start=first[k];delta=first[(k+1)%3]-start
                if np.linalg.norm(delta)<1e-12:continue
                hit=intersect_ray_tri(*[Vector(v)for v in second],Vector(delta),Vector(start),True)
                if hit is not None:
                    u=float((np.array(hit)-start)@delta/(delta@delta))
                    if 1e-7<u<1-1e-7:point=list(hit);break
            if point is not None:break
        if point is not None:confirmed.append({'hairTriangle':int(hi),'otherTriangle':int(bi),'pointM':point})
    return {'bvhCandidatePairs':len(pairs),'confirmedEdgeTriangleCrossings':len(confirmed),'witnesses':confirmed[:30],'scope':'Independent finite-edge/triangle intersection of actual saved displayed card surfaces, double sided. No triangle alpha exclusions; no thickness/self/dynamic inference.'}
def main():
    tick=time.time();bpy.ops.wm.open_mainfile(filepath=str(a.SRC));before=f.state();rows=[]
    for tag,path,summaryFile in [('A',a.OUT,'a-build-summary.json'),('B',S/'aevrynd-female-next-r0047-b-authored-rail-pilot.blend','b-pilot-summary.json')]:
        import json
        summary=json.loads((E/summaryFile).read_text());assert b.sha(path)==summary['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(path));after=f.state()
        assert all(after['meshes'][name]==row for name,row in before['meshes'].items());assert all(after['materials'][name]==row for name,row in before['materials'].items());assert after['skinFields']==before['skinFields'] and after['stage']==before['stage'] and after['curves']==before['curves'];assert bpy.data.objects['AFN33_C_BODY_BOUND_FIBRES'].hide_render
        cards=bpy.data.objects['AFN47_CC0_Bob02_AuthoredCards'];assert cards.hide_render==(tag=='B');texture=bpy.data.images.get('bob02_diffuse.png');assert texture and texture.packed_file
        row={'tag':tag,'source':str(path),'sha256':b.sha(path),'bytes':path.stat().st_size,'reopened':True,'originalBodySkinOpticsBrowLashTissueGroomDataStageExact':True,'packedCC0Texture':True,'cardVisible':not cards.hide_render,'qualification':'Rejected static study, not a character acceptance'}
        if tag=='A':
            original,uv,faces,tfaces=a.obj(a.ASSET/'bob02.obj');assert [list(p.vertices)for p in cards.data.polygons]==faces
            actualUV=np.array([x.uv[:]for x in cards.data.uv_layers.active.data]);expectedUV=uv[np.array([q for face in tfaces for q in face])];assert np.max(abs(actualUV-expectedUV))<1e-7
            H,HT=b.evaluated(cards,True);V,T=b.evaluated(bpy.data.objects[b.BODY],True);bt=a.i.i.tree(V,T);ht=a.i.i.tree(H,HT);row['bodyContact']=crossings(H,HT,V,T,ht.overlap(bt));optics={}
            for side in ('L','R'):
                for part in ('Sclera','Cornea','Iris','Pupil'):
                    name=f'AFN30_{side}_{part}';v,t=b.evaluated(bpy.data.objects[name],True);optics[name]=crossings(H,HT,v,t,ht.overlap(a.i.i.tree(v,t)))
            row['opticsContact']=optics;row['originalUVAndTopologyExact']=True
        else:
            guide=bpy.data.objects['AFN47_B_AUTHORED_RAIL_GUIDES'];cache=np.load(E/'b-pilot-paths.npz');P=np.array([[p.co[:3]for p in sp.points]for sp in guide.data.splines]);mx=np.array(guide.matrix_world);W=P@mx[:3,:3].T+mx[:3,3];rr=np.array([[p.radius*guide.data.bevel_depth for p in sp.points]for sp in guide.data.splines]);assert np.max(abs(W-cache['positions']))<2e-7 and np.max(abs(rr-cache['radii']))<1e-10;row.update(guides=len(P),nativePointReadbackErrorMaxM=float(np.max(abs(W-cache['positions']))),actualNativeRadiusReadbackMaxErrorM=float(np.max(abs(rr-cache['radii']))),denseFibresGenerated=False)
        rows.append(row)
    a.save('reopen-verification.json',{'status':'PASS_EXACT_REOPEN_AND_CONTACT_WITNESSES_NOT_CHARACTER_ACCEPTANCE','rows':rows,'seconds':time.time()-tick});print('R47_REOPENED',[(r['tag'],r.get('bodyContact',{}).get('confirmedEdgeTriangleCrossings'))for r in rows],flush=True)
if __name__=='__main__':main()
