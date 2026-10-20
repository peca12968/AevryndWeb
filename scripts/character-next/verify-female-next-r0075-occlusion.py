"""Independent actual-surface falsification before bounded mouth-operation acceptance."""
from pathlib import Path
import bpy,numpy as np,json,time,hashlib,importlib.util,sys
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0075-occlusion-authoring';OLD=E.parent/'r0074-oral-controls'
sp=importlib.util.spec_from_file_location('oral75screen',Path(__file__).with_name('screen-female-next-r0074-oral-contact.py'));screen=importlib.util.module_from_spec(sp);sp.loader.exec_module(screen)
from mathutils.bvhtree import BVHTree
def main():
    baseline='--baseline-r74' in sys.argv;tag='source-r74' if baseline else ('c' if '--candidate-c' in sys.argv else ('b' if '--candidate-b' in sys.argv else 'a'));track='--track-scoped' in sys.argv;tick=time.time();ref=json.loads(((OLD/'c-build-summary.json') if baseline else E/(tag+'-build-summary.json')).read_text());assert hashlib.sha256(Path(ref['output']).read_bytes()).hexdigest()==ref['outputSha256'];bpy.ops.wm.open_mainfile(filepath=ref['output']);s=bpy.context.scene;rows=[];failed=False;mainfailed=False
    charts=json.loads((OLD/'source-oral-uv-islands.json').read_text())[3:];lookup={int(f):i for i,c in enumerate(charts) for f in c['faces']}
    names={'upper':'AFN74_UPPER_TEETH_RIGID','lower':'AFN74_LOWER_TEETH_RIGID','skin':'AFN74_SKIN_AND_EXISTING_OCULAR_LINING','tongue':'AFN74_TONGUE_REGION'}
    for frame in (1,7,13,31,37):
        s.frame_set(frame);bpy.context.view_layer.update();data={k:screen.arrays(bpy.data.objects[names[k]]) for k in ('upper','lower','tongue')};teeth=np.r_[data['upper'][0],data['lower'][0]];data['skin']=screen.arrays(bpy.data.objects[names['skin']],(teeth.min(0)-.002,teeth.max(0)+.002));trees={k:BVHTree.FromPolygons(p.tolist(),t.tolist(),all_triangles=True) for k,(p,t) in data.items()};pairs=[]
        for a,b in (('upper','lower'),('upper','skin'),('lower','skin'),('upper','tongue'),('lower','tongue'),('lower','lower')):
            if a==b and frame!=1:continue
            candidates=trees[a].overlap(trees[b]);witness=None;examined=0
            if a==b:
                d=bpy.data.objects[names[a]].evaluated_get(bpy.context.evaluated_depsgraph_get()).data;d.calc_loop_triangles();fids=np.array([x.value for x in d.attributes['AFN60_NativeFaceID'].data]);owner=np.array([lookup[int(fids[t.polygon_index])] for t in d.loop_triangles])
            for ia,ib in candidates:
                if a==b and (ia>=ib or owner[ia]==owner[ib]):continue
                examined+=1;point=screen.proper_cross(data[a][0][data[a][1][ia]],data[b][0][data[b][1][ib]])
                if point is not None:witness={'triangleA':int(ia),'triangleB':int(ib),'worldPointM':point};failed=True;mainfailed |=a!=b;break
            pairs.append({'pair':[a,b],'broadCandidatePairs':len(candidates),'examinedDifferentToothPairsOrSurfacePairs':examined,'firstStrongProperCrossing':witness,'zeroWitnessIsNotClearanceProof':True});print('R75_SCREEN',frame,a,b,len(candidates),examined,bool(witness),flush=True)
        rows.append({'frame':frame,'jawOpen':bpy.data.objects['AFN74_ORAL_CONTROLS']['jaw_open'],'pairs':pairs})
        if (mainfailed if track else failed):break
    result={'status':'SCOPED_PAIR_SCREEN_NO_NEW_CROSSINGS_DENTAL_SELF_CONTACT_FAILED' if track and failed and not mainfailed else ('FALSIFIED_ACTUAL_SURFACE_CROSSING' if failed else 'NO_STRONG_CROSSING_FOUND_SCOPE_UNACCEPTED'),'source':ref['output'],'sha256':ref['outputSha256'],'rows':rows,'anyDentalContactFailed':failed,'mainCrossBodyPairFailed':mainfailed,'globalSignedMinimumM':None,'continuousAndGumRootAndBodyHairClothNotCertified':True,'seconds':time.time()-tick};(E/(tag+'-actual-contact-screen.json')).write_text(json.dumps(result,indent=2),encoding='utf8');print('R75_ACTUAL_SCREEN_DONE',result['status'],flush=True)
if __name__=='__main__':main()
