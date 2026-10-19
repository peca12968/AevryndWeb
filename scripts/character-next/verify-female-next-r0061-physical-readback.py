"""Read-only C/history portability, root metadata and unchanged-geometry proof."""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,sys
sp=importlib.util.spec_from_file_location('physical61verify',Path(__file__).with_name('verify-female-next-r0061-complete-groom.py'));v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v)
g=v.g;k=g.k

def main():
    history='--history' in sys.argv;ref=json.loads((g.E/'c-build-summary.json').read_text());source=Path(ref['source']);candidate=Path(ref['output'])
    if history:candidate=g.R/'sites-engine-journey/assets-source/aevrynd-character/female-next'/candidate.name
    assert g.sha(candidate)==ref['outputSha256'] and g.sha(source)==ref['sourceSha256']
    bpy.ops.wm.open_mainfile(filepath=str(source));names=list(json.loads((g.E.parent/'r0060-ocular-assembly/b-build-summary.json').read_text())['visibleComponents'].values());before={n:v.mesh_signature(bpy.data.objects[n]) for n in names};Q,R=v.read_hair(bpy.data.objects['AFN61_SCALP_ATTACHED_PONYTAIL_FIBRES']);stage=k.f.v.stage()
    bpy.ops.wm.open_mainfile(filepath=str(candidate));after={n:v.mesh_signature(bpy.data.objects[n]) for n in names};assert before==after
    ob=bpy.data.objects['AFN61_SCALP_ATTACHED_PONYTAIL_FIBRES'];P,rr=v.read_hair(ob);assert np.array_equal(P,Q) and np.array_equal(rr,R);now=k.f.v.stage();assert now['lights']==stage['lights']
    for key in ('transform','look','exposure','gamma','world'):assert now['config'][key]==stage['config'][key],key
    attrs={}
    for name in ('AFN61_RestRenderTriangle','AFN61_NativeScalpFace','AFN61_RestBarycentric'):
        a=ob.data.attributes[name];assert a.domain=='CURVE' and len(a.data)==len(P);attrs[name]={'domain':a.domain,'type':a.data_type,'count':len(a.data)}
    raw=np.load(g.E/'b-fibres-authoring.npz')
    for name,key,kind,field,size in [('AFN61_RestRenderTriangle','rootTriangles','i4','value',1),('AFN61_NativeScalpFace','rootNativeFaces','i4','value',1),('AFN61_RestBarycentric','rootBarycentric','f4','vector',3)]:
        array=np.empty(len(P)*size,kind);ob.data.attributes[name].data.foreach_get(field,array);assert np.array_equal(array,raw[key].astype(kind).ravel()),name
    images=[]
    for im in bpy.data.images:
        if im.source=='FILE':
            p=Path(bpy.path.abspath(im.filepath));assert im.filepath.startswith('//') and p.exists();im.reload();images.append({'relative':im.filepath,'sha256':g.sha(p)})
    assert len(images)==15;assert not bpy.data.libraries and not bpy.app.handlers.frame_change_pre and not bpy.app.handlers.frame_change_post
    hair=next(n for n in ob.data.materials[0].node_tree.nodes if n.bl_idname=='ShaderNodeBsdfHairPrincipled');assert hair.model=='CHIANG' and hair.parametrization=='MELANIN'
    result={'source':str(candidate),'sha256':g.sha(candidate),'openedFromHistory':history,'actualCurves':len(P),'actualPositionsRadiiExactToB':True,'originalAnatomicalMeshesKeysUVMaterialsExactToB':True,'originalLightsExposureSkinUnchanged':True,'rendererExplicitlyChanged':'Eevee to Cycles for a hair-specific shader; equal-Cycles controls required. No runtime compatibility claim.','nativeRootAttributes':attrs,'textures':images,'externalLibrariesOrAutoRunHandlers':False,'transferredContactScope':'Only exact-geometry neutral free-fibre vs body/optics evidence. Tie self-shaft failure also transfers unchanged; no dynamic/full-character acceptance.'}
    g.save('c-history-readback.json' if history else 'c-source-readback.json',result);print('R61_C_READBACK_PASS',history,len(P),flush=True)
if __name__=='__main__':main()
