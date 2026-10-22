"""Reconstruction of the executed one-time chart coordinate convention fix.
This does not flip physical normals or move any source/target surface vertex.
"""
from pathlib import Path
import numpy as np,json,datetime
E=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158/evidence/character-female-next/r0171-actual-scalp-chart')
def main():
 a=np.load(E/'actual-scalp-chart-construction.npz');d={k:a[k] for k in a.files};d['sourceUV']=d['sourceUV'].copy();d['sourceUV'][:,0]*=-1
 for key in ['source','target']:
  P=d[key+'World'];F=d[key+'Triangles'];U=d[key+'UV'];e=U[F[:,1]]-U[F[:,0]];f=U[F[:,2]]-U[F[:,0]];area=e[:,0]*f[:,1]-e[:,1]*f[:,0];assert (area>1e-12).all() and np.corrcoef(U[:,0],P[:,0])[0,1]>0
 np.savez_compressed(E/'actual-scalp-canonical-charts.npz',**d)
if __name__=='__main__':main()
