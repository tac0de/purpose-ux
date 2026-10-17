#!/usr/bin/env node
/** Original synthetic fixtures. No network requests, source sites or image assets. */
import { mkdirSync, writeFileSync, readFileSync, mkdtempSync, rmSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { tmpdir } from 'node:os';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const cli = process.env.PLAYWRIGHT_CLI || 'playwright-cli';
const render = !process.argv.includes('--manifest-only');
if (process.argv.includes('--check')) {
  const ownership = new Map(), hashes = new Map(), ids = new Set(), summary = {};
  const fail = message => { throw new Error(message); };
  for (const [split,expected] of Object.entries({train:128,val:16,test:32,coverage:6})) {
    const rows=readFileSync(join(root,`data/${split}.jsonl`),'utf8').trim().split('\n').map(JSON.parse);
    if(rows.length!==expected)fail(`${split}: expected ${expected} rows, got ${rows.length}`);
    const balance={}; const groups=new Map();
    for(const row of rows) {
      if(ids.has(row.id))fail(`duplicate id ${row.id}`);ids.add(row.id);
      if(row.split!==split||row.label_source!=='synthetic_rubric'||!row.purpose||!row.context)fail(`bad schema ${row.id}`);
      if(!(split==='coverage'?['T','N','U']:['A','B']).includes(row.label))fail(`bad label ${row.id}`);
      for(const field of ['label','rationale','candidate_order','label_source'])if(Object.hasOwn(row.context,field))fail(`input metadata leakage ${row.id}`);
      if(split!=='coverage')for(const key of [`group:${row.group}`,`family:${row.family}`]) {
        if(ownership.has(key)&&ownership.get(key)!==split)fail(`split overlap ${key}`);ownership.set(key,split);
      }
      const buf=readFileSync(join(root,row.image));
      if(buf.readUInt32BE(16)!==960||buf.readUInt32BE(20)!==640)fail(`wrong PNG dimensions ${row.image}`);
      const hash=createHash('sha256').update(buf).digest('hex');
      if(hashes.has(hash)&&hashes.get(hash)!==split)fail(`image content crosses splits ${row.image}`);hashes.set(hash,split);
      balance[row.label]=(balance[row.label]||0)+1;
      if(!groups.has(row.group))groups.set(row.group,[]);groups.get(row.group).push(row);
    }
    if(split!=='coverage') {
      if(balance.A!==expected/2||balance.B!==expected/2)fail(`${split}: unbalanced A/B`);
      for(const [group,items] of groups) {
        if(items.length!==4||new Set(items.map(x=>x.image)).size!==2)fail(`${group}: purpose/swap pairing missing`);
        for(const image of new Set(items.map(x=>x.image))){const pair=items.filter(x=>x.image===image);if(pair.length!==2||pair[0].purpose===pair[1].purpose||pair[0].label===pair[1].label)fail(`${group}: purpose reversal missing`);}
        for(const purpose of new Set(items.map(x=>x.purpose))){const pair=items.filter(x=>x.purpose===purpose);if(pair.length!==2||pair[0].label===pair[1].label||JSON.stringify(pair[0].candidate_order)!==JSON.stringify([...pair[1].candidate_order].reverse()))fail(`${group}: candidate swap missing`);}
      }
    }
    summary[split]={rows:rows.length,groups:groups.size,labels:balance,families:[...new Set(rows.map(x=>x.family))]};
  }
  console.log(JSON.stringify({status:'pass',scope:'Schema, split families/groups, byte-identical image split isolation, 960x640 dimensions, balanced labels, purpose reversals and candidate swaps. Does not establish user preference or general visual quality.',summary},null,2));process.exit(0);
}
const families = [
  { id:'courses', split:'train', n:6, brand:'Fieldwork Academy', section:'Short courses', item:'Practical typography', type:'Course', verb:'Enroll', facts:['4 weekly sessions','Tuesday · 18:30','Beginner friendly'], options:[['Practical typography','4 weeks','Live feedback'],['Editorial systems','6 weeks','Portfolio project'],['Type foundations','3 weeks','Self-paced']], columns:['Course','Length','Teaching format'], detail:'Compare time commitments and teaching formats before choosing your next course.', action:'The course you saved is open for enrollment.', focus:'enroll in the already-selected course', explore:'choose a course by comparing its length and teaching format' },
  { id:'travel', split:'train', n:6, brand:'Northbound Rail', section:'Rail journeys', item:'Harbor to Meadow', type:'Journey', verb:'Book this train', facts:['08:40 departure','1 h 25 min · direct','Standard seat'], options:[['08:40 direct','1 h 25 min','Changes allowed'],['09:10 express','1 h 05 min','No changes'],['09:35 regional','1 h 50 min','Refundable']], columns:['Departure','Duration','Ticket rules'], detail:'Review departure times and ticket rules to decide which journey fits your plans.', action:'Your selected departure has seats available.', focus:'book the already-selected 08:40 direct train', explore:'compare departure times, journey duration and ticket flexibility' },
  { id:'appointments', split:'train', n:5, brand:'Common Ground Studio', section:'Creative sessions', item:'Introductory ceramics', type:'Session', verb:'Reserve a place', facts:['Saturday · 10:00','Clay and tools included','90-minute workshop'], options:[['Introductory ceramics','Saturday 10:00','Tools included'],['Wheel practice','Sunday 14:00','Prior class needed'],['Glazing workshop','Friday 18:00','Bring fired work']], columns:['Workshop','Next session','Requirements'], detail:'Check materials and prior-experience requirements before selecting a workshop.', action:'Your chosen workshop is ready to reserve.', focus:'reserve the already-selected introductory ceramics session', explore:'compare workshop schedules and participation requirements' },
  { id:'jobs', split:'train', n:5, brand:'Small Teams', section:'Open roles', item:'Interface designer', type:'Role', verb:'Apply for this role', facts:['Remote · UTC ± 3','Full time','Portfolio required'], options:[['Interface designer','Remote','Portfolio required'],['Design systems lead','Hybrid','5 years experience'],['Research associate','On site','Methods sample']], columns:['Role','Work arrangement','Application evidence'], detail:'Compare working arrangements and required application materials before choosing a role.', action:'Continue with the opening you have selected.', focus:'apply for the already-selected interface designer role', explore:'compare roles by working arrangement and application requirements' },
  { id:'events', split:'train', n:5, brand:'Open Practice', section:'Community program', item:'Making useful tools', type:'Event', verb:'Get a ticket', facts:['June 14 · 18:00','Main hall','Talk + discussion'], options:[['Making useful tools','June 14 · 18:00','Talk + discussion'],['Repair together','June 15 · 11:00','Hands-on session'],['Open critique','June 15 · 15:00','Small group review']], columns:['Session','Schedule','Format'], detail:'Explore the schedule and session formats before planning your visit.', action:'Tickets for your selected session are available.', focus:'get a ticket for the already-selected Making useful tools session', explore:'compare the event schedule and session formats' },
  { id:'workspaces', split:'train', n:5, brand:'Corner Rooms', section:'Work spaces', item:'Window desk', type:'Workspace', verb:'Book this desk', facts:['Tomorrow · 09:00–17:00','Quiet floor','Power and Wi-Fi'], options:[['Window desk','Quiet floor','Power + Wi-Fi'],['Team table','Collaborative floor','Whiteboard + display'],['Meeting room','Private room','Video call equipment']], columns:['Space','Environment','Amenities'], detail:'Compare space types and amenities before choosing a place to work.', action:'The desk you selected is available tomorrow.', focus:'book the already-selected window desk for tomorrow', explore:'compare spaces by working environment and available amenities' },
  { id:'library', split:'val', n:4, brand:'Chapter Library', section:'Borrow and discover', item:'Ways of seeing cities', type:'Book', verb:'Reserve this book', facts:['Print edition','Central branch','Available for collection'], options:[['Ways of seeing cities','Print · 240 pages','Central branch'],['The walkable atlas','Large print · 190 pages','Riverside branch'],['Streets in common','Audio · 6 hours','Digital lending']], columns:['Title','Edition','Collection'], detail:'Compare editions and collection locations before choosing what to borrow.', action:'Your selected title can be reserved for collection.', focus:'reserve the already-selected print book Ways of seeing cities', explore:'compare books by edition and collection location' },
  { id:'local_services', split:'test', n:8, brand:'Civic Service Desk', section:'Neighborhood services', item:'Community room request', type:'Service', verb:'Start this request', facts:['Neighborhood residents','Noncommercial gatherings','ID and event summary'], options:[['Community room','Residents','ID + event summary'],['Outdoor activity space','Local groups','Activity + safety plan'],['Equipment loan','Registered clubs','Club ID + item list']], columns:['Service','Who can request','Documents needed'], detail:'Review eligibility and required documents before selecting a service.', action:'Continue with the community room request you selected.', focus:'start the already-selected community room request', explore:'compare services by eligibility and required documents' },
];
const palettes = [['#264b40','#edf5f1'],['#354b83','#eff2fa'],['#86482d','#fcf0e9'],['#635080','#f5f0f9'],['#32616f','#edf6f8'],['#6e5c29','#f8f5e9']];
const esc = x => String(x).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
const baseCss = `*{box-sizing:border-box}body{margin:0;background:#e7e9ed;color:#202729;font-family:Arial,sans-serif;font-size:14px}main{width:960px;height:640px;padding:16px 18px;display:grid;grid-template-columns:1fr 1fr;gap:16px}.candidate{min-width:0;position:relative;background:#fff;border:1px solid #ccd1d6;border-radius:12px;overflow:hidden;height:608px}.label{padding:9px 16px;border-bottom:1px solid #d9dfe3;font-size:13px;font-weight:bold;letter-spacing:.12em;background:#f9fafb}header{padding:15px 20px;border-bottom:1px solid #e7eaed;display:flex;justify-content:space-between;align-items:center;gap:12px}.brand{font-size:15px;font-weight:700;letter-spacing:-.3px}.nav{font-size:11px;color:#606b72;white-space:nowrap}.content{padding:20px 22px}p{line-height:1.5;margin:10px 0 16px}.eyebrow{font-size:11px;letter-spacing:.11em;text-transform:uppercase;color:#65716f;font-weight:700}h1{font-size:29px;line-height:1.12;letter-spacing:-1px;margin:10px 0 12px}h2{font-size:20px;line-height:1.25;letter-spacing:-.4px;margin:12px 0}h3{font-size:14px;margin:0 0 4px}.muted{color:#5c696e;font-size:13px}button{background:var(--accent);border:0;color:#fff;border-radius:6px;font-size:14px;font-weight:700;padding:13px 16px;min-height:43px;cursor:default}.secondary{background:#fff;color:var(--accent);border:1px solid #c8d0ce;padding:9px 12px;min-height:35px;font-size:12px}.feature{background:var(--tint);padding:20px;border-radius:8px;margin:20px 0}.facts{display:grid;gap:12px;margin:16px 0 23px;font-size:14px}.fact{display:flex;gap:10px;align-items:center}.dot{width:6px;height:6px;border-radius:50%;background:var(--accent);flex:none}.link{color:var(--accent);font-size:12px;text-decoration:underline;margin-top:17px}.pill{display:inline-block;border:1px solid #ccd8d2;border-radius:20px;font-size:11px;padding:5px 9px;color:var(--accent);background:#fff}.table{margin:18px 0 14px;border:1px solid #d9dfde;border-radius:7px;overflow:hidden}.row{display:grid;grid-template-columns:1.25fr .85fr 1fr;gap:8px;padding:13px 10px;border-bottom:1px solid #e2e7e5;font-size:12px;line-height:1.4;align-items:start}.row:last-child{border-bottom:0}.row.head{background:var(--tint);font-size:10px;text-transform:uppercase;font-weight:700;padding-top:10px;padding-bottom:10px}.row b{font-size:12px}footer{color:#788184;font-size:10px;position:absolute;bottom:16px;left:22px;right:22px;border-top:1px solid #ecefee;padding-top:10px}.note{border-left:3px solid var(--accent);padding:9px 12px;background:#f5f7f6;font-size:12px;line-height:1.5}.layout1 .feature{border-left:5px solid var(--accent);border-radius:0}.layout2 header{background:var(--accent);color:white}.layout2 .nav{color:#eef3f2}.layout3 .feature{background:#fff;border:1px solid #d4dcd8}.layout3 h1{font-family:Georgia,serif;font-size:31px}.layout3 button{border-radius:2px}`;

function candidate(f, mode, label, variant, altered=false) {
  const [accent,tint]=palettes[(variant+Math.max(0,families.indexOf(f)))%palettes.length];
  const item = f.item;
  let body;
  if(mode==='focused') body=`<div class="eyebrow">${esc(f.section)}</div><h1>${esc(item)}</h1><p class="muted">${esc(f.action)}</p><div class="feature"><span class="pill">${esc(f.type)} selected</span><h2>${esc(item)}</h2><div class="facts">${f.facts.map(x=>`<div class="fact"><i class="dot"></i>${esc(x)}</div>`).join('')}</div><button>${altered?'Save for later':esc(f.verb)}</button></div><div class="link">Browse all ${esc(f.section.toLowerCase())}</div>`;
  else if(mode==='comparative') body=`<div class="eyebrow">${esc(f.section)}</div><h1>Find the right fit.</h1><p class="muted">${esc(f.detail)}</p><div class="table"><div class="row head">${f.columns.map(x=>`<span>${esc(x)}</span>`).join('')}</div>${f.options.map(row=>`<div class="row"><b>${esc(row[0])}</b><span>${esc(row[1])}</span><span>${esc(row[2])}</span></div>`).join('')}</div><div class="note">Select an option to see its complete details and continue.</div><div style="margin-top:17px"><button class="secondary">View selected option</button></div>`;
  else body=`<div class="eyebrow">${esc(f.section)}</div><h1>Welcome back.</h1><p class="muted">Updates and announcements from ${esc(f.brand)}.</p><div class="feature"><h2>What is new this month</h2><p>Read our latest news and team notes.</p><button>Read the news</button></div>`;
  return `<article class="candidate layout${variant%4}" style="--accent:${accent};--tint:${tint}"><div class="label">Candidate ${label}</div><header><div class="brand">${esc(f.brand)}</div><div class="nav">Home &nbsp; Help</div></header><div class="content">${body}</div><footer>Original synthetic interface · Static design fixture</footer></article>`;
}
function composite(f,modes,variant){ return `<!doctype html><html lang="en"><head><meta charset="UTF-8"><title>Original comparison fixture</title><style>${baseCss}</style></head><body><main>${modes.map((m,i)=>candidate(f,m,i?'B':'A',variant)).join('')}</main></body></html>`; }
mkdirSync(join(root,'data/images'),{recursive:true});mkdirSync(join(root,'data/html'),{recursive:true});
const records=[], coverage=[], renders=[];
function addRender(id,html){ const source=`data/html/${id}.html`,image=`data/images/${id}.png`;writeFileSync(join(root,source),html);renders.push({id,source,image,html});return image; }
for(const f of families) for(let g=0;g<f.n;g++){
  const group=`${f.id}-${String(g+1).padStart(2,'0')}`;
  for(let swap=0;swap<2;swap++){
    // Counterbalance candidate position, palette and layout without changing the brief.
    const modes=((g+swap)%2===0)?['focused','comparative']:['comparative','focused'];
    const image=addRender(`${group}-${swap?'reversed':'original'}`,composite(f,modes,g));
    for(const goal of ['focus','explore']){
      const wanted=goal==='focus'?'focused':'comparative'; const label=modes.indexOf(wanted)===0?'A':'B';
      records.push({id:`${group}-${swap}-${goal}`,group,split:f.split,family:f.id,purpose:`${goal==='focus'?'Help a returning visitor':'Help a first-time visitor'} ${f[goal]}.`,context:{audience:goal==='focus'?'A returning visitor with a specific option already chosen.':'A first-time visitor who has not yet chosen an option.',task:goal==='focus'?'Make the selected action available immediately with minimal navigation.':'Support an informed choice using the comparison criteria named in the purpose.',evidence_scope:'Judge only the visible static interface. Do not infer conversion rates, hidden pages, speed, or accessibility behavior.',viewport:{width:960,height:640},language:'en'},image,label,label_source:'synthetic_rubric',rationale:goal==='focus'?`Candidate ${label} names the already-selected option and exposes the requested action on this screen; the other candidate requires opening an option first.`:`Candidate ${label} exposes multiple options with the purpose-specific comparison criteria; the other candidate foregrounds one chosen option and hides the alternatives.`,candidate_order:modes,rubric_version:'1.0'});
    }
  }
}
const f={...families[0],brand:'Workshop Sandbox'};
for(const label of ['T','N','U'])for(let i=0;i<2;i++){
  const group=`coverage-${label.toLowerCase()}-${i+1}`;
  const modes=label==='N'?['news','news']:label==='T'?['focused','focused']:['focused','comparative'];
  const image=addRender(group,composite(f,modes,i));
  coverage.push({id:group,group,split:'coverage',family:'coverage',purpose:label==='U'?'Choose the candidate with a measured higher successful enrollment rate over a month.':`Help a returning visitor ${f.focus}.`,context:{audience:'A returning visitor with a specific option already chosen.',task:label==='U'?'Compare measured real user outcomes.':'Make the selected action available immediately.',evidence_scope:'Only a static screenshot is available; no user study, backend, interaction trace, or measured outcome is supplied.',viewport:{width:960,height:640},language:'en'},image,label,label_source:'synthetic_rubric',rationale:label==='T'?'Both candidates show the same information and direct enrollment action, so the visible evidence supports a tie.':label==='N'?'Neither candidate exposes the selected course or an enrollment action.': 'A static screenshot cannot establish measured successful enrollment rates.',rubric_version:'1.0'});
}
for(const split of ['train','val','test'])writeFileSync(join(root,`data/${split}.jsonl`),records.filter(x=>x.split===split).map(x=>JSON.stringify(x)).join('\n')+'\n');
writeFileSync(join(root,'data/coverage.jsonl'),coverage.map(x=>JSON.stringify(x)).join('\n')+'\n');
writeFileSync(join(root,'data/render_manifest.json'),JSON.stringify({version:1,viewport:{width:960,height:640},renderer:'Playwright CLI headless Chromium',items:renders.map(({html,...x})=>x)},null,2)+'\n');
if(render){
  const scratch=mkdtempSync(join(tmpdir(),'purpose-ux-render-')),session=`purposeux-${process.pid}`;
  const config=join(scratch,'cli.config.json');
  writeFileSync(config,JSON.stringify({browser:{browserName:'chromium',isolated:true,launchOptions:{headless:true},contextOptions:{viewport:{width:960,height:640},deviceScaleFactor:1}}}));
  function call(args){const r=spawnSync(cli,[`-s=${session}`,...args],{cwd:scratch,encoding:'utf8',timeout:240000,maxBuffer:8*1024*1024,env:{...process.env,PLAYWRIGHT_MCP_HEADLESS:'1'}});if(r.error||r.status!==0||/### Error/.test(r.stdout||''))throw new Error(r.error?.message||r.stderr||r.stdout);return r.stdout;}
  try{
    call(['open','about:blank','--config',config]);
    // Batch only four pages per command: bounded CLI calls and useful progress.
    const geometry=[];
    for(let start=0;start<renders.length;start+=4){
      const batch=renders.slice(start,start+4).map(x=>({id:x.id,html:x.html,path:join(root,x.image)}));
      const code=`async(page)=>{const batch=${JSON.stringify(batch)};const results=[];for(const item of batch){await page.setViewportSize({width:960,height:640});await page.setContent(item.html);await page.evaluate(()=>document.fonts.ready);await page.evaluate(()=>new Promise(requestAnimationFrame));const problems=await page.evaluate(()=>{const issues=[];for(const el of document.querySelectorAll('.content,.feature,.table,button,h1,h2,.row,.facts')){const r=el.getBoundingClientRect(),p=el.closest('.candidate').getBoundingClientRect();if(el.scrollWidth>el.clientWidth+1||r.right>p.right+1||r.bottom>p.bottom-35||r.left<p.left-1)issues.push({tag:el.tagName,cls:el.className,text:el.innerText.slice(0,70),box:[r.x,r.y,r.width,r.height]});}return issues;});if(problems.length)throw new Error(item.id+' geometry '+JSON.stringify(problems));await page.screenshot({path:item.path});results.push({id:item.id,clippingIssues:problems.length});}console.log(JSON.stringify(results));}`;
      const codePath=join(scratch,'batch.js');writeFileSync(codePath,code);geometry.push({batch:start,output:call(['run-code','--filename',codePath])});
      process.stdout.write(`Rendered ${Math.min(start+4,renders.length)}/${renders.length}\n`);
    }
    writeFileSync(join(root,'data/render_check.json'),JSON.stringify({renderer:'Playwright CLI headless Chromium',viewport:{width:960,height:640},screens:renders.length,clippingIssues:0,scope:'Bounding boxes and horizontal overflow for candidate content, headings, actions, rows and facts. Representative assets require separate direct visual inspection.'},null,2)+'\n');
  } finally {try{call(['close']);}finally{rmSync(scratch,{recursive:true,force:true});}}
}
console.log(JSON.stringify({train:records.filter(x=>x.split==='train').length,val:records.filter(x=>x.split==='val').length,test:records.filter(x=>x.split==='test').length,coverage:coverage.length,images:renders.length,rendered:render}));
