import bpy, math, os, sys, json, random, argparse
from mathutils import Vector,Matrix,Quaternion,Euler
from bpy_extras.object_utils import world_to_camera_view
from pathlib import Path
P=Path(__file__).resolve().parent
def mat(name,color):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color[:3],color[3] if len(color)>3 else 1);return m
def mesh(name,verts,faces,material):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o)
 if material:o.data.materials.append(material)
 for p in o.data.polygons:p.use_smooth=True
 return o
def uv(name,pos,scale,material,segments=20,rings=12):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,location=pos);o=bpy.context.object;o.name=name;o.scale=scale
 o.data.materials.append(material)
 for p in o.data.polygons:p.use_smooth=True
 return o
def box(name,pos,size,material,bevel=.04):
 bpy.ops.mesh.primitive_cube_add(size=1,location=pos);o=bpy.context.object;o.name=name;o.scale=size
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 o.data.materials.append(material)
 if bevel:
  b=o.modifiers.new('Soft edges','BEVEL');b.width=bevel;b.segments=3
  o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
 return o
def cylinder(name,pos,radius,depth,material,vertices=16):
 bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=pos);o=bpy.context.object;o.name=name;o.data.materials.append(material)
 for p in o.data.polygons:p.use_smooth=True
 return o
def segment(name,material,radius=.06):return cylinder(name,(0,0,0),radius,1,material)
def between(obj,a,b,radius=None):
 a,b=Vector(a),Vector(b);d=b-a;obj.location=(a+b)/2;obj.rotation_mode='QUATERNION';obj.rotation_quaternion=d.to_track_quat('Z','Y');obj.scale.z=d.length
 if radius:obj.scale.x=radius;obj.scale.y=radius
def point_camera(cam,target):cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
def blend(a,b,t):return Vector(a).lerp(Vector(b),max(0,min(1,t)))
def ease(t):t=max(0,min(1,t));return t*t*(3-2*t)
def ik(a,b,l1,l2,bend):
 a,b=Vector(a),Vector(b);d=b-a;dist=max(.001,min(d.length,l1+l2-.002));u=d.normalized()
 bend=Vector(bend);p=bend-u*bend.dot(u)
 if p.length<.001:p=Vector((1,0,0))
 p.normalize();along=(l1*l1-l2*l2+dist*dist)/(2*dist);h=math.sqrt(max(.001,l1*l1-along*along))
 return a+u*along+p*h

class Actor:
 def __init__(self,name,scale=1,female=False,elder=False,shirt=(.11,.29,.36)):
  self.name=name;self.size=scale;self.female=female;self.elder=elder
  self.skin=mat(name+' skin',(.86,.64,.46));self.shirt=mat(name+' clothing',shirt);self.pants=mat(name+' trousers',(.22,.30,.36));self.white=mat(name+' shoes',(.92,.90,.83));self.hairmat=mat(name+' hair',(.77,.78,.72) if elder else (.19,.095,.045))
  self.parts={};self.parts['torso']=uv(name+' tailored shirt',(0,0,0),(.235,.125,.30),self.shirt)
  self.parts['pelvis']=uv(name+' hips',(0,0,0),(.18,.11,.13),self.pants)
  self.parts['neck']=uv(name+' neck',(0,0,0),(.063,.065,.10),self.skin)
  self.parts['collarL']=box(name+' left collar',(0,0,0),(.07,.02,.08),self.white,.01)
  self.parts['collarR']=box(name+' right collar',(0,0,0),(.07,.02,.08),self.white,.01)
  self.head=bpy.data.objects.new(name+' head control',None);bpy.context.collection.objects.link(self.head)
  def headpart(key,pos,sc,m):
   o=uv(name+' '+key,pos,sc,m);o.parent=self.head;return o
  headpart('face',(0,0,0),(.135,.13,.178),self.skin)
  headpart('hair',(0,-.03,.085),(.142,.126,.13),self.hairmat)
  if female:
   headpart('hair back',(0,-.085,-.055),(.149,.095,.205),self.hairmat)
  if elder:
   for j in range(6):headpart('silver hair curl',(.09*math.cos(j),-.045+.04*math.sin(j),.13),(.065,.07,.065),self.hairmat)
  headpart('nose',(0,.135,-.002),(.026,.035,.035),self.skin)
  eye=mat(name+' eye white',(.96,.96,.90));black=mat(name+' pupils',(.025,.035,.042));self.eyes=[]
  for side in [-1,1]:
   headpart('ear',(.133*side,.003,-.01),(.026,.025,.05),self.skin)
   w=headpart('eye white',(.058*side,.115,.035),(.036,.018,.026),eye)
   q=headpart('pupil',(.058*side,.132,.035),(.013,.009,.017),black);self.eyes.extend([w,q])
   if elder:
    bpy.ops.mesh.primitive_torus_add(major_radius=.039,minor_radius=.003,major_segments=20,minor_segments=6,location=(.058*side,.14,.035),rotation=(math.pi/2,0,0));o=bpy.context.object;o.parent=self.head;o.data.materials.append(self.pants)
  # A small warm smile modeled as an actual curved line.
  curve=bpy.data.curves.new(name+' smile','CURVE');curve.dimensions='3D';curve.bevel_depth=.0035;curve.bevel_resolution=2;s=curve.splines.new('POLY');s.points.add(10)
  for j,p in enumerate(s.points):
   x=-.037+j*.0074;p.co=(x,.129,-.055+.015*(x/.037)**2,1)
  o=bpy.data.objects.new(name+' smile',curve);bpy.context.collection.objects.link(o);o.parent=self.head;o.data.materials.append(mat(name+' lip',(.34,.14,.105)))
  self.arms={};self.legs={};self.hands={}
  for side in [-1,1]:
   self.arms[side]=[segment(name+' sleeve',self.shirt,.063),segment(name+' forearm',self.skin,.045),uv(name+' elbow',(0,0,0),(.057,.057,.057),self.skin)]
   self.legs[side]=[segment(name+' thigh',self.pants,.083),segment(name+' shin',self.pants,.061),uv(name+' knee',(0,0,0),(.077,.077,.077),self.pants),uv(name+' shoe',(0,0,0),(.085,.14,.048),self.white)]
   palm=uv(name+' palm',(0,0,0),(.046,.065,.025),self.skin);fingers=[]
   for j in range(4):
    fingers.append([segment(name+' finger',self.skin,.009),segment(name+' fingertip',self.skin,.008)])
   thumb=[segment(name+' thumb',self.skin,.012),segment(name+' thumb tip',self.skin,.01)]
   self.hands[side]=(palm,fingers,thumb)
 def pose(self,pelvis=(1,0,.95),yaw=-.8,t=0,walk=0,reach=None,sit=0,sleep=0,head_yaw=0,head_pitch=0,eyes_closed=False,hand_targets=None,rotation=None,hand_axes=None):
  R=rotation if rotation is not None else Matrix.Rotation(yaw,3,'Z');base=Vector(pelvis);sz=self.size
  def W(v):return base+R@(Vector(v)-Vector((0,0,.95)))*sz
  q=R.to_quaternion()
  for key,loc,sc in [('torso',(0,.012,1.205),(.235,.125*(1+.012*math.sin(t*2.5)),.30)),('pelvis',(0,0,.95),(.18,.11,.13)),('neck',(0,0,1.49),(.063,.065,.1))]:
   o=self.parts[key];o.location=W(loc);o.rotation_mode='QUATERNION';o.rotation_quaternion=q;o.scale=Vector(sc)*sz
  self.head.location=W((0,0,1.69));self.head.rotation_mode='QUATERNION';self.head.rotation_quaternion=q@Euler((-head_pitch,0,head_yaw),'XYZ').to_quaternion();self.head.scale=(sz,sz,sz)
  for key,x,rz in [('collarL',-.045,-.35),('collarR',.045,.35)]:
   o=self.parts[key];o.location=W((x,.112,1.445));o.rotation_mode='QUATERNION';o.rotation_quaternion=q@Euler((0,0,rz)).to_quaternion();o.scale=(sz,sz,sz)
  blink=.06 if eyes_closed else (0.08 if t%3.7<.12 else 1)
  for o in self.eyes:o.scale.z=(.026 if 'white' in o.name else .017)*blink
  for side in [-1,1]:
   hip=W((side*.12,0,.94));phase=t*7+side*math.pi
   ankle_local=(side*.12,.18*math.sin(phase)*walk+.32*sit,.085+.08*max(0,math.sin(phase))*walk+.24*sit)
   ankle=W(ankle_local);knee=ik(hip,ankle,.43*sz,.43*sz,R@Vector((0,1,0)))
   a,b,kneeobj,shoe=self.legs[side];between(a,hip,knee);between(b,knee,ankle);a.scale.x=a.scale.y=sz;b.scale.x=b.scale.y=sz;kneeobj.location=knee;kneeobj.scale=(.077*sz,)*3
   shoe.location=ankle+R@Vector((0,.065,-.035))*sz;shoe.rotation_mode='QUATERNION';shoe.rotation_quaternion=q;shoe.scale=(.085*sz,.14*sz,.048*sz)
   shoulder=W((side*.215,0,1.425));swing=-.11*math.sin(phase)*walk
   wrist=W((side*.27,.04+swing,1.0+.02*math.sin(t*2)))
   target=(hand_targets or {}).get(side)
   if target is not None:wrist=Vector(target)
   elif reach is not None and side==-1:wrist=blend(wrist,reach[0],reach[1])
   elbow=ik(shoulder,wrist,.31*sz,.295*sz,R@Vector((side*.6,.25,-.65)))
   up,low,elbowobj=self.arms[side];between(up,shoulder,elbow);between(low,elbow,wrist);up.scale.x=up.scale.y=sz;low.scale.x=low.scale.y=sz;elbowobj.location=elbow;elbowobj.scale=(.053*sz,)*3
   forward=Vector(hand_axes[side]).normalized() if hand_axes and side in hand_axes else (wrist-elbow).normalized();upvec=R@Vector((0,0,1));right=forward.cross(upvec)
   if right.length<.05:right=R@Vector((1,0,0))
   right.normalize();upvec=right.cross(forward).normalized();HQ=Matrix((right,forward,upvec)).transposed().to_quaternion()
   palm,fingers,thumb=self.hands[side];palm.location=wrist+forward*.045*sz;palm.rotation_mode='QUATERNION';palm.rotation_quaternion=HQ;palm.scale=(.046*sz,.065*sz,.025*sz)
   pointing=reach is not None and side==-1 and reach[1]>.55
   for j,pair in enumerate(fingers):
    start=wrist+forward*.09*sz+right*(j-1.5)*.021*sz
    ext=.055 if j in [1,2] else .044
    mid=start+forward*ext*.55*sz;end=mid+forward*ext*.45*sz-(upvec*.022*sz if pointing and j!=1 else Vector((0,0,0)))
    between(pair[0],start,mid);between(pair[1],mid,end);pair[0].scale.x=pair[0].scale.y=sz;pair[1].scale.x=pair[1].scale.y=sz
   start=wrist+forward*.025*sz+right*.045*sz;mid=start+forward*.023*sz+right*.016*sz;end=mid+forward*.025*sz
   between(thumb[0],start,mid);between(thumb[1],mid,end)
   for o in thumb:o.scale.x=o.scale.y=sz

class World:
 def __init__(self,index):
  self.i=index;self.t=0;bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
  self.m={k:mat(k,c) for k,c in {'ivory':(.76,.72,.62),'wall':(.84,.82,.74),'oak':(.55,.37,.20),'teal':(.10,.40,.45),'navy':(.07,.15,.23),'metal':(.47,.56,.57),'sea':(.17,.51,.64),'sand':(.75,.65,.44),'green':(.19,.37,.24),'leaf':(.20,.46,.31),'glass':(.36,.66,.71),'black':(.012,.025,.042),'gold':(.83,.61,.28),'white':(.92,.91,.83),'red':(.64,.23,.18)}.items()}
  self.city();self.weather_setup();self.school=index==12;self.bedroom=index in [3,4,9]
  if index not in [0,14]:self.room()
  self.actors=[];self.props=[];self.screen=None;self.sash=None
  if index in [1,2,5,6,7,8,10,11]:
   self.actor=Actor('Student' if index in [5,6] else 'Resident',female=index not in [5,6],shirt=(.09,.20,.31) if index in [5,6] else (.29,.49,.47));self.actors=[self.actor]
  if self.bedroom:
   self.actor=Actor('Morning resident',female=True,shirt=(.40,.52,.54));self.actors=[self.actor];self.bed()
  if index==12:
   self.actor=Actor('Student with phone',shirt=(.08,.19,.29));self.actors=[self.actor];self.schoolroom()
  if index==13:
   self.grandma=Actor('Grandmother',scale=.95,female=True,elder=True,shirt=(.63,.52,.38));self.child=Actor('Child',scale=.56,shirt=(.12,.48,.48));self.actors=[self.grandma,self.child];self.family_props()
  if index==8:self.book()
  if index==6:self.umbrella_setup()
  if index not in [0,14]:self.window()
  self.setup_camera();self.setup_render();self.optimize_static()
 def city(self):
  m=self.m;rng=random.Random(2035)
  # A fully modeled ocean, coast, pavilion and green skyline.
  verts=[];faces=[];self.water_base=[]
  for j in range(24):
   for k in range(32):verts.append((-14+k*.9,2+j*1.1,-.40));self.water_base.append((-14+k*.9,2+j*1.1,-.40))
  for j in range(23):
   for k in range(31):a=j*32+k;faces.append((a,a+1,a+33,a+32))
  self.water=mesh('Animated ocean',verts,faces,m['sea'])
  box('Coastal sand',(-11,9,-.46),(4,15,.18),m['sand'],.2)
  box('Coastal promenade',(-9.1,9,-.25),(.5,14,.11),m['white'],.04)
  self.cars=[]
  for j in range(3):
   car=box('Autonomous coastal vehicle',(-9.1,4+j*3,-.03),(.30,.60,.23),m['white'],.09);self.cars.append(car)
  for j in range(13):
   x=-7+j*.60;h=rng.uniform(2.8,6.8);y=13+rng.uniform(0,1)
   box('Green tower',(x,y,h/2-.4),(.43,.65,h),m['glass'],.055)
   for z in range(1,int(h*5),3):
    box('Tower balcony',(x,y-.35,z*.20-.4),(.46,.06,.025),m['white'],.007)
   box('Green roof',(x,y,h-.36),(.46,.70,.08),m['leaf'],.025)
  for j in range(7):
   x=2.5+j*.8;box('Future steel plant',(x,15,.35),(.65,.8,1.5),m['metal'],.04)
   if j%2==0:cylinder('Green steel chimney',(x,15,1.7),.09,2,m['metal'])
  for j in range(8):uv('Coastal green hills',(-10+j*3,24,-.2),(3,3,1.5+rng.random()),m['green'],16,8)
  box('Yeongildae pier',(-2.6,5.1,-.14),(.16,3.2,.1),m['oak'],.02)
  box('Pavilion platform',(-2.6,6.8,.0),(1.2,1.1,.15),m['white'],.025)
  for x in [-3,-2.2]:
   for y in [6.4,7.2]:cylinder('Pavilion column',(x,y,.5),.04,.95,m['oak'])
  roof=[];rf=[]
  for z,s in [(1.04,.82),(1.3,.58),(1.40,.08)]:
   roof.extend([(-2.6-s,6.8-s,z),(-2.6+s,6.8-s,z),(-2.6+s,6.8+s,z),(-2.6-s,6.8+s,z)])
  for j in range(2):
   for k in range(4):a=j*4+k;b=j*4+(k+1)%4;rf.append((a,b,b+4,a+4))
  rf.append((8,9,10,11));mesh('Korean pavilion tiled roof',roof,rf,m['navy'])
 def room(self):
  m=self.m
  box('Oak floor',(-.3,0,-.10),(7,7,.18),m['oak'],.04)
  for j in range(15):box('Floor board joint',(-3.5+j*.45,0,.002),(.009,6.8,.004),m['sand'],0)
  right_wall=box('Right plaster wall',(3.1,.1,1.7),(.18,4.2,3.6),m['wall'],.035);right_wall.hide_render=True
  box('Window sill',(-.55,2,.36),(5.2,.28,.27),m['ivory'],.035)
  box('Above window wall',(-.55,2,3.25),(5.2,.20,.50),m['wall'],.04)
  box('Left window pier',(-3.14,2,1.72),(.2,.25,3.2),m['wall'],.035)
  box('Right window pier',(2.04,2,1.72),(.2,.25,3.2),m['wall'],.035)
  box('Back wall left',(-4.22,2,1.68),(2.0,.20,3.4),m['wall'],.025)
  box('Back wall right',(2.65,2,1.68),(1.1,.20,3.4),m['wall'],.025)
  box('Left room wall',(-3.35,.1,1.68),(.17,3.8,3.4),m['wall'],.025)
  if not self.bedroom:
   before=set(bpy.context.scene.objects)
   box('Sofa base',(1.9,.6,.42),(1.25,.9,.55),m['ivory'],.14)
   box('Sofa back',(1.9,.99,.85),(1.25,.20,.8),m['ivory'],.09)
   for x in [1.35,2.45]:box('Sofa arm',(x,.6,.72),(.16,.9,.6),m['ivory'],.08)
   for x in [1.65,2.13]:
    o=box('Teal cushion',(x,.9,.95),(.38,.14,.38),m['teal'],.09);o.rotation_euler.y=.15
   cylinder('Coffee table',(1.65,-.55,.48),.47,.06,m['ivory'])
   for x in [1.4,1.85]:cylinder('Coffee table leg',(x,-.55,.25),.025,.45,m['metal'])
   if self.i!=8:
    for o in set(bpy.context.scene.objects)-before:o.location.x+=.85
  cylinder('Plant pot',(-2.85,1.25,.24),.20,.48,m['ivory']);self.leaves=[]
  for j in range(8):
   a=j*math.pi*.75;z=.55+j*.085;end=Vector((-2.85+math.cos(a)*.30,1.25+math.sin(a)*.21,z+.21))
   stem=segment('Plant stem',m['green'],.012);between(stem,(-2.85,1.25,.45),end)
   leaf=uv('Moving plant leaf',end,(.11,.055,.24),m['leaf'],12,8);leaf.rotation_euler=(.5*math.sin(a),.65*math.cos(a),a);self.leaves.append((leaf,leaf.rotation_euler.copy()))
  # Curtains use a waved mesh and deform with the ventilation.
  self.curtains=[]
  for side in [-1,1]:
   verts=[];faces=[];xx=-3.0 if side<0 else 1.82
   for j in range(15):
    for k in range(8):verts.append((xx+k*.036,1.84+.022*math.sin(k*2),.48+j*.18))
   for j in range(14):
    for k in range(7):a=j*8+k;faces.append((a,a+1,a+9,a+8))
   o=mesh('Curtain fabric',verts,faces,m['white']);self.curtains.append((o,[v[:] for v in verts]))
 def weather_setup(self):
  self.clouds=[];self.raindrops=[]
  if self.i in [1,10,11]:
   cloudmat=mat('Storm cloud',(.25,.31,.34))
   for j in range(8):
    o=uv('Cloud '+str(j),(-9+j*2.2,11,4.3+.3*math.sin(j)),(2.1,1.1,.65),cloudmat,12,8);self.clouds.append(o)
   rng=random.Random(33)
   for j in range(42):
    o=segment('Rain streak',self.m['glass'],.006);self.raindrops.append((o,rng.uniform(-2.9,1.85),rng.uniform(.6,3.0)))
 def book(self):
  m=self.m
  for x in [1.64,1.86]:box('Book teal cover',(x,-.28,1.055),(.22,.29,.025),m['teal'],.008)
  for x in [1.65,1.85]:box('Book ivory pages',(x,-.28,1.075),(.19,.26,.028),m['white'],.005)
  self.page=mesh('Turning book page',[(1.75,-.41,1.098),(1.95,-.41,1.098),(1.95,-.15,1.098),(1.75,-.15,1.098)],[(0,1,2,3)],m['white'])
 def umbrella_setup(self):
  self.umbrella=bpy.data.objects.new('Umbrella hand control',None);bpy.context.collection.objects.link(self.umbrella)
  o=cylinder('Umbrella pole',(0,0,-.35),.012,.8,self.m['gold']);o.parent=self.umbrella
  bpy.ops.mesh.primitive_cone_add(vertices=16,radius1=.075,radius2=.025,depth=.50,location=(0,0,-.34));o=bpy.context.object;o.name='Folded umbrella';o.data.materials.append(self.m['teal']);o.parent=self.umbrella
  curve=bpy.data.curves.new('Umbrella curved handle','CURVE');curve.dimensions='3D';curve.bevel_depth=.012;s=curve.splines.new('POLY');s.points.add(16)
  for j,p in enumerate(s.points):a=j*math.pi/16;p.co=(.035-.035*math.cos(a),0,.04+.035*math.sin(a),1)
  o=bpy.data.objects.new('Umbrella handle',curve);bpy.context.collection.objects.link(o);o.data.materials.append(self.m['gold']);o.parent=self.umbrella
 def window(self):
  m=self.m
  for x in [-3.02,1.94]:box('Titanium window jamb',(x,1.98,1.75),(.055,.08,2.56),m['metal'],.012)
  for z in [.48,3.02]:box('Titanium window rail',(-.54,1.98,z),(5.0,.08,.055),m['metal'],.012)
  self.sash=box('Motorized sliding sash',(-.54,1.95,1.75),(.055,.07,2.5),m['metal'],.01)
  self.shade=box('Switchable opaque glass',(-.54,2.00,1.75),(4.92,.025,2.48),m['black'],.005)
  self.shade.hide_render=True
  self.lock=box('Moving safety latch',(1.83,1.90,1.56),(.09,.11,.2),m['gold'],.02)
  self.lock.hide_render=self.i!=11
  self.touch_ring=[]
  for j in range(2):
   bpy.ops.mesh.primitive_torus_add(major_radius=.09+j*.05,minor_radius=.006,major_segments=32,minor_segments=6,location=(.56,1.91,1.43),rotation=(math.pi/2,0,0));o=bpy.context.object;o.data.materials.append(m['glass']);self.touch_ring.append(o)
  self.display=bpy.data.objects.new('Window display control',None);bpy.context.collection.objects.link(self.display)
  tex={2:'weather',3:'alarm',4:'weather',5:'weather',6:'schedule',7:'privacy',8:'frost',9:'blackout',10:'weather',11:'warning',13:'energy'}.get(self.i)
  self.panel=None
  if tex:
   self.panel=self.panel_mesh(tex,(-1.55,1.88,1.97),(1.8,1.24));self.panel.parent=self.display
 def panel_mesh(self,name,pos,dimensions):
  w,h=dimensions;x,y,z=pos
  o=mesh('AI display '+name,[(-w/2,0,-h/2),(w/2,0,-h/2),(w/2,0,h/2),(-w/2,0,h/2)],[(0,1,2,3)],None);o.location=(x,y,z)
  uv=o.data.uv_layers.new(name='UVMap')
  for loop,co in zip(o.data.loops,[(0,0),(1,0),(1,1),(0,1)]):uv.data[loop.index].uv=co
  m=mat('Display '+name,(.06,.18,.24));m.use_nodes=True;node=m.node_tree.nodes.new('ShaderNodeTexImage');node.image=bpy.data.images.load(str(P/'textures'/f'{name}.png'));m.node_tree.nodes.active=node;m.node_tree.links.new(node.outputs['Color'],m.node_tree.nodes.get('Principled BSDF').inputs['Base Color']);o.data.materials.append(m)
  return o
 def bed(self):
  m=self.m;box('Bed frame',(1.13,-.15,.30),(2.4,1.55,.48),m['ivory'],.14)
  box('Mattress',(1.13,-.15,.48),(2.34,1.50,.24),m['white'],.14)
  box('Upholstered headboard',(2.32,-.15,.77),(.15,1.63,1.0),m['teal'],.08)
  uv('Soft pillow',(1.79,-.17,.65),(.33,.55,.10),m['white'])
  verts=[];faces=[]
  for j in range(14):
   for k in range(18):
    x=.03+k*.071;y=-.83+j*.105;z=1.01-.15*(abs(y+.15)/.72)**3+.022*math.sin(k*.8+j*.2);verts.append((x,y,z))
  for j in range(13):
   for k in range(17):a=j*18+k;faces.append((a,a+1,a+19,a+18))
  self.blanket=mesh('Breathing duvet',verts,faces,m['teal']);self.blanket_base=verts
  box('Bedside table',(2.65,.95,.45),(.44,.44,.86),m['oak'],.05)
  cylinder('Bedside lamp foot',(2.65,.95,.94),.12,.08,m['gold']);uv('Bedside lamp shade',(2.65,.95,1.17),(.22,.22,.2),m['ivory'])
 def optimize_static(self):
  dynamic=['Animated ocean','Autonomous coastal vehicle','Moving plant leaf','Curtain fabric','Motorized sliding sash','Switchable opaque glass','Moving safety latch','Breathing duvet','Child wooden block','Rain streak','Cloud','Turning book']
  names=[a.name for a in self.actors];groups={}
  for o in list(bpy.context.scene.objects):
   if o.type!='MESH' or o.parent or o.hide_render or any(o.name.startswith(x) for x in dynamic+names) or o in getattr(self,'touch_ring',[]):continue
   key=tuple(m.name for m in o.data.materials);groups.setdefault(key,[]).append(o)
  for key,objects in groups.items():
   if len(objects)<2:continue
   bpy.ops.object.select_all(action='DESELECT')
   for o in objects:o.select_set(True)
   bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.convert(target='MESH');bpy.ops.object.join()
   bpy.context.object.name='Static set '+(key[0] if key else 'base')
 def schoolroom(self):
  m=self.m;box('School desk',(.75,-.3,.78),(1.65,.8,.08),m['oak'],.04)
  for x in [.1,1.4]:box('Desk leg',(x,-.3,.38),(.06,.6,.76),m['white'],.02)
  for j in range(3):box('School notebook',(.25,-.3,.85+j*.025),(.36,.27,.024),m['teal'] if j%2 else m['ivory'],.008)
  self.phone=bpy.data.objects.new('Hand held phone control',None);bpy.context.collection.objects.link(self.phone)
  o=box('Phone titanium body',(0,0,0),(.14,.025,.26),m['navy'],.018);o.parent=self.phone
  self.phone_screen=self.panel_mesh('phone',(0,-.018,0),(.127,.24));self.phone_screen.parent=self.phone
 def family_props(self):
  m=self.m
  box('Armchair seat',(1.65,.25,.43),(.8,.72,.18),m['ivory'],.10);box('Armchair back',(1.65,.55,.89),(.8,.20,.95),m['ivory'],.10)
  for x in [1.23,2.07]:box('Armchair arm',(x,.25,.65),(.15,.75,.4),m['ivory'],.07)
  self.blocks=[]
  for j,c in enumerate(['teal','gold','white','red']):self.blocks.append(box('Child wooden block '+str(j),(.2+(j%2)*.2,-.6+(j//2)*.20,.09),(.15,.15,.15),m[c],.02))
 def setup_camera(self):
  bpy.ops.object.camera_add();self.cam=bpy.context.object;bpy.context.scene.camera=self.cam;self.cam.data.lens=39
  if self.i in [0,14]:self.camera_base=Vector((4,-7,9));self.target=Vector((-1,10,2.0));self.cam.data.lens=30
  elif self.i==12:self.camera_base=Vector((3.7,-3.6,2.35));self.target=Vector((.45,.25,1.05));self.cam.data.lens=46
  elif self.i==13:self.camera_base=Vector((3.1,-4.0,2.15));self.target=Vector((.9,.1,.8));self.cam.data.lens=36
  elif self.bedroom:self.camera_base=Vector((-2.2,-3.7,2.5));self.target=Vector((.85,.35,1.05));self.cam.data.lens=35
  else:self.camera_base=Vector((3.15,-4.3,2.35));self.target=Vector((-.4,1.2,1.35));self.cam.data.lens=35
  self.cam.location=self.camera_base;point_camera(self.cam,self.target)
 def setup_render(self):
  s=bpy.context.scene;s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=1280;s.render.resolution_y=720;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.render.image_settings.compression=0
  s.render.threads_mode='FIXED';s.render.threads=1;s.render.film_transparent=False
  sh=s.display.shading;sh.light='STUDIO';sh.studiolight_rotate_z=.35;sh.color_type='TEXTURE';sh.show_shadows=True;sh.show_cavity=True;sh.cavity_type='BOTH';sh.curvature_ridge_factor=.7;sh.curvature_valley_factor=.6;sh.cavity_ridge_factor=.7;sh.cavity_valley_factor=.6;sh.background_type='WORLD';sh.show_specular_highlight=False
  s.world.color=(.33,.52,.63);s.display.render_aa='FXAA';s.view_settings.view_transform='Standard';s.view_settings.look='Medium High Contrast'
  if self.i in [3,9]:s.world.color=(.035,.055,.095)
  if self.i==8:s.world.color=(.57,.37,.28)
 def update(self,t):
  self.t=t;i=self.i;m=self.m
  for j,v in enumerate(self.water.data.vertices):
   x,y,z=self.water_base[j];v.co.z=z+.026*math.sin(x*2+y*1.3+t*1.8)+.013*math.sin(y*3-t*1.2)
  self.water.data.update()
  for j,car in enumerate(self.cars):car.location.y=3+(t*.65+j*3)%11
  storm=self.i in [1,11] or (self.i==10 and t>4)
  for j,o in enumerate(self.clouds):o.hide_render=not storm;o.location.x=-9+j*2.2+.22*math.sin(t*.25+j)
  for j,(o,x,z) in enumerate(self.raindrops):
   o.hide_render=not storm;zz=.58+(z-t*2.1)%2.4;between(o,(x,2.16,zz),(x-.015,2.16,zz-.12))
  if storm:bpy.context.scene.world.color=(.18,.25,.32);m['sea'].diffuse_color=(.15,.34,.43,1)
  self.cam.location=self.camera_base+Vector((-.16*ease(t/10),.20*ease(t/10),.035*math.sin(t*.25)));point_camera(self.cam,self.target)
  if i==7 and t>4:
   u=ease((t-4)/2.5);a=-1.02+2.08*u;radius=7.25-2*u
   self.cam.location=(-.54+radius*math.cos(a),2+radius*math.sin(a),2.35+.15*u);point_camera(self.cam,(-.54,2,1.7))
  if i in [0,14]:return
  for j,(leaf,rot) in enumerate(self.leaves):leaf.rotation_euler=(rot.x+.055*math.sin(t*2.2+j),rot.y+.045*math.sin(t*1.8+j),rot.z)
  for curtain,verts in self.curtains:
   for j,(x,y,z) in enumerate(verts):curtain.data.vertices[j].co=(x+.018*math.sin(t*2+z*2)*(3.1-z)/3,y+.025*math.sin(t*2.5+z*2),z)
   curtain.data.update()
  self.sash.location.x=-.54+1.2*ease((t-2.4)/1.2) if i in [4,10] else -.54
  if i==10 and t>4:self.sash.location.x=-.54+1.2*(1-ease((t-4)/.9))
  self.shade.hide_render=not(i in [3,9] or (i==4 and t<1.7) or (i==8 and t>2) or (i==7 and t>5))
  if i==8:self.shade.data.materials[0]=m['ivory']
  if self.panel:self.panel.hide_render=i in [2,5] and t<.8
  for j,o in enumerate(self.touch_ring):o.hide_render=not(i in [2,5,6] and 4<t<8);o.scale=(1+.2*math.sin(t*5+j),)*3
  if i==1:
   u=ease(t/5);pos=blend((.55,-.35,.95),(3.7,-.65,.95),u);self.actor.pose(pos,yaw=-math.pi/2,t=t,walk=1 if t<4.8 else 0,head_yaw=.12*math.sin(t))
  elif i in [2,5,6,7,8,10,11]:
   if i in [2,5,6]:
    u=ease(t/2.8);root=blend((.15,.05,.95),(1.02,1.27,.95),u);amount=ease((t-2.8)/1.5)
    target=(.57,1.87,1.43+.035*math.sin(max(0,t-5)*1.4))
    hands=None
    if i==6:
     handle=blend((1.43,1.52,1.07),(1.40,1.10,1.16),ease((t-6)/1.4));self.umbrella.location=handle;self.umbrella.rotation_euler.y=.15*ease((t-6)/1.4)
     if t>5.1:hands={1:blend((1.24,1.06,.98),handle,ease((t-5.1)/.9))};amount*=1-ease((t-5)/1.0)
    self.actor.pose(root,yaw=-.52,t=t,walk=math.sin(math.pi*u) if t<2.8 else 0,reach=(target,amount),head_yaw=-.25-1.0*ease((t-5)/1.5),head_pitch=.06*math.sin(t),hand_targets=hands)
   elif i==7:
    root=blend((-1.3,.2,.95),(1.15,.5,.95),ease(t/8));self.actor.pose(root,yaw=-math.pi/2,t=t,walk=.75,head_yaw=.25*math.sin(t*.5))
   elif i==8:
    a=math.pi*ease((t-3)/1.6);edge=(1.75+.20*math.cos(a),-.25,1.10+.20*math.sin(a))
    for j,v in enumerate(self.page.data.vertices):v.co=(1.75+(.2*math.cos(a) if j in [1,2] else 0),-.41 if j<2 else -.15,1.098+(.2*math.sin(a) if j in [1,2] else 0))
    self.page.data.update()
    self.actor.pose((1.72,.18,.73),yaw=math.pi,t=t,sit=1,head_pitch=.15+.05*math.sin(t),hand_targets={-1:edge if 3<t<5 else (1.90,-.25,1.04),1:(1.58,-.30,1.04)})
   elif i==10:
    self.actor.pose((1.15,.65,.95),yaw=-.8,t=t,head_yaw=.1+.45*ease((t-4)/.8),reach=((.65,1.75,1.4),.2*ease(t/2)))
   else:self.actor.pose((1.10,.45,.95),yaw=-1.1,t=t,head_yaw=.8*ease((t-1)/1.2),head_pitch=.04*math.sin(t))
  elif i in [3,4,9]:self.bed_animation(t)
  elif i==12:
   root=(.75,.18,.95);left=Vector((.42,-.15,1.28));tap=ease((t-2)/.8)-ease((t-3.2)/.8)+ease((t-5)/.8)-ease((t-6.2)/.8)
   right=blend((1.03,-.32,1.02),(.52,-.17,1.29),tap)
   self.actor.pose(root,yaw=math.pi,t=t,head_pitch=.15,head_yaw=.03*math.sin(t),hand_targets={1:left,-1:right})
   self.phone.location=left+Vector((0,-.01,.09));self.phone.rotation_euler=(math.radians(8),0,math.radians(-5))
  elif i==13:self.family_animation(t)
  if i==11:self.lock.location.x=1.83-.055*ease((t-.8)/.4)
 def bed_animation(self,t):
  i=self.i
  flat=Matrix(((0,0,1),(1,0,0),(0,1,0)))
  upright=Matrix.Rotation(math.pi,3,'Z')
  if i==9:
   R=flat;root=(.93,-.13,.80);hands={-1:(.99+.36*ease(t/2.5),-.53,1.05),1:(.95,.18,1.05)}
   self.actor.pose(root,t=t,rotation=R,eyes_closed=t>2.4,head_pitch=.03*math.sin(t),hand_targets=hands,hand_axes={-1:(-1,0,0),1:(-1,0,0)})
   edge=.88+.36*ease(t/2.5)
  elif i==3:
   u=ease((t-3)/3);R=flat.to_quaternion().slerp(upright.to_quaternion(),u).to_matrix();root=blend((.93,-.13,.80),(1.1,-.69,.72),u)
   self.actor.pose(root,t=t,rotation=R,sit=u,eyes_closed=t<1.5,head_pitch=-.12*ease((t-1.5)/1))
   edge=.9-.28*u
  else:
   stand=ease(t/2);rootz=.72+.23*stand;u=ease((t-2.3)/3)
   root=blend((1.1,-.69,rootz),(.95,1.24,.95),u)
   self.actor.pose(root,yaw=math.pi*(1-ease((t-1.7)/1))-.52*ease((t-1.7)/1),t=t,sit=1-stand,walk=.7*math.sin(math.pi*u),reach=((.57,1.87,1.43),ease((t-5.5)/1)),head_yaw=-.30)
   edge=.55
  for j,(x,y,z) in enumerate(self.blanket_base):
   x2=-.15+(x-.03)*(edge+.15)/1.24;self.blanket.data.vertices[j].co=(x2,y,z+.022*math.sin(t*2.2)*(1-x/1.3))
  self.blanket.data.update()
 def family_animation(self,t):
  g=(1.65,.17,.64);hands={-1:(2.04,-.12,.88),1:(1.26,-.12,.88)}
  self.grandma.pose((1.65,.17,.68),yaw=math.pi,t=t,sit=1,head_yaw=-.65+.10*math.sin(t*.5),head_pitch=.13,hand_targets=hands)
  cycle=t%5;which=0 if t<5 else 1;start=Vector((.35+which*.20,-.62,.12));end=Vector((.50,-.62,.23+which*.15))
  lift=ease((cycle-1)/2.2);pos=start.lerp(end,lift);pos.z+=.28*math.sin(math.pi*lift)
  block=self.blocks[which];block.location=pos
  wrist=pos+Vector((0,.015,.11));rest=Vector((.40,-.38,.50));amount=ease(cycle/.8)*(1-ease((cycle-3.5)/1))
  target=rest.lerp(wrist,amount)
  child_R=Matrix.Rotation(math.pi,3,'Z')@Matrix.Rotation(-.75,3,'X')
  self.child.pose((.55,-.35,.31),rotation=child_R,t=t,sit=1,head_pitch=.30,hand_targets={-1:(.70,-.40,.41),1:target})
  self.blocks[2].location=(.5,-.62,.08)

def main():
 args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
 p=argparse.ArgumentParser();p.add_argument('--scene',type=int,default=5);p.add_argument('--frames',type=int,default=240);p.add_argument('--width',type=int,default=1280);p.add_argument('--test',action='store_true');p.add_argument('--sample',type=int,default=-1);a=p.parse_args(args)
 w=World(a.scene);s=bpy.context.scene;s.render.resolution_x=a.width;s.render.resolution_y=round(a.width*9/16);meta=[]
 folder=P/'frames'/f'{a.scene:02}';folder.mkdir(parents=True,exist_ok=True)
 frames=[a.sample] if a.sample>=0 else ([0,36,72,120,180,239] if a.test else range(a.frames))
 for f in frames:
  t=f/24;w.update(t);s.render.filepath=str(folder/f'{f:04}.png');bpy.ops.render.render(write_still=True)
  if f%8==0:
   actors=[]
   for actor in w.actors:actors.append({'name':actor.name,'pelvis':list(actor.parts['pelvis'].location),'head':list(actor.head.location),'head_rotation':list(actor.head.rotation_quaternion),'left_hand':list(actor.hands[-1][0].location),'right_hand':list(actor.hands[1][0].location),'left_foot':list(actor.legs[-1][3].location),'right_foot':list(actor.legs[1][3].location)})
   meta.append({'frame':f,'time':t,'actors':actors,'environment':{'wave_z':float(w.water.data.vertices[100].co.z),'vehicles':[list(o.location) for o in w.cars],'camera':list(w.cam.location)}})
  if f%24==0:print('MOTION_FRAME',a.scene,f,flush=True)
 (P/f'motion_{a.scene:02}.json').write_text(json.dumps(meta,ensure_ascii=False)+'\n');print('SCENE_COMPLETE',a.scene,flush=True)
if __name__=='__main__':main()
