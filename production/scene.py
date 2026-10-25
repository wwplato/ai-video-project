"""LUMINEX: textured rigged characters, retargeted motion, PBR interiors."""
import bpy,math,sys,argparse,json,gzip,random,time
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix,Euler
from bpy_extras.object_utils import world_to_camera_view
P=Path(__file__).resolve().parent
ASSET=Path('/workspace/ai-video-project/production/assets') if str(P).startswith('/workspace/work') else P/'assets'
TEXTURES=ASSET.parent/'textures'
with gzip.open(ASSET/'motion.json.gz','rt') as f:MOTION=json.load(f)
def ease(x):x=max(0,min(1,x));return x*x*(3-2*x)
def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
def mat(n,c,rough=.5,metal=0):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.use_nodes=True;s=m.node_tree.nodes.get('Principled BSDF');s.inputs['Base Color'].default_value=(*c,1);s.inputs['Roughness'].default_value=rough;s.inputs['Metallic'].default_value=metal;return m
def cube(n,p,sz,m,b=.02):
 bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.name=n;o.scale=sz;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m)
 if b:z=o.modifiers.new('Crafted edges','BEVEL');z.width=b;z.segments=3;o.modifiers.new('Normals','WEIGHTED_NORMAL')
 return o
def sphere(n,p,sz,m):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,location=p);o=bpy.context.object;o.name=n;o.scale=sz;o.data.materials.append(m)
 for f in o.data.polygons:f.use_smooth=True
 return o
def cyl(n,p,r,d,m):
 bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=r,depth=d,location=p);o=bpy.context.object;o.name=n;o.data.materials.append(m);z=o.modifiers.new('Edge finish','BEVEL');z.width=.008;z.segments=2
 for f in o.data.polygons:f.use_smooth=True
 return o
def textured(n,path,emission=False,alpha=False):
 m=mat(n,(1,1,1));nodes=m.node_tree.nodes;links=m.node_tree.links;tex=nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(path),check_existing=True)
 if emission:
  nodes.remove(nodes.get('Principled BSDF'));shader=nodes.new('ShaderNodeEmission');shader.inputs['Strength'].default_value=.8;links.new(tex.outputs['Color'],shader.inputs['Color']);links.new(shader.outputs[0],nodes.get('Material Output').inputs['Surface'])
 else:links.new(tex.outputs['Color'],nodes.get('Principled BSDF').inputs['Base Color'])
 return m
class Character:
 def __init__(self,name,scale=1):
  with bpy.data.libraries.load(str(ASSET/(name+'.blend')),link=False) as (src,dst):dst.objects=src.objects
  objects=[o for o in dst.objects if o]
  for o in objects:bpy.context.collection.objects.link(o)
  self.rig=next(o for o in objects if o.type=='ARMATURE');self.rig.name=name+' rig';self.root=bpy.data.objects.new(name+' motion control',None);bpy.context.collection.objects.link(self.root)
  self.rig.parent=self.root;self.hip=self.rig.location.z;self.inv=self.rig.rotation_euler.to_quaternion().inverted();self.rig.location=(0,0,0);self.root.scale=(scale,)*3;self.factor=scale
  self.rest={};self.parent={}
  # Normalize the child rig's Biped prefix to the common animation skeleton.
  for b in self.rig.data.bones:
   if b.name.startswith('Bip02'):b.name=b.name.replace('Bip02','Bip01',1)
  for b in self.rig.pose.bones:
   q=b.bone.matrix_local.to_quaternion();p=b.parent
   self.rest[b.name]=(p.bone.matrix_local.to_quaternion().inverted()@q).inverted() if p else q.inverted();self.parent[b.name]=p.name if p else None;b.rotation_mode='QUATERNION'
  self.last=None
 def sample(self,clip,t,loop=True):
  a=MOTION[clip];frames=a['frames'];at=t*a['fps'];at=at%(len(frames)-1) if loop else min(max(0,at),len(frames)-1);i=int(at);j=min(i+1,len(frames)-1);x=at-i;f=frames[i];g=frames[j]
  return f[0]*(1-x)+g[0]*x,{n:Quaternion(f[k+1]).slerp(Quaternion(g[k+1]),x) for k,n in enumerate(a['bones'])}
 def pose(self,clip,t,pos=(.6,.6,0),yaw=0,pitch=0,blend=None,pelvis=None,loop=True):
  h,quats=self.sample(clip,t,loop)
  if blend:
   h2,q2=self.sample(blend[0],blend[1],blend[3] if len(blend)>3 else True);w=blend[2];h=h*(1-w)+h2*w
   quats={n:q.slerp(q2.get(n,q),w) for n,q in quats.items()}
  desired={};ident=Quaternion()
  for pb in self.rig.pose.bones:
   if pb.name not in quats:continue
   q=self.inv@quats[pb.name];desired[pb.name]=q;p=self.parent[pb.name];par=desired.get(p,ident)
   pb.rotation_quaternion=self.rest[pb.name]@par.inverted()@q
  self.root.location=(pos[0],pos[1],(h*self.hip/.914 if pelvis is None else pelvis)+pos[2]);self.root.rotation_euler=(pitch,0,yaw)
  self.last=(clip,t);bpy.context.view_layer.update()
 def joint(self,name):return self.rig.matrix_world@self.rig.pose.bones['Bip01 '+name].head
 def head_turn(self,angle):
  p=self.rig.pose.bones['Bip01 Head'];p.rotation_quaternion=p.rotation_quaternion@Quaternion((1,0,0),angle);bpy.context.view_layer.update()
 def reach(self,side,target,weight=1):
  rig=self.rig;u=rig.pose.bones['Bip01 '+side+' UpperArm'];l=rig.pose.bones['Bip01 '+side+' Forearm'];hand=rig.pose.bones['Bip01 '+side+' Hand'];dest=rig.matrix_world.inverted()@Vector(target);dest=hand.head.lerp(dest,weight);s=u.head.copy();e=l.head.copy();h=hand.head.copy();a=(e-s).length;b=(h-e).length;v=dest-s;dist=min(v.length,a+b-.01);axis=v.normalized();bend=e-s-axis*(e-s).dot(axis)
  if bend.length<.01:bend=Vector((0,0,-1))
  bend.normalize();along=(a*a-b*b+dist*dist)/(2*max(.01,dist));elbow=s+axis*along+bend*math.sqrt(max(.001,a*a-along*along));q=(e-s).rotation_difference(elbow-s)@u.matrix.to_quaternion();u.matrix=Matrix.LocRotScale(s,q,Vector((1,1,1)));bpy.context.view_layer.update()
  e=l.head.copy();h=hand.head.copy();q=(h-e).rotation_difference(dest-e)@l.matrix.to_quaternion();l.matrix=Matrix.LocRotScale(e,q,Vector((1,1,1)));bpy.context.view_layer.update()
 def telemetry(self):return {n:[round(x,4) for x in self.joint(n)] for n in ['Head','L Hand','R Hand','L Foot','R Foot']}
class Set:
 def __init__(self,i):
  self.i=i;bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);self.people=[];self.plants=[];self.rain=[]
  self.ivory=mat('Lime plaster',(.75,.72,.66),.9);self.oak=mat('Natural oak',(.38,.24,.13),.48);self.metal=mat('Brushed titanium',(.11,.15,.16),.25,.75);self.bronze=mat('Champagne anodized metal',(.42,.28,.12),.3,.65);self.black=mat('Blackout laminate',(.002,.004,.007),.8);self.cloth=mat('Woven linen',(.59,.64,.61),.95)
  # Fine timber grain, pores and a subtle textile weave.
  n=self.oak.node_tree.nodes;links=self.oak.node_tree.links;coord=n.new('ShaderNodeTexCoord');mapping=n.new('ShaderNodeVectorMath');mapping.operation='MULTIPLY';mapping.inputs[1].default_value=(3,120,6);links.new(coord.outputs['Generated'],mapping.inputs[0]);noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=3;noise.inputs['Detail'].default_value=3;links.new(mapping.outputs[0],noise.inputs['Vector']);r=n.new('ShaderNodeValToRGB');r.color_ramp.elements[0].color=(.14,.078,.034,1);r.color_ramp.elements[1].color=(.42,.29,.16,1);links.new(noise.outputs['Fac'],r.inputs[0]);links.new(r.outputs[0],n.get('Principled BSDF').inputs['Base Color']);bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.13;bump.inputs['Distance'].default_value=.015;links.new(noise.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs[0],n.get('Principled BSDF').inputs['Normal'])
  # A photographed wood texture gives the floor fine natural grain.
  tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(ASSET/'Image_3.png'));mapping.inputs[1].default_value=(12,4,1);links.new(mapping.outputs[0],tex.inputs['Vector']);links.new(tex.outputs['Color'],r.inputs[0]);links.new(tex.outputs['Color'],bump.inputs['Height'])
  self.room();self.window();self.lights();self.actors();self.camera();self.render()
 def imported(self,file,pos,yaw=0,scale=1):
  before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(ASSET/file));objects=list(set(bpy.data.objects)-before);root=bpy.data.objects.new(file+' placement',None);bpy.context.collection.objects.link(root)
  for o in objects:
   if o.parent not in objects:o.parent=root
  for o in objects:
   if o.type=='LIGHT':bpy.data.objects.remove(o,do_unlink=True)
  root.location=pos;root.rotation_euler.z=yaw;root.scale=(scale,)*3;return root
 def room(self):
  i=self.i;cube('Oak floor',(0,0,-.09),(9,9,.18),self.oak)
  for x in range(29):cube('Oak plank seam',(-4.2+x*.30,0,.002),(.002,8.8,.002),self.bronze,0)
  cube('Architectural plaster wall',(-3.4,.5,1.8),(.17,6,3.6),self.ivory)
  cube('Stone window ledge',(-.25,2.12,.10),(6.4,.32,.2),self.ivory)
  self.imported('GlamVelvetSofa.glb',(-2.35,-.2,0),math.pi/2,.9)
  rug=mat('Boucle rug',(.65,.64,.58),.98);cube('Wool area rug',(.0,-.35,.013),(3.7,2.7,.022),rug,.05)
  cyl('Travertine side table',(-1.9,1.05,.38),.33,.72,self.ivory);cyl('Table brass rim',(-1.9,1.05,.755),.35,.02,self.bronze)
  self.imported('IridescenceLamp.glb',(-1.9,1.05,.77),0,1.2)
  cyl('Stone pedestal',(2.25,1.1,.42),.26,.84,self.ivory);self.imported('IridescenceLamp.glb',(2.25,1.1,.85),0,.95)
  if i in [3,4,9]:self.bed()
  if i in [8,13]:self.imported('SheenChair.glb',(.45,.32,0),0,1)
  if i==12:
   cube('School worktop',(.4,-.8,.79),(2.2,.85,.055),self.oak,.025)
   for x in [-.55,1.35]:cube('Desk titanium support',(x,-.8,.39),(.045,.65,.78),self.metal)
   for j in range(3):cube('Notebooks',(-.35,-.75,.84+j*.025),(.34,.25,.024),self.cloth,.007)
  if i==13:
   self.blocks=[cube('Child play block',(-.8+j*.19,-.65,.07),(.13,.13,.13),mat('Toy color'+str(j),c),.015) for j,c in enumerate([(.12,.38,.36),(.68,.39,.12),(.52,.18,.14)])]
 def plant(self,pos,h):
  x,y,z=pos;cyl('Ceramic planter',(x,y,.2*h),.22*h,.4*h,self.ivory);stem=mat('Plant stem',(.15,.22,.075),.8);leaf=mat('Leaf wax',(.12,.25,.11),.36)
  for j in range(13):
   a=j*2.399;zz=.45*h+j*.07*h;r=.26*h;end=Vector((x+math.cos(a)*r,y+math.sin(a)*r,zz+.14*h));start=Vector((x,y,.25*h));d=end-start;o=cyl('Branch',(start+end)/2,.009*h,d.length,stem);o.rotation_euler=d.to_track_quat('Z','Y').to_euler()
   o=sphere('Ficus leaf',end,(.11*h,.23*h,.012*h),leaf);o.rotation_euler=(.35*math.cos(a),.3*math.sin(a),a);self.plants.append((o,o.rotation_euler.copy(),j))
 def backdrop(self):
  name='city.png';path=ASSET/name
  bpy.ops.mesh.primitive_plane_add(size=2,location=(-.3,2.8,1.9),rotation=(math.pi/2,0,0));o=bpy.context.object;o.name='Pohang 2035 scenic backdrop';o.scale=(5.5,3.1,1);m=textured('Coastal panorama',path,True);o.data.materials.append(m);self.panorama=o;self.panorama_shader=next(n for n in m.node_tree.nodes if n.type=='EMISSION')
 def window(self):
  self.backdrop();i=self.i
  for x in [-3.3,2.9]:cube('Slim titanium jamb',(x,2.07,1.8),(.065,.10,3.4),self.metal,.009)
  for z in [.13,3.48]:cube('Slim window track',(-.2,2.07,z),(6.25,.1,.055),self.metal,.009)
  self.sash=cube('Animated sliding mullion',(-.2,2.02,1.8),(.045,.08,3.3),self.metal,.008)
  self.blackout=cube('Electrochromic blackout',(-.2,2.14,1.8),(6.12,.025,3.28),self.black,.005);self.blackout.hide_render=True
  self.frost=cube('Privacy diffuse membrane',(-.2,2.12,1.8),(6.12,.02,3.28),mat('Milky smart glass',(.31,.43,.46),.75),.004);self.frost.hide_render=True
  self.latch=cube('Safety motor latch',(2.78,1.98,1.45),(.10,.09,.22),self.bronze,.018);self.latch.hide_render=i!=11
  tex={1:'weather',2:'weather',3:'alarm',4:'weather',5:'weather',6:'schedule',7:'privacy',8:'frost',9:'blackout',10:'weather',11:'warning',12:'phone',13:'energy'}.get(i,'weather')
  self.panel=self.screen(tex,(-1.25,1.96,2.0),(1.8,1.285));self.panel.hide_render=i in [1,9]
  self.ring=cyl('Touch feedback',(.55,1.94,1.55),.055,.006,self.bronze);self.ring.rotation_euler.x=math.pi/2;self.ring.hide_render=True
  if i in [1,11]:
   material=mat('Rain highlights',(.42,.64,.75),.17)
   rng=random.Random(23)
   for j in range(55):
    o=cyl('Animated rain streak',(0,0,0),.002,rng.uniform(.10,.18),material);self.rain.append((o,rng.uniform(-3.15,2.75),rng.uniform(.2,3.3)))
 def screen(self,name,pos,size):
  w,h=size;me=bpy.data.meshes.new('Display surface');me.from_pydata([(-w/2,0,-h/2),(w/2,0,-h/2),(w/2,0,h/2),(-w/2,0,h/2)],[],[(0,1,2,3)]);me.update();o=bpy.data.objects.new('LUMINEX '+name+' display',me);bpy.context.collection.objects.link(o);o.location=pos;uv=me.uv_layers.new()
  for loop,co in zip(me.loops,[(0,0),(1,0),(1,1),(0,1)]):uv.data[loop.index].uv=co
  o.data.materials.append(textured('LUMINEX UI '+name,TEXTURES/(name+'.png'),True));return o
 def bed(self):
  cube('Upholstered bed frame',(.3,.18,.30),(1.65,2.5,.45),self.cloth,.12);cube('Linen mattress',(.3,.18,.55),(1.62,2.40,.25),self.ivory,.12);cube('Linen headboard',(.3,1.47,.85),(1.85,.16,1.25),self.cloth,.1)
  sphere('Soft linen pillow',(.3,1.05,.76),(.65,.32,.105),self.ivory)
  verts=[];faces=[]
  for j in range(25):
   for k in range(23):
    x=-.52+k*.075;y=-1.0+j*.066;z=.76+.15*math.exp(-((x-.3)/.45)**2)+.016*math.sin(j*.65+k*.8);verts.append((x,y,z))
  for j in range(24):
   for k in range(22):a=j*23+k;faces.append((a,a+1,a+24,a+23))
  me=bpy.data.meshes.new('Duvet cloth');me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new('Breathing linen duvet',me);bpy.context.collection.objects.link(o);o.data.materials.append(self.cloth)
  for f in me.polygons:f.use_smooth=True
  self.duvet=o;self.duvet_base=verts
 def lights(self):
  self.lightobjects=[]
  for loc,energy,color,size in [((0,1.8,3.2),320,(.87,.94,1),5),((1,-3,2.7),170,(1,.88,.72),4)]:
   bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=energy;o.data.color=color;o.data.size=size;o.data.use_shadow=False;aim(o,(0,.3,1));self.lightobjects.append(o)
  bpy.ops.object.light_add(type='SUN',rotation=(math.radians(62),.2,.15));o=bpy.context.object;o.data.energy=.65;o.data.angle=0;o.data.use_shadow_jitter=False;o.data.color=(1,.91,.79);self.sun=o
 def actors(self):
  i=self.i
  if i in [0,14]:return
  name='Male_Adult_09' if i in [5,6,12] else 'Female_Adult_08';self.actor=Character(name);self.people=[self.actor]
  if i==13:
   # Replace the resident with an elderly man and a child.
   old=[o for o in bpy.data.objects if o==self.actor.root or o==self.actor.rig or o.parent==self.actor.rig]
   for o in old:bpy.data.objects.remove(o,do_unlink=True)
   self.actor=Character('Male_Adult_03');self.child=Character('Male_Child_01',.8);self.people=[self.actor,self.child]
  if i==12:
   self.phone=cube('Phone metal body',(0,0,0),(.075,.014,.15),self.metal,.009);self.phone_screen=self.screen('phone',(0,0,0),(.067,.135))
 def camera(self):
  bpy.ops.object.camera_add();self.cam=bpy.context.object;self.cam.data.lens=40;bpy.context.scene.camera=self.cam
  if self.i in [3,4,9]:self.cam.location=(3.4,-4.9,2.7);self.target=(.15,.65,1.1);self.cam.data.lens=37
  elif self.i==12:self.cam.location=(2.5,-3.1,2.1);self.target=(.25,.0,1.0);self.cam.data.lens=47
  elif self.i==13:self.cam.location=(3.2,-5.1,2.3);self.target=(.0,.4,1.0);self.cam.data.lens=40
  else:self.cam.location=(4.05,-5.8,2.65);self.target=(-.3,.65,1.5);self.cam.data.lens=39
  self.camera_base=self.cam.location.copy();aim(self.cam,self.target)
 def render(self):
  s=bpy.context.scene;s.render.engine='BLENDER_EEVEE_NEXT';s.eevee.taa_render_samples=2;s.eevee.use_raytracing=False;s.eevee.shadow_ray_count=1;s.eevee.shadow_step_count=2;s.eevee.shadow_pool_size='256';s.render.resolution_x=1280;s.render.resolution_y=720;s.render.resolution_percentage=100;s.render.fps=12;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.render.image_settings.compression=0;s.render.threads_mode='FIXED';s.render.threads=1;s.render.use_persistent_data=True;s.world.color=(.22,.27,.30);s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast'
 def update(self,t):
  i=self.i
  # Slow camera travel accompanies articulated animation, rather than replacing it.
  self.cam.location=self.camera_base+Vector((-.025*t,.018*t,0));aim(self.cam,self.target)
  for o,rot,j in self.plants:o.rotation_euler=Vector(rot)+Vector((.015*math.sin(t*1.2+j),.018*math.cos(t*.8+j),0))
  for o,x,z in self.rain:o.hide_render=not(i in [1,11] or (i==10 and t>4));o.location=(x,2.0,.2+(z-t*1.7)%3.1);o.rotation_euler.y=.12
  storm=i in [1,11];self.panorama_shader.inputs['Strength'].default_value=.25 if storm else (.48 if i==8 else .8)
  self.blackout.hide_render=not(i in [3,9] or (i==4 and t<2.0));self.frost.hide_render=not(i==8 and t>3)
  if not self.blackout.hide_render:
   for o in self.lightobjects:o.data.energy=30 if i==9 else 55
   self.sun.data.energy=.02
  else:
   for j,o in enumerate(self.lightobjects):o.data.energy=[320,170][j]
   self.sun.data.energy=.4 if storm else .65
  opened=0
  if i==4:opened=ease((t-3)/2)
  elif i==10:opened=1-ease((t-4)/.7)
  elif i==11:opened=1-ease(t/.8)
  self.sash.location.x=-.2+opened*1.4
  self.panel.hide_render=i in [1,9] or (i==2 and t<.6)
  self.ring.hide_render=not(i in [2,5,6] and 3.8<t<7.6)
  if i in [0,14]:return
  a=self.actor;pos=(.60,.55,0);yaw=0
  if i==1:
   w=ease(t/5);a.pose('f_walk_neutral',t,pos=(.6-1.5*w,.5-1.7*w,0),yaw=-.65)
  elif i in [2,5,6]:
   walk=1-ease((t-1.6)/1.0);w=ease(t/2.6);a.pose('f_walk_neutral',t,pos=(.70,.05+.85*w,0),yaw=math.pi-.35,blend=('f_idle_breathe_01',t,1-walk))
   reach=ease((t-3.0)/1.1)*(1-ease((t-7.2)/1.1));a.reach('L',(.52,1.88,1.53),reach);a.head_turn(.05*math.sin(t))
  elif i in [3,9]:
   a.pose('f_idle_breathe_01',t,pos=(.3,.40,0),yaw=0,pitch=-math.pi/2,pelvis=.81);a.head_turn(.025*math.sin(t*.5))
   for k,v in enumerate(self.duvet.data.vertices):x,y,z=self.duvet_base[k];v.co.z=z+.008*math.sin(t*1.7)*math.exp(-((y-.1)/.5)**2)
  elif i==4:
   w=ease((t-1.0)/3.8);a.pose('f_idle_breathe_01',t,pos=(.3,.4,0),pitch=-math.pi/2*(1-w),pelvis=.81-.10*w,blend=('f_sit_chair_breathe_01',t,w));a.head_turn(.04*math.sin(t*.6))
  elif i==8:
   a.pose('f_sit_chair_breathe_01',t,pos=(.45,.32,-.06),yaw=0);a.head_turn(.08*math.sin(t*.65))
  elif i==12:
   a.pose('m_cell_phone_textmessage',6+t,pos=(.2,.2,0),yaw=-.2);a.head_turn(.02*math.sin(t))
   p=a.joint('R Hand');self.phone.location=p+Vector((0,-.03,.025));self.phone.rotation_euler=(math.pi/2+.4,0,-.2);self.phone_screen.location=self.phone.location+Vector((0,-.010,.018));self.phone_screen.rotation_euler=self.phone.rotation_euler
  elif i==13:
   a.pose('m_sit_chair_breathe_01',t,pos=(.45,.32,-.02));a.head_turn(-.13+.05*math.sin(t))
   w=ease(t/2.5);crouch=ease((t-2.6)/1.1)*(1-ease((t-8.7)/1.2));self.child.pose('f_walk_neutral',t,pos=(-.65,.55-.85*w,0),yaw=0,blend=('f_crouch_idle',t,crouch))
   # Ease from walking to the crouched play pose, then raise and stack a block.
   if t>2.5:self.child.pose('f_idle_breathe_01',t,pos=(-.65,-.30,0),blend=('f_crouch_idle',t,crouch))
   lift=ease((t-4.6)/1.2);lower=ease((t-6.3)/1.1);target=Vector((-.80+.19*lift,-.65,.16+.22*lift-.10*lower));reach=ease((t-3.3)/.9)*(1-ease((t-7.8)/.8));self.child.reach('R',target,reach)
   if 4.25<t<7.8:self.blocks[0].location=self.child.joint('R Hand')+Vector((0,0,-.07))
   elif t>=7.8:self.blocks[0].location=(-.61,-.65,.20)
  else:
   a.pose('f_idle_breathe_01',t,pos=pos,yaw=.15 if i==7 else 2.65);a.head_turn(.10*math.sin(t*.55))
   if i in [10,11]:a.reach('L',(.45,1.82,1.45),.35*ease((t-5)/1.5))
  if i==11:self.latch.location.z=1.45-.05*ease((t-.8)/.4)

def main():
 p=argparse.ArgumentParser();p.add_argument('--scene',type=int,default=5);p.add_argument('--frames',type=int,default=120);p.add_argument('--width',type=int,default=1280);p.add_argument('--sample',type=int);p.add_argument('--fps',type=int,default=12);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);world=Set(a.scene);s=bpy.context.scene;s.render.resolution_x=a.width;s.render.resolution_y=round(a.width*9/16);s.render.fps=a.fps;out=P/'frames'/f'{a.scene:02}';out.mkdir(parents=True,exist_ok=True)
 if a.sample is not None:
  world.update(a.sample/a.fps);s.render.filepath=str(P/f'sample_{a.scene:02}_{a.sample}.png');bpy.ops.render.render(write_still=True);return
 telemetry=[];projection=[]
 def update(scene):
  t=(scene.frame_current-1)/a.fps;world.update(t)
  corners=[world_to_camera_view(scene,world.cam,world.panel.matrix_world@v.co) for v in world.panel.data.vertices]
  projection.append([[float(v.x),float(1-v.y)] for v in corners])
  if scene.frame_current in [1,13,37,61,85,109]:telemetry.append({'time':t,'characters':[c.telemetry() for c in world.people]})
 bpy.app.handlers.frame_change_pre.clear();bpy.app.handlers.frame_change_pre.append(update);s.frame_start=1;s.frame_end=a.frames;s.render.filepath=str(out)+'/';bpy.ops.render.render(animation=True);(P/f'motion_{a.scene:02}.json').write_text(json.dumps(telemetry,indent=2));(P/f'projection_{a.scene:02}.json').write_text(json.dumps(projection));print('SCENE_DONE',a.scene,flush=True)
if __name__=='__main__':main()
