// Research house style: ship lossless-ish WebP (~q82) at <=150KB, max 1712px
// asset width (Google), which renders at 856px. AVIF is avoided: its edge
// softening degrades small UI text.
import sharp from 'sharp';
import fs from 'fs';
const RAW = process.env.OUT + '/shots/raw', OUTD = process.env.OUT + '/shots/web';
fs.mkdirSync(OUTD, { recursive: true });
const files = fs.readdirSync(RAW).filter(f => f.endsWith('.png') && !f.startsWith('_'));
let total = 0;
for (const f of files) {
  const src = `${RAW}/${f}`, dst = `${OUTD}/${f.replace(/\.png$/, '.webp')}`;
  let q = 82, buf;
  for (;;) {
    buf = await sharp(src).resize({ width: 1712, withoutEnlargement: true }).webp({ quality: q, effort: 6 }).toBuffer();
    if (buf.length <= 150 * 1024 || q <= 58) break;
    q -= 6;
  }
  fs.writeFileSync(dst, buf);
  const before = fs.statSync(src).size;
  total += buf.length;
  console.log(`${f.replace('.png','').padEnd(20)} ${(before/1024).toFixed(0).padStart(4)}KB -> ${(buf.length/1024).toFixed(0).padStart(3)}KB  q${q}`);
}
console.log(`\n${files.length} images, ${(total/1024).toFixed(0)}KB total`);
