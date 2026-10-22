"""Minimum actual first-failure reproduction; no source change or tolerance rescue."""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,time
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0144-current-skin-blink'
def module(n,name):
    sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(name));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
h=module('r144witnessbase','build-female-next-r0144-current-skin-blink.py');a=h.a;sockets=module('r144independentedge','build-female-next-r0138-native-sockets.py')
def main():
    tick=time.time();b=json.loads((E/'a-build-summary.json').read_text('utf-8'));contact=json.loads((E/'actual-blink-ocular-surface-contact.json').read_text('utf-8'));fail=contact['firstRelatedFailure'];src=Path(b['output']);assert a.a.sha(src)==b['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(src));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update();skin=bpy.data.objects[h.h.SKIN];rest,_=a.geometry(skin);cutters={}
    for side in ['L','R']:
        ob=bpy.data.objects['AFN138_'+side+'_ANATOMICAL_SOCKET_CONSTRUCTION'];W,T=a.geometry(ob);cutters[side]=BVHTree.FromPolygons([Vector(p) for p in W],T.tolist(),all_triangles=True)
    scene.frame_set(fail['frame']);bpy.context.view_layer.update();W,T=a.geometry(skin);V,F=a.geometry(bpy.data.objects[fail['object']]);assert a.a.hasharray(W)==fail['actualSkinWorldHash'] and a.a.hasharray(V)==fail['actualEyeWorldHash']
    rows=[]
    for si,ei in fail['firstProperSkinEyeFacePairs']:
        ids=T[si];side='L' if W[ids,0].mean()>0 else 'R';hits=sockets.witness(W[ids],V[F[ei]]);assert len(hits)>=2
        rows.append({'skinFace':si,'eyeFace':ei,'skinVertexIds':ids,'side':side,'actualSkinTriangleWorld':W[ids],'actualOpticalTriangleWorld':V[F[ei]],'independentFiniteEdgeFaceWitnesses':hits,'restSkinTriangleWorld':rest[ids],'actualSkinVertexMovementM':np.linalg.norm(W[ids]-rest[ids],axis=1),'originalSkinAngularFieldRadians':{s:[float(skin.data.attributes['AFN144_Angle_'+s].data[int(i)].value) for i in ids] for s in ['L','R']},'restPointDistanceToOriginalCavityConstructionSurfaceM':[float(cutters[side].find_nearest(Vector(rest[i]))[3]) for i in ids]})
    h.save('first-blink-failure-independent-witness.json',{'source':str(src),'sha256':b['sha256'],'frame':fail['frame'],'actualBlinkControls':fail['actualControls'],'object':fail['object'],'properSATPairs':fail['properTriangleSurfaceCrossingPairs'],'independentFiniteEdgeFaceCorroboratedPairs':len(rows),'rows':rows,'predicateUnchangedM':1e-12,'signedPenetrationDepthNotMeasured':True,'finiteThicknessRenderAlphaOrWholeCharacterContactNotInferred':True,'noGeometryOrRangeOrMaterialsChanged':True,'secondsBeforePreview':time.time()-tick})
    h.save('first-failure-face-view-control.json',a.b.u.v.image('first-failure-blink-f007','face'));scene.frame_set(1);bpy.context.view_layer.update();assert a.a.sha(src)==b['sha256'];print('R144_FIRST_FAILURE_INDEPENDENT_FINITE_EDGES_REPRODUCED',len(rows),time.time()-tick,flush=True)
if __name__=='__main__':main()
