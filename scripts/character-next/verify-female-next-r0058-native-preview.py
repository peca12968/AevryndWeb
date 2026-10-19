"""Independent readback, compare every non-head-hair geometry to r57D."""
from pathlib import Path
import bpy,numpy as np,hashlib,json,importlib.util,time
sp=importlib.util.spec_from_file_location('verify58base',Path(__file__).with_name('build-female-next-r0057-coherent-preview.py'))
k=importlib.util.module_from_spec(sp);sp.loader.exec_module(k)
b=k.b;f=k.f;E=b.R/'Evidence/character-female-next/r0058-source-emitter'
def digest(x):return hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()
def state():
    result={}
    for o in bpy.context.scene.objects:
        if o.type not in ('MESH','CURVES') or o.name in ('AFN57_CANONICAL_BOB_GUIDES','AFN58_NATIVE_SOURCE_BOB_17KEY_GUIDES'):continue
        row={'type':o.type,'matrix':digest(np.array(o.matrix_world)),'materials':[m.name if m else None for m in o.data.materials],'modifiers':[(m.name,m.type,m.show_viewport,m.show_render,m.levels if m.type=='SUBSURF' else None,m.render_levels if m.type=='SUBSURF' else None) for m in o.modifiers]}
        if o.type=='MESH':
            row['positions']=digest(np.array([v.co[:] for v in o.data.vertices],dtype='f4'));row['corners']=digest(np.array([v for p in o.data.polygons for v in p.vertices],dtype='i4'));row['materialsByPolygon']=digest(np.array([p.material_index for p in o.data.polygons],dtype='i4'));row['uv']={u.name:digest(np.array([v.uv[:] for v in u.data],dtype='f4')) for u in o.data.uv_layers};row['keys']={key.name:{'value':key.value,'positions':digest(np.array([v.co[:] for v in key.data],dtype='f4'))} for key in o.data.shape_keys.key_blocks} if o.data.shape_keys else {}
        else:
            row['counts']=digest(np.array([len(c.points) for c in o.data.curves],dtype='i4'));row['positions']=digest(np.array([p.vector[:] for p in o.data.position_data],dtype='f4'));row['radii']=digest(np.array([p.value for p in o.data.attributes['radius'].data],dtype='f4'))
        result[o.name]=row
    return result
def main():
    tick=time.time();a=json.loads((E/'a-build-summary.json').read_text());source=Path(a['source']);out=Path(a['output']);assert b.sha(source)==a['sourceSha256'] and b.sha(out)==a['outputSha256']
    bpy.ops.wm.open_mainfile(filepath=str(source));original=state();stage=f.v.stage()
    bpy.ops.wm.open_mainfile(filepath=str(out));assert state()==original;assert f.v.stage()==stage
    raw=np.load(E/'a-native-guide-data.npz');hair=bpy.data.objects['AFN58_NATIVE_SOURCE_BOB_17KEY_GUIDES'];P,R=f.v.hair_arrays(hair);assert np.array_equal(P,raw['positions']) and np.array_equal(R,raw['radii']) and np.array_equal(np.array(hair.matrix_world),raw['matrix'])
    assert np.isfinite(P).all() and (R>0).all() and P.shape==(248,17,3)
    images=[]
    for im in bpy.data.images:
        if im.source not in ('FILE','TILED'):continue
        path=Path(bpy.path.abspath(im.filepath));assert im.source=='FILE' and im.filepath.startswith('//') and path.exists();images.append({'relativePath':im.filepath,'sha256':b.sha(path)})
    assert len(images)==15 and not bpy.data.libraries
    x={'source':str(out),'sourceSha256':b.sha(out),'reopened':True,'allNonHeadHairMeshShapeKeysUVMaterialAssignmentCurvesAndStageExactToR57D':True,'headHairNativePositionsRadiiMatrixExact':True,'headHairGuides':248,'pointsPerGuide':17,'sourceNativeRootIncluded':True,'relativeResourceImages':images,'capsuleScope':'Exact saved curve/body data match already tested a-build-summary; no redundant rerun. All finite POLY capsules vs actual render-level body, neutral only, still190unqualified.','notTested':'Hair self, facial-hair/tissue, full body self, dynamic sweeps and actual engine','seconds':time.time()-tick}
    (E/'a-reopened-verification.json').write_text(json.dumps(x,indent=2)+'\n',encoding='utf8');print('R58_REOPENED_NONHAIR_EXACT',len(original),P.shape,len(images),time.time()-tick,flush=True)
if __name__=='__main__':main()
