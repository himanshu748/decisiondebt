const { chromium } = require('../web/node_modules/playwright');
const fs = require('node:fs/promises');
const path = require('node:path');
const root = path.resolve('.');
const VIEW_STYLE='html{zoom:2}.graph-canvas>.react-flow{zoom:.5;width:100%!important;height:100%!important}';
const preflight=process.argv.includes('--preflight');
const out = path.join(root,preflight?'work/demo-4k/preflight':'evidence/demo-v3');
const receipt = { started_at:new Date().toISOString(), format:'Continuous Chromium compositor video capture; actual application interactions', viewport:{width:3840,height:2160}, device_scale_factor:1, browser_view_zoom:2, fps:30, screenshots_used_as_video:false, actor:'Automated browser choreography; not participant verification', scenes:[], actions:[], writes:[], errors:[], provider_calls:0 };
let page, epoch;
const stamp = ()=>({wall_time:new Date().toISOString(),capture_seconds:(Date.now()-epoch)/1000});
const pause = ms=>new Promise(r=>setTimeout(r,ms));
async function save(){await fs.writeFile(path.join(out,'capture-receipt.json'),JSON.stringify(receipt,null,2)+'\n');}
async function click(locator,label){
 const graphNode=await locator.evaluate(e=>e.classList.contains('react-flow__node'));
 if(graphNode) await scrollTo(page.locator('.graph-panel'));
 else await locator.evaluate(e=>e.scrollIntoView({block:'center',inline:'nearest',behavior:'instant'}));
 await pause(180);
 const b=await locator.evaluate(e=>{const r=e.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height}});
 const point={x:b.x+b.width/2,y:b.y+b.height/2};
 const onTarget=await locator.evaluate((e,p)=>e.contains(document.elementFromPoint(p.x,p.y)),point);
 if(!onTarget)throw new Error('Pointer target is obscured: '+label);
 if(b) await page.mouse.move(b.x+b.width/2,b.y+b.height/2,{steps:22});
 await pause(220);await page.mouse.click(point.x,point.y);
 receipt.actions.push({...stamp(),action:'click',label});
}
async function scrollTo(locator){
 const b=await locator.evaluate(e=>{const r=e.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height}});
 if(b){ await page.mouse.move(3810,1000,{steps:10});await page.mouse.wheel(0,b.y-160);await pause(850); }
}
async function focus(name,locator){
 let box=await locator.evaluate(e=>{const r=e.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height}});
 if(/live-paths|expanded-graph/.test(name)) box=await page.locator('.react-flow__node').evaluateAll(nodes=>{const r=nodes.map(n=>n.getBoundingClientRect());const x=Math.min(...r.map(b=>b.left)),y=Math.min(...r.map(b=>b.top));return {x,y,width:Math.max(...r.map(b=>b.right))-x,height:Math.max(...r.map(b=>b.bottom))-y}});
 receipt.actions.push({...stamp(),action:'editorial_focus',label:name,box});
 if(!preflight) await page.screenshot({path:path.join(out,'checkpoints',name+'.png')});
}
async function fitGraph(){
 const b=await page.getByRole('button',{name:'Fit View',exact:true}).evaluate(e=>e.getBoundingClientRect().toJSON());
 await page.mouse.move(b.x+b.width/2,b.y+b.height/2,{steps:18});
 await page.mouse.click(b.x+b.width/2,b.y+b.height/2);await pause(500);
 receipt.actions.push({...stamp(),action:'fit_graph',label:'Native Fit View after capture-only display scaling'});
}
async function scene(id,fn){
 const narration=JSON.parse(await fs.readFile(path.join(root,'evidence/demo-v3/deepgram-receipt.json'),'utf8')).segments.find(s=>s.id===id);
 const s={id,chapter:narration.chapter,...stamp(),narration_seconds:narration.duration_seconds};
 receipt.scenes.push(s);console.log(JSON.stringify({scene:id,event:'start',...stamp()}));await save();
 const start=Date.now();
 const at=async seconds=>{if(preflight)return;const ms=start+seconds*1000-Date.now();if(ms>0)await pause(ms);};
 await fn(at);
 await at(narration.duration_seconds+1.8);
 s.end_capture_seconds=(Date.now()-epoch)/1000;s.end_wall_time=new Date().toISOString();
 s.duration_seconds=s.end_capture_seconds-s.capture_seconds;
 await save();console.log(JSON.stringify({scene:id,event:'end',duration_seconds:s.duration_seconds}));
}
(async()=>{
 await fs.mkdir(path.join(out,'checkpoints'),{recursive:true});
 const envText=await fs.readFile('work/demo-4k/recording.env','utf8');
 const token=envText.split('\n').find(l=>l.startsWith('ADMIN_TOKEN=')).slice('ADMIN_TOKEN='.length);
 const browser=await chromium.launch({headless:true});
 receipt.browser_version=browser.version();
 const context=await browser.newContext({viewport:receipt.viewport,deviceScaleFactor:1,...(preflight?{}:{recordVideo:{dir:path.join(out,'raw'),size:receipt.viewport,fps:30,showActions:{cursor:'pointer',duration:100,style:{title:'display:none'}}}}),reducedMotion:'no-preference'});
 page=await context.newPage();epoch=Date.now();receipt.page_created_at=new Date(epoch).toISOString();
 page.on('pageerror',e=>receipt.errors.push(String(e)));
 page.on('response',async response=>{
  const url=response.url();const request=response.request();
  if(request.method()==='POST'&&url.includes('/api/')){
   let body;try{body=await response.json()}catch{body=null}
   receipt.writes.push({...stamp(),url,method:'POST',status:response.status(),response:body});
  }
 });
 await page.goto('http://127.0.0.1:8002/');
 await page.addStyleTag({content:VIEW_STYLE});receipt.recording_only_style=VIEW_STYLE;
 await page.getByRole('heading',{name:'Replace OrionAuth with NovaID',exact:true}).waitFor();
 await page.evaluate(()=>document.fonts.ready);
 await pause(1200);
 await scene('01-intro',async at=>{
  await focus('01-landing',page.locator('.landing-hero'));
  await page.mouse.move(1700,760,{steps:25});await at(6);
  await page.mouse.move(2300,1020,{steps:25});
 });
 await click(page.getByRole('link',{name:'Explore the live company brain',exact:true}),'Open studio');
 await page.locator('.metrics strong').first().waitFor();
 await page.addStyleTag({content:VIEW_STYLE});
 const previewBefore=await (await context.request.get('http://127.0.0.1:8002/api/decisions/dec-auth-002/preview')).json();
 receipt.preview_before=previewBefore;
 if(previewBefore.counts.services!==12||previewBefore.decision_status!=='proposed')throw new Error('Unexpected baseline');
 await scene('02-impact',async at=>{
  await focus('02-impact-metrics',page.locator('.metrics'));await at(7);
  await scrollTo(page.locator('.graph-panel'));await fitGraph();await focus('02-live-paths',page.locator('.graph-layout'));await at(13);
  await page.mouse.move(2050,900,{steps:25});
 });
 await scene('03-conflict',async at=>{
  await click(page.locator('.react-flow__node[data-id="svc-session-broker"]'),'Select Session Broker');
  await page.getByRole('button',{name:/^doc-021/}).waitFor();
  await scrollTo(page.locator('.evidence-rail'));
  await focus('03-conflicting-owners',page.locator('.evidence-rail'));await at(7.5);
  await click(page.getByRole('button',{name:/^doc-021/}),'Open original ownership source');
  await page.getByRole('dialog',{name:'Source evidence'}).waitFor();
  await focus('03-original-source',page.getByRole('dialog',{name:'Source evidence'}));await at(14.8);
  await click(page.getByRole('button',{name:'Close source evidence'}),'Close source');
 });
 await scene('04-unowned',async at=>{
  await click(page.locator('.react-flow__node[data-id="svc-token-cache"]'),'Select Token Cache');
  await page.getByText('Unassigned. No verified primary owner.',{exact:true}).waitFor();
  await scrollTo(page.locator('.evidence-rail'));await focus('04-missing-owner',page.locator('.evidence-rail'));await at(10);
 });
 await click(page.getByRole('button',{name:'Evidence',exact:true}),'Open evidence view');
 await scene('05-drift',async at=>{
  await page.getByLabel('Search source aliases').fill('OrionAuth');
  await click(page.getByRole('button',{name:'Search sources',exact:true}),'Native full-text alias search');
  await page.getByRole('heading',{name:/verified alias matches/}).waitFor();
  await scrollTo(page.locator('.drift-grid'));
  await focus('05-three-drift-tiers',page.locator('.drift-grid'));await at(8.5);
  await click(page.locator('section.surface').filter({has:page.getByRole('heading',{name:'Unlinked obsolete mentions',exact:true})}).getByRole('button',{name:/^doc-002/}),'Inspect unlinked mention source');
  await page.getByRole('dialog',{name:'Source evidence'}).waitFor();
  await focus('05-unlinked-mention',page.getByRole('dialog',{name:'Source evidence'}));await at(15.6);
  await click(page.getByRole('button',{name:'Close source evidence'}),'Close mention source');
 });
 await scrollTo(page.locator('section.surface').filter({has:page.getByRole('heading',{name:'Investigation trace',exact:true})}));
 await scene('06-agent',async at=>{
  await focus('06-recorded-provider-coverage',page.locator('.trace-coverage'));await at(7.5);
  const step=page.locator('.trace-step').filter({hasText:'read evidence'}).first();
  await click(step.locator('summary'),'Inspect a retained rejected tool call');
  await scrollTo(step);await focus('06-retained-tool-call',step);await at(14.2);
  await click(step.locator('summary'),'Close trace detail');
 });
 receipt.private_auth_start=stamp();
 await click(page.getByRole('button',{name:'Local admin',exact:true}),'Unlock isolated local actions');
 await page.getByLabel('Admin token',{exact:true}).fill(token);
 await click(page.getByRole('button',{name:'Unlock local actions',exact:true}),'Confirm local unlock');
 receipt.private_auth_end=stamp();
 await click(page.getByRole('button',{name:/^Action Board/}),'Open action board');
 const conflictTask=page.locator('.task-card').filter({has:page.getByRole('heading',{name:'Resolve conflicting ownership claims for Session Broker',exact:true})});
 await conflictTask.waitFor();await scrollTo(page.locator('.action-grid'));
 await scene('07-actions',async at=>{
  await focus('07-source-backed-drafts',page.locator('.action-grid'));await at(5);
  await click(conflictTask.getByRole('button',{name:'Approve locally',exact:true}),'Request local task approval');
  await page.getByRole('dialog',{name:'Confirm local approval'}).waitFor();
  await focus('07-separate-confirmation',page.getByRole('dialog',{name:'Confirm local approval'}));await at(11.5);
  await click(page.getByRole('button',{name:'Confirm local approval',exact:true}),'Confirm only the local task');
  await conflictTask.getByText('approved',{exact:true}).waitFor();
  await focus('07-task-approved',conflictTask);
 });
 await click(page.getByRole('button',{name:'Preview',exact:true}),'Return to preview');
 await click(page.getByRole('button',{name:'Import source',exact:true}),'Open synthetic import');
 await scene('08-import',async at=>{
  await focus('08-import-source',page.getByRole('dialog',{name:'Import synthetic evidence'}));await at(6);
  await click(page.getByRole('button',{name:'Import and refresh live preview',exact:true}),'Import explicit dependency');
  await page.getByTestId('affected-count').filter({hasText:'13'}).waitFor();
  await scrollTo(page.locator('.metrics'));await focus('08-thirteen-affected',page.locator('.metrics'));await at(11.5);
  await scrollTo(page.locator('.graph-panel'));
  await fitGraph();
  await click(page.locator('.react-flow__node[data-id="svc-external-portal"]'),'Select newly affected External Portal');
  await focus('08-expanded-graph',page.locator('.graph-layout'));
  receipt.preview_after_import=await (await context.request.get('http://127.0.0.1:8002/api/decisions/dec-auth-002/preview')).json();
 });
 await click(page.getByRole('button',{name:'Import source',exact:true}),'Update the same ticket');
 await scene('09-retract',async at=>{
  await click(page.getByRole('button',{name:'Use retraction text',exact:true}),'Remove this source assertion');
  await focus('09-retraction-text',page.getByRole('dialog',{name:'Import synthetic evidence'}));await at(5.5);
  await click(page.getByRole('button',{name:'Import and refresh live preview',exact:true}),'Import source-specific retraction');
  await page.getByTestId('affected-count').filter({hasText:'12'}).waitFor();
  await scrollTo(page.locator('.metrics'));await focus('09-back-to-twelve',page.locator('.metrics'));
  receipt.preview_after_retraction=await (await context.request.get('http://127.0.0.1:8002/api/decisions/dec-auth-002/preview')).json();
 });
 await click(page.getByRole('button',{name:'Evidence',exact:true}),'Inspect live query proof');
 await scrollTo(page.locator('.query-details'));
 await click(page.locator('.query-details > summary'),'Expand actual measured Cypher');
 const query2=page.locator('.query').filter({hasText:'DEPENDS_ON*1..5'});
 await scrollTo(query2);
 await scene('10-query',async at=>{
  await focus('10-load-bearing-cypher',query2);await at(9);
  await page.mouse.move(3810,1000,{steps:10});await page.mouse.wheel(0,450);await pause(900);
  await focus('10-connected-projects-query',page.locator('.query').filter({hasText:'via_service'}));
 });
 await page.goto('http://decisiondebt.52.202.25.181.sslip.io:8081/studio');
 await page.locator('.metrics strong').first().waitFor();await page.addStyleTag({content:VIEW_STYLE});
 await scrollTo(page.locator('.graph-panel'));await fitGraph();await page.evaluate(()=>window.scrollTo({top:0,behavior:'instant'}));
 await page.getByRole('button',{name:'Public read-only demo',exact:true}).waitFor();
 await scene('11-public',async at=>{
  await focus('11-live-public-demo',page.locator('body'));
  await page.mouse.move(205,2030,{steps:25});await at(7);
 });
 receipt.completed_at=new Date().toISOString();receipt.raw_video_path=preflight?null:path.relative(root,await page.video().path());
 await context.close();await browser.close();
 receipt.passed=receipt.errors.length===0&&receipt.preview_after_import.counts.services===13&&receipt.preview_after_retraction.counts.services===12&&receipt.preview_after_retraction.decision_status==='proposed';
 await save();console.log(JSON.stringify({completed:true,passed:receipt.passed,raw:receipt.raw_video_path}));
 if(!receipt.passed)process.exitCode=1;
})().catch(async e=>{receipt.errors.push(String(e));if(page)try{await page.screenshot({path:'work/demo-4k/failure.png'});await fs.writeFile('work/demo-4k/failure-ax.txt',await page.locator('body').ariaSnapshot())}catch{}await save();console.error(e);process.exit(1)});
