import { chromium } from 'playwright';
import fs from 'fs';
const OUT = process.env.OUT, BASE = 'https://app.vaquill.ai';
const SHOTS = JSON.parse(fs.readFileSync(OUT + '/detail_urls.json', 'utf8'));
const DECHROME = () => {
  document.querySelectorAll('div,section,span,a,button').forEach(el => {
    const r = el.getBoundingClientRect();
    if (r.height > 90) return;
    if (el.querySelectorAll('*').length > 25) return;
    const t = (el.textContent || '').trim().toLowerCase().replace(/\s+/g, ' ');
    if ((t.includes('free trial') && t.includes('days left')) || /^upgrade \d+d left$/.test(t)) el.style.visibility = 'hidden';
  });
  document.querySelectorAll('[role="dialog"]').forEach(el => {
    const t = (el.textContent || '').toLowerCase();
    if (/\d+ of \d+/.test(t) || (t.includes('next') && t.includes('back'))) el.remove();
  });
};
const b = await chromium.launch({ executablePath: process.env.CHROME_BIN });
const ctx = await b.newContext({ storageState: OUT + '/auth-state.json', viewport: { width: 1440, height: 900 }, deviceScaleFactor: 2 });
const p = await ctx.newPage(); await p.emulateMedia({ colorScheme: 'light' });
for (const s of SHOTS) {
  try {
    await p.goto(BASE + s.url, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForTimeout(s.wait);
    await p.keyboard.press('Escape').catch(()=>{});
    await p.evaluate(DECHROME); await p.waitForTimeout(700);
    await p.screenshot({ path: `${OUT}/shots/raw/${s.name}.png` });
    const title = await p.title();
    console.log(`OK  ${s.name.padEnd(20)} ${title.slice(0,45)}`);
  } catch (e) { console.log('ERR ' + s.name + ' ' + e.message.split('\n')[0].slice(0,60)); }
}
await b.close();
