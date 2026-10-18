"""Describe owned offline groom arrays with exact inherited skin bindings."""
import json,hashlib,sys
from pathlib import Path
import numpy as np
R=Path(r'D:\Download\Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0017-volume-locks'
VARIANT='c' if '--exact-crown' in sys.argv else 'b' if '--crown-preserve' in sys.argv else 'a'
if VARIANT=='b':E=E/'b-crown-transition'
if VARIANT=='c':E=E/'c-exact-crown-transition'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    build=json.loads((E/'saved-build-verification.json').read_text());surface=json.loads((E/'saved-surface-verification.json').read_text())
    assert surface['status']=='PASS_TESTED_STATIC_SURFACE_SCOPE' and len(surface['poses'])==5
    assert sha(build['output'])==build['outputSha256']==surface['candidateSha256']
    old=json.loads((S/'aevrynd-female-next-r0014-c-groom.authoring.json').read_text())
    # Check every inherited file against the descriptor before reusing bindings.
    for row in old['sourceFiles']:assert sha(S/row['file'])==row['sha256']
    priorG=np.load(S/old['guideData']);priorH=np.load(S/old['renderHairData']);newG=np.load(S/f'aevrynd-female-next-r0017-{VARIANT}-volume-guides.npz');newH=np.load(S/f'aevrynd-female-next-r0017-{VARIANT}-hair-data.npz')
    assert np.array_equal(priorG['guides'][:,0],newG['guides'][:,0])
    assert np.array_equal(priorH['offsets'],newH['offsets']) and np.array_equal(priorH['radii'],newH['radii']) and np.array_equal(priorH['layers'],newH['layers'])
    roots=newH['positions'][newH['offsets'][:-1]];assert np.array_equal(roots,priorH['positions'][priorH['offsets'][:-1]])
    assert len(roots)==21086 and newG['guides'].shape==(424,64,3)
    crownRows=[]
    for label,a,b in (('guides',priorG['guides'],newG['guides']),('children',priorH['positions'],newH['positions'])):
        mask=a[...,2]>=1.515;delta=np.linalg.norm(a[mask].astype(np.float64)-b[mask].astype(np.float64),axis=1)
        crownRows.append({'array':label,'sourceRegion':'source z >= 1.515 m','points':int(mask.sum()),'changedPoints':int(np.count_nonzero(delta)),'maximumDisplacementM':float(delta.max())})
    crownExact=all(row['changedPoints']==0 for row in crownRows)
    if VARIANT=='c':assert crownExact,crownRows
    (E/'crown-invariant-verification.json').write_text(json.dumps({'status':'PASS_EXACT_SOURCE_CROWN' if crownExact else 'FAIL_EXACT_CROWN_INVARIANT','candidate':VARIANT,'sourceSha256':build['outputSha256'],'arrays':crownRows,'scope':'Neutral authoring-array identity to the original r0014 crown region; not a collision or visual realism metric.'},indent=2)+'\n')
    descriptor=dict(old);descriptor.update({'sourceBlender':Path(build['output']).name,'guideData':'aevrynd-female-next-r0017-a-volume-guides.npz','renderHairData':'aevrynd-female-next-r0017-a-hair-data.npz','releaseState':'OFFLINE_STATIC_VOLUME_RESEARCH_ONLY','inheritedObjectIds':'AFN14 object and collection names remain stable; current arrays and descriptor revision are r0017.','masterLockCount':24,'guideMasterAssignmentField':'guideMasterAssignments indexes masterGuideIds in guideData','childMappingScope':'Root/guide IDs and weights are retained. Exact child geometry is renderHairData; root mappings alone do not reconstruct the authored volume deformation.','collisionEnvelopeScope':'Neutral support planes are authoring route guards only. Final saved complete capsules independently checked against actual body and optical/brow/lash surfaces in five static poses. No continuous or self-contact proof.','notImplemented':['Complete-hair dynamics, moving-contact/root-transition solution, self collision, calibrated friction/twist/aerodynamics.','Native runtime importer/renderer/LOD/performance acceptance.'],'runtimePromotionApproved':False})
    descriptor['guideData']=f'aevrynd-female-next-r0017-{VARIANT}-volume-guides.npz';descriptor['renderHairData']=f'aevrynd-female-next-r0017-{VARIANT}-hair-data.npz'
    paths=[S/descriptor[k] for k in ('sourceBlender','guideData','renderHairData','guideBindings','renderHairBindings')]
    descriptor['sourceFiles']=[{'file':p.name,'sha256':sha(p),'bytes':p.stat().st_size} for p in paths]
    descriptor['validation']=dict(old['validation'],guideRootIdentityToValidatedR0014=True,allChildRootsIdentityToValidatedR0014=True,countsRadiiLayersUnchanged=True,rootErrorScope='Reconstruction bounds inherited exactly: body geometry, bind matrices, root positions and root binding files are unchanged. Not a motion proof.')
    dest=S/f'aevrynd-female-next-r0017-{VARIANT}-groom.authoring.json';dest.write_text(json.dumps(descriptor,indent=2)+'\n')
    (E/'authoring-binding-verification.json').write_text(json.dumps({'status':'PASS_EXACT_ROOT_BINDING_INHERITANCE','descriptor':str(dest),'descriptorSha256':sha(dest),'sourceSha256':build['outputSha256'],'guideRootsChecked':424,'childRootsChecked':21086,'allRootArraysBitwiseEqual':True,'radiiOffsetsLayersExact':True,'inheritanceSource':'aevrynd-female-next-r0014-c-groom.authoring.json','scope':'Owned offline neutral authoring arrays and bound-root metadata only; no native runtime or dynamic proof.'},indent=2)+'\n')
    print('R0017_AUTHORING_BINDINGS_PASS')
if __name__=='__main__':main()
