"""Inspect native mouth target data, exact subdivision transfer and lip profiles."""
import bpy,json,gzip,shutil,time,importlib.util
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
spec=importlib.util.spec_from_file_location('native',Path(__file__).with_name('prepare-female-next-r0019-native-blink.py'));native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
R,S,SRC,ADDON=native.R,native.S,native.SRC,native.ADDON;E=R/'Evidence/character-female-next/r0023-neutral-mouth';E.mkdir(exist_ok=True);sha=native.sha
UNITS=('compression','elevation','depression','open')
def save(name,obj):(E/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def profile(P,T):
    tree=BVHTree.FromPolygons(P.tolist(),T.tolist());rows=[]
    for x in (-.024,-.016,0.,.016,.024):
        hits=[]
        for z in np.linspace(1.365,1.425,601):
            hit,n,face,d=tree.ray_cast(Vector((x,-.4,float(z))),Vector((0,1,0)),.5);hits.append([float(z),float(hit.y) if hit else None,int(face) if face is not None else None])
        rows.append({'x':x,'rays':hits})
    return rows
def main():
    started=time.time();manifest=json.loads((S.parent/'female-next.asset.json').read_text());assert sha(SRC)==manifest['workingReviewSha256'];refs=E/'cc0-native-targets';refs.mkdir(exist_ok=True);sources=[];D={}
    for unit in UNITS:
        delta=np.zeros((19158,3),np.float64)
        for race,weight in (('african',.2),('asian',.5),('caucasian',.3)):
            source=ADDON/f'data/targets/expression/units/{race}/mouth-{unit}.target.gz';archive=refs/f'{race}-mouth-{unit}.target.gz';shutil.copyfile(source,archive);raw=gzip.decompress(source.read_bytes()).decode('utf8');rows=np.array([[float(x) for x in line.split()] for line in raw.splitlines() if line and not line.startswith('#')]);ids=rows[:,0].astype(np.int64);dv=rows[:,[1,3,2]]*.1;dv[:,1]*=-1;delta[ids]+=weight*dv;sources.append({'installed':str(source),'archive':str(archive),'sha256':sha(source),'weight':weight,'license':'CC0 core graphical target data','author':'MakeHuman Community contributors'})
        D[unit]=delta
    save('references.json',{'assets':sources,'licenseDeclaration':'https://static.makehumancommunity.org/mpfb/faq/build_other_chargen.html','targetFormat':'https://static.makehumancommunity.org/mpfb/docs/assets/concept_targets.html','licenseVerifiedDate':'2026-10-19','reuseScope':'Sparse graphical target data only; no MPFB Python program imported into the engine. Our parser and indexed transfer code, Blender offline evaluator.'})
    bpy.ops.wm.open_mainfile(filepath=str(SRC));rig=bpy.data.objects['AFN_R0005_Rig']
    for bone in rig.pose.bones:bone.matrix_basis.identity()
    bpy.context.view_layer.update();raw=bpy.data.objects['AFN_R0005_EditableNativeCC0'];body=bpy.data.objects['AFN_R0008_Body'];P=native.positions(body.data);F=np.array([tuple(p.vertices) for p in body.data.polygons],np.int32);temp=raw.copy();temp.data=raw.data.copy();temp.name='AFN23_TEMP_NATIVE_TRANSFER';bpy.context.scene.collection.objects.link(temp);temp.hide_viewport=False;temp.hide_set(False);temp.hide_render=True;sub=temp.modifiers.new('AFN23_MATCH_SUBDIVISION','SUBSURF');sub.levels=2;sub.render_levels=2;sub.subdivision_type='CATMULL_CLARK';baseline,faces=native.evaluate(temp);assert len(baseline)==len(P) and np.array_equal(faces,F);basis=temp.data.shape_keys.key_blocks[0];co=np.empty((len(basis.data),3),np.float32);basis.data.foreach_get('co',co.ravel());key=temp.shape_key_add(name='AFN23_TEMP_UNIT',from_mix=False);key.relative_key=basis;fields={'neutralBody':P,'nativeNeutral':baseline.astype(np.float32),'faces':F};statistics=[]
    # Attributes use a different subdivision stencil from coordinates; expand
    # support four coarse edge rings and independently bound outside movement.
    edges=np.array([tuple(e.vertices) for e in temp.data.edges],np.int32)
    for unit,delta in D.items():
        mask=np.linalg.norm(delta,axis=1)>0
        for _ in range(4):mask[edges[mask[edges].any(axis=1)].ravel()]=True
        attr=temp.data.attributes.new('AFN23_SUPPORT_'+unit,'FLOAT','POINT');attr.data.foreach_set('value',mask.astype(np.float32))
    bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();ev=temp.evaluated_get(dg);mesh=ev.to_mesh(preserve_all_data_layers=True,depsgraph=dg);supports={}
    for unit in UNITS:
        vals=np.empty(len(mesh.vertices),np.float32);mesh.attributes['AFN23_SUPPORT_'+unit].data.foreach_get('value',vals);supports[unit]=vals>0
    ev.to_mesh_clear();inverse=np.linalg.inv(np.array(body.matrix_world))[:3,:3]
    for unit,delta in D.items():
        key.data.foreach_set('co',(co.astype(np.float64)+delta).astype(np.float32).ravel());key.value=1.;deformed,df=native.evaluate(temp);key.value=0.;assert np.array_equal(df,F);field=(deformed-baseline)@inverse.T;outside=float(np.linalg.norm(field[~supports[unit]],axis=1).max());assert outside<5.e-7;field[~supports[unit]]=0.;fields['delta_'+unit]=field.astype(np.float32);fields['support_'+unit]=supports[unit];changed=np.linalg.norm(field,axis=1)>1.e-7;statistics.append({'unit':unit,'verticesAbove0p1um':int(changed.sum()),'maximumMoveM':float(np.linalg.norm(field,axis=1).max()),'changedBoundsM':[P[changed].min(axis=0).tolist(),P[changed].max(axis=0).tolist()],'outsideSupportMaximumNoiseM':outside});save(unit+'-front-profile.json',{'unitWeight':1.,'rays':profile(P.astype(np.float64)+field,F),'scope':'Actual body front-ray depths, fixed x/z samples; no aperture/collision/visual acceptance.'})
    save('baseline-front-profile.json',{'rays':profile(P,F),'scope':'Actual neutral front-ray depths; identify the lip opening from data, not a fixed target-name assumption.'});cache=S/'aevrynd-female-next-r0023-native-mouth-data.npz';np.savez_compressed(cache,**fields)
    inventory=[]
    for o in bpy.data.objects:
        if o.type=='MESH' and o!=temp:inventory.append({'name':o.name,'vertices':len(o.data.vertices),'hideRender':o.hide_render,'materials':[m.name for m in o.data.materials]})
    save('mouth-source-inspection.json',{'source':str(SRC),'sourceSha256':sha(SRC),'bodyMaterials':[m.name for m in body.data.materials],'objects':inventory,'exactTopologyCorrespondence':True,'vertices':len(P),'polygons':len(F),'targets':statistics,'cache':str(cache),'cacheSha256':sha(cache),'sourceNotModifiedOrSaved':True,'wallSeconds':time.time()-started});print('R0023_MOUTH_TRANSFER_PASS '+json.dumps(statistics),flush=True)
if __name__=='__main__':main()
