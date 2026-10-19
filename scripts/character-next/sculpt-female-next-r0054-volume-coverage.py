"""Specific editable-mesh coverage correction after actual orthographic review.

Regional cage vertices are edited, not a density/radius candidate sweep. The
quad topology and object/Face Set partition stay intact. Overlapping design
volumes do not constitute physically separated hair or collision acceptance.
"""
from pathlib import Path
import bpy,importlib.util,numpy as np,json,time
sp=importlib.util.spec_from_file_location('volume54',Path(__file__).with_name('build-female-next-r0054-clump-volume.py'))
k=importlib.util.module_from_spec(sp);sp.loader.exec_module(k)
b=k.b;f=k.f;E=k.E;SRC=k.OUT;OUT=b.S/'aevrynd-female-next-r0054-b-edited-clump-volume.blend'

def main():
    tick=time.time();report=json.loads((E/'a-build-summary.json').read_text());assert b.sha(SRC)==report['outputSha256']
    bpy.ops.wm.open_mainfile(filepath=str(SRC));before=f.state();records=[]
    for side in ('L','R'):
        clumps=[row for row in report['clumps'] if row['object'].startswith('AFN54_'+side+'_')]
        centres=np.array([row['constructionStationsM'] for row in clumps])
        for ci,row in enumerate(clumps):
            ob=bpy.data.objects[row['object']];mesh=ob.data
            X=np.array([list(v.co) for v in mesh.vertices],dtype='f8');original=X.copy();C=centres[ci]
            groups=np.argmin(np.linalg.norm(X[:,None]-C[None],axis=2),axis=1)
            edits=[]
            for station in range(len(C)):
                ids=np.flatnonzero(groups==station)
                if not len(ids):continue
                ys=centres[:,station,1];y=C[station,1]
                prev=ys[ci-1] if ci else y-(ys[1]-y)
                nxt=ys[ci+1] if ci+1<len(clumps) else y+(y-ys[ci-1])
                lo=.5*(prev+y)-.004;hi=.5*(nxt+y)+.004
                oldLo=float(X[ids,1].min());oldHi=float(X[ids,1].max())
                if oldHi-oldLo>1e-7:
                    X[ids,1]=lo+(X[ids,1]-oldLo)*(hi-lo)/(oldHi-oldLo)
                if station==0:
                    # Tight part footprint; old root centre and inherited
                    # follicle anchors are unrelated to these volume cages.
                    xx=X[ids,0];mn=float(xx.min());mx=float(xx.max())
                    if mx-mn>1e-7:
                        if side=='L':X[ids,0]=mn+(xx-mn)*(-.0007-mn)/(mx-mn)
                        else:X[ids,0]=.0007+(xx-mn)*(mx-.0007)/(mx-mn)
                if ci==len(clumps)-1 and station>0:
                    # Central rear coverage is required; a long bald slot is
                    # not a hair part. Keep the outside silhouette and extend
                    # only the inward cage edge across the rear midline.
                    xx=X[ids,0];mn=float(xx.min());mx=float(xx.max())
                    if mx-mn>1e-7:
                        if side=='L':X[ids,0]=mn+(xx-mn)*(.010-mn)/(mx-mn)
                        else:X[ids,0]=-.010+(xx-mn)*(mx+.010)/(mx-mn)
                if station==len(C)-1:
                    X[ids,2]=float(X[ids,2].mean())+.003
                edits.append({'station':station,'vertices':len(ids),'newSectionYBoundsM':[float(lo),float(hi)]})
            for vertex,p in zip(mesh.vertices,X):vertex.co=p
            mesh.update();ob['scope']='Edited mass-coverage proxy, separate quad clump/Face Set. Root/other mass overlap intentional for design; not physical hair.'
            records.append({'object':ob.name,'editedVertices':int((np.linalg.norm(X-original,axis=1)>1e-8).sum()),
                'maximumNativeVertexMoveM':float(np.linalg.norm(X-original,axis=1).max()),'regionalEdits':edits,
                'nativeVerticesUnchanged':len(mesh.vertices),'nativeFacesUnchanged':len(mesh.polygons)})
    bpy.context.view_layer.update();after=f.state()
    assert all(after['meshes'][name]==row for name,row in before['meshes'].items() if not name.startswith('AFN54_'))
    assert all(after['materials'][name]==row for name,row in before['materials'].items())
    assert all(after[key]==before[key] for key in ('skinFields','curves','stage'))
    b.camera('face');bpy.context.scene.camera.data.lens=85
    bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    k.save('b-build-summary.json',{'source':str(SRC),'sourceSha256':b.sha(SRC),'output':str(OUT),'outputSha256':b.sha(OUT),
        'edits':records,'originalBodyOpticsHairSkinMaterialsStageUnchanged':True,
        'scope':'Specific mesh coverage/perimeter edit of the same12-clump proxy, not a final hairstyle or collision-qualified mesh.',
        'status':'EDITED_VOLUME_PENDING_COMPLETE_FORM_REVIEW','seconds':time.time()-tick})
    f.E=E;f.render('b-proxy',('face','oblique','profile'));k.k.k.k.a.i.ch.review.extras('b-proxy',E);k.orthographic('b-proxy')
    print('R54_VOLUME_COVERAGE_EDITED',time.time()-tick,flush=True)

if __name__=='__main__':main()
