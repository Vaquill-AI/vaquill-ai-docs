import { chromium } from 'playwright';
import fs from 'fs';
const b = await chromium.launch({ executablePath: process.env.CHROME_BIN });
const ctx = await b.newContext({ viewport: { width: 1440, height: 900 } });
const p = await ctx.newPage();
await p.goto('https://app.vaquill.ai/auth/login', { waitUntil: 'domcontentloaded', timeout: 60000 });
await p.waitForTimeout(3000);
console.log('step: login page');
await p.fill('input[type="email"]', process.env.VQ_USER);
await p.click('button:has-text("Continue")');
console.log('step: email submitted');
await p.waitForSelector('input[type="password"]', { timeout: 30000 });
await p.fill('input[type="password"]', process.env.VQ_PASS);
await p.click('button[type="submit"], button:has-text("Sign in"), button:has-text("Continue")');
console.log('step: password submitted');
await p.waitForURL(u => !u.pathname.includes('/auth/'), { timeout: 90000 });
console.log('step: landed', p.url());
await p.waitForTimeout(5000);
const store = await p.evaluate(() => {
  const out = {};
  for (let i = 0; i < localStorage.length; i++) {
    const k = localStorage.key(i);
    out[k] = (localStorage.getItem(k)||'').slice(0,40);
  }
  return out;
});
let token = null;
for (const v of Object.values(store)) {
  try { const j = JSON.parse(v); if (j.access_token) token = j.access_token; } catch {}
}
await ctx.storageState({ path: process.env.OUT + '/auth-state.json' });
fs.writeFileSync(process.env.OUT + '/token.txt', token || '');
console.log('token:', token ? 'captured len=' + token.length : 'NOT FOUND');
console.log('keys:', Object.keys(store).join(','));
await b.close();
