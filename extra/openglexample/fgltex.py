from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

import re
import numpy as np
from PIL import Image
from objloader import ObjFile
from openglutil import Utilc
utili=Utilc()
shapes=('lightsource','sphere','texture')
shape='lightsource'
transformation={x:[] for x in shapes}
lightposition=(0,0,5)

vertsource="""\
#version 330
uniform mat4 projection;
uniform mat4 modelviewsphere;
uniform mat4 modelviewtexture;
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
 vertex_texcoord=(modelviewtexture * vec4(texcoord,1.0,1.0)).xy;
};"""

fragsource="""\
#version 330
struct Material {
 sampler2D diffuse;
 sampler2D diffuse2;
 vec3 specular;
 float shininess;
};

struct Light {
 vec4 position;
 vec3 ambient;
 vec3 specular;
 vec3 diffuse;
};

uniform mat4 modelviewlight;
uniform Material material;
uniform Light light;
uniform mat4 transposeinversemodelviewlight;

varying vec3 vertex_coord;
varying vec3 vertex_normal;
varying vec2 vertex_texcoord;
void main() {
 vec3 N,L,R,E,D;
 float spotfactor=0.7;
 N=normalize(vertex_normal);
 L=normalize((modelviewlight*light.position).xyz-vertex_coord);
 D=normalize((transposeinversemodelviewlight*vec4(0,0,1,1)).xyz);
 R=-reflect(L,N);
 E=normalize(vec3(0,0,0)-vertex_coord);
 if (dot(D,L) >= cos((3.14*30)/180)) {
  spotfactor=pow(max(0,dot(D,L)),0);
 }
 vec4 colord=vec4(light.ambient*texture(material.diffuse,vertex_texcoord).rgb + light.specular * pow(max(0.0,dot(E,R)),material.shininess) * material.specular + light.diffuse * max(0.0,dot(L,N)) * texture(material.diffuse,vertex_texcoord).rgb,1.0);
 vec4 colors=vec4(light.ambient*texture(material.diffuse2,vertex_texcoord).rgb + light.specular * pow(max(0.0,dot(E,R)),material.shininess) * material.specular + light.diffuse * max(0.0,dot(L,N)) * texture(material.diffuse2,vertex_texcoord).rgb,1.0);
 // (1-As) As=0.2
 //gl_FragColor=vec4(spotfactor*vec3(colord.r*(1-0)+colors.r*0,colord.g*(1-0)+colors.g*0,colord.b*(1-0)+colors.b*0),1.0);
 gl_FragColor=vec4(vec3(colord.r*(1-0)+colors.r*0,colord.g*(1-0)+colors.g*0,colord.b*(1-0)+colors.b*0),1.0);
};"""

vertsource2="""\
#version 330
uniform mat4 projection;
uniform mat4 modelviewlight;
attribute vec3 coord;
varying vec4 vertex_color;
void main() {
 gl_Position=projection * (modelviewlight * vec4(coord,1.0));
 vertex_color=vec4(1,1,1,1);
};"""

fragsource2="""\
#version 330
varying vec4 vertex_color;
void main() {
gl_FragColor=vertex_color;
};
"""


def init():
 glClearColor(0,0,0,0)
 setattr(init,'texname',glGenTextures(2))

 img=Image.open('earth.jpg').convert('RGBA')
 img=img.transpose(Image.FLIP_TOP_BOTTOM)
 glBindTexture(GL_TEXTURE_2D,init.texname[0])
 glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA,img.width,img.height,0,GL_RGBA,GL_UNSIGNED_BYTE,img.tobytes())
 glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,GL_REPEAT)
 glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,GL_REPEAT)
 glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST)
# glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST)
 glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST_MIPMAP_NEAREST)
 glGenerateMipmap(GL_TEXTURE_2D)

 img=Image.open('airplane.png').convert('RGBA')
 img=img.transpose(Image.FLIP_TOP_BOTTOM)
 glBindTexture(GL_TEXTURE_2D,init.texname[1])
 glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA,img.width,img.height,0,GL_RGBA,GL_UNSIGNED_BYTE,img.tobytes())
 glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,GL_REPEAT)
 glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,GL_REPEAT)
 glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST)
 glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST)


 setattr(init,'matt',list(ObjFile('sphere.obj').objects.values())[0].vertices)
 setattr(init,'matt2',list(ObjFile('cube0.1.obj').objects.values())[0].vertices)
 setattr(init,'shaderprogram',utili.compileshader((vertsource,fragsource),(vertsource2,fragsource2)))
 setattr(init,'vao',utili.createvao((init.shaderprogram[0],init.matt,8,('coord',0,3),('normal',3,3),('texcoord',6,2)),(init.shaderprogram[1],init.matt2,8,('coord',0,3))))
 glUseProgram(init.shaderprogram[0])
 glUniform1i(utili.getuniloc(init.shaderprogram[0],'material.diffuse'),0)
 glUniform1i(utili.getuniloc(init.shaderprogram[0],'material.diffuse2'),1)
 glUniform3f(utili.getuniloc(init.shaderprogram[0],'material.specular'),0.5,0.5,0.5)
 glUniform1f(utili.getuniloc(init.shaderprogram[0],'material.shininess'),40)
 glUniform4f(utili.getuniloc(init.shaderprogram[0],'light.position'),*lightposition,1)
 glUniform3f(utili.getuniloc(init.shaderprogram[0],'light.ambient'),0.2,0.2,0)
 glUniform3f(utili.getuniloc(init.shaderprogram[0],'light.diffuse'),1.5,1.5,1.5)
 glUniform3f(utili.getuniloc(init.shaderprogram[0],'light.specular'),1,1,1)

 setattr(init,'cube',0);
 glShadeModel(GL_SMOOTH)
 glEnable(GL_DEPTH_TEST)

def display():
 glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
 glPushMatrix()
 glTranslate(0,0,-15)
 glUseProgram(init.shaderprogram[0])
 glUniformMatrix4fv(utili.getuniloc(init.shaderprogram[0],'projection'),1,GL_FALSE,glGetFloatv(GL_PROJECTION_MATRIX))

 glPushMatrix()
 [glTranslate(*x) if len(x)==3 else glRotate(*x) for x in transformation['lightsource']]
 glUniformMatrix4fv(utili.getuniloc(init.shaderprogram[0],'modelviewlight'),1,GL_FALSE,glGetFloatv(GL_MODELVIEW_MATRIX))
 glUniformMatrix4fv(utili.getuniloc(init.shaderprogram[0],'transposeinversemodelviewlight'),1,GL_FALSE,np.transpose(np.linalg.inv(glGetFloatv(GL_MODELVIEW_MATRIX))))
 glPopMatrix()

 glPushMatrix()
 [glTranslate(*x) if len(x)==3 else glRotate(*x) for x in transformation['texture']]
 glUniformMatrix4fv(utili.getuniloc(init.shaderprogram[0],'modelviewtexture'),1,GL_FALSE,glGetFloatv(GL_MODELVIEW_MATRIX))
 glPopMatrix()

 glPushMatrix()
 [glTranslate(*x) if len(x)==3 else glRotate(*x) for x in transformation['sphere']]
 glUniformMatrix4fv(utili.getuniloc(init.shaderprogram[0],'modelviewsphere'),1,GL_FALSE,glGetFloatv(GL_MODELVIEW_MATRIX))
 glUniformMatrix4fv(utili.getuniloc(init.shaderprogram[0],'transposeinversemodelviewsphere'),1,GL_FALSE,np.transpose(np.linalg.inv(glGetFloatv(GL_MODELVIEW_MATRIX))))
 glActiveTexture(GL_TEXTURE0)
 glEnable(GL_TEXTURE_2D)
 glBindTexture(GL_TEXTURE_2D,init.texname[0])
 glBindVertexArray(init.vao[0])

 glActiveTexture(GL_TEXTURE1)
 glEnable(GL_TEXTURE_2D)
 glBindTexture(GL_TEXTURE_2D,init.texname[1])
 glBindVertexArray(init.vao[0])

 glDrawArrays(GL_TRIANGLES,0,len(init.matt)//8)
 glDisable(GL_TEXTURE_2D)
 glPopMatrix()

 if init.cube:
  glUseProgram(init.shaderprogram[1])
  glPushMatrix()
  [glTranslate(*x) if len(x)==3 else glRotate(*x) for x in transformation['lightsource']]
  glTranslate(*lightposition)
  glUniformMatrix4fv(utili.getuniloc(init.shaderprogram[1],'projection'),1,GL_FALSE,glGetFloatv(GL_PROJECTION_MATRIX))
  glUniformMatrix4fv(utili.getuniloc(init.shaderprogram[1],'modelviewlight'), 1 , GL_FALSE, glGetFloatv(GL_MODELVIEW_MATRIX))
  glBindVertexArray(init.vao[1])
  glDrawArrays(GL_TRIANGLES,0,len(init.matt2)//8)
  glPopMatrix()

 '''
# glActiveTexture(GL_TEXTURE0)
 glEnable(GL_TEXTURE_2D)
 glBindTexture(GL_TEXTURE_2D,init.texname)
 glTexEnvf(GL_TEXTURE_ENV,GL_TEXTURE_ENV_MODE,GL_REPLACE)
 glEnableClientState(GL_VERTEX_ARRAY)
 glVertexPointer(3,GL_FLOAT,0,np.array(Utilc.getbuffer(init.matt,0,3,8),dtype=np.float32))
 glEnableClientState(GL_TEXTURE_COORD_ARRAY)
 glTexCoordPointer(2,GL_FLOAT,0,np.array(Utilc.getbuffer(init.matt,6,2,8),dtype=np.float32))
 glDrawArrays(GL_TRIANGLES,0,len(init.matt)//8)
 glDisableClientState(GL_TEXTURE_COORD_ARRAY)
 glDisableClientState(GL_VERTEX_ARRAY)
 glDisable(GL_TEXTURE_2D)
 '''

 glPopMatrix()

# glFlush()
 glutSwapBuffers()

def reshape(w,h):
 glViewport(0,0,w,h)
 glMatrixMode(GL_PROJECTION)
 glLoadIdentity()
 gluPerspective(20,w/h if w>=h else h/w, 1, 30)
# glOrtho(-2.5,2.5,-2.5*h/w,2.5*h/w,1,20) if (w<=h) else glOrtho(-2.5*w/h,2.5*w/h,-2.5,2.5,1,20)
 glMatrixMode(GL_MODELVIEW)
 glLoadIdentity()

def keyboard(key,x,y):
 global transformation,shapes,shape
 key=bytes(key)
 if key==b'\t':
  shape=shapes[(shapes.index(shape)+1)%len(shapes)]
 utili.keyboard(key,transformation[shape])
 if key==b'v':
  print(f'{shape=} {transformation=}')
 if re.search(r'[cC]',key.decode()):
  init.cube=1 if key==b'c' else 0;
 glutPostRedisplay()

if __name__=='__main__':
 glutInit()
 glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
 glutInitWindowSize(500,500)
 glutInitWindowPosition(100,100)
 glutCreateWindow('GLSL Texture')
 init()
 glutDisplayFunc(display)
 glutReshapeFunc(reshape)
 glutKeyboardFunc(keyboard)
 glutMainLoop()
