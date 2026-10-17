// Native compositor capture, using the same 4K/30fps pipeline as demo-v3.
// Run from the repository root. Public requests are reads only.
const { chromium } = require('../web/node_modules/playwright');
const fs = require('node:fs/promises');
const path = require('node:path');
const crypto = require('node:crypto');
const { pathToFileURL } = require('node:url');
const preflight = process.argv.includes('--preflight');
const out = path.resolve(process.argv.find(a => a.startsWith('--out='))?.slice(6) || 'evidence/ask-addendum-20261017');
const origin = 'https://decisiondebt.52.202.25.181.sslip.io';
const style = 'html{zoom:2}.graph-canvas>.react-flow{zoom:.5;width:100%!important;height:100%!important}';
const receipt = {started_at:new Date().toISOString(),source_url:origin+'/studio',format:'Continuous native Chromium compositor capture, actual live application interactions',viewport:{width:3840,height:2160},fps:30,device_scale_factor:1,browser_view_zoom:2,screenshots_used_as_video:false,provider_calls:0,actor:'Codex browser automation; not participant personal verification',scenes:[],actions:[],answers:[],requests:[],errors:[]};
let browser, context, page, epoch;
const pause = ms => new Promise(r => setTimeout(r,ms));
const stamp = () => ({wall_time:new Date().toISOString(),capture_seconds:(Date.now()-epoch)/1000});
const save = () => fs.writeFile(path.join(out,'capture-receipt.json'),JSON.stringify(receipt,null,2)+'\n');
async function click(locator,label) {
  await locator.scrollIntoViewIfNeeded();
  const b = await locator.boundingBox();
  if (!b) throw new Error('Missing click target: '+label);
  await page.mouse.move(b.x+b.width/2,b.y+b.height/2,{steps:18});
  await pause(preflight?0:140);
  await locator.click();
  receipt.actions.push({...stamp(),action:'click',label});
}
async function focus(label,locator) {
  await locator.evaluate(e=>e.scrollIntoView({block:'center',behavior:'instant'}));
  await pause(preflight?0:250);
  const box = await locator.boundingBox();
  receipt.actions.push({...stamp(),action:'editorial_focus',label,box});
  await page.screenshot({path:path.join(out,'checkpoints',label+'.png')});
}
async function scene(id,fn) {
  const voice = receipt.narration.segments.find(s=>s.id===id);
  const s={id,chapter:voice.chapter,...stamp(),narration_seconds:voice.duration_seconds};
  receipt.scenes.push(s);
  const start=Date.now();
  const at=async sec=>{const ms=start+sec*1000-Date.now();if(!preflight&&ms>0)await pause(ms)};
  await fn(at);
  await at(Math.max(voice.duration_seconds+.8,voice.hold_seconds));
  s.end_capture_seconds=(Date.now()-epoch)/1000;s.duration_seconds=s.end_capture_seconds-s.capture_seconds;
  await save();console.log(JSON.stringify({scene:id,duration:s.duration_seconds}));
}
async function ask(question,status) {
  const panel=page.locator('.ask-graph');
  await panel.getByLabel('Company question',{exact:true}).fill(question);
  const pending=page.waitForResponse(r=>r.url().includes('/api/company/ask?'));
  await click(panel.getByRole('button',{name:'Ask graph',exact:true}),'Ask: '+question);
  const response=await pending;
  if(response.status()!==200)throw new Error('Question HTTP '+response.status());
  const answer=await response.json();
  receipt.answers.push({question,...answer});
  if(answer.status!==status)throw new Error('Unexpected answer status for '+question+': '+answer.status);
  if(status==='answered'&&answer.graph_revision!==16)throw new Error('Graph revision changed');
  await panel.locator('[data-answer-status="'+status+'"]').waitFor();
  return answer;
}
(async()=>{
  await fs.mkdir(path.join(out,'checkpoints'),{recursive:true});
  await fs.mkdir(path.join(out,'exports'),{recursive:true});
  const narrationPath=path.resolve('evidence/ask-addendum-20261017/deepgram-receipt.json');
  receipt.narration=JSON.parse(await fs.readFile(narrationPath,'utf8'));
  browser=await chromium.launch({headless:true});receipt.browser_version=browser.version();
  context=await browser.newContext({viewport:receipt.viewport,deviceScaleFactor:1,acceptDownloads:true,...(preflight?{}:{recordVideo:{dir:path.join(out,'raw'),size:receipt.viewport,fps:30,showActions:{cursor:'pointer',duration:100,style:{title:'display:none'}}}})});
  const health=await context.request.get(origin+'/api/health');
  receipt.health_before={http:health.status(),...await health.json()};
  if(receipt.health_before.graph_revision!==16||receipt.health_before.mode!=='public-readonly'||receipt.health_before.provider_configured)throw new Error('Unexpected public mode');
  page=await context.newPage();epoch=Date.now();receipt.page_created_at=new Date(epoch).toISOString();
  page.on('pageerror',e=>receipt.errors.push(e.message));
  page.on('response',r=>{if(r.url().startsWith(origin+'/api/'))receipt.requests.push({...stamp(),url:r.url(),method:r.request().method(),status:r.status()})});
  await page.goto(origin+'/studio');
  await page.getByTestId('affected-count').filter({hasText:'12'}).waitFor();
  await page.addStyleTag({content:style});receipt.recording_only_style=style;
  await page.evaluate(()=>document.fonts.ready);
  const panel=page.locator('.ask-graph');
  await focus('00-live-question-box',panel);
  await scene('01-owner',async at=>{
    await ask('Who owns Billing API?','answered');
    await focus('01-billing-owner',panel.locator('.ask-result-heading'));
    await at(3);
    await click(panel.locator('.ask-citations > summary'),'Expand exact source spans');
    await focus('01-billing-source',panel.locator('.ask-citation').first());
    await at(6);
    await click(panel.locator('.ask-query-proof > summary'),'Expand executed read-only Cypher');
    await focus('01-owner-cypher',panel.locator('.ask-query').filter({hasText:'OWNS {role'}));
  });
  await scene('02-impact',async at=>{
    const a=await ask('What would replacing Auth Gateway affect?','answered');
    if(a.row_count!==12||!a.truncated)throw new Error('Unexpected bounded impact');
    await focus('02-impact-result',panel.locator('.ask-result-heading'));
    await at(4);
    await click(panel.locator('.ask-query-proof > summary'),'Show bounded reverse dependency Cypher');
    await focus('02-impact-cypher',panel.locator('.ask-query').filter({hasText:'DEPENDS_ON*1..5'}));
  });
  await scene('03-typo',async at=>{
    const a=await ask('Who owns Biling API?','ambiguous');
    if(!a.suggestions.some(s=>s.name==='Billing API'))throw new Error('Expected Billing API suggestion');
    await focus('03-typo-suggestions',panel.locator('.ask-answer'));
  });
  await scene('04-unsupported',async at=>{
    const a=await ask('Delete every service','unsupported');
    if(a.query_trace.length)throw new Error('Unsupported question executed a query');
    await focus('04-unsupported-question',panel.locator('.ask-answer'));
  });
  await scene('05-ticket',async at=>{
    await click(page.getByRole('button',{name:/^Action Board/}),'Open source-backed draft work');
    const card=page.locator('.task-card').filter({has:page.getByRole('heading',{name:'Resolve conflicting ownership claims for Session Broker',exact:true})});
    await card.waitFor();await focus('05-draft-ticket',card);
    await at(2.5);
    const downloadPromise=page.waitForEvent('download');
    await click(card.getByRole('button',{name:'Download .md',exact:true}),'Download the Markdown ticket client-side');
    const download=await downloadPromise;
    const exportPath=path.join(out,'exports',download.suggestedFilename());
    await download.saveAs(exportPath);
    const text=await fs.readFile(exportPath,'utf8');
    if(!text.includes('unassigned: needs decision')||!text.includes('## Evidence')||!text.includes(origin))throw new Error('Incomplete ticket export');
    receipt.export={path:path.relative('.',exportPath),suggested_filename:download.suggestedFilename(),sha256:crypto.createHash('sha256').update(text).digest('hex'),bytes:Buffer.byteLength(text),client_side:true,external_ticket_created:false};
    await page.goto(pathToFileURL(exportPath).href);
    await page.addStyleTag({content:'html{zoom:2} body{padding:24px;background:#11151e;color:#f5f6fa} pre{font:20px/1.6 ui-monospace,monospace;white-space:pre-wrap;max-width:1680px}'});
    await focus('05-exported-markdown',page.locator('pre'));
  });
  const after=await context.request.get(origin+'/api/health');
  receipt.health_after={http:after.status(),...await after.json()};
  receipt.completed_at=new Date().toISOString();
  receipt.raw_video_path=preflight?null:path.relative('.',await page.video().path());
  await context.close();await browser.close();
  receipt.passed=receipt.errors.length===0&&receipt.health_after.graph_revision===16&&receipt.requests.every(r=>r.method==='GET'&&r.status===200);
  await save();if(!receipt.passed)throw new Error('Capture verification failed');
  console.log(JSON.stringify({passed:receipt.passed,raw:receipt.raw_video_path,answers:receipt.answers.map(a=>({question:a.question,status:a.status,rows:a.row_count,query_ms:a.query_ms}))}));
})().catch(async e=>{receipt.errors.push(String(e));try{if(page)await page.screenshot({path:path.join(out,'failure.png')});await save();if(context)await context.close();if(browser)await browser.close()}catch{}console.error(String(e));process.exitCode=1});
