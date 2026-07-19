import { chromium } from 'playwright';
const [,, htmlPath, outPng, theme='light', scale='2'] = process.argv;
const b = await chromium.launch();
const p = await b.newPage({ deviceScaleFactor: Number(scale) });
await p.emulateMedia({ colorScheme: theme });
await p.goto('file://' + htmlPath, { waitUntil: 'networkidle' });
if (theme) await p.evaluate(t => document.documentElement.setAttribute('data-theme', t), theme);
await p.evaluate(() => document.fonts.ready);
await p.waitForTimeout(400);
await p.screenshot({ path: outPng, fullPage: true });
// also report the poster pixel size
const box = await p.$eval('.poster', el => ({w: el.scrollWidth, h: el.scrollHeight}));
console.log('poster', theme, box.w+'x'+box.h);
await b.close();
