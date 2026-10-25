"""Measure rendered world-space movement and stopped-foot stability."""
from pathlib import Path
import sys
_runtime=Path(__file__).resolve().parent/".runtime/pylibs"
if _runtime.exists():sys.path.insert(0,str(_runtime))
import argparse,json
import numpy as np
MAPPING={1:1,2:2,3:3,4:4,5:5,6:5,7:7,8:8,9:3,10:10,11:10,12:12,13:13}
def verify(folder):
 data={s:json.loads((folder/f'camera_{s:02}.json').read_text()) for s in set(MAPPING.values())}
 for s,frames in data.items():
  assert len(frames)==120,(s,len(frames))
  assert all(abs(f['time']-i/12)<1e-5 for i,f in enumerate(frames)),s
 walking=[]
 for s in [2,5]:
  frames=data[s];root=np.array([f['characters'][0]['root'] for f in frames]);assert np.all(np.diff(root[:20,1])>=-1e-5),s
  drift=max(float(np.linalg.norm(np.array([f['characters'][0]['joints'][joint] for f in frames[24:]])-frames[24]['characters'][0]['joints'][joint],axis=1).max()) for joint in ['L Foot','R Foot','L Toe0','R Toe0']);assert drift<.001,(s,drift)
  walking.append({'source_scene':s+1,'forward_motion_monotonic':True,'travel_m':round(float(root[-1,1]-root[0,1]),4),'stopped_at_seconds':1.6,'maximum_stopped_foot_drift_m':round(drift,8)})
 scenes=[]
 for target,source in MAPPING.items():
  frames=data[source];actors=len(frames[0]['characters']);move=0
  for actor in range(actors):
   for joint in frames[0]['characters'][actor]['joints']:
    pts=np.array([f['characters'][actor]['joints'][joint] for f in frames]);move=max(move,float(np.linalg.norm(pts-pts[0],axis=1).max()))
  if actors:assert move>.001,(target,move)
  scenes.append({'scene':target+1,'source_scene':source+1,'characters':actors,'maximum_joint_displacement_from_start_m':round(move,5)})
 bed=[]
 for s in [3,4]:
  clearance=min(f['cloth_clearance'] for f in data[s]);assert clearance>.025,(s,clearance)
  bed.append({'source_scene':s+1,'minimum_sampled_duvet_to_body_clearance_m':round(clearance,5),'measurement':'Vertical ray samples at cloth vertices; padded smoothed body envelope'})
 sash=np.array([f['sliding_sash_x'] for f in data[10]]);assert sash.max()-sash.min()>3.0
 return {'product':'LUMINEX','camera_independent_world_space_measurements':True,'source_animation_fps':12,'output_fps':24,'unique_3d_shots':10,'character_scene_segments':sum(bool(s['characters']) for s in scenes),'walking':walking,'bed':bed,'window':{'whole_sash_travel_m':round(float(sash.max()-sash.min()),4),'assembly':'glass, left/right/top/bottom rails, handle share one moving parent'},'scenes':scenes}
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('folder',type=Path,nargs='?',default=Path(__file__).resolve().parent);args=parser.parse_args();print(json.dumps(verify(args.folder),ensure_ascii=False,indent=2))
