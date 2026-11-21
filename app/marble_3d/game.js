/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import {MarbleScene,squareIndex,squareName} from "./scene.js";

const byId=id=>document.getElementById(id);
const grid=byId("square-grid");
const canvas=document.querySelector("canvas");
const notice=byId("notice"),dialog=byId("choice");
const sideName={w:"Weiß",b:"Schwarz"};
const pieceName={K:"König",Q:"Dame",R:"Turm",B:"Läufer",N:"Springer",P:"Bauer"};
const outcomes={
  STALEMATE:"Remis durch Patt",
  DRAW_INSUFFICIENT_MATERIAL:"Remis durch unzureichendes Material",
  DRAW_DEAD_POSITION:"Remis durch tote Stellung",
  DRAW_FIVEFOLD_REPETITION:"Remis durch fünffache Wiederholung",
  DRAW_SEVENTY_FIVE_MOVE:"Remis nach der 75-Züge-Regel",
  DRAW_CLAIMED:"Remis beansprucht",
  RESIGNED:"Partie durch Aufgabe beendet",
  RECORDED_RESULT:"Partie beendet",
};
const claimNames={THREEFOLD_REPETITION:"Dreifache Wiederholung",FIFTY_MOVE_RULE:"50-Züge-Regel"};
const cells=new Map();
let state=null, scene=null, busy=false, selected=null, cursor="e2", keyboard=false, pointer=null;
let carry=null;
let replay=null, replayPly=0;

for (let rank=8;rank>=1;rank--) {
  const row=document.createElement("div");
  row.setAttribute("role","row");
  for (const file of "abcdefgh") {
    const square=file+rank, cell=document.createElement("div");
    cell.id=`feld-${square}`;
    cell.setAttribute("role","gridcell");
    cell.setAttribute("aria-label",square);
    row.append(cell);
    cells.set(square,cell);
  }
  grid.append(row);
}

function candidates(source=selected) {
  return source&&state&&!replay?state.moves.filter(move=>move.startsWith(source)):[];
}

function message(text="") {
  notice.textContent=text;
  notice.hidden=!text;
}

function refreshBoard() {
  if (!state) return;
  const shown=replay?replay[replayPly]:state;
  const targets=new Set(candidates().map(move=>move.slice(2,4)));
  for (const [square,cell] of cells) {
    const figure=shown.board[squareIndex(square)];
    let label=`${square}, ${figure?`${pieceName[figure[1]]} (${sideName[figure[0]]})`:"frei"}`;
    if (targets.has(square)) label+=", legales Ziel";
    if (shown.check===square) label+=", im Schach";
    cell.setAttribute("aria-label",label);
    cell.setAttribute("aria-selected",String(square===selected));
  }
  grid.setAttribute("aria-activedescendant",cells.get(cursor).id);
  paintBoard(targets);
}

function paintBoard(targets=new Set(candidates().map(move=>move.slice(2,4)))) {
  if (!state) return;
  const shown=replay?replay[replayPly]:state;
  scene?.update(shown.board,{
    selected,last:shown.last,check:shown.check,targets,
    focus:keyboard&&document.activeElement===grid?cursor:null,carry,
  });
}

function showMoves() {
  const container=byId("move-list");
  container.replaceChildren();
  const entries=state.firstTurn==="b"?[null,...state.san]:state.san;
  byId("empty").hidden=Boolean(state.san.length);
  for (let i=0;i<entries.length;i+=2) {
    const row=document.createElement("li");
    const entriesForRow=[`${state.firstMove+i/2}.`,entries[i]||"…",entries[i+1]||""];
    for (const [column,entry] of entriesForRow.entries()) {
      const field=document.createElement("span");
      field.textContent=entry;
      const offset=state.firstTurn==="b"?1:0;
      if (replay&&column&&entry&&i+column-offset===replayPly) field.setAttribute("aria-current","step");
      row.append(field);
    }
    container.append(row);
  }
  const current=container.querySelector("[aria-current=step]");
  if (current) {
    container.scrollTop+=current.getBoundingClientRect().top-container.getBoundingClientRect().top;
  } else container.scrollTop=replay?0:container.scrollHeight;
}

function showGame() {
  if (!state) return;
  const shown=replay?replay[replayPly]:state;
  const side=sideName[shown.turn];
  const status=state.status;
  let description=outcomes[status]??"Partie beendet";
  if (status==="ACTIVE") description=state.check?`${side} steht im Schach`:`${side} am Zug`;
  if (status==="CHECKMATE") description=`Schachmatt · ${sideName[state.winner]} gewinnt`;
  const finished=replay&&replayPly===replay.length-1&&status!=="ACTIVE";
  const reviewing=shown.check?`${side} steht im Schach`:`${side} am Zug`;
  byId("turn").textContent=replay&&!finished?`Wiedergabe · ${reviewing}`:description;
  byId("side-stone").classList.toggle("dark",shown.turn==="b");
  byId("replay").disabled=busy||(!state.san.length&&!replay);
  byId("replay").textContent=replay?"Zur laufenden Partie":"Partie nachspielen";
  byId("live-actions").hidden=Boolean(replay);
  byId("replay-controls").hidden=!replay;
  if (replay) {
    byId("replay-ply").max=String(replay.length-1);
    byId("replay-ply").value=String(replayPly);
    byId("replay-step").textContent=`${replayPly} von ${replay.length-1}`;
    byId("replay-back").disabled=replayPly===0;
    byId("replay-forward").disabled=replayPly===replay.length-1;
  }
  byId("undo").disabled=busy||!state.undo;
  byId("redo").disabled=busy||!state.redo;
  byId("new").disabled=busy;
  byId("import").disabled=busy;
  byId("claim").hidden=!state.claims.length;
  byId("claim").disabled=busy;
  showMoves();
  refreshBoard();
}

async function send(action,extra={},file=null) {
  if (!state||busy||replay) return;
  endPointer();
  busy=true;
  message();
  showGame();
  try {
    const response=await fetch(file?"/api/import":"/api/game",{
      method:"POST",
      headers:file?{"Content-Type":extra.mime,"X-Board-Revision":String(state.revision)}
        :{"Content-Type":"application/json"},
      body:file??JSON.stringify({action,revision:state.revision,...extra}),
    });
    const result=await response.json();
    if (response.ok) {
      state=result;
      selected=null;
      if (action==="new") cursor=scene?.orientation==="b"?"e7":"e2";
      if (file) message("Datei geladen.");
    } else if (response.status===409&&result.state) {
      state=result.state;
      selected=null;
      message("Die Stellung wurde aktualisiert. Wähle die Figur erneut.");
    } else {
      message(file?"Die Datei konnte nicht gelesen werden. Die aktuelle Partie bleibt erhalten."
        :"Die Aktion ist in dieser Stellung nicht möglich.");
    }
  } catch {
    message("Der lokale Spielprozess ist nicht erreichbar. Starte die Ansicht erneut.");
  } finally {
    busy=false;
    showGame();
  }
}

function choose(title,description,choices) {
  byId("choice-title").textContent=title;
  byId("choice-description").textContent=description;
  const actions=byId("choice-actions");
  actions.replaceChildren();
  for (const [label,command] of choices) {
    const button=document.createElement("button");
    button.type="button";
    button.textContent=label;
    button.addEventListener("click",()=>{
      dialog.close();
      command();
    });
    actions.append(button);
  }
  dialog.showModal();
}

function playDestination(square,moves) {
  const matching=moves.filter(move=>move.slice(2,4)===square);
  if (!matching.length) return false;
  cursor=square;
  if (matching.length===1) {
    send("move",{move:matching[0]});
  } else {
    choose("Bauernumwandlung",`Wähle die neue Figur für ${square}.`,
      matching.map(move=>[pieceName[move[4].toUpperCase()],()=>send("move",{move})]));
  }
  return true;
}

function selectSquare(square) {
  if (!state||busy||!square||replay||state.status!=="ACTIVE") return;
  cursor=square;
  if (playDestination(square,candidates())) return;
  const piece=state.board[squareIndex(square)];
  if (square===selected) selected=null;
  else if (piece?.[0]===state.turn) {
    selected=state.moves.some(move=>move.startsWith(square))?square:null;
    message(selected?"":`Die Figur auf ${square} hat keinen legalen Zug.`);
  } else if (selected) {
    message(`${square} ist kein legales Zielfeld für die gewählte Figur.`);
  }
  refreshBoard();
}

grid.addEventListener("focus",()=>{
  if (!pointer) keyboard=true;
  refreshBoard();
});
grid.addEventListener("blur",refreshBoard);
grid.addEventListener("keydown",event=>{
  const shift={ArrowLeft:[-1,0],ArrowRight:[1,0],ArrowUp:[0,1],ArrowDown:[0,-1]}[event.key];
  if (pointer) {
    if (event.key==="Escape") {
      selected=null;
      message();
      cancelPointer();
    }
    if (shift||["Enter"," ","Escape"].includes(event.key)) event.preventDefault();
    return;
  }
  keyboard=true;
  if (shift) {
    const index=squareIndex(cursor);
    const side=scene?.orientation==="b"?-1:1;
    const file=Math.max(0,Math.min(7,index%8+shift[0]*side));
    const rank=Math.max(0,Math.min(7,Math.floor(index/8)+shift[1]*side));
    cursor=squareName(rank*8+file);
  } else if (event.key==="Enter"||event.key===" ") selectSquare(cursor);
  else if (event.key==="Escape") {
    selected=null;
    message();
  } else return;
  event.preventDefault();
  refreshBoard();
});

function endPointer() {
  const id=pointer?.id;
  if (pointer?.mode==="carry") scene.holdCamera(false);
  pointer=null;
  carry=null;
  canvas.classList.remove("is-grabbing");
  if (id!==undefined&&canvas.hasPointerCapture(id)) canvas.releasePointerCapture(id);
}

function cancelPointer() {
  if (!pointer) return;
  endPointer();
  refreshBoard();
}

canvas.addEventListener("pointerdown",event=>{
  if (!scene?.camera||!state||pointer||!event.isPrimary||event.button!==0) return;
  // Native canvas focusing would otherwise take focus back from the keyboard grid.
  event.preventDefault();
  const {clientX:x,clientY:y}=event;
  const source=scene.pick(x,y);
  const shown=replay?replay[replayPly]:state;
  const occupant=source&&shown.board[squareIndex(source)];
  const offset=!busy&&occupant?.[0]===state.turn&&candidates(source).length
    ?scene.grabOffset(source,x,y):null;
  pointer={
    id:event.pointerId,x,y,source,offset,moved:false,
    mode:offset?"carry":occupant?"click":"orbit",
  };
  keyboard=false;
  grid.focus({preventScroll:true});
  if (offset) {
    scene.holdCamera(true);
    canvas.classList.add("is-grabbing");
  }
  canvas.setPointerCapture(event.pointerId);
});

canvas.addEventListener("pointermove",event=>{
  if (event.pointerId!==pointer?.id) return;
  const dx=event.clientX-pointer.x,dy=event.clientY-pointer.y;
  if (!pointer.moved&&Math.hypot(dx,dy)<6) return;
  pointer.moved=true;
  pointer.x=event.clientX;
  pointer.y=event.clientY;
  if (pointer.mode==="orbit") {
    canvas.classList.add("is-grabbing");
    scene.orbit(dx,dy);
    byId("top-view").setAttribute("aria-pressed","false");
  } else if (pointer.mode==="carry") {
    const held=scene.holdAt(event.clientX,event.clientY,pointer.offset);
    if (!held) return;
    const first=!carry;
    carry={...held,source:pointer.source};
    if (first) {
      selected=pointer.source;
      cursor=selected;
      message();
      refreshBoard();
    } else paintBoard();
  }
});

canvas.addEventListener("pointerup",event=>{
  if (event.pointerId!==pointer?.id) return;
  const {moved,source,offset}=pointer;
  const landing=carry?scene.holdAt(event.clientX,event.clientY,offset)?.target:null;
  const wasHolding=Boolean(carry);
  endPointer();
  if (wasHolding) {
    if (landing&&playDestination(landing,candidates(source))) {
      refreshBoard();
      return;
    }
    if (landing&&landing!==source) {
      message(`${landing} ist kein legales Zielfeld für die gewählte Figur.`);
    }
  } else if (!moved) {
    selectSquare(source);
  }
  refreshBoard();
});

for (const type of ["pointercancel","lostpointercapture"]) canvas.addEventListener(type,event=>{
  if (event.pointerId===pointer?.id) cancelPointer();
});
window.addEventListener("blur",cancelPointer);

function seekReplay(step) {
  if (!replay) return;
  replayPly=Math.max(0,Math.min(step,replay.length-1));
  showGame();
}

byId("replay").addEventListener("click",async()=>{
  if (!state||busy) return;
  endPointer();
  selected=null;
  busy=true;
  message();
  showGame();
  try {
    const response=await fetch(replay?"/api/game":"/api/replay");
    if (!response.ok) throw new Error();
    const result=await response.json();
    if (replay) {
      state=result;
      replay=null;
    } else if (result.revision===state.revision) {
      replay=result.frames;
      replayPly=0;
    } else {
      const live=await fetch("/api/game");
      if (!live.ok) throw new Error();
      state=await live.json();
      message("Die Partie hat sich geändert. Öffne die Wiedergabe erneut.");
    }
  } catch {
    message("Die lokale Partie konnte nicht gelesen werden.");
  } finally {
    busy=false;
    showGame();
    if (document.activeElement===document.body) byId("replay").focus();
  }
});
byId("replay-ply").addEventListener("input",event=>seekReplay(event.target.valueAsNumber));
byId("replay-back").addEventListener("click",()=>seekReplay(replayPly-1));
byId("replay-forward").addEventListener("click",()=>seekReplay(replayPly+1));

byId("undo").addEventListener("click",()=>send("undo"));
byId("redo").addEventListener("click",()=>send("redo"));
byId("import").addEventListener("click",()=>byId("import-file").click());
byId("import-file").addEventListener("change",event=>{
  const file=event.target.files[0];
  event.target.value="";
  if (!file||!state||busy) return;
  const suffix=file.name.toLowerCase().split(".").pop();
  const limit=suffix==="pgn"?262144:suffix==="fen"?4096:0;
  if (!file.size||file.size>limit) {
    message("Wähle eine PGN-Datei bis 256 KiB oder eine FEN-Datei bis 4 KiB.");
    return;
  }
  const open=()=>send("import",{mime:`application/x-chess-${suffix}`},file);
  if (state.san.length||state.redo||state.status!=="ACTIVE") {
    choose("Datei laden?", "Die Datei ersetzt die aktuelle Stellung und ihre Zugliste.",
      [["Datei laden",open]]);
  } else open();
});
byId("new").addEventListener("click",()=>{
  if (state.san.length&&state.status==="ACTIVE") {
    choose("Neue Partie beginnen?", "Die laufende Stellung und die Zugliste werden zurückgesetzt.",
      [["Neue Partie beginnen",()=>send("new")]]);
  } else send("new");
});
byId("claim").addEventListener("click",()=>{
  choose("Remis beanspruchen","Wähle die zutreffende Regel.",
    state.claims.map(({reason,move})=>[
      claimNames[reason]+(move?` nach ${move.slice(0,2)}–${move.slice(2)}`:""),
      ()=>send("claim",{reason,move}),
    ]));
});

byId("flip").addEventListener("click",()=>{
  if (!scene?.ready) return;
  cancelPointer();
  scene.flip();
  byId("flip").setAttribute("aria-pressed",String(scene.orientation==="b"));
  refreshBoard();
});
byId("top-view").addEventListener("click",()=>{
  if (!scene?.ready) return;
  cancelPointer();
  scene.setTop(!scene.topView);
  byId("top-view").setAttribute("aria-pressed",String(scene.topView));
});
byId("reset-view").addEventListener("click",()=>{
  cancelPointer();
  scene?.reset();
  byId("top-view").setAttribute("aria-pressed","false");
});

async function init() {
  try {
    const response=await fetch("/api/game");
    if (!response.ok) throw new Error();
    state=await response.json();
    showGame();
  } catch {
    message("Die lokale Partie konnte nicht geladen werden. Starte den Spielprozess erneut.");
  }
  const sceneStatus=byId("scene-status");
  try {
    scene=new MarbleScene(canvas);
    await scene.load();
    sceneStatus.textContent="";
    refreshBoard();
  } catch (error) {
    sceneStatus.textContent=error.message;
  }
  canvas.addEventListener("webglcontextlost",()=>{
    sceneStatus.textContent="Die 3D-Grafik wurde unterbrochen. Lade den Tab neu, um die laufende Partie weiterzuspielen.";
  });
}

init();
