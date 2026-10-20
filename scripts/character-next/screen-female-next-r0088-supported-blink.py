"""Bounded actual changed-eye surface sampling after neutral screen success."""
from pathlib import Path
import bpy,json,importlib.util,time,hashlib
R=Path(r'D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0088-lid-aperture'
sp=importlib.util.spec_from_file_location('r88screen',Path(__file__).with_name('verify-female-next-r0088-lid-aperture.py'));k=importlib.util.module_from_spec(sp);sp.loader.exec_module(k)
def main():
 tick=time.time();ref=json.loads((E/'b-build-summary.json').read_text());check=json.loads((E/'b-minimum-source-readback.json').read_text());assert check['candidateContactStatus']=='NO_STRONG_CROSSING_FOUND_STILL_UNACCEPTED';p=Path(ref['output']);assert hashlib.sha256(p.read_bytes()).hexdigest()==ref['outputSha256'];k.prepare(p);rows=[];result={'source':str(p),'sha256':ref['outputSha256'],'status':'RUNNING','poses':rows,'globalSignedMinimumM':None,'scope':'Four additional actual static blink samples of changed skin/lining against all four optical meshes, neutral already recorded. Not finite tissue/lashes/self/containment, exact minimum or continuous time.'}
 for b in (.25,.5,.75,1.):
  k.controls(b);row=k.screen('b-blink-'+str(int(b*100)));row['blinkLeftRight']=b;rows.append(row)
  if row['status']=='FALSIFIED_STRONG_SURFACE_CROSSING':result['status']='FAIL_SAMPLED_BLINK_STOP_EXPANSION';break
 else:result['status']='NO_STRONG_CROSSING_FOUND_IN_FIVE_TESTED_POSES_STILL_UNACCEPTED'
 result['seconds']=time.time()-tick;(E/'b-sampled-blink-contact-screen.json').write_text(json.dumps(result,indent=2)+'\n');print('R88_SAMPLED_BLINK_SCREEN_DONE',result['status'],time.time()-tick,flush=True)
if __name__=='__main__':main()
