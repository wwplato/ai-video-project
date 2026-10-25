"""Retargeted characters with calibrated planted-foot locomotion and contact IK."""
import bpy,math,gzip,json
from pathlib import Path
import numpy as np
from mathutils import Vector,Quaternion,Matrix
ASSET=Path(__file__).resolve().parent/'assets'
with gzip.open(ASSET/'motion.json.gz','rt') as f:MOTION=json.load(f)
def ease(x):x=max(0,min(1,x));return x*x*(3-2*x)
class Character:
 def __init__(self,name,scale=1):
  with bpy.data.libraries.load(str(ASSET/(name+'.blend')),link=False) as (src,dst):dst.objects=src.objects
  for o in dst.objects:bpy.context.collection.objects.link(o)
  self.meshes=[o for o in dst.objects if o.type=='MESH'];self.rig=next(o for o in dst.objects if o.type=='ARMATURE');self.rig.name=name+' rig';self.root=bpy.data.objects.new(name+' movement',None);bpy.context.collection.objects.link(self.root);self.rig.parent=self.root;self.hip=self.rig.location.z;self.inv=self.rig.rotation_euler.to_quaternion().inverted();self.rig.location=(0,0,0);self.root.scale=(scale,)*3;self.factor=scale;self.rest={};self.parent={};self.plans={};self.ref={};self.stable_refs={}
  for b in self.rig.data.bones:
   if b.name.startswith('Bip02'):b.name=b.name.replace('Bip02','Bip01',1)
  for b in self.rig.pose.bones:
   q=b.bone.matrix_local.to_quaternion();p=b.parent;self.rest[b.name]=(p.bone.matrix_local.to_quaternion().inverted()@q).inverted() if p else q.inverted();self.parent[b.name]=p.name if p else None;b.rotation_mode='QUATERNION'
  self.foot_ids={}
  for o in self.meshes:
   for mod in o.modifiers:
    if mod.type=='ARMATURE':mod.use_deform_preserve_volume=True
   for side in ['L','R']:
    ids={g.index for g in o.vertex_groups if g.name.startswith('Bip01 '+side+' Foot') or g.name.startswith('Bip01 '+side+' Toe')};self.foot_ids[o.name,side]=np.array([v.index for v in o.data.vertices if any(g.group in ids and g.weight>.12 for g in v.groups)],dtype=np.int32)
   for m in o.data.materials:
    if not m or not m.use_nodes:continue
    bs=m.node_tree.nodes.get('Principled BSDF');stem=m.name.split(' PBR')[0].split('.')[0];normal=ASSET/'normals'/(stem+'_normal.png')
    if bs:
     bs.inputs['Roughness'].default_value=.48 if 'head' in stem else .72
     if 'head' in stem:bs.inputs['Subsurface Weight'].default_value=.045;bs.inputs['Subsurface Scale'].default_value=.005
     if normal.exists():
      n=m.node_tree.nodes.new('ShaderNodeTexImage');n.image=bpy.data.images.load(str(normal),check_existing=True);n.image.colorspace_settings.name='Non-Color';nm=m.node_tree.nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.42;m.node_tree.links.new(n.outputs['Color'],nm.inputs['Color']);m.node_tree.links.new(nm.outputs['Normal'],bs.inputs['Normal'])
 def sample(self,clip,t,loop=True):
  a=MOTION[clip];fs=a['frames'];at=t*a['fps'];at=at%(len(fs)-1) if loop else max(0,min(at,len(fs)-1));i=int(at);j=min(i+1,len(fs)-1);w=at-i;f,g=fs[i],fs[j]
  return f[0]*(1-w)+g[0]*w,{n:Quaternion(f[k+1]).slerp(Quaternion(g[k+1]),w) for k,n in enumerate(a['bones'])}
 def apply(self,h,q,pos=(0,0,0),yaw=0,pitch=0,pelvis=None):
  want={};identity=Quaternion()
  for pb in self.rig.pose.bones:
   pb.location=(0,0,0);pb.scale=(1,1,1)
   if 'Blink' in pb.name:pb.matrix_basis=Matrix.Identity(4)
   if pb.name not in q:continue
   rot=self.inv@q[pb.name];want[pb.name]=rot;pb.rotation_quaternion=self.rest[pb.name]@want.get(self.parent[pb.name],identity).inverted()@rot
  self.root.location=(pos[0],pos[1],(h*self.hip/.914 if pelvis is None else pelvis)+pos[2]);self.root.rotation_euler=(pitch,0,yaw);bpy.context.view_layer.update()
 def pose(self,clip,t,pos=(0,0,0),yaw=0,pitch=0,blend=None,pelvis=None,loop=True,stable=False):
  h,q=self.sample(clip,t,loop)
  if blend:
   h2,q2=self.sample(blend[0],blend[1]);w=blend[2];h=h*(1-w)+h2*w;q={n:v.slerp(q2.get(n,v),w) for n,v in q.items()}
  if stable:
   hr,qr=self.sample(clip,0)
   for n in q:
    if any(x in n for x in ['Pelvis','Thigh','Calf','Foot','Toe']):q[n]=qr[n]
   h=hr
  self.apply(h,q,pos,yaw,pitch,pelvis)
  if stable:
   if clip not in self.stable_refs:
    hr,qr=self.sample(clip,0);self.apply(hr,qr,pos,yaw,pitch,pelvis);self.stable_refs[clip]={b.name:b.matrix.copy() for b in self.rig.pose.bones if any(x in b.name for x in ['Thigh','Calf','Foot','Toe'])};self.apply(h,q,pos,yaw,pitch,pelvis)
   for name,m in self.stable_refs[clip].items():self.rig.pose.bones[name].matrix=m.copy();bpy.context.view_layer.update()
 def joint(self,name):return self.rig.matrix_world@self.rig.pose.bones['Bip01 '+name].head
 def surface_z(self,side=None):
  dg=bpy.context.evaluated_depsgraph_get();lowest=100
  for o in self.meshes:
   ob=o.evaluated_get(dg);me=ob.to_mesh();co=np.empty(len(me.vertices)*3,np.float32);me.vertices.foreach_get('co',co);co=co.reshape(-1,3);row=np.array(ob.matrix_world)[2]
   if side:
    ids=self.foot_ids.get((o.name,side),[])
    if len(ids)==0:ob.to_mesh_clear();continue
    co=co[ids]
   lowest=min(lowest,float((co@row[:3]+row[3]).min()));ob.to_mesh_clear()
  return lowest
 def ground(self,z=.006):
  self.root.location.z+=z-self.surface_z();bpy.context.view_layer.update()
 def idle(self,t,pos=(0,0,0),yaw=0):self.pose('f_idle_breathe_01',t,pos,yaw,stable=True);self.ground()
 def _reference_stance(self):
  if hasattr(self,'standing'):return self.standing
  self.pose('f_idle_breathe_01',0,stable=True);self.ground();self.standing={'height':float(self.root.location.z),'bones':{p.name:self.rig.matrix_world@p.matrix.copy() for p in self.rig.pose.bones if any(x in p.name for x in ['Thigh','Calf','Foot','Toe'])}};return self.standing
 def place_leg(self,side,hip,target,foot_rotation,reference,yaw):
  inv=self.rig.matrix_world.inverted();R=Matrix.Rotation(yaw,3,'Z');Q=R.to_quaternion();u,l,f=[self.rig.pose.bones['Bip01 '+side+' '+n] for n in ['Thigh','Calf','Foot']];um,lm,fm=[reference[p.name] for p in [u,l,f]];h0,k0,a0=[m.translation for m in [um,lm,fm]];len1=(k0-h0).length;len2=(a0-k0).length;v=target-hip;dist=min(v.length,len1+len2-.0001);axis=v.normalized();old_axis=(a0-h0).normalized();hint=(k0-h0)-old_axis*(k0-h0).dot(old_axis)
  if hint.length<.002:hint=Vector((0,-1,0))
  hint=R@hint;hint=hint-axis*hint.dot(axis);hint.normalize();along=(len1*len1-len2*len2+dist*dist)/(2*dist);knee=hip+axis*along+hint*math.sqrt(max(.000001,len1*len1-along*along));rotu=(R@(k0-h0)).rotation_difference(knee-hip)@Q@um.to_quaternion();rotl=(R@(a0-k0)).rotation_difference(target-knee)@Q@lm.to_quaternion()
  for p,pos,q,m in [(u,hip,rotu,um),(l,knee,rotl,lm),(f,target,foot_rotation,fm)]:p.matrix=inv@Matrix.LocRotScale(pos,q,m.to_scale());bpy.context.view_layer.update()
  delta=foot_rotation@fm.to_quaternion().inverted()
  for p in self.rig.pose.bones:
   if p.name.startswith('Bip01 '+side+' Toe'):
    m=reference[p.name];p.matrix=inv@Matrix.LocRotScale(target+delta@(m.translation-a0),delta@m.to_quaternion(),m.to_scale());bpy.context.view_layer.update()
 def walk(self,t,duration,end=(0,1.48),yaw=math.pi,cycles=1,intensity=.7):
  if t>=duration:self.idle(t-duration,(*end,0),yaw);return
  ref=self._reference_stance();bones=ref['bones'];u=max(0,t/duration);R=Matrix.Rotation(yaw,3,'Z');Q=R.to_quaternion();forward=R@Vector((0,-1,0));distance=.54*cycles;start=Vector((end[0],end[1],0))-forward*distance
  if u<.1:progress=.5*u*u/.1/.9
  elif u>.9:progress=(.9-.5*(1-u)**2/.1)/.9
  else:progress=(u-.05)/.9
  root=start+forward*distance*progress;env=min(ease(u/.15),ease((1-u)/.15));root+=R@Vector((.008*math.sin(u*cycles*2*math.pi)*env,0,0));targets={};rotations={}
  for side,parity in [('R',0),('L',1)]:
   advance=0;lift=0;roll=0
   for step in range(parity,cycles*2,2):
    a=.08+step*(.84/(cycles*2));b=a+.76*(.84/(cycles*2));phase=max(0,min(1,(u-a)/(b-a)));advance+=distance/cycles*ease(phase)
    if 0<phase<1:lift=.055*math.sin(math.pi*phase);roll=.10*math.sin(2*math.pi*phase)
   fm=bones['Bip01 '+side+' Foot'];targets[side]=start+R@fm.translation+forward*advance+Vector((0,0,lift));rotations[side]=Quaternion(R@Vector((1,0,0)),roll)@Q@fm.to_quaternion()
  height=ref['height']+.007*math.sin(u*cycles*4*math.pi)*env
  for side in ['L','R']:
   hm=bones['Bip01 '+side+' Thigh'];km=bones['Bip01 '+side+' Calf'];fm=bones['Bip01 '+side+' Foot'];length=(km.translation-hm.translation).length+(fm.translation-km.translation).length;offset=hm.translation-Vector((0,0,ref['height']));hip_xy=root+R@offset;horizontal=(Vector((hip_xy.x,hip_xy.y,0))-Vector((targets[side].x,targets[side].y,0))).length;max_z=targets[side].z+math.sqrt(max(.01,(length*.994)**2-horizontal**2))-offset.z;height=min(height,max_z)
  hs,qs=self.sample('f_idle_breathe_01',0);period=(len(MOTION['f_walk_neutral']['frames'])-1)/30;hw,qw=self.sample('f_walk_neutral',.4+u*cycles*period);q={n:p.slerp(qw.get(n,p),.44*env) for n,p in qs.items()}
  for n in q:
   if any(x in n for x in ['Pelvis','Thigh','Calf','Foot','Toe']):q[n]=qs[n]
  self.apply(0,q,(root.x,root.y,0),yaw,pelvis=height)
  for side in ['L','R']:
   offset=bones['Bip01 '+side+' Thigh'].translation-Vector((0,0,ref['height']));hip=Vector((root.x,root.y,height))+R@offset;self.place_leg(side,hip,targets[side],rotations[side],bones,yaw)
 def limb(self,side,target,weight=1,leg=False,preserve=False,bend_hint=None):
  if weight<=0:return
  names=['Thigh','Calf','Foot'] if leg else ['UpperArm','Forearm','Hand'];u,l,end=[self.rig.pose.bones['Bip01 '+side+' '+n] for n in names];old=end.matrix.to_quaternion();dest=self.rig.matrix_world.inverted()@Vector(target);dest=end.head.lerp(dest,weight);s=u.head.copy();e=l.head.copy();h=end.head.copy();a=(e-s).length;b=(h-e).length;vec=dest-s;dist=min(vec.length,a+b-.001);axis=vec.normalized();bend=e-s-axis*(e-s).dot(axis)
  if bend_hint is not None:
   hint=self.rig.matrix_world.inverted().to_3x3()@Vector(bend_hint);bend=hint-axis*hint.dot(axis)
  if bend.length<.001:bend=Vector((0,0,-1))
  bend.normalize();along=(a*a-b*b+dist*dist)/(2*max(.01,dist));elbow=s+axis*along+bend*math.sqrt(max(.0001,a*a-along*along));q=(e-s).rotation_difference(elbow-s)@u.matrix.to_quaternion();u.matrix=Matrix.LocRotScale(s,q,Vector((1,1,1)));bpy.context.view_layer.update();e=l.head.copy();h=end.head.copy();q=(h-e).rotation_difference(dest-e)@l.matrix.to_quaternion();l.matrix=Matrix.LocRotScale(e,q,Vector((1,1,1)));bpy.context.view_layer.update()
  if preserve:end.matrix=Matrix.LocRotScale(end.head,old,Vector((1,1,1)));bpy.context.view_layer.update()
 def reach(self,side,target,weight=1):self.limb(side,target,weight)
 def plant_feet(self):
  for side in ['L','R']:
   delta=self.surface_z(side)-.006;target=self.joint(side+' Foot')-Vector((0,0,delta));self.limb(side,target,1,True,True)
 def sleep_pose(self,t,rise=0):
  for p in self.rig.pose.bones:p.matrix_basis=Matrix.Identity(4)
  self.root.location=(.3,.4,.855);self.root.rotation_euler=(-math.pi/2,0,0);bpy.context.view_layer.update()
  inv=self.rig.matrix_world.inverted()
  for side,x in [('L',.42),('R',.18)]:
   u,l,f=[self.rig.pose.bones['Bip01 '+side+' '+n] for n in ['Thigh','Calf','Foot']];old=[self.rig.matrix_world@p.matrix for p in [u,l,f]];h,k,a=[m.translation.copy() for m in old];target=Vector((x,-.39,.80));v=target-h;dist=v.length;axis=v.normalized();a1=(k-h).length;a2=(a-k).length;bend=Vector((0,0,1));bend=(bend-axis*bend.dot(axis)).normalized();along=(a1*a1-a2*a2+dist*dist)/(2*dist);knee=h+axis*along+bend*math.sqrt(max(.00001,a1*a1-along*along));rotu=(k-h).rotation_difference(knee-h)@old[0].to_quaternion();rotl=(a-k).rotation_difference(target-knee)@old[1].to_quaternion();toe=self.joint(side+' Toe0');turn=(toe-a).normalized().rotation_difference(Vector((0,-.6,.8)));toe_bones=[(p,self.rig.matrix_world@p.matrix) for p in self.rig.pose.bones if p.name.startswith('Bip01 '+side+' Toe')]
   for p,pos,rot,m in [(u,h,rotu,old[0]),(l,knee,rotl,old[1]),(f,target,turn@old[2].to_quaternion(),old[2])]:p.matrix=inv@Matrix.LocRotScale(pos,rot,m.to_scale());bpy.context.view_layer.update()
   for p,m in toe_bones:p.matrix=inv@Matrix.LocRotScale(target+turn@(m.translation-a),turn@m.to_quaternion(),m.to_scale());bpy.context.view_layer.update()
  legs={p.name:p.matrix.copy() for p in self.rig.pose.bones if any(x in p.name for x in ['Thigh','Calf','Foot','Toe'])};self.bend_torso(math.radians(82)*rise+.005*math.sin(t*1.6))
  for name,m in legs.items():self.rig.pose.bones[name].matrix=m;bpy.context.view_layer.update()
 def touch(self,side,target,weight=1,direction=(0,1,0)):
  if weight<=0:return
  hand=self.rig.pose.bones['Bip01 '+side+' Hand'];old=hand.matrix.to_quaternion()
  for suffix in ['Finger1','Finger11','Finger12']:
   p=self.rig.pose.bones.get('Bip01 '+side+' '+suffix)
   if p:p.rotation_quaternion=Quaternion()
  bpy.context.view_layer.update();tip=self.joint(side+' Finger12');wrist=self.joint(side+' Hand');d=tip-wrist;desired=Vector(direction).normalized();worlddelta=d.normalized().rotation_difference(desired);localdelta=self.rig.matrix_world.to_quaternion().inverted()@worlddelta@self.rig.matrix_world.to_quaternion();targetrot=(localdelta@old).slerp(old,1-weight);offset=worlddelta@d+desired*.022*self.factor;self.limb(side,Vector(target)-offset,weight);hand.matrix=Matrix.LocRotScale(hand.head,targetrot,Vector((1,1,1)));bpy.context.view_layer.update()
 def head_turn(self,angle):
  p=self.rig.pose.bones['Bip01 Head'];world=self.rig.matrix_world.to_quaternion();q=world.inverted()@Quaternion((0,0,1),angle)@world;p.matrix=Matrix.LocRotScale(p.head,q@p.matrix.to_quaternion(),Vector((1,1,1)));bpy.context.view_layer.update()
 def blink(self,t,closed=False):
  age=(t+.7)%4.3;weight=1 if closed else (math.sin(math.pi*age/.18) if age<.18 else 0)
  if weight<=0:return
  up=self.root.matrix_world.to_quaternion()@Vector((0,0,1));delta=self.rig.matrix_world.inverted().to_3x3()@up
  for side in ['L','R']:
   for suffix,amount in [('EyeBlinkTop',-.010),('EyeBlinkBottom',.002)]:
    p=self.rig.pose.bones.get('Bip01 '+side+suffix)
    if p:m=p.matrix.copy();m.translation+=delta*amount*weight;p.matrix=m
  bpy.context.view_layer.update()
 def bend_torso(self,amount):
  for name,factor in [('Spine',.85),('Spine1',.10),('Spine2',.05)]:
   p=self.rig.pose.bones['Bip01 '+name];world=self.rig.matrix_world.to_quaternion();q=world.inverted()@Quaternion((1,0,0),amount*factor)@world;p.matrix=Matrix.LocRotScale(p.head,q@p.matrix.to_quaternion(),Vector((1,1,1)));bpy.context.view_layer.update()
 def telemetry(self):return {n:[round(x,5) for x in self.joint(n)] for n in ['Head','L Hand','R Hand','L Foot','R Foot','L Toe0','R Toe0']}
