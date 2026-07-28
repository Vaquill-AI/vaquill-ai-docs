import { chromium } from 'playwright';
const OUT=process.env.OUT, BASE='https://app.vaquill.ai';
const only=process.argv[2];
const SHOTS=[
 { name:'step-palette', url:'/workflows/builder/new', wait:6000, steps: async p => {
     const b=p.locator('button:has-text("Add first step")').first();
     if(await b.count()){ await b.click({timeout:8000}).catch(()=>{}); await p.waitForTimeout(2500);} } },
 { name:'branch-editor', url:'/workflows/builder/new', wait:6000, steps: async p => {
     const g=p.locator('button:has-text("Graph")').first();
     if(await g.count()){ await g.click({timeout:6000}).catch(()=>{}); await p.waitForTimeout(2500);} } },
 { name:'nl-generate', url:'/workflows/custom', wait:6000, steps: async p => {
     for(const t of ['Describe','Generate','New workflow','Create']){
       const b=p.locator(`button:has-text("${t}")`).first();
       if(await b.count()){ await b.click({timeout:5000}).catch(()=>{}); await p.waitForTimeout(2500); break; } } } },
 { name:'playbook-lint', url:'/playbooks/cfb7dd3d-6369-43a8-9faf-917d941a4942', wait:6500, steps: async p => {
     for(const t of ['Structure','Lint','Health','Check']){
       const b=p.locator(`text=${t}`).first();
       if(await b.count()){ await b.click({timeout:5000}).catch(()=>{}); await p.waitForTimeout(2500); break; } } } },
 { name:'mcp-settings', url:'/settings', wait:5000, steps: async p => {
     const m=p.locator('text=MCP').first();
     if(await m.count()){ await m.click({timeout:6000}).catch(()=>{}); await p.waitForTimeout(2500);} } },
];
const DECHROME=()=>{document.querySelectorAll('div,section,span,a,button').forEach(el=>{const r=el.getBoundingClientRect();
 if(r.height>90)return; if(el.querySelectorAll('*').length>25)return;
 const t=(el.textContent||'').trim().toLowerCase().replace(/\s+/g,' ');
 if((t.includes('free trial')&&t.includes('days left'))||/^upgrade \d+d left$/.test(t)) el.style.visibility='hidden';});
 document.querySelectorAll('[role="dialog"]').forEach(el=>{const t=(el.textContent||'').toLowerCase();
  if(/\d+ of \d+/.test(t)||(t.includes('next')&&t.includes('back'))) el.remove();});};
const b=await chromium.launch({executablePath:process.env.CHROME_BIN});
const ctx=await b.newContext({storageState:OUT+'/auth-state.json',viewport:{width:1440,height:900},deviceScaleFactor:2});
const p=await ctx.newPage(); await p.emulateMedia({colorScheme:'light'});
for(const s of SHOTS){ if(only&&s.name!==only)continue;
 try{ await p.goto(BASE+s.url,{waitUntil:'domcontentloaded',timeout:60000}); await p.waitForTimeout(s.wait);
  await p.keyboard.press('Escape').catch(()=>{}); await s.steps(p);
  await p.evaluate(DECHROME); await p.waitForTimeout(800);
  await p.screenshot({path:`${OUT}/shots/raw/${s.name}.png`}); console.log('OK  '+s.name);
 }catch(e){ console.log('ERR '+s.name+' '+e.message.split('\n')[0].slice(0,60)); } }
await b.close();
