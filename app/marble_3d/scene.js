/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

const BOARD_EDGE = 4.32;
const PLATE_RADIUS = 0.324;
const PLATE_HEIGHT = 0.108;
const CARRY_HEIGHT = 0.16;
const DEFAULT_YAW = -0.145;
const DEFAULT_TILT = 0.92;
const TOP_TILT = 1.568;
const MAX_ORBIT_TILT = 1.12;
const CAMERA_EASE_MS = 44;
const TURN_MS = 420;
const HALF_BOARD_DIAGONAL = BOARD_EDGE * Math.SQRT2;
const HALF_VIEW_HEIGHT = 5.86;
const MOTION_PIXEL_BUDGET = 830_000;
const ASSETS = [..."wb"].flatMap(side => [..."KQRBNP"].map(kind => side + kind));
const literalColor = (red, green, blue, alpha = 1) => [red / 255, green / 255, blue / 255, alpha];
const GRAPHITE = literalColor(31, 33, 39);
const WHITE_EDGE = literalColor(39, 43, 54);
const BLACK_EDGE = literalColor(22, 25, 31);
const LAST_MOVE = literalColor(242, 195, 24);
const SELECTION = literalColor(250, 202, 27);
const TARGET = literalColor(34, 75, 178);
const FOCUS = literalColor(27, 83, 202);
const LIGHT = literalColor(250, 250, 239);
const CHECK = literalColor(191, 53, 57);
const DROP = literalColor(19, 111, 86);
const BOARD_SHADOW = literalColor(0, 0, 0, .39);
const CARRY_SHADOW = literalColor(0, 0, 0, .31);

export const squareName = index => "abcdefgh"[index % 8] + (Math.floor(index / 8) + 1);
export const squareIndex = square => (Number(square[1]) - 1) * 8 + "abcdefgh".indexOf(square[0]);
const centers = Array.from({length:64},(_,index)=>[index % 8 - 3.5,0,3.5 - Math.floor(index / 8)]);
const centerOf = index => centers[index];

function fieldAt(x,z) {
  const column=Math.floor(x+4), row=Math.floor(4-z);
  return column>=0&&column<8&&row>=0&&row<8?squareName(column+row*8):null;
}

const VERTEX = `
attribute vec3 position;
attribute vec3 normal;
attribute vec2 uv;
uniform mat4 camera;
uniform vec3 offset;
uniform float rotation;
varying vec2 textureUV;
varying vec3 worldNormal;
varying vec2 local;
vec2 rotate(vec2 p) {
  float c=cos(rotation), s=sin(rotation);
  return vec2(c*p.x-s*p.y,s*p.x+c*p.y);
}
void main() {
  textureUV=uv;
  local=position.xz;
  vec2 xz=rotate(position.xz);
  vec2 nxz=rotate(normal.xz);
  worldNormal=vec3(nxz.x,normal.y,nxz.y);
  gl_Position=camera*vec4(vec3(xz.x,position.y,xz.y)+offset,1.);
}`;

const FRAGMENT = `
precision mediump float;
varying vec2 textureUV;
varying vec3 worldNormal;
varying vec2 local;
uniform vec4 color;
uniform sampler2D artwork;
uniform int surface;
void main() {
  if (surface==3) {
    float shadow=(1.-smoothstep(.37,1.,length(local)/.40))*color.a;
    gl_FragColor=vec4(color.rgb,shadow);
    return;
  }
  if (surface==0) {
    gl_FragColor=color;
    return;
  }
  vec3 normal=normalize(worldNormal);
  float light=max(0.,dot(normal,normalize(vec3(-.55,1.,.52))));
  if (surface==1) {
    vec4 tile=texture2D(artwork,textureUV);
    if (tile.a<.025) discard;
    gl_FragColor=vec4(tile.rgb*(.91+.12*light),tile.a);
  } else {
    float bevel=max(0.,normal.y)*light*.036;
    gl_FragColor=vec4(color.rgb*(.70+.65*light)+bevel,color.a);
  }
}`;

const addVertex = (mesh, x, y, z, nx, ny, nz, u = 0, v = 0) => mesh.push(x,y,z,nx,ny,nz,u,v);
const order = [0, 1, 2, 0, 2, 3];

function quad(mesh, corners, normal) {
  const uv = [[0,1], [1,1], [1,0], [0,0]];
  for (const index of order) addVertex(mesh, ...corners[index], ...normal, ...uv[index]);
}

function rectangle(mesh, left, right, front, back) {
  quad(mesh, [[left,0,front], [right,0,front], [right,0,back], [left,0,back]], [0,1,0]);
}

function squareOutline(size, width) {
  const mesh = [];
  for (const [left,right,front,back] of [
    [-size,size,-size,-size+width], [-size,size,size-width,size],
    [-size,-size+width,-size+width,size-width], [size-width,size,-size+width,size-width],
  ]) rectangle(mesh,left,right,front,back);
  return mesh;
}

function disk(outer, inner = 0, steps = 40) {
  const mesh = [];
  const add = (angle,radius) => addVertex(mesh,Math.cos(angle)*radius,0,Math.sin(angle)*radius,0,1,0);
  for (let i=0;i<steps;i++) {
    const a=i*2*Math.PI/steps,b=(i+1)*2*Math.PI/steps;
    add(a,inner); add(a,outer); add(b,outer);
    if (inner) { add(a,inner); add(b,outer); add(b,inner); }
  }
  return mesh;
}

function plateMeshes() {
  const face=[], edge=[];
  const profile = [
    [.952,0,-.81], [.99,.013,-.44], [1,.023,0],
    [1,.088,0], [.99,.098,.48], [.962,PLATE_HEIGHT,.8],
  ];
  function ring(angle,[factor,height,ny]) {
    const x=Math.cos(angle),z=Math.sin(angle);
    const radius=factor*PLATE_RADIUS,radial=Math.sqrt(1-ny*ny);
    addVertex(edge,x*radius,height,z*radius,x*radial,ny,z*radial);
  }
  function top(angle) {
    const x=Math.cos(angle),z=Math.sin(angle),radius=profile.at(-1)[0]*PLATE_RADIUS;
    addVertex(face,x*radius,PLATE_HEIGHT,z*radius,0,1,0,.5+x*119.56/260,.5-z*119.56/260);
  }
  for (let i=0;i<56;i++) {
    const a=i*2*Math.PI/56,b=(i+1)*2*Math.PI/56;
    addVertex(face,0,PLATE_HEIGHT,0,0,1,0,.5,.5);
    top(a); top(b);
    for (let level=0;level<profile.length-1;level++) {
      const low=profile[level], high=profile[level+1];
      ring(a,low); ring(b,low); ring(b,high);
      ring(a,low); ring(b,high); ring(a,high);
    }
  }
  return {face,edge};
}

function boardMeshes() {
  const face=[],edge=[];
  const half=BOARD_EDGE, bottom=-.25;
  rectangle(face,-half,half,-half,half);
  for (const [a,b,n] of [
    [[-half,-half],[half,-half],[0,0,-1]], [[half,-half],[half,half],[1,0,0]],
    [[half,half],[-half,half],[0,0,1]], [[-half,half],[-half,-half],[-1,0,0]],
  ]) quad(edge,[[a[0],0,a[1]],[b[0],0,b[1]],[b[0],bottom,b[1]],[a[0],bottom,a[1]]],n);
  return {face,edge};
}

function programFor(gl) {
  const program=gl.createProgram();
  for (const [type,source] of [[gl.VERTEX_SHADER,VERTEX],[gl.FRAGMENT_SHADER,FRAGMENT]]) {
    const shader=gl.createShader(type);
    gl.shaderSource(shader,source);
    gl.compileShader(shader);
    if (!gl.getShaderParameter(shader,gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(shader));
    gl.attachShader(program,shader);
    gl.deleteShader(shader);
  }
  gl.linkProgram(program);
  if (!gl.getProgramParameter(program,gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(program));
  gl.useProgram(program);
  return program;
}

function buildBuffers(gl) {
  const plate=plateMeshes(), board=boardMeshes();
  const arrays={
    table:board.face, tableSide:board.edge, top:plate.face, side:plate.edge,
    last:squareOutline(.461,.056), focus:squareOutline(.485,.034), select:squareOutline(.479,.086),
    target:disk(.098), targetHalo:disk(.131,.092), capture:disk(.407,.342), captureHalo:disk(.442,.405),
    shadow:disk(.398), check:disk(.392,.295),
  };
  const buffers={}, vertices=[];
  for (const [name,mesh] of Object.entries(arrays)) {
    buffers[name]={start:vertices.length/8,count:mesh.length/8};
    vertices.push(...mesh);
  }
  const vbo=gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER,vbo);
  gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(vertices),gl.STATIC_DRAW);
  return buffers;
}

async function loadImage(url, pixels) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`SVG fehlt: ${url}`);
  const svg=new DOMParser().parseFromString(await response.text(),"image/svg+xml").documentElement;
  if (svg.localName!=="svg") throw new Error(`Ungültiges SVG: ${url}`);
  svg.setAttribute("width",String(pixels));
  svg.setAttribute("height",String(pixels));
  const blob=new Blob([new XMLSerializer().serializeToString(svg)],{type:"image/svg+xml"});
  const source=URL.createObjectURL(blob);
  try {
    const image=new Image();
    image.src=source;
    await image.decode();
    return image;
  } finally {
    URL.revokeObjectURL(source);
  }
}

function uploadTexture(gl,image) {
  const texture=gl.createTexture();
  gl.bindTexture(gl.TEXTURE_2D,texture);
  gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,true);
  gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,image);
  gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);
  gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);
  gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR_MIPMAP_LINEAR);
  gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);
  gl.generateMipmap(gl.TEXTURE_2D);
  return texture;
}

const dot = (a,b) => a.reduce((sum,x,i)=>sum+x*b[i],0);
const norm = v => { const magnitude=Math.hypot(...v); return v.map(x=>x/magnitude); };
const cross = (a,b) => [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
function multiply(a,b) {
  const matrix=new Float32Array(16);
  for (let col=0;col<4;col++) for (let row=0;row<4;row++) {
    for (let i=0;i<4;i++) matrix[col*4+row]+=a[i*4+row]*b[col*4+i];
  }
  return matrix;
}

function cameraAt(yaw,tilt,aspect) {
  const back=[Math.sin(yaw)*Math.cos(tilt),Math.sin(tilt),Math.cos(yaw)*Math.cos(tilt)];
  const right=norm(cross([0,1,0],back)),up=cross(back,right);
  const near=.1, far=40;
  // Framing depends only on the viewport, never on the projected corner positions.
  const halfHeight=Math.max(HALF_VIEW_HEIGHT,(HALF_BOARD_DIAGONAL+.36)/aspect);
  const halfWidth=halfHeight*aspect;
  const eye=back.map(value=>value*16);
  const view=[
    right[0],up[0],back[0],0, right[1],up[1],back[1],0, right[2],up[2],back[2],0,
    -dot(right,eye),-dot(up,eye),-dot(back,eye),1,
  ];
  const projection=[
    1/halfWidth,0,0,0,0,1/halfHeight,0,0,0,0,-2/(far-near),0,0,0,-(far+near)/(far-near),1,
  ];
  return {eye,back,right,up,matrix:multiply(projection,view),halfWidth,halfHeight};
}

function approach(current,target,blend) {
  const next=current+(target-current)*blend;
  return Math.abs(next-target)<.001?target:next;
}

export class MarbleScene {
  constructor(canvas) {
    this.canvas=canvas;
    this.gl=canvas.getContext("webgl",{alpha:true,antialias:true});
    if (!this.gl) throw new Error("Für die 3D-Brettansicht ist WebGL erforderlich.");
    const gl=this.gl, program=programFor(gl);
    this.buffers=buildBuffers(gl);
    for (const [name,count,start] of [["position",3,0],["normal",3,3],["uv",2,6]]) {
      const attribute=gl.getAttribLocation(program,name);
      gl.enableVertexAttribArray(attribute);
      gl.vertexAttribPointer(attribute,count,gl.FLOAT,false,32,start*4);
    }
    this.uniform=Object.fromEntries(["camera","offset","rotation","surface","color"].map(name=>[name,gl.getUniformLocation(program,name)]));
    gl.enable(gl.DEPTH_TEST);
    gl.enable(gl.BLEND);
    gl.blendFuncSeparate(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA,gl.ONE,gl.ONE_MINUS_SRC_ALPHA);
    gl.clearColor(0,0,0,0);
    this.ready=false;
    this.board=Array(64).fill(null);
    this.feedback={targets:new Set()};
    this.orientation="w";
    this.topView=false;
    this.viewYaw=DEFAULT_YAW;
    this.viewTilt=DEFAULT_TILT;
    this.heading=0;
    this.turn=null;
    this.frame=null;
    this.lastFrame=null;
    this.moving=false;
    this.cameraHeldAt=null;
    this.reducedMotion=window.matchMedia("(prefers-reduced-motion: reduce)");
    this.reset();
    new ResizeObserver(()=>this.requestFrame()).observe(canvas);
  }

  async load() {
    const entries=await Promise.all([["board",2048],...ASSETS.map(name=>[name,512])].map(async ([key,size])=>{
      const image=await loadImage(`/art/${key}.svg`,size);
      return [key,uploadTexture(this.gl,image)];
    }));
    this.textures=Object.fromEntries(entries);
    if (this.gl.getError()!==this.gl.NO_ERROR) throw new Error("Die Marmor-SVGs konnten nicht als Texturen geladen werden.");
    this.ready=true;
    this.requestFrame();
  }

  reset() {
    this.yaw=DEFAULT_YAW;
    this.tilt=DEFAULT_TILT;
    this.topView=false;
    this.requestFrame();
  }

  setTop(enabled) {
    this.topView=enabled;
    this.requestFrame();
  }

  flip() {
    this.orientation=this.orientation==="w"?"b":"w";
    const target=this.orientation==="b"?Math.PI:0;
    this.turn={from:this.heading,target,start:performance.now()};
    this.requestFrame();
  }

  orbit(dx,dy) {
    const yaw=Math.max(-.74,Math.min(.74,this.yaw-dx*.006));
    const tilt=Math.max(.55,Math.min(MAX_ORBIT_TILT,this.tilt+dy*.006));
    if (!this.topView&&yaw===this.yaw&&tilt===this.tilt) return;
    this.topView=false;
    this.yaw=yaw;
    this.tilt=tilt;
    this.requestFrame();
  }

  holdCamera(held) {
    const now=performance.now();
    if (held) {
      this.cameraHeldAt=now;
      return;
    }
    if (this.cameraHeldAt!==null&&this.turn) this.turn.start+=now-this.cameraHeldAt;
    this.cameraHeldAt=null;
    this.requestFrame();
  }

  requestFrame() {
    if (!this.ready||this.frame!==null) return;
    this.frame=requestAnimationFrame(time=>{
      this.frame=null;
      const elapsed=this.lastFrame===null?16.67:Math.min(time-this.lastFrame,34);
      const moving=this.advanceCamera(time,elapsed);
      this.moving=moving||Boolean(this.feedback.carry);
      this.draw();
      this.lastFrame=moving?time:null;
      if (moving) this.requestFrame();
    });
  }

  advanceCamera(time,elapsed) {
    if (this.cameraHeldAt!==null) return false;
    const reduced=this.reducedMotion.matches;
    const blend=reduced?1:1-Math.exp(-elapsed/CAMERA_EASE_MS);
    const yaw=this.topView?0:this.yaw;
    const tilt=this.topView?TOP_TILT:this.tilt;
    this.viewYaw=approach(this.viewYaw,yaw,blend);
    this.viewTilt=approach(this.viewTilt,tilt,blend);
    if (this.turn) {
      const {from,target,start}=this.turn;
      const progress=reduced?1:Math.max(0,Math.min(1,(time-start)/TURN_MS));
      const ease=progress*progress*(3-2*progress);
      this.heading=from+(target-from)*ease;
      if (progress===1) this.turn=null;
    }
    return this.turn!==null||this.viewYaw!==yaw||this.viewTilt!==tilt;
  }

  update(board,feedback) {
    this.board=board;
    this.feedback=feedback;
    this.requestFrame();
  }

  mesh(name,offset,surface,color=LIGHT,texture=null,rotation=0) {
    const gl=this.gl,{start,count}=this.buffers[name];
    gl.uniform3fv(this.uniform.offset,offset);
    gl.uniform1f(this.uniform.rotation,rotation);
    gl.uniform1i(this.uniform.surface,surface);
    gl.uniform4fv(this.uniform.color,color);
    if (texture) gl.bindTexture(gl.TEXTURE_2D,texture);
    gl.drawArrays(gl.TRIANGLES,start,count);
  }

  draw() {
    if (!this.ready) return;
    const gl=this.gl, canvas=this.canvas;
    const cssWidth=canvas.clientWidth,cssHeight=canvas.clientHeight;
    if (!cssWidth||!cssHeight) return;
    // Keep the same CSS-space projection at every rendering resolution.
    const deviceScale=Math.min(2,window.devicePixelRatio||1);
    const scale=this.moving?Math.min(deviceScale,Math.sqrt(MOTION_PIXEL_BUDGET/(cssWidth*cssHeight))):deviceScale;
    const width=Math.round(cssWidth*scale), height=Math.round(cssHeight*scale);
    if (canvas.width!==width || canvas.height!==height) {
      canvas.width=width;
      canvas.height=height;
    }
    gl.viewport(0,0,width,height);
    gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);
    // A turn from overhead lowers the camera until the opposite side is in view.
    const nearTop=Math.max(0,(this.viewTilt-MAX_ORBIT_TILT)/(TOP_TILT-MAX_ORBIT_TILT));
    const tilt=this.viewTilt-.64*nearTop*Math.sin(this.heading);
    this.camera=cameraAt(this.heading+this.viewYaw,tilt,cssWidth/cssHeight);
    gl.uniformMatrix4fv(this.uniform.camera,false,this.camera.matrix);
    this.mesh("tableSide",[0,0,0],2,GRAPHITE);
    this.mesh("table",[0,0,0],1,LIGHT,this.textures.board);
    const {last,check,selected,focus,targets,carry}=this.feedback;
    const heldIndex=carry?squareIndex(carry.source):-1;
    for (const [index,occupant] of this.board.entries()) {
      if (occupant&&index!==heldIndex) {
        const [x,,z]=centerOf(index);
        this.mesh("shadow",[x+.025,.001,z+.025],3,BOARD_SHADOW);
      }
    }
    if (carry) {
      const [x,,z]=carry.position;
      this.mesh("shadow",[x+.066,.002,z+.048],3,CARRY_SHADOW);
    }
    const mark=(shape,name,y,color)=>{
      const [x,,z]=centerOf(squareIndex(name));
      this.mesh(shape,[x,y,z],0,color);
    };
    if (last) {
      mark("last",last.slice(0,2),.003,LAST_MOVE);
      mark("last",last.slice(2,4),.003,LAST_MOVE);
    }
    if (check) mark("check",check,.005,CHECK);
    if (selected) mark("select",selected,.007,SELECTION);
    for (const target of targets) {
      const occupied=this.board[squareIndex(target)];
      mark(occupied?"captureHalo":"targetHalo",target,.009,LIGHT);
      mark(occupied?"capture":"target",target,.011,TARGET);
    }
    if (focus) mark("focus",focus,.014,FOCUS);
    if (carry?.target&&targets.has(carry.target)) mark("select",carry.target,.017,DROP);
    for (const [index,occupant] of this.board.entries()) {
      if (!occupant||index===heldIndex) continue;
      this.plate(occupant,centerOf(index),this.heading);
    }
    if (carry&&this.board[heldIndex]) {
      this.plate(this.board[heldIndex],carry.position,this.heading);
    }
    this.canvas.dataset.ready="true";
  }

  plate(occupant,position,flip) {
    this.mesh("side",position,2,occupant[0]==="w"?WHITE_EDGE:BLACK_EDGE);
    this.mesh("top",position,1,LIGHT,this.textures[occupant],flip);
  }

  pointerRay(clientX,clientY) {
    if (!this.camera) return null;
    const rect=this.canvas.getBoundingClientRect(), camera=this.camera;
    const x=((clientX-rect.left)/rect.width*2-1)*camera.halfWidth;
    const y=(1-(clientY-rect.top)/rect.height*2)*camera.halfHeight;
    const origin=camera.eye.map((value,i)=>value+x*camera.right[i]+y*camera.up[i]);
    return {rect,pointAt:height=>{
      const distance=(origin[1]-height)/camera.back[1];
      return origin.map((coordinate,i)=>coordinate-camera.back[i]*distance);
    }};
  }

  pick(clientX,clientY) {
    const trace=this.pointerRay(clientX,clientY);
    if (!trace) return null;
    for (const height of [PLATE_HEIGHT,PLATE_HEIGHT/2]) {
      const [x,,z]=trace.pointAt(height);
      const field=fieldAt(x,z);
      if (field&&this.board[squareIndex(field)]) {
        const [cx,,cz]=centerOf(squareIndex(field));
        if (Math.hypot(x-cx,z-cz)<PLATE_RADIUS) return field;
      }
    }
    const [x,,z]=trace.pointAt(0);
    return fieldAt(x,z);
  }

  grabOffset(square,clientX,clientY) {
    const trace=this.pointerRay(clientX,clientY);
    if (!trace) return null;
    const [x,,z]=trace.pointAt(PLATE_HEIGHT+CARRY_HEIGHT);
    const [cx,,cz]=centerOf(squareIndex(square));
    return [cx-x,cz-z];
  }

  holdAt(clientX,clientY,[offsetX,offsetZ]) {
    const trace=this.pointerRay(clientX,clientY);
    if (!trace) return null;
    const {left,right,top,bottom}=trace.rect;
    const inside=clientX>=left&&clientX<right&&clientY>=top&&clientY<bottom;
    const [x,,z]=trace.pointAt(PLATE_HEIGHT+CARRY_HEIGHT);
    const position=[x+offsetX,CARRY_HEIGHT,z+offsetZ];
    // The highlighted field is directly beneath the held plate, independent of its height.
    return {position,target:inside?fieldAt(position[0],position[2]):null};
  }
}
