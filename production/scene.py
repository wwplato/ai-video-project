"""LUMINEX: textured rigged characters, retargeted motion, PBR interiors."""
import bpy,math,sys,argparse,json,gzip,random,time,subprocess,os
sys.path.insert(0,str(__import__("pathlib").Path(__file__).resolve().parent))
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix,Euler
from bpy_extras.object_utils import world_to_camera_view
P=Path(__file__).resolve().parent
ASSET=P/'assets'
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
from character import Character
class BaseSet:
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
  if i!=1:cyl('Stone pedestal',(2.25,1.1,.42),.26,.84,self.ivory);self.imported('IridescenceLamp.glb',(2.25,1.1,.85),0,.95)
  if i==1:self.ordinary_curtains()
  if i in [3,4,9]:self.bed()
  if i in [8,13]:self.imported('SheenChair.glb',(.45,.32,0),0,1)
  if i==12:
   cube('School worktop',(.4,-.8,.79),(2.2,.85,.055),self.oak,.025)
   for x in [-.55,1.35]:cube('Desk titanium support',(x,-.8,.39),(.045,.65,.78),self.metal)
   for j in range(3):cube('Notebooks',(-.35,-.75,.84+j*.025),(.34,.25,.024),self.cloth,.007)
  if i==13:
   self.blocks=[cube('Child play block',(-.8+j*.19,-.65,.07),(.13,.13,.13),mat('Toy color'+str(j),c),.015) for j,c in enumerate([(.12,.38,.36),(.68,.39,.12),(.52,.18,.14)])]
 def ordinary_curtains(self):
  fabric=mat('Ordinary linen curtains',(.77,.74,.67),.94);self.curtain_data=[]
  n=fabric.node_tree.nodes;l=fabric.node_tree.links;noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=160;bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.08;bump.inputs['Distance'].default_value=.002;l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],n.get('Principled BSDF').inputs['Normal'])
  for side in [-1,1]:
   vs=[];fs=[]
   for j in range(19):
    for k in range(37):u=k/36;v=j/18;vs.append((0,1.9+.045*math.sin(u*math.pi*18),.15+3.28*v))
   for j in range(18):
    for k in range(36):q=j*37+k;fs.append((q,q+1,q+38,q+37))
   me=bpy.data.meshes.new('Pleated linen');me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new('Manual curtain '+str(side),me);bpy.context.collection.objects.link(o);o.data.materials.append(fabric)
   for f in me.polygons:f.use_smooth=True
   self.curtain_data.append((o,side))
  cube('Curtain ceiling track',(-.2,1.92,3.48),(6.3,.08,.055),self.metal,.012)
  wet=mat('Rainwater on oak',(.09,.13,.14),.08,.25);sphere('Rainwater puddle',(1.3,1.5,.022),(.50,.27,.006),wet)
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
  if i==1:opened=.8
  if i==4:opened=ease((t-3)/2)
  elif i==10:opened=1-ease((t-4)/.7)
  elif i==11:opened=1-ease(t/.8)
  self.sash.location.x=-.2+opened*1.4
  self.panel.hide_render=i in [1,9] or (i==2 and t<.6)
  self.ring.hide_render=not(i in [2,5,6] and 3.8<t<7.6)
  if i in [0,14,10,11]:return
  a=self.actor;pos=(.60,.55,0);yaw=0
  if i==1:
   close=ease((t-5.6)/2.5)
   for o,side in self.curtain_data:
    width=.30+(1.4*close if side==1 else 0);left=2.83-width if side==1 else -3.28
    for j,v in enumerate(o.data.vertices):u=(j%37)/36;v.co.x=left+u*width
    o.data.update()
   if t<5:
    w=ease(t/4.4);a.pose('f_walk_neutral',t,pos=(.6-1.5*w,.5-1.7*w,0),yaw=-.65)
   else:
    self.panorama_shader.inputs['Strength'].default_value=.07;self.sun.data.energy=.015
    for k,o in enumerate(self.lightobjects):o.data.energy=[65,100][k]
    self.cam.location=(3.4,-4.4,2.4);aim(self.cam,(.65,1.3,1.5));a.pose('f_walk_neutral',t,pos=(2.25-1.4*close,1.35,0),yaw=-math.pi/2,blend=('f_idle_breathe_01',t,ease((t-8.2)/.5)));a.reach('R',(2.55-1.4*close,1.80,1.48),ease((t-5)/.5))
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
   elif t>=7.8:self.blocks[0].location=(-.61,-.65,.38)
  else:
   a.pose('f_idle_breathe_01',t,pos=pos,yaw=.15 if i==7 else 2.65);a.head_turn(.10*math.sin(t*.55))
   if i in [10,11]:a.reach('L',(.45,1.82,1.45),.35*ease((t-5)/1.5))
  if i==11:self.latch.location.z=1.45-.05*ease((t-.8)/.4)

class Set(BaseSet):
 def room(self):
  if self.i==12:
   ground=mat('Campus shadow receiver',(.5,.5,.5),.8);o=cube('Outdoor contact shadows',(0,0,-.04),(30,30,.08),ground);o.is_shadow_catcher=True;self.panel=None;return
  super().room()
  n=self.cloth.node_tree.nodes;l=self.cloth.node_tree.links;grain=n.new('ShaderNodeTexNoise');grain.inputs['Scale'].default_value=210;grain.inputs['Detail'].default_value=2;normal=n.new('ShaderNodeBump');normal.inputs['Strength'].default_value=.12;normal.inputs['Distance'].default_value=.0015;l.new(grain.outputs['Fac'],normal.inputs['Height']);l.new(normal.outputs[0],n.get('Principled BSDF').inputs['Normal'])
  if self.i==13:
   cube('Low child play surface',(-.61,-.65,.09),(.90,.48,.18),self.oak,.025)
   for ob in self.blocks:ob.location.z=.25
  for o in bpy.data.objects:
   if o.name.startswith('Wool area rug'):o.scale.z=.2;o.location.z=.002
 def screen(self,name,pos,size):
  w,h=size;me=bpy.data.meshes.new('Glass HUD projection target');me.from_pydata([(-w/2,0,-h/2),(w/2,0,-h/2),(w/2,0,h/2),(-w/2,0,h/2)],[],[(0,1,2,3)]);me.update();o=bpy.data.objects.new('LUMINEX '+name+' surface',me);bpy.context.collection.objects.link(o);o.location=pos;uv=me.uv_layers.new()
  for loop,co in zip(me.loops,[(0,0),(1,0),(1,1),(0,1)]):uv.data[loop.index].uv=co
  if name=='phone':o.data.materials.append(textured('Phone OLED',TEXTURES/'phone.png',True))
  else:o.hide_render=True
  return o
 def window(self):
  if self.i==12:return
  self.backdrop();self.panorama.visible_shadow=False;self.glass_nodes=[];self.pane_roots=[]
  nodes=self.panorama_shader.id_data.nodes;links=self.panorama_shader.id_data.links;clear=next(n for n in nodes if n.type=='TEX_IMAGE');blur=nodes.new('ShaderNodeTexImage');blur.image=bpy.data.images.load(str(ASSET/'city_diffused.png'),check_existing=True);self.diffusion=nodes.new('ShaderNodeMixRGB');links.new(clear.outputs['Color'],self.diffusion.inputs[1]);links.new(blur.outputs['Color'],self.diffusion.inputs[2]);links.new(self.diffusion.outputs[0],self.panorama_shader.inputs['Color'])
  for x in [-3.3,2.9]:cube('Outer titanium jamb',(x,2.07,1.8),(.075,.12,3.4),self.metal,.012)
  for z in [.13,3.48]:cube('Double sliding track',(-.2,2.07,z),(6.25,.14,.07),self.metal,.012)
  for k,(x0,x1,y) in enumerate([(-3.24,-.20,2.04),(-.20,2.84,1.985)]):
   root=bpy.data.objects.new('Fixed glazed sash' if k==0 else 'Complete sliding glazed sash',None);bpy.context.collection.objects.link(root);self.pane_roots.append(root)
   def part(o):o.parent=root;return o
   for x in [x0,x1]:part(cube('Sash vertical frame',(x,y,1.80),(.038,.06,3.27),self.metal,.006))
   for z in [.18,3.42]:part(cube('Sash horizontal frame',((x0+x1)/2,y,z),(x1-x0,.06,.038),self.metal,.006))
   material=bpy.data.materials.new('Architectural thin glass '+str(k));material.use_nodes=True;ns=material.node_tree.nodes;ns.clear();glass=ns.new('ShaderNodeBsdfGlossy');glass.inputs['Color'].default_value=(.85,.96,.98,1);glass.inputs['Roughness'].default_value=.08;transparent=ns.new('ShaderNodeBsdfTransparent');transparent.inputs[0].default_value=(.975,.995,1,1);mix=ns.new('ShaderNodeMixShader');mix.inputs[0].default_value=0.0;out=ns.new('ShaderNodeOutputMaterial');material.node_tree.links.new(transparent.outputs[0],mix.inputs[1]);material.node_tree.links.new(glass.outputs[0],mix.inputs[2]);material.node_tree.links.new(mix.outputs[0],out.inputs[0]);self.glass_nodes.append(glass)
   part(cube('Actual glass sheet '+str(k),((x0+x1)/2,y+.01,1.8),(x1-x0-.045,.008,3.20),material,.002))
   if k:
    for z in [1.48,1.67]:part(cube('Handle mounting block',(x1-.12,y-.045,z),(.033,.06,.033),self.bronze,.008))
    part(cyl('Sliding window grip',(x1-.12,y-.08,1.575),.015,.19,self.bronze))
  self.sash=self.pane_roots[1]
  self.blackout=cube('Electrochromic blackout laminate',(-.2,2.10,1.8),(6.12,.008,3.22),self.black,.003);self.blackout.hide_render=True
  material=bpy.data.materials.new('Variable transmission blackout');material.use_nodes=True;ns=material.node_tree.nodes;ns.clear();a=ns.new('ShaderNodeBsdfTransparent');b=ns.new('ShaderNodeBsdfDiffuse');b.inputs['Color'].default_value=(.001,.002,.004,1);self.opacity=ns.new('ShaderNodeMixShader');nsout=ns.new('ShaderNodeOutputMaterial');material.node_tree.links.new(a.outputs[0],self.opacity.inputs[1]);material.node_tree.links.new(b.outputs[0],self.opacity.inputs[2]);material.node_tree.links.new(self.opacity.outputs[0],nsout.inputs[0]);self.blackout.data.materials.clear();self.blackout.data.materials.append(material)
  self.latch=cube('Safety motor latch',(2.76,1.91,1.45),(.08,.06,.19),self.bronze,.012);self.latch.hide_render=self.i not in [10,11]
  self.panel=self.screen('window',(-1.70,1.94,2.03),(2.80,1.70));self.rain=[]
  if self.i==1:
   rng=random.Random(22);rainmat=mat('Rain glints',(.6,.8,.9),.1)
   for j in range(18):o=cyl('Raindrop',(0,0,0),.0015,.1,rainmat);self.rain.append((o,rng.uniform(-3.1,2.7),rng.uniform(0,3)))
 def bed(self):
  cube('Upholstered bed base',(.3,.18,.30),(1.65,2.5,.45),self.cloth,.12);cube('Linen mattress',(.3,.18,.55),(1.62,2.40,.25),self.ivory,.12);cube('Soft headboard',(.3,1.47,.85),(1.85,.16,1.25),self.cloth,.10);sphere('Compressible pillow',(.3,1.04,.72),(.66,.34,.045),self.ivory)
  self.duvet_verts=[];faces=[];self.duvet_nx=43;self.duvet_ny=43
  for j in range(self.duvet_ny):
   for k in range(self.duvet_nx):self.duvet_verts.append((-.49+k*1.58/(self.duvet_nx-1),-1+j*1.72/(self.duvet_ny-1),.78))
  for j in range(self.duvet_ny-1):
   for k in range(self.duvet_nx-1):q=j*self.duvet_nx+k;faces.append((q,q+1,q+1+self.duvet_nx,q+self.duvet_nx))
  me=bpy.data.meshes.new('Contact fitted cloth');me.from_pydata(self.duvet_verts,[],faces);me.update();self.duvet=bpy.data.objects.new('Duvet kept above body',me);bpy.context.collection.objects.link(self.duvet);self.duvet.data.materials.append(self.cloth)
  for f in me.polygons:f.use_smooth=True
  solid=self.duvet.modifiers.new('Linen thickness','SOLIDIFY');solid.thickness=.009
  self.cloth_clearance=.025
 def drape(self,t,pull=0):
  from mathutils.bvhtree import BVHTree
  dg=bpy.context.evaluated_depsgraph_get();verts=[];faces=[]
  for ob in self.actor.meshes:
   ev=ob.evaluated_get(dg);me=ev.to_mesh();offset=len(verts);verts.extend([ev.matrix_world@v.co for v in me.vertices]);faces.extend([tuple(offset+k for k in p.vertices) for p in me.polygons]);ev.to_mesh_clear()
  # Use a padded height envelope, not independent point contacts.  Cloth
  # triangles between sample points must also clear knees, shins and shoes.
  n=self.duvet_nx;m=self.duvet_ny;upper=.72-.62*pull;dx=1.58/(n-1);dy=(upper+1)/(m-1)
  base=[[.705 for k in range(n)] for row in range(m)]
  for v in verts:
   if v.z<.675:continue
   k=round((v.x+.49)/dx);row=round((v.y+1)/dy)
   if 0<=k<n and 0<=row<m:base[row][k]=max(base[row][k],v.z+.07)
  # Dilate support over 10 cm, then smooth the envelope into broad folds.
  height=[[max(base[r][c] for r in range(max(0,j-4),min(m,j+5)) for c in range(max(0,k-3),min(n,k+4))) for k in range(n)] for j in range(m)]
  for iteration in range(4):
   height=[[max(base[j][k],sum(height[r][c] for r in range(max(0,j-1),min(m,j+2)) for c in range(max(0,k-1),min(n,k+2)))/((min(m,j+2)-max(0,j-1))*(min(n,k+2)-max(0,k-1)))) for k in range(n)] for j in range(m)]
  self.cloth_clearance=100;bvh=BVHTree.FromPolygons(verts,faces)
  for j,v in enumerate(self.duvet.data.vertices):
   k=j%n;row=j//n;u=k/(n-1);a=row/(m-1);x=-.49+u*1.58;y=-1+(upper+1)*a
   z=height[row][k]+.003*math.sin(x*39+y*27)+.035*pull*math.exp(-((a-.91)/.065)**2)
   v.co=(x,y,z);hit=bvh.ray_cast(Vector((x,y,2.5)),Vector((0,0,-1)),2.5)
   if hit[0] is not None and hit[0].z>.675:self.cloth_clearance=min(self.cloth_clearance,z-hit[0].z)
  self.duvet.data.update()
 def lights(self):
  super().lights();s=bpy.context.scene;s.world.use_nodes=True;s.world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.67,.77,.95,1);s.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.22;self.sun.data.angle=.07
  for o in self.lightobjects:o.data.use_shadow=True;o.data.specular_factor=0.0;o.visible_glossy=False;o.visible_transmission=False;o.visible_camera=False
  if self.i==12:self.sun.rotation_euler=(.55,-.45,-.6);self.sun.data.energy=1.3
 def actors(self):
  if self.i in [10,11]:self.people=[];self.actor=None;return
  super().actors()
  if self.i==12:self.panel=self.phone_screen
 def camera(self):
  super().camera()
  if self.i in [10,11]:self.cam.location=(-.2,-5.7,2.2);self.target=(-.2,2.0,1.0);self.cam.data.lens=32;self.camera_base=self.cam.location.copy();aim(self.cam,self.target)
  if self.i==12:self.cam.location=(2.2,-3.5,1.95);self.target=(.1,.0,1.18);self.cam.data.lens=49;self.camera_base=self.cam.location.copy();aim(self.cam,self.target)
 def render(self):
  s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=4;s.cycles.use_denoising=False;s.cycles.max_bounces=8;s.cycles.diffuse_bounces=2;s.cycles.glossy_bounces=2;s.cycles.transmission_bounces=6;s.cycles.transparent_max_bounces=8;s.cycles.use_adaptive_sampling=False;s.cycles.use_animated_seed=False;s.cycles.seed=2035;s.cycles.sample_clamp_indirect=3;s.cycles.caustics_reflective=False;s.cycles.caustics_refractive=False;s.render.threads_mode='FIXED';s.render.threads=1;s.render.use_persistent_data=True;s.render.resolution_x=1280;s.render.resolution_y=720;s.render.resolution_percentage=100;s.render.fps=12;s.render.image_settings.file_format='OPEN_EXR_MULTILAYER';s.render.image_settings.color_depth='16';s.render.image_settings.exr_codec='ZIP';s.view_layers[0].use_pass_diffuse_color=False;s.view_layers[0].use_pass_normal=False;s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.render.film_transparent=self.i==12;s.view_layers[0].cycles.denoising_store_passes=True
 def update(self,t):
  i=self.i;self.cam.location=self.camera_base;aim(self.cam,self.target)
  if i!=12:
   for o,x,z in self.rain:o.location=(x,2.0,.20+(z-t*1.6)%3.1)
   opacity=1 if i in [3,9] else (1-ease((t-1.4)/1.5) if i==4 else 0);self.blackout.hide_render=opacity<.001;self.opacity.inputs[0].default_value=opacity
   opened=.85 if i==1 else (ease((t-6)/2.2) if i==4 else (1-ease((t-4.1)/1.7) if i in [10,11] else 0));self.sash.location.x=-3.02*opened
   rough=.002+(.28*ease((t-2.5)/2) if i==8 else 0)
   self.diffusion.inputs[0].default_value=ease((t-2.5)/2) if i==8 else 0
   for g in self.glass_nodes:g.inputs['Roughness'].default_value=.08+.30*ease((t-2.5)/2) if i==8 else .08
   daylight=1-opacity
   for k,o in enumerate(self.lightobjects):o.data.energy=[320,145][k]*(.04+.96*daylight)
   self.sun.data.energy=.65*(.015+.985*daylight);self.panorama_shader.inputs['Strength'].default_value=.45 if i==8 else .8
   if i==8:
    self.sun.data.color=(1,.70,.43)
    for o in self.lightobjects:o.data.color=(1,.86,.70)
   appear=1 if i in [3,9] else ease((t-(.5 if i==2 else 2.9 if i in [5,6] else 0))/.8);self.panel.location.y=2.0-.08*appear;self.panel.scale=(.02+.98*appear,)*3
  if i in [0,14,10,11]:return
  a=self.actor
  if i==1:
   if t<5:
    a.walk(t,4.2,(-1.7,-2.0),-.65,4,.7)
    for o,side in self.curtain_data:
     for j,v in enumerate(o.data.vertices):v.co.x=(2.53 if side==1 else -3.28)+(j%37)/36*.3
     o.data.update()
   else:
    self.panorama_shader.inputs['Strength'].default_value=.045;self.sun.data.energy=.01
    for k,o in enumerate(self.lightobjects):o.data.energy=[55,85][k]
    self.cam.location=(3.4,-4.4,2.4);aim(self.cam,(.65,1.3,1.5));a.walk(max(0,t-5),2.6,(.8,1.48),-math.pi/2);target=(a.root.location.x+.23,1.84,1.50);a.reach('R',target,ease((t-5)/.4))
    for o,side in self.curtain_data:
     left=a.root.location.x+.27 if side==1 else -3.28;width=2.83-left if side==1 else .30
     for j,v in enumerate(o.data.vertices):v.co.x=left+(j%37)/36*width
     o.data.update()
  elif i in [2,5,6]:
   a.walk(t,1.6,(0,1.48),math.pi);contact=ease((t-3.0)/.8)*(1-ease((t-7.1)/.9));a.touch('L',(-.42,1.965,1.48),contact);a.head_turn(-.07*ease((t-2.6)/.8))
  elif i in [3,4,9]:
   rise=ease((t-1.5)/3.5) if i==4 else 0;a.sleep_pose(t,rise);pull=ease((t-.7)/1.3) if i==4 else 0
   for side,sign in [('L',1),('R',-1)]:
    spread=.35-.17*rise;a.reach(side,(.3+sign*spread,.65-.40*pull,.91+.045*rise),1)
   self.drape(t,pull)
   a.blink(t,closed=i in [3,9] or t<1.3)
  elif i==8:
   a.pose('f_sit_chair_breathe_01',t*.65,pos=(.45,.32,0),pelvis=.55,stable=True);a.plant_feet();a.head_turn(.05*math.sin(t*.5))
  elif i==12:
   a.pose('m_cell_phone_textmessage',6+t*.65,pos=(0,0,0),stable=True);a.ground();p=a.joint('R Hand');head=a.joint('Head');direction=(head-p).normalized();q=direction.to_track_quat('-Y','Z');self.phone.location=p+Vector((0,-.01,.025));self.phone.rotation_mode='QUATERNION';self.phone.rotation_quaternion=q;self.phone_screen.location=self.phone.location+q@Vector((0,-.009,0));self.phone_screen.rotation_mode='QUATERNION';self.phone_screen.rotation_quaternion=q
   # The captured right-hand grip and thumb motion control the phone naturally.
  elif i==13:
   a.pose('m_sit_chair_breathe_01',t*.65,pos=(.45,.32,0),pelvis=.62,stable=True);a.plant_feet();a.head_turn(-.10+.025*math.sin(t*.6));c=self.child;c.pose('f_crouch_idle',t*.6,pos=(-.65,-.3,0),stable=True);c.ground();lift=ease((t-2.2)/1.4);lower=ease((t-5)/1.3);target=(-.80+.19*lift,-.65,.34+.22*lift-.10*lower);reach=ease((t-.5)/1)*(1-ease((t-7.1)/1));c.reach('R',target,reach)
   if 1.5<t<7.1:self.blocks[0].location=c.joint('R Hand')+Vector((0,0,-.07))
   elif t>=7.1:self.blocks[0].location=(-.61,-.65,.38)
   c.blink(t)
  else:
   a.idle(t,(.7,.8,0),2.8 if i in [10,11] else .15);a.head_turn(.035*math.sin(t*.5))
  if i not in [3,4,9]:a.blink(t)

def main():
 import shutil
 p=argparse.ArgumentParser();p.add_argument('--scene',type=int,default=5);p.add_argument('--frames',type=int,default=120);p.add_argument('--width',type=int,default=1280);p.add_argument('--sample',type=int);p.add_argument('--fps',type=int,default=12);p.add_argument('--samples',type=int);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);w=Set(a.scene);s=bpy.context.scene;s.render.resolution_x=a.width;s.render.resolution_y=round(a.width*9/16);s.render.fps=a.fps;s.cycles.samples=a.samples or (8 if a.scene==8 else 4);raw=P/'raw'/f'{a.scene:02}';out=P/'frames'/f'{a.scene:02}';raw.mkdir(parents=True,exist_ok=True);out.mkdir(parents=True,exist_ok=True);python=os.environ.get('LUMINEX_PYTHON') or shutil.which('python') or shutil.which('python3');ocio=str(Path(bpy.utils.system_resource('DATAFILES',path='colormanagement'))/'config.ocio');ocio=ocio if Path(ocio).exists() else '/usr/share/blender/datafiles/colormanagement/config.ocio'
 def uv(v):q=world_to_camera_view(s,w.cam,v);return [float(q.x),float(1-q.y)]
 def meta(t):
  hands=[]
  for actor in w.people:
   for side in ['L','R']:
    a1=actor.joint(side+' Finger11');a2=actor.joint(side+' Finger12');tip=a2+(a2-a1).normalized()*.022*actor.factor;hands.append([uv(actor.joint(side+' Hand')),uv(actor.joint(side+' Finger1')),uv(a1),uv(tip)])
  return {'time':t,'quad':[uv(w.panel.matrix_world@v.co) for v in w.panel.data.vertices],'hands':hands,'characters':[{'joints':actor.telemetry(),'root':list(actor.root.location),'minimum_mesh_z':actor.surface_z()} for actor in w.people],'cloth_clearance':getattr(w,'cloth_clearance',None),'sliding_sash_x':float(w.sash.location.x) if hasattr(w,'sash') else None}
 common=[python,str(P/'denoise.py'),'--ocio',ocio]
 if a.scene==12:common+=['--background',str(ASSET/'campus.png')]
 if a.sample is not None:
  t=a.sample/a.fps;w.update(t);f=P/f'sample_{a.scene:02}_{a.sample}.exr';s.render.filepath=str(f);bpy.ops.render.render(write_still=True);subprocess.run(common+['--input',str(f),'--output',str(f.with_suffix('.png'))],check=True);f.with_suffix('.json').write_text(json.dumps(meta(t)));return
 metadata=[];seen=set()
 def update(scene):
  if len(seen)>=a.frames and scene.frame_current==1:return
  t=(scene.frame_current-1)/a.fps;w.update(t)
  if scene.frame_current not in seen:metadata.append(meta(t));seen.add(scene.frame_current)
 bpy.app.handlers.frame_change_pre.clear();bpy.app.handlers.frame_change_pre.append(update);render_frames=47 if a.scene==3 and a.frames==120 else a.frames;s.frame_start=1;s.frame_end=render_frames;s.render.filepath=str(raw)+'/';bpy.ops.render.render(animation=True);assert len(metadata)==render_frames
 (P/f'camera_pending_{a.scene:02}.json').write_text(json.dumps(metadata));subprocess.run(common+['--folder',str(raw),'--outdir',str(out)],check=True)
 if render_frames<a.frames:
  import copy
  for index in range(render_frames,a.frames):
   source=index%render_frames;shutil.copy2(out/f'{source+1:04}.png',out/f'{index+1:04}.png');entry=copy.deepcopy(metadata[source]);entry['time']=index/a.fps;metadata.append(entry)
 assert len(list(out.glob('*.png')))==a.frames;(P/f'camera_{a.scene:02}.json').write_text(json.dumps(metadata));print('SCENE_DONE',a.scene,flush=True)
if __name__=='__main__':main()
