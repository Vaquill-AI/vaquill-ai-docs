// One launcher per built-in workflow. Each renders that workflow's own document
// slots and typed input form, so these are not interchangeable.
import { chromium } from 'playwright';
import fs from 'fs';
const OUT = process.env.OUT, BASE = 'https://app.vaquill.ai';
const MAP = JSON.parse(fs.readFileSync(OUT + '/wf_map.json', 'utf8'));
const DECHROME = () => {
  document.querySelectorAll('div,section,span,a,button').forEach(el => {
    const r = el.getBoundingClientRect();
    if (r.height > 90 || el.querySelectorAll('*').length > 25) return;
    const t = (el.textContent || '').trim().toLowerCase().replace(/\s+/g, ' ');
    if ((t.includes('free trial') && t.includes('days left')) || /^upgrade \d+d left$/.test(t)) el.style.visibility = 'hidden';
  });
  document.querySelectorAll('[role="dialog"]').forEach(el => {
    const t = (el.textContent || '').toLowerCase();
    if (/\d+ of \d+/.test(t) || (t.includes('next') && t.includes('back'))) el.remove();
  });
};
const b = await chromium.launch({ executablePath: process.env.CHROME_BIN });
const ctx = await b.newContext({ storageState: OUT + '/auth-state.json', viewport: { width: 1440, height: 1150 }, deviceScaleFactor: 2 });
const p = await ctx.newPage(); await p.emulateMedia({ colorScheme: 'light' });
let ok = 0, bad = [];
for (const [slug, wfid] of Object.entries(MAP)) {
  try {
    await p.goto(`${BASE}/workflows/${wfid}`, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForTimeout(4200);
    await p.keyboard.press('Escape').catch(()=>{});
    await p.evaluate(DECHROME); await p.waitForTimeout(500);
    const body = (await p.locator('body').innerText().catch(()=>'')).slice(0, 200);
    if (/not found|404|unavailable/i.test(body)) { bad.push(slug + ' (not available)'); continue; }
    await p.screenshot({ path: `${OUT}/shots/raw/wf-${slug}.png` });
    ok++; console.log('OK  wf-' + slug);
  } catch (e) { bad.push(slug + ' ' + e.message.split('\n')[0].slice(0, 40)); }
}
console.log(`\ncaptured ${ok}/25`); if (bad.length) console.log('failed:', bad.join(' | '));
await b.close();
