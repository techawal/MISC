#from abc import ABC, abstractmethod
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import re
from PIL import Image
import numpy as np
import sys;sys.path.append('/home/minhinc/tmp')
from MISC.extra import objfileloader
from MISC.extra.openglutil import Utilc
from MISC.utillib.util import Util

vertsource1="""\
#version 330
uniform mat4 projection;
uniform mat4 modelviewsphere;
uniform mat4 transposeinversemodelviewsphere;
attribute vec3 coord;
attribute vec3 normal;
attribute vec2 texcoord;
varying vec3 vertex_coord;
varying vec3 vertex_normal;
varying vec2 vertex_texcoord;
void main() {
 gl_Position=projection * (modelviewsphere * vec4(coord,1.0));
 vertex_coord=(modelviewsphere*vec4(coord,1.0)).xyz;
 vertex_normal=(transposeinversemodelviewsphere*vec4(normal,1.0)).xyz;
 vertex_texcoord=texcoord;
};"""

fragsource1="""\
#version 330
#define MAXLIGHTCOUNT 4
struct Material {
 sampler2D diffuse;
 vec3 diffuse2;
 vec3 ambient;
 vec3 specular;
 vec3 emission;
 int shininess;
};

struct Light {
 vec4 position;
 vec3 ambient;
 vec3 diffuse;
 vec3 specular;
 vec3 spotdirection;
 int spotangle;
 int spotexponent;
};

uniform Material material;
uniform Light[MAXLIGHTCOUNT] light;
uniform int textureb;
uniform int lightcounti;
varying vec3 vertex_coord;
varying vec3 vertex_normal;
varying vec2 vertex_texcoord;
void main() {
 vec3 N,L,R,E,D;
 vec3 out_color=vec3(0,0,0);
 N=normalize(vertex_normal);
 E=normalize(vec3(0,0,0)-vertex_coord);
 float attenuation=0.0;
 float distanceLV=0.0;
 for (int i=0;i<lightcounti; i++) {
  L=normalize(light[i].position.w==1.0?light[i].position.xyz-vertex_coord:light[i].position.xyz);
  R=-reflect(L,N);
  D=normalize(light[i].spotdirection);
  float spotfactor=(light[i].spotangle==90 || light[i].position.w==0.0?1.0:0.0);
  attenuation=1.0;
  if (light[i].position.w==1.0) {
   distanceLV=distance(light[i].position.xyz,vertex_coord);
//   attenuation=clamp(10/(1+distanceLV*distanceLV),0.0,1.0);
   attenuation=clamp(4/(1+distanceLV),0.0,1.0);
  }
  if (light[i].spotangle!=90 && light[i].position.w!=0.0 && dot(D,L) >= cos((3.14*light[i].spotangle)/180)) {
   spotfactor=pow(max(0,dot(D,L)),light[i].spotexponent);
  }
  if (textureb==1) {
   out_color+=vec3(attenuation*spotfactor*vec3(material.emission + light[i].ambient*material.ambient * texture(material.diffuse,vertex_texcoord).rgb + light[i].specular * pow(max(0.0,dot(E,R)),material.shininess) * material.specular + light[i].diffuse * max(0.0,dot(L,N)) * texture(material.diffuse,vertex_texcoord).rgb));
  } else {
   out_color+=vec3(attenuation*spotfactor*vec3(material.emission + light[i].ambient*material.ambient + light[i].specular * pow(max(0.0,dot(E,R)),material.shininess) * material.specular + light[i].diffuse * max(0.0,dot(L,N)) * material.diffuse2));
  }
 }
 gl_FragColor=vec4(clamp(out_color,0,1),1.0);
// gl_FragColor=vec4(out_color,1.0);
};"""

#class shader(ABC):
class shader:
 shaderprogram=None
 texturename={} # {'abc.png':1,..} {<imagename>,<textureid>}
 lightposition={} # {<objectinstance>:{'position':(1,0,10),spotangle:20,spotdirection:(0,0,1,0),spotexponent:23},..}
 utili=Utilc()
 unknowntexture='__UNKNOWN__'
 defaultuniform=dict((('material.diffuse',0),('material.diffuse2',(1,0,0)),('material.specular',(0,0,0)),('material.emission',(0,0,0)),('material.ambient',(0,0,0)),('material.shininess',40)))
 vao={} # {'objfile':[imagecolor,vaomaterialname,vaolength,vaoid],..} # vao can be texture or color vao
 focusobject=None
 def __init__(self,*,objfile,**kwarg):
  """shader(objfile='sphere.obj','material.diffuse':['yellowworldmap.png','__UNKNOWN__'],fixtransformation=[[0,0,6],['s',1.0,1.0,1.0]])"""
  self.children=[]
  [setattr(self,x[0],x[1]) for x in dict({'transformation':[],'fixtransformation':[]},**kwarg).items() if not hasattr(self,x[0])]
  self.fixtransformation.sort(key=lambda x:len(x)!=3);self.fixtransformation.sort(key=lambda x:len(x)==4 and x[0]=='s')
  if not shader.shaderprogram:
   shader.shaderprogram=self.utili.compileshader(vertsource1,fragsource1)
   glUseProgram(shader.shaderprogram)
  shader.focusobject=self
  self.addlight(**{re.sub('^light_','light.',x):y for x,y in kwarg.items() if re.search(r'^light_',x)}) if 'light_position' in kwarg else None
  self.objfile=objfile
  if not objfile or objfile in shader.vao:
   Util.pprint('DID NOT PROCEED',objfile)
   return
  obj=objfileloader.OBJ(objfile)
  #coord and normal is expected in all obj file
  texcoord,usemtl=obj.drawarrayvertices[6]!=-1,obj.drawarrayvertices[8]
  countl=0
  def pushtovao(count1,count2,imagecolor,vaomaterialname):
   '''\
   pushtovao(0,72,'abc.png','material002')
   pushtovao(0,729,'__UNKNOWN__','__UNKNOWN__') #texcoord present but imagename not known
   pushtovao(0.360,None) # color VAO but color not present
   pushtovao(0,144,(1,1,0))'''
   nonlocal self
#   self.utili.pushuniattribtoshader(*[x for x in shader.defaultuniform.items()])
#   print(f" TEST {imagecolor=} {shader.shaderprogram=}")
   if objfile not in shader.vao:
    shader.vao[objfile]=[]
   shader.vao[objfile].append([imagecolor,vaomaterialname,count2-count1,self.utili.createvao(shader.shaderprogram,obj.drawarrayvertices[count1*9:count2*9],9,*[x for x in [('coord',0,3),('normal',3,3),('texcoord',6,2)] if x!=('texcoord',6,2) or type(imagecolor)==str])])
  for count,i in enumerate([obj.drawarrayvertices[count:count+9] for count in range(len(obj.drawarrayvertices)) if not count%9]):
   if (i[6]!=-1)!=texcoord or usemtl!=i[8]:
#    print(f"TEST for {i=} {texcoord=} {usemtl=} {countl=} {count=} {obj.mtl[usemtl]['Kd']=}")
#    pushtovao(countl,count,texcoord and usemtl!=-1 and 'map_Kd' in obj.mtl[usemtl] and obj.mtl[usemtl]['map_Kd'] or texcoord and usemtl!=-1 and shader.unknowntexture or texcoord and shader.unknowntexture or usemtl!=-1 and 'Kd' in obj.mtl[usemtl] and obj.mtl[usemtl]['Kd']  or shader.defaultuniform['material.diffuse2'],usemtl!=-1 and obj.mtl[usemtl]['name'] or texcoord and shader.unkowntexture or None)
    pushtovao(countl,count,texcoord and usemtl!=-1 and 'map_Kd' in obj.mtl[usemtl] and obj.mtl[usemtl]['map_Kd'] or usemtl!=-1 and 'Kd' in obj.mtl[usemtl] and obj.mtl[usemtl]['Kd']  or shader.defaultuniform['material.diffuse2'],usemtl!=-1 and obj.mtl[usemtl]['name'] or texcoord and shader.unkowntexture or None)
    texcoord,usemtl=i[6]!=-1,i[8]
    countl=count
#  print(f'TEsT pushtovao {texcoord=} {usemtl=} {obj.mtl=}')
  pushtovao(countl,count+1,texcoord and usemtl!=-1 and 'map_Kd' in obj.mtl[usemtl] and obj.mtl[usemtl]['map_Kd'] or usemtl!=-1 and 'Kd' in obj.mtl[usemtl] and obj.mtl[usemtl]['Kd']  or shader.defaultuniform['material.diffuse2'],usemtl!=-1 and obj.mtl[usemtl]['name'] or texcoord and shader.unknowntexture or None)
#  pushtovao(countl,count+1,texcoord and usemtl!=-1 and 'map_Kd' in obj.mtl[usemtl] and obj.mtl[usemtl]['map_Kd'] or texcoord and usemtl!=-1 and shader.unknowntexture or texcoord and shader.unknowntexture or usemtl!=-1 and 'Kd' in obj.mtl[usemtl] and obj.mtl[usemtl]['Kd']  or shader.defaultuniform['material.diffuse2'],usemtl!=-1 and obj.mtl[usemtl]['name'] or texcoord and shader.unknowntexture or None)

 def transformmatrix(self,transformation):
  [glTranslate(*x) if len(x)==3 else glRotate(*x) if not x[0]=='s' else glScalef(*x[1:]) for x in transformation]

 def addlight(self,**kwarg):
  if not self in shader.lightposition:
   shader.lightposition[self]=dict({'light.position':(0,0,0,1),'light.ambient':(0,0,0),'light.diffuse':(1.5,1.5,1.5),'light.specular':(0,0,0),'light.spotangle':90,'light.spotexponent':0,'light.spotdirection':(0,0,1)},**kwarg)
   shader.utili.pushuniattribtoshader(*[('light['+str(len(shader.lightposition)-1)+'].'+re.sub(r'^.*[.](.*)$',r'\1',x),y) for x,y in shader.lightposition[self].items()])
   shader.utili.pushuniattribtoshader('lightcounti',len(shader.lightposition))
  print(f'<>shader.addlight {self=} {kwarg=} {shader.lightposition=}')

 '''
 def drawtexture(self):
  for i in self.texname:
   glActiveTexture(GL_TEXTURE0+count)
   glEnable(GL_TEXTURE_2D)
   glBindTexture(GL_TEXTURE_2D,self.texname[count])
   glBindVertexArray(self.vao)
  glDrawArrays(GL_TRIANGLES,0,len(self.matt)//8)
  glDisable(GL_TEXTURE_2D)
 '''

 def difftranslation(self,transformation):
  difftransformation=[]
  if len(self.transformation)==0 or len(self.transformation[0])!=3:
   difftransformation=(len(transformation)==0 or len(transformation[0])!=3) and [] or transformation[0]
   if transformation and len(transformation[0])==3:
    self.transformation[0:0]=[x for x in transformation[0]]
  else:
   difftransformation=[transformation[0][i]-self.transformation[0][i] for i in range(3)]
   self.transformation[0]=[x for x in transformation[0]]
  return difftransformation

 def diffrotation(self,transformation):
  difftransformation=[]
  diffcount=count=0
  if transformation and len(transformation[0])==3:
   count+=1
  if self.transformation and len(self.transformation[0])==3:
   diffcount+=1
  while count<len(transformation) or diffcount<len(self.transformation):
   if diffcount==len(self.transformation) and count<len(transformation):
    for i in transformation[count:]:
     self.transformation.append([x for x in i])
     difftransformation.append([x for x in i])
     count+=1
   elif diffcount==(len(self.transformation)-1) and count==(len(transformation)-1) and self.transformation[0]==transformation[0]:
    difftransformation=[transformation[count]-self.transformation[diffcount] for x in transformation[count]]
    self.transformation[diffcount]=[x for x in transformation[count]]
    diffcount+=1
    count+=1
   elif self.transformation[diffcount][0] != transformation[count][0]:
    count+=1
   else:
    diffcount+=1
    count+=1
  return difftransformation

# @abstractmethod
 '''
 def getchildrencount(self):
  if not hasattr(self,'childrencount'):
   setattr(self,'childrencount',0)
  else:
   self.childrencount+=1
  return self.childrencount
 '''

 def keyboard(self,**kwarg):
  '''keyboard(key)
  keyboard(key,transformation=[2,0,0])'''
#  print(f'TEST shader.keyboard {kwarg=}')
#  print(f'TEST shader.keyboard {shader.keyboard.key=}') if hasattr(shader.keyboard,'key') else None
  kwarg['key']=kwarg['key'].decode() if type(kwarg['key'])==bytes else kwarg['key']
  if not hasattr(shader.keyboard,'count'):
   setattr(shader.keyboard,'count',0)
  if not hasattr(shader.keyboard,'key'):
   setattr(shader.keyboard,'key','')
#  print(f'TEST shader.keyboard {shader.keyboard.key=} {shader.focusobject=}')
  if type(kwarg['key'])==str and type(shader.keyboard.key)==str and (kwarg['key']=='i' or kwarg['key']=='I' or re.search(r'^i[^I]*$',shader.keyboard.key)):
   shader.keyboard.key='' if kwarg['key']=='i' else shader.keyboard.key
   shader.keyboard.key+=kwarg['key']
   if re.search(r'^i\d+I$',shader.keyboard.key):
    shader.focusobject=kwarg['rootshader']
    shader.keyboard.count=re.sub(r'^i(.*)I$',r'\1',shader.keyboard.key)
    for i in str(shader.keyboard.count):
     shader.focusobject=shader.focusobject.children[int(i)]
    shader.keyboard.count=int(shader.keyboard.count[0])
  elif kwarg['key']=='\t':
    shader.keyboard.count=(shader.keyboard.count+1)%(len(shader.root)+1)
    shader.focusobject=kwarg['rootshader'].children[shader.keyboard.count] if not shader.keyboard.count==len(shader.keyboard.count) else kwarg['rootshader']
  elif type(kwarg['key'])==str and re.search(r'^\d+$',kwarg['key']):
   shader.keyboard.count=int(kwarg['key'])
   shader.focusobject=kwarg['rootshader'].children[shader.keyboard.count] if not shader.keyboard.count==len(kwarg['rootshader'].children) else kwarg['rootshader']
  elif kwarg['key']=='v':
   kwarg['rootshader'].printchildren()
  elif shader.focusobject:
#   print(f'TEST calling utili shader.keyboard {shader.focusobject=} {shader.focusobject.objfile=} {kwarg=} {shader.keyboard.key=}')
   shader.utili.keyboard(kwarg['key'].encode(),shader.focusobject.transformation if not 'transformation' in kwarg else kwarg['transformation']) if kwarg['key'] in 'lrudnfxXyYzZgGsS' or type(kwarg['key'])==tuple or type(kwarg['key'])==list else None
   shader.keyboard.key=kwarg['key']
   return True
  print(f'TEST shader.keyboard {shader.focusobject=} {shader.focusobject.objfile=}')
  return False

 def keyboard2(self,**kwarg):
  return shader.focusobject.keyboard(**dict(kwarg,rootshader=self))

 '''
 def add(self,*,object,**kwarg):
  self.children.append({'object':object,'transformation':[],'fixtransformation':[],**kwarg})
#  print(f'TEST shader.add {object=} {kwarg=} {self.children=}')

 def getlightchildren(self):
  retvalue=[]
  if not self.children:
   return []
  elif self in shader.lightposition:
   return [self]
  for i in self.children:
   [retvalue.extend(self.getlightchildren()) for count in range(len(self.children))]
  return retvalue
 '''

 def printchildren(self,level=0):
  print(f'{level} {" "*level*4}{str(self.objfile)}')
  for i in self.children:
   i.printchildren(level=level+1)
 def display(self,**kwarg):
#  print(f'TEST  ----------- shader.display {self=} {kwarg=} {shader.focusobject=} {shader.lightposition=}{self.objfile=} {self.focusobject.objfile=}')
#  print(f'TEST shader.display {self=} {self.children=} {kwarg=}')
  tmp=None
  glPushMatrix()
  self.transformmatrix(self.transformation) if hasattr(self,'transformation') else None
  self.transformmatrix(self.fixtransformation) if hasattr(self,'fixtransformation') else None
#  for i in self.getlightchildren():
  if hasattr(self,'extratransformation'):
   glPushMatrix()
   self.transformmatrix(self.extratransformation)
  glUniformMatrix4fv(self.utili.getuniloc('projection'),1,GL_FALSE,glGetFloatv(GL_PROJECTION_MATRIX).tolist())
  glUniformMatrix4fv(self.utili.getuniloc('modelviewsphere'),1,GL_FALSE,glGetFloatv(GL_MODELVIEW_MATRIX).tolist())
  glUniformMatrix4fv(self.utili.getuniloc('transposeinversemodelviewsphere'),1,GL_FALSE,np.transpose(np.linalg.inv(glGetFloatv(GL_MODELVIEW_MATRIX).tolist())))
#  print(f"TEST shader.display lightpostion={list(np.transpose(glGetFloatv(GL_MODELVIEW_MATRIX))@self.opengl['light.position'])}") if hasattr(self,'opengl') and 'light.position' in self.opengl else None
#  self.utili.pushuniattribtoshader('light.position',list(np.transpose(glGetFloatv(GL_MODELVIEW_MATRIX))@self.opengl['light.position'])) if hasattr(self,'opengl') and 'light.position' in self.opengl else None
#  shader.utili.pushuniattribtoshader('light['+str([count for count,k in enumerate(shader.lightposition) if k==self][0])+'].position',np.transpose(glGetFloatv(GL_MODELVIEW_MATRIX))@shader.lightposition[self]['light.position']) if self in shader.lightposition else None
#  shader.utili.pushuniattribtoshader('light['+str(list(shader.lightposition).index(self))+'].position',np.transpose(glGetFloatv(GL_MODELVIEW_MATRIX))@shader.lightposition[self]['light.position']) if self in shader.lightposition and shader.lightposition[self]['light.position'][3]==1 else None
#  print(f"TEST shader.display {glGetFloatv(GL_MODELVIEW_MATRIX)=} {shader.lightposition[self]['light.spotdirection']=}") if self in shader.lightposition else None
  print(f"TEST shader.display {np.transpose(glGetFloatv(GL_MODELVIEW_MATRIX))@shader.lightposition[self]['light.position']=} {shader.lightposition[self]['light.spotdirection']=} {np.transpose(np.linalg.inv(np.transpose(glGetFloatv(GL_MODELVIEW_MATRIX))))@(list(shader.lightposition[self]['light.spotdirection'])+[1.0])=}") if self in shader.lightposition else None
  shader.utili.pushuniattribtoshader('light['+str(list(shader.lightposition).index(self))+'].position',(np.transpose(glGetFloatv(GL_MODELVIEW_MATRIX))@shader.lightposition[self]['light.position']).tolist()) if self in shader.lightposition else None
#  shader.utili.pushuniattribtoshader('light['+str(list(shader.lightposition).index(self))+'].spotdirection',(np.transpose(np.transpose(np.linalg.inv(glGetFloatv(GL_MODELVIEW_MATRIX))))@(list(shader.lightposition[self]['light.spotdirection'])+[1.0])).tolist()[0:3]) if self in shader.lightposition else None
  shader.utili.pushuniattribtoshader('light['+str(list(shader.lightposition).index(self))+'].spotdirection',(np.transpose(np.linalg.inv(np.transpose(glGetFloatv(GL_MODELVIEW_MATRIX))))@(list(shader.lightposition[self]['light.spotdirection'])+[1.0])).tolist()[0:3]) if self in shader.lightposition else None
#  print(f'{shader.vao=}')
  for i in (shader.vao[self.objfile] if self.objfile else []):
   tmp=hasattr(self,'material_diffuse') and self.material_diffuse or None
#   print(f'TEST shader {tmp=}')
   shader.utili.pushuniattribtoshader(*[x for x in dict(shader.defaultuniform,**{re.sub('^material_','material.',x[0]):x[1] for x in self.__dict__.items()}).items() if re.search(r'^material[.](?!diffuse)',x[0])])
   if type(i[0])==str and (not tmp or type(tmp[0])==str):
    tmp=tmp and type(tmp[0])==str and tmp[1]==i[1] and tmp[0] or i[0]
#    print(f'TEST shader.display TEXTURE {tmp=}')
    if not tmp in shader.texturename:
     shader.texturename[tmp]=self.utili.createtextureobject(imagename=tmp,textureid=1)
    shader.utili.pushuniattribtoshader('textureb',1)
    glActiveTexture(GL_TEXTURE0)
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D,shader.texturename[tmp])
    glBindVertexArray(i[3])
    glDrawArrays(GL_TRIANGLES,0,i[2])
    glDisable(GL_TEXTURE_2D)
   else:
    self.utili.pushuniattribtoshader('material.diffuse2',tmp and i[1]==tmp[1] and tmp[0] or i[0])
    shader.utili.pushuniattribtoshader('textureb',0)
    glBindVertexArray(i[3])
    glDrawArrays(GL_TRIANGLES,0,i[2])
#   self.utili.pushuniattribtoshader(*[x for x in shader.defaultuniform.items()])
#  print(f'{self.children=} {kwarg=}')
  '''
  for i in [(count,x) for count,x in enumerate(self.children) if 'parent' in kwarg and x['object'][1]==kwarg['count'] or 'parent' not in kwarg and count]:
   self.children[i[0]]['object'][0].display(**{'parent':self,'count':i[0],**({'key':kwarg['key']} if 'key' in kwarg else {}),'active':kwarg['active'] if 'parent' in kwarg else i[0]==kwarg['active']})
  '''
  if hasattr(self,'extratransformation'):
   glPopMatrix()
#  [x.display(**dict(kwarg,active=kwarg['active'] if type(kwarg['active'])==bool else kwarg['active']==count)) for count,x in enumerate(self.children)]
#  print(f'TEST display {shader.focusobject} {self=}')
  [x.display(**dict(kwarg,active=kwarg['active'] or x.objfile and x==shader.focusobject)) for x in self.children]
  glPopMatrix()
