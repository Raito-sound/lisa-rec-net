/* Language preference and first-visit routing for lisa-rec.net / raito.studio.
   - Reads <html lang> and <link rel="alternate" hreflang="..."> of the current page.
   - A stored choice (set by the header switch or ?lang=) always wins.
   - Without a stored choice, the browser language decides once, then is stored.
   - Never redirects crawlers, automated browsers, or visitors arriving from this site. */
(function () {
  var KEY = 'site-lang';
  var page = (document.documentElement.lang || '').slice(0, 2).toLowerCase();
  var alternates = {};
  var links = document.querySelectorAll('link[rel="alternate"][hreflang]');
  for (var i = 0; i < links.length; i++) {
    var code = links[i].getAttribute('hreflang');
    if (code && code !== 'x-default') alternates[code.slice(0, 2).toLowerCase()] = links[i].href;
  }
  function store(value) { try { localStorage.setItem(KEY, value); } catch (e) {} }
  function stored() { try { return localStorage.getItem(KEY); } catch (e) { return null; } }

  var switches = document.querySelectorAll('[data-lang-switch]');
  for (var s = 0; s < switches.length; s++) {
    switches[s].addEventListener('click', function () { store(this.getAttribute('data-lang-switch')); });
  }

  var params = new URLSearchParams(location.search);
  if (params.has('lang')) { store(params.get('lang').slice(0, 2).toLowerCase()); return; }
  if (navigator.webdriver) return;
  if (/bot|crawl|spider|slurp|preview|fetch|lighthouse|headless|archive|scrapy|python-requests|curl|wget/i.test(navigator.userAgent || '')) return;
  try { if (document.referrer && new URL(document.referrer).origin === location.origin) return; } catch (e) {}

  var preferred = stored();
  if (!preferred) {
    var candidates = navigator.languages && navigator.languages.length ? navigator.languages : [navigator.language || ''];
    for (var c = 0; c < candidates.length; c++) {
      var base = (candidates[c] || '').slice(0, 2).toLowerCase();
      if (base === 'ja' || base === 'en') { preferred = base; break; }
    }
    if (!preferred) return;
    store(preferred);
  }
  if (preferred !== page && alternates[preferred] && alternates[preferred] !== location.href) {
    location.replace(alternates[preferred]);
  }
})();
