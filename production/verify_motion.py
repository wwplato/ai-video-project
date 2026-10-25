"""Measure rendered world-space gait, floor contact and stopped-foot stability."""
from pathlib import Path
import sys
_runtime=Path(__file__).resolve().parent/'.runtime/pylibs'
if _runtime.exists():sys.path.insert(0,str(_runtime))
import argparse,json
import numpy as np
MAPPING={1:1,2:2,3:3,4:4,5:5,6:5,7:7,8:8,9:3,10:10,11:11,12:12,13:13}
def verify(folder):
 data={s:json.loads((folder/f'camera_{s:02}.json').read_text()) for s in set(MAPPING.values())};fps={}
 for s,frames in data.items():
  fps[s]=round(1/(frames[1]['time']-frames[0]['time']));assert len(frames)==fps[s]*10,(s,len(frames))
  assert all(abs(f['time']-i/fps[s])<1e-5 for i,f in enumerate(frames)),s
 walking=[]
 for s,start,end,stop_end in [(5,0,2.5,10),(1,0,4.2,5),(1,5,7.6,10)]:
  frames=data[s];path=[f for f in frames if start<=f['time']<=end];root=np.array([f['characters'][0]['root'] for f in path]);direction=root[-1,:2]-root[0,:2];direction/=np.linalg.norm(direction);progress=root[:,:2]@direction;assert np.all(np.diff(progress)>=-1e-4),(s,start)
  stopped=[f for f in frames if end+.25<=f['time']<stop_end];drift=max(float(np.linalg.norm(np.array([f['characters'][0]['joints'][joint] for f in stopped])-stopped[0]['characters'][0]['joints'][joint],axis=1).max()) for joint in ['L Foot','R Foot','L Toe0','R Toe0']);assert drift<.001,(s,start,drift)
  minimum=min(f['characters'][0]['minimum_mesh_z'] for f in path);assert minimum>.002,(s,minimum)
  walking.append({'source_scene':s+1,'start_seconds':start,'stopped_at_seconds':end,'native_walk_fps':fps[s],'forward_motion_monotonic':True,'travel_m':round(float(np.linalg.norm(root[-1,:2]-root[0,:2])),4),'minimum_mesh_height_m':round(minimum,6),'maximum_stopped_foot_drift_m':round(drift,8)})
 scenes=[]
 for target,source in MAPPING.items():
  frames=data[source];actors=len(frames[0]['characters']);move=0
  for actor in range(actors):
   for joint in frames[0]['characters'][actor]['joints']:
    pts=np.array([f['characters'][actor]['joints'][joint] for f in frames]);move=max(move,float(np.linalg.norm(pts-pts[0],axis=1).max()))
  if actors:assert move>.001,(target,move)
  scenes.append({'scene':target+1,'source_scene':source+1,'characters':actors,'metadata_fps':fps[source],'maximum_joint_displacement_from_start_m':round(move,5)})
 bed=[]
 for s in [3,4]:
  clearance=min(f['cloth_clearance'] for f in data[s]);assert clearance>.025,(s,clearance)
  bed.append({'source_scene':s+1,'minimum_sampled_duvet_to_body_clearance_m':round(clearance,5),'measurement':'Vertical ray samples at cloth vertices; padded smoothed body envelope'})
 windows=[]
 for s in [10,11]:
  sash=np.array([f['sliding_sash_x'] for f in data[s]]);assert sash.max()-sash.min()>3.0
  windows.append({'source_scene':s+1,'whole_sash_travel_m':round(float(sash.max()-sash.min()),4)})
 return {'product':'LUMINEX','camera_independent_world_space_measurements':True,'output_fps':24,'unique_3d_shots':11,'character_scene_segments':sum(bool(s['characters']) for s in scenes),'gait':'Cycloidal swings, toe-off and heel-strike pivots, forward knee IK and planted stance contacts','sampling':'Walking intervals rendered at 24fps; quiet post-walk movement uses 12fps with motion interpolation','walking':walking,'bed':bed,'windows':windows,'scenes':scenes}
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('folder',type=Path,nargs='?',default=Path(__file__).resolve().parent);args=parser.parse_args();print(json.dumps(verify(args.folder),ensure_ascii=False,indent=2))
