#!/usr/bin/env python3
"""Builds the PWA from ../yokdil-cep-kocu.html. Run: python3 build.py"""
import hashlib, json, pathlib
here = pathlib.Path(__file__).parent
src = (here.parent / 'yokdil-cep-kocu.html').read_text(encoding='utf8')
assert src.startswith('<meta charset="utf-8">\n')
body = src[len('<meta charset="utf-8">\n'):]
head = '''<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="YÖKDİL kelime kartları, test, gramer ve sözlük. İnternetsiz çalışır.">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" href="icons/icon-192.png" type="image/png">
<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Kelime Durağı">
<meta name="robots" content="noindex, nofollow">
'''
sw_reg = '''<script>
/* PWA: offline cache; a new version activates on the next launch */
if ('serviceWorker' in navigator && location.protocol !== 'file:') {
  addEventListener('load', () => { navigator.serviceWorker.register('sw.js').catch(() => {}); });
  let reloaded = false;
  navigator.serviceWorker.addEventListener('controllerchange', () => {
    if (reloaded || !navigator.serviceWorker.controller) return; reloaded = true;
    try { typeof toastMsg === 'function' && toastMsg('Uygulama güncellendi.'); } catch (e) {}
  });
}
</script>
'''
index = head + body + '\n' + sw_reg + '</html>\n'
(here / 'index.html').write_text(index, encoding='utf8')
assets = ['./', 'index.html', 'manifest.webmanifest', 'icons/icon-192.png', 'icons/icon-512.png', 'icons/maskable-512.png', 'icons/apple-touch-icon.png']
h = hashlib.sha256()
for a in assets[1:]:
    h.update((here / a).read_bytes())
version = h.hexdigest()[:10]
sw = '''/* Kelime Durağı service worker. CACHE changes whenever any asset changes. */
const CACHE = 'kelime-duragi-%s';
const ASSETS = %s;
self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS.map(u => new Request(u, { cache: 'reload' })))).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k.startsWith('kelime-duragi-') && k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET' || new URL(req.url).origin !== location.origin) return;
  e.respondWith(
    caches.match(req, { ignoreSearch: true }).then(hit => hit || fetch(req).catch(() =>
      req.mode === 'navigate' ? caches.match('index.html') : Response.error()))
  );
});
''' % (version, json.dumps(assets))
(here / 'sw.js').write_text(sw, encoding='utf8')
print('built', version, len(index) // 1024, 'KB')
