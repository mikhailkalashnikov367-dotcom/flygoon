const canvas = document.querySelector("#game"), ctx = canvas.getContext("2d"), svg = document.querySelector("#brain");
const grid = 12, cell = canvas.width / grid;
const els = { score:document.querySelector("#score"), action:document.querySelector("#action"), status:document.querySelector("#status"), source:document.querySelector("#source"), provenance:document.querySelector("#provenance"), nodeCount:document.querySelector("#node-count"), edgeCount:document.querySelector("#edge-count"), inputCount:document.querySelector("#input-count"), model:document.querySelector("#model-name"), inputs:document.querySelector("#inputs"), reward:document.querySelector("#reward"), totalReward:document.querySelector("#total-reward"), steps:document.querySelector("#steps"), event:document.querySelector("#event"), dataStatus:document.querySelector("#data-status"), rewardFill:document.querySelector("#reward-fill"), episodes:document.querySelector("#episodes"), epsilon:document.querySelector("#epsilon"), learnedStates:document.querySelector("#learned-states"), averageScore:document.querySelector("#average-score"), history:document.querySelector("#history"), executionCode:document.querySelector("#execution-code"), executionStatus:document.querySelector("#execution-status"), executionTick:document.querySelector("#execution-tick") };
let state = null;
function post(path) { return fetch(path, {method:"POST"}); }
document.querySelector("#simulate").onclick = () => post("/api/simulate");
document.querySelector("#pause").onclick = () => post("/api/pause");
document.querySelector("#reset").onclick = () => post("/api/reset");
document.querySelectorAll("[data-speed]").forEach(button => {
  button.onclick = async () => {
    await post(`/api/speed/${button.dataset.speed}`);
    document.querySelectorAll("[data-speed]").forEach(item => item.classList.toggle("selected", item === button));
  };
});
function drawGame() {
  const background=ctx.createLinearGradient(0,0,canvas.width,canvas.height); background.addColorStop(0,"#102d42"); background.addColorStop(1,"#171332"); ctx.fillStyle=background; ctx.fillRect(0,0,canvas.width,canvas.height);
  ctx.strokeStyle="#214b61"; ctx.lineWidth=1;
  for (let i=0;i<=grid;i++){const p=i*cell;ctx.beginPath();ctx.moveTo(p,0);ctx.lineTo(p,canvas.height);ctx.moveTo(0,p);ctx.lineTo(canvas.width,p);ctx.stroke();}
  ctx.strokeStyle="#3b8290"; ctx.lineWidth=2; ctx.strokeRect(1,1,canvas.width-2,canvas.height-2);
  if (!state) return;
  const fruitX=state.fruit[0]*cell+cell/2, fruitY=state.fruit[1]*cell+cell/2;
  ctx.save(); ctx.shadowColor="#e4518288"; ctx.shadowBlur=18; ctx.fillStyle="#e45182"; ctx.beginPath(); ctx.arc(fruitX,fruitY,cell*.28,0,Math.PI*2); ctx.fill(); ctx.restore();
  ctx.fillStyle="#78b89c"; ctx.beginPath(); ctx.ellipse(fruitX+6,fruitY-13,7,3,-.45,0,Math.PI*2); ctx.fill();
  state.snake.slice().reverse().forEach((p,reverseIndex)=>{const i=state.snake.length-1-reverseIndex; const x=p[0]*cell+cell/2,y=p[1]*cell+cell/2,r=cell*.36; const gradient=ctx.createRadialGradient(x-4,y-5,2,x,y,r); gradient.addColorStop(0,i===0?"#a2eee1":"#a1e2d7"); gradient.addColorStop(1,i===0?"#249985":"#55b9aa"); ctx.fillStyle=gradient; ctx.shadowColor="#2e9d8d55"; ctx.shadowBlur=i===0?10:4; ctx.beginPath(); ctx.arc(x,y,r,0,Math.PI*2); ctx.fill(); ctx.shadowBlur=0;});
  const head=state.snake[0], hx=head[0]*cell+cell/2, hy=head[1]*cell+cell/2; ctx.fillStyle="#173f4b";
  const eyeOffset=state.action==="turn_left"?[-5,-4]:state.action==="turn_right"?[5,-4]:[4,-5]; [1,-1].forEach(sign=>{ctx.beginPath();ctx.arc(hx+eyeOffset[0]+sign*4,hy+eyeOffset[1],2.6,0,Math.PI*2);ctx.fill();});
  els.score.textContent=state.score; els.action.textContent={turn_left:"rẽ trái",straight:"đi thẳng",turn_right:"rẽ phải"}[state.action]||state.action; els.source.textContent="Nguồn đồ thị: "+state.graph_source; els.status.textContent=state.done?"VA CHẠM":state.running?"ĐANG CHẠY":"ĐANG TẠM DỪNG";
  const p=state.provenance||{}; els.provenance.textContent=p.dataset?`Dataset: ${p.dataset} · Truy vấn: ${p.query} · ${p.retrieved}`:"";
  els.nodeCount.textContent=state.node_count; els.edgeCount.textContent=`${state.vfb_edge_count} / ${state.edge_count}`; els.inputCount.textContent=Object.keys(state.inputs).length; els.model.textContent=state.model;
  els.reward.textContent=(state.reward>0?"+":"")+state.reward.toFixed(2); els.totalReward.textContent=state.total_reward.toFixed(2); els.steps.textContent=state.steps; els.dataStatus.textContent=state.data_status;
  const eventLabels={reward_fruit:"🍎 Ăn quả — phần thưởng",punishment_collision:"💥 Va chạm — hình phạt",step_cost:"• Chi phí bước",ready:"Sẵn sàng"}; els.event.textContent=eventLabels[state.event]||state.event;
  els.rewardFill.style.width=Math.min(100,Math.max(4,50+state.reward*4))+"%"; els.rewardFill.style.background=state.reward>0?"#139b8a":state.reward<0?"#e45182":"#c8d9df";
  els.episodes.textContent=state.episodes; els.epsilon.textContent=state.epsilon.toFixed(2); els.learnedStates.textContent=state.learned_states; els.averageScore.textContent=state.average_score.toFixed(2);
  const scores=state.score_history||[], max=Math.max(1,...scores); els.history.innerHTML=scores.map(score=>`<span class="history-bar" title="Điểm: ${score}" style="height:${Math.max(4,score/max*100)}%"></span>`).join("");
  els.inputs.innerHTML=Object.entries(state.inputs).map(([name,value])=>`<div class="input-cell"><b>${value}</b><span>${name.replaceAll("_"," ")}</span></div>`).join("");
  const trace=state.execution_trace||[];
  els.executionCode.innerHTML=trace.map((entry,index)=>`<span class="code-line ${entry.kind} ${index===trace.length-1?"current":""}"><b>${String(index+1).padStart(2,"0")}</b><code>${escapeHtml(entry.text)}</code></span>`).join("");
  els.executionStatus.textContent=state.running?"Đang xử lý vòng lặp thần kinh":"Mô phỏng đang tạm dừng";
  els.executionTick.textContent=state.steps?`tick ${String(state.steps).padStart(4,"0")}`:"tick —";
}
function escapeHtml(value){return value.replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;");}
function drawBrain() {
  if (!state) return; const nodes = new Set(); state.edges.forEach(e=>{nodes.add(e.source);nodes.add(e.target);}); const list=[...nodes], positions={};
  list.forEach((n,i)=>{ const col=i%5,row=Math.floor(i/5); positions[n]=[70+col*120,42+row*88]; });
  svg.innerHTML="";
  state.edges.forEach(e=>{const a=positions[e.source],b=positions[e.target];if(!a||!b)return; const line=document.createElementNS("http://www.w3.org/2000/svg","line");line.setAttribute("x1",a[0]);line.setAttribute("y1",a[1]);line.setAttribute("x2",b[0]);line.setAttribute("y2",b[1]);line.setAttribute("class","edge");svg.appendChild(line);});
  list.forEach(n=>{const [x,y]=positions[n], circle=document.createElementNS("http://www.w3.org/2000/svg","circle"), activity=state.activity[n]||0, isOutput=["turn_left","straight","turn_right"].includes(n), isSelected=isOutput&&n===state.action, isActive=isOutput?isSelected:activity>0;circle.setAttribute("cx",x);circle.setAttribute("cy",y);circle.setAttribute("r",Math.max(5,Math.min(18,10+Math.abs(activity)*3)));circle.setAttribute("class","node "+(isActive?"active":""));svg.appendChild(circle); const label=document.createElementNS("http://www.w3.org/2000/svg","text");label.setAttribute("x",x);label.setAttribute("y",y+32);label.setAttribute("class","node-label");label.textContent=n;svg.appendChild(label);});
}
function drawFlyBrain() {
  if (!state) return;
  const activity = state.activity || {};
  const visual = (activity.visual_left || 0) + (activity.visual_right || 0) + (activity.fruit_left || 0) + (activity.fruit_right || 0) + (activity.fruit_front || 0);
  const central = (activity.VFB_fw106047 || 0) + (activity.approach_front || 0);
  const motor = state.action === "turn_left" || state.action === "turn_right" || state.action === "straight" ? 1 : 0;
  const mushroom = (activity.navigation_left || 0) + (activity.navigation_right || 0) + central;
  [["region-visual", visual], ["region-mushroom", mushroom], ["region-central", central], ["region-motor", motor]].forEach(([id, value]) => {
    const region = document.querySelector(`#${id}`);
    region.classList.toggle("active", value > 0);
    region.style.opacity = value > 0 ? String(Math.min(1, .58 + Math.abs(value) / 20)) : ".82";
  });
}
async function refresh(){try{state=await (await fetch("/api/state")).json();drawGame();drawBrain();drawFlyBrain();}catch(e){els.status.textContent="MẤT KẾT NỐI";}}
setInterval(refresh,100); refresh();
