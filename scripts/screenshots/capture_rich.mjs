// Interaction-aware captures. The passive landing state of a screen is rarely
// the instructive state: the value is in the opened cell, the expanded panel,
// the visible dropdown. Each shot declares steps that run before the shutter.
import { chromium } from 'playwright';
const OUT = process.env.OUT, BASE = 'https://app.vaquill.ai';
const only = process.argv[2];

const SHOTS = [
  {
    name: 'matrix-grid', url: '/matrix/0c1a1400-d990-4ac6-bab0-61753a9541dc', wait: 6500,
    // Open a populated cell so answer, reasoning and citations are visible.
    // Cells expose data-cell-id; pick the first with real extracted text.
    steps: async (p) => {
      const cells = p.locator('[data-cell-id]');
      const n = await cells.count();
      for (let i = 0; i < n; i++) {
        const c = cells.nth(i);
        const t = (await c.innerText().catch(() => '')).trim();
        if (t && t !== '\u2014' && t.length > 3) {
          await c.click({ timeout: 6000 }).catch(() => {});
          await p.waitForTimeout(3500);
          break;
        }
      }
    },
  },
  {
    name: 'review-hub', url: '/legal-tools', wait: 5000,
    // Expand Advanced options so playbook / markup / negotiation round show.
    steps: async (p) => {
      const adv = p.locator('text=Advanced options').first();
      if (await adv.count()) { await adv.click({ timeout: 8000 }).catch(()=>{}); await p.waitForTimeout(1800); }
    },
  },
  {
    name: 'playbook-detail', url: '/playbooks/cfb7dd3d-6369-43a8-9faf-917d941a4942', wait: 6500,
    steps: async (p) => {
      for (const t of ['Positions','Clauses','Edit']) {
        const el = p.locator(`text=${t}`).first();
        if (await el.count()) { await el.click({ timeout: 5000 }).catch(()=>{}); await p.waitForTimeout(2000); break; }
      }
    },
  },
  { name: 'draft-editor', url: '/drafting/b1f2b418-41a5-494c-876b-13e144674a73', wait: 7000, steps: async () => {} },
];

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
  if (only && s.name !== only) continue;
  try {
    await p.goto(BASE + s.url, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForTimeout(s.wait);
    await p.keyboard.press('Escape').catch(()=>{});
    await s.steps(p);
    await p.evaluate(DECHROME); await p.waitForTimeout(800);
    await p.screenshot({ path: `${OUT}/shots/raw/${s.name}.png` });
    console.log('OK  ' + s.name);
  } catch (e) { console.log('ERR ' + s.name + ' ' + e.message.split('\n')[0].slice(0,70)); }
}
await b.close();
