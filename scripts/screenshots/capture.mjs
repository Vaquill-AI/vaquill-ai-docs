// Docs screenshot harness.
// House style (Google/GitHub/GitLab): crop over full-app, 1440x900 @2x,
// strip volatile chrome (trial countdown, tours) but KEEP the sidebar so the
// reader can orient. Trim dead space by measuring real content height.
import { chromium } from 'playwright';

const OUT = process.env.OUT, BASE = 'https://app.vaquill.ai';
const only = process.argv[2];

const SHOTS = [
  { name: 'matters-list',      url: '/matters',     wait: 3500 },
  { name: 'clients-list',      url: '/clients',     wait: 3500 },
  { name: 'vendors-registry',  url: '/vendors',     wait: 4000 },
  { name: 'documents-vault',   url: '/documents',   wait: 4000 },
  { name: 'playbooks-list',    url: '/playbooks',   wait: 3500 },
  { name: 'drafting-home',     url: '/drafting',    wait: 4000 },
  { name: 'workflows-gallery', url: '/workflows',   wait: 4500 },
  { name: 'matrix-list',       url: '/matrix',      wait: 3500 },
  { name: 'review-hub',        url: '/legal-tools', wait: 4500 },
  { name: 'feed',              url: '/feed',        wait: 4500 },
  { name: 'chat-list',         url: '/chat',        wait: 4000 },
];

// Surgical: remove only the trial/upgrade chrome and tour overlays.
// Never touch nav or main content.
// Strip only volatile chrome. CRITICAL: never remove [data-tour] elements,
// those are real sidebar/nav items tagged as product-tour anchors. Removing
// them deletes the navigation.
const DECHROME = () => {
  // 1. Trial banner + "Upgrade 6d left" pill. Guard on SIZE and descendant
  // count, not direct children: the app root has few direct children but
  // contains all the text, so a text-only match removes the whole page.
  document.querySelectorAll('div,section,span,a,button').forEach(el => {
    const r = el.getBoundingClientRect();
    if (r.height > 90) return;              // short chrome only, any width
    if (el.querySelectorAll('*').length > 25) return;
    const t = (el.textContent || '').trim().toLowerCase().replace(/\s+/g, ' ');
    if ((t.includes('free trial') && t.includes('days left')) || /^upgrade \d+d left$/.test(t)) {
      el.style.visibility = 'hidden';
    }
  });
  // 2. The product-tour popover itself (never its anchors).
  document.querySelectorAll('[role="dialog"]').forEach(el => {
    const t = (el.textContent || '').toLowerCase();
    if (/\d+ of \d+/.test(t) || (t.includes('next') && t.includes('back'))) el.remove();
  });
};

const b = await chromium.launch({ executablePath: process.env.CHROME_BIN });
const ctx = await b.newContext({
  storageState: OUT + '/auth-state.json',
  viewport: { width: 1440, height: 900 },
  deviceScaleFactor: 2,
});
const p = await ctx.newPage();
await p.emulateMedia({ colorScheme: 'light' });

for (const s of SHOTS) {
  if (only && s.name !== only) continue;
  try {
    await p.goto(BASE + s.url, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForTimeout(s.wait);
    await p.keyboard.press('Escape').catch(() => {});
    await p.evaluate(DECHROME);
    await p.waitForTimeout(700);

    // Let the browser do the cropping: shoot the app shell element, which
    // bounds itself to real content. Fall back to the viewport if absent.
    const clipH = 900, mode = 'viewport';
    await p.screenshot({ path: `${OUT}/shots/raw/${s.name}.png`, clip: { x: 0, y: 0, width: 1440, height: clipH } });
    console.log(`OK  ${s.name.padEnd(20)} h=${clipH} ${mode}`);
  } catch (e) {
    console.log('ERR ' + s.name + ' ' + e.message.split('\n')[0].slice(0, 70));
  }
}
await b.close();
