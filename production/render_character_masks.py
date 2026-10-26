"""Render foreground occlusion at the original shot rate without re-rendering beauty."""
from pathlib import Path
import sys,argparse,bpy,json,os
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));from scene import Set
p=argparse.ArgumentParser();p.add_argument('--scene',type=int,required=True);p.add_argument('--sample',type=int);p.add_argument('--static-room',action='store_true');a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);w=Set(a.scene);s=bpy.context.scene;fps=24 if a.scene==5 else 6 if a.scene==8 else 12
s.render.engine='BLENDER_WORKBENCH';s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='BW';s.render.image_settings.color_depth='8';s.render.resolution_x=1280;s.render.resolution_y=720;s.render.film_transparent=False;s.render.threads=1;s.display.shading.light='FLAT';s.display.shading.color_type='OBJECT';s.display.shading.show_shadows=False;s.display.shading.show_cavity=False;s.display.shading.show_specular_highlight=False;s.display.shading.show_object_outline=False;s.display.shading.background_type='WORLD';s.world.color=(0,0,0);s.view_settings.view_transform='Standard';s.view_settings.look='None';s.display.render_aa='8'
actors={o for actor in w.people for o in actor.meshes}
for o in bpy.data.objects:
 background=o in getattr(w,'exterior_objects',[]) or o==getattr(w,'panorama',None) or o==getattr(w,'blackout',None) or o.name.startswith(('Actual glass','Second low E'))
 o.color=(0,0,0,1) if background else (1,1,1,1)
 if a.static_room and o in actors:o.hide_render=True
out=P/'character_masks'/f'{a.scene:02}';out.mkdir(parents=True,exist_ok=True)
for k in range(fps*10):
 s.frame_set(k+1);w.update((k%47)/fps if a.scene==3 else k/fps);bpy.context.view_layer.update()
 if a.scene==7 and k>=fps*5 and a.sample is None:continue
 if a.sample is not None and k!=a.sample:continue
 if not a.static_room and (out/f'{k+1:04}.png').exists():continue
 target=P/f'room_mask_{a.scene:02}.png' if a.static_room else out/f'{k+1:04}.png';temp=target.with_name(f'.{target.stem}.{os.getpid()}.png');s.render.filepath=str(temp);bpy.ops.render.render(write_still=True);os.replace(temp,target)
 if k%24==0:print('MASK_READY',a.scene,k+1,flush=True)
 if a.sample is not None:break
print('CHARACTER_MASKS_DONE',a.scene,flush=True)
